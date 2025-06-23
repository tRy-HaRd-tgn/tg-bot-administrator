/**
 * JavaScript для модального окна настройки расписания публикаций
 */
class ScheduleModal {
  constructor() {
    this.modal = null;
    this.currentSettings = null;
    this.onSettingsChanged = null;
    this.selectedDates = new Set();
    this.currentDate = new Date();
    this.timeMode = "single";
    this.individualTimes = {};
    this.init();
  }

  init() {
    this.modal = document.getElementById("scheduleModal");
    if (!this.modal) {
      console.warn("Schedule modal not found");
      return;
    }

    this.bindEvents();
    this.renderCalendar();
    this.updatePreview();
  }

  bindEvents() {
    // Изменение периода
    ["scheduleStartDate", "scheduleEndDate"].forEach((id) => {
      const element = document.getElementById(id);
      if (element) {
        element.addEventListener("change", () => {
          this.validatePeriod();
          this.renderCalendar();
          this.updatePreview();
        });
      }
    });

    // Кнопки управления датами
    this.bindButton("selectAllDatesBtn", () => this.selectAllDates());
    this.bindButton("clearAllDatesBtn", () => this.clearAllDates());
    this.bindButton("selectWeekendsBtn", () => this.selectWeekends());
    this.bindButton("selectWorkdaysBtn", () => this.selectWorkdays());

    // Навигация по календарю
    this.bindButton("calendarPrevBtn", () => this.navigateCalendar(-1));
    this.bindButton("calendarNextBtn", () => this.navigateCalendar(1));

    // Режим времени
    document.querySelectorAll('input[name="timeMode"]').forEach((radio) => {
      radio.addEventListener("change", () => this.handleTimeModeChange());
    });

    // Глобальное время
    const globalTimeInput = document.getElementById("globalTime");
    if (globalTimeInput) {
      globalTimeInput.addEventListener("change", () => this.updatePreview());
    }

    // Кнопка сохранения
    this.bindButton("saveScheduleBtn", () => this.saveSettings());

    // Сброс при закрытии модала
    if (this.modal) {
      this.modal.addEventListener("hidden.bs.modal", () => this.resetModal());
    }
  }

  bindButton(id, handler) {
    const button = document.getElementById(id);
    if (button) {
      button.addEventListener("click", handler);
    }
  }

  validatePeriod() {
    const startDate = document.getElementById("scheduleStartDate");
    const endDate = document.getElementById("scheduleEndDate");
    const startError = document.getElementById("scheduleStartDateError");
    const endError = document.getElementById("scheduleEndDateError");

    let isValid = true;

    this.clearError(startDate, startError);
    this.clearError(endDate, endError);

    if (!startDate.value) {
      this.showError(startDate, startError, "Дата начала обязательна");
      isValid = false;
    }

    if (startDate.value && endDate.value) {
      const start = new Date(startDate.value);
      const end = new Date(endDate.value);

      if (start > end) {
        this.showError(
          endDate,
          endError,
          "Дата окончания не может быть раньше даты начала"
        );
        isValid = false;
      }
    }

    // Очищаем выбранные даты если период изменился
    if (!isValid) {
      this.selectedDates.clear();
      this.updateSelectedDatesInfo();
    }

    return isValid;
  }

  renderCalendar() {
    const calendarContainer = document.getElementById("scheduleCalendar");
    if (!calendarContainer) return;

    const startDateStr = document.getElementById("scheduleStartDate").value;
    const endDateStr = document.getElementById("scheduleEndDate").value;

    if (!startDateStr) {
      this.currentDate = new Date();
      this.currentDate.setHours(0, 0, 0, 0);
      calendarContainer.innerHTML =
        '<div class="text-center text-muted">Сначала выберите дату начала</div>';
      return;
    }

    const startDate = new Date(startDateStr);
    const endDate = endDateStr ? new Date(endDateStr) : null;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    startDate.setHours(0, 0, 0, 0);
    if (endDate) endDate.setHours(0, 0, 0, 0);

    // Устанавливаем текущий месяц на основе даты начала если это первый рендер
    if (this.currentDate < startDate) {
      this.currentDate = new Date(startDate);
    }

    const year = this.currentDate.getFullYear();
    const month = this.currentDate.getMonth();

    const monthNames = [
      "Январь",
      "Февраль",
      "Март",
      "Апрель",
      "Май",
      "Июнь",
      "Июль",
      "Август",
      "Сентябрь",
      "Октябрь",
      "Ноябрь",
      "Декабрь",
    ];

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay() === 0 ? 7 : firstDay.getDay();

    let calendarHTML = `
            <div class="calendar-header">
                <button type="button" class="calendar-nav-btn" id="calendarPrevBtn">
                    <i class="fa-solid fa-chevron-left"></i>
                </button>
                <div class="calendar-month-year">${monthNames[month]} ${year}</div>
                <button type="button" class="calendar-nav-btn" id="calendarNextBtn">
                    <i class="fa-solid fa-chevron-right"></i>
                </button>
            </div>
            <div class="calendar-grid">
        `;

    // Заголовки дней недели
    const dayHeaders = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
    dayHeaders.forEach((dayName) => {
      calendarHTML += `<div class="calendar-day-header">${dayName}</div>`;
    });

    // Пустые ячейки для дней предыдущего месяца
    for (let i = 1; i < startingDayOfWeek; i++) {
      calendarHTML += '<div class="calendar-day other-month"></div>';
    }

    // Дни текущего месяца
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      date.setHours(0, 0, 0, 0);
      const dateStr = toLocalDateString(date);

      let classes = ["calendar-day"];
      let clickable = true;

      // Проверяем, попадает ли дата в разрешенный период
      if (date < startDate || (endDate && date > endDate)) {
        classes.push("other-month");
        clickable = false;
      }

      // Проверяем, не в прошлом ли дата
      if (date < today) {
        classes.push("past");
        clickable = false;
      }

      // Если это будущий день (после today)
      if (date > today) {
        classes.push("future");
      }

      // Проверяем, сегодня ли это
      if (date.getTime() === today.getTime()) {
        classes.push("today");
      }

      // Проверяем, выбрана ли дата
      if (this.selectedDates.has(dateStr)) {
        classes.push("selected");
      }

      calendarHTML += `
                <div ${
                  clickable ? " style=color:black" : ""
                } class="${classes.join(" ")}${
        clickable ? " clickable" : ""
      }" data-date="${dateStr}">
                    ${day}
                </div>
            `;
    }

    calendarHTML += "</div>";
    calendarContainer.innerHTML = calendarHTML;

    // Повторно привязываем события навигации
    this.bindButton("calendarPrevBtn", () => this.navigateCalendar(-1));
    this.bindButton("calendarNextBtn", () => this.navigateCalendar(1));

    // Назначаем обработчики клика для кликабельных дат
    calendarContainer
      .querySelectorAll(".calendar-day.clickable")
      .forEach((dayEl) => {
        dayEl.addEventListener("click", (e) => {
          const dateStr = dayEl.getAttribute("data-date");
          this.toggleDate(dateStr);
        });
      });

    this.updateSelectedDatesInfo();
  }

  navigateCalendar(direction) {
    this.currentDate.setMonth(this.currentDate.getMonth() + direction);
    this.renderCalendar();
  }

  toggleDate(dateStr) {
    if (this.selectedDates.has(dateStr)) {
      this.selectedDates.delete(dateStr);
      delete this.individualTimes[dateStr];
    } else {
      this.selectedDates.add(dateStr);
      if (this.timeMode === "multiple") {
        this.individualTimes[dateStr] = "12:00";
      }
    }

    this.renderCalendar();
    this.updateIndividualTimes();
    this.updatePreview();
  }

  selectAllDates() {
    const startDateStr = document.getElementById("scheduleStartDate").value;
    const endDateStr = document.getElementById("scheduleEndDate").value;

    if (!startDateStr) return;

    const startDate = new Date(startDateStr);
    const endDate = endDateStr
      ? new Date(endDateStr)
      : new Date(startDate.getTime() + 30 * 24 * 60 * 60 * 1000); // 30 дней по умолчанию
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    this.selectedDates.clear();
    this.individualTimes = {};

    for (
      let date = new Date(Math.max(startDate.getTime(), today.getTime()));
      date <= endDate;
      date.setDate(date.getDate() + 1)
    ) {
      const dateStr = toLocalDateString(date);
      this.selectedDates.add(dateStr);
      if (this.timeMode === "multiple") {
        this.individualTimes[dateStr] = "12:00";
      }
    }

    this.renderCalendar();
    this.updateIndividualTimes();
    this.updatePreview();
  }

  clearAllDates() {
    this.selectedDates.clear();
    this.individualTimes = {};
    this.renderCalendar();
    this.updateIndividualTimes();
    this.updatePreview();
  }

  selectWeekends() {
    this.selectDaysByType((date) => date.getDay() === 0 || date.getDay() === 6);
  }

  selectWorkdays() {
    this.selectDaysByType((date) => date.getDay() >= 1 && date.getDay() <= 5);
  }

  selectDaysByType(dayFilter) {
    const startDateStr = document.getElementById("scheduleStartDate").value;
    const endDateStr = document.getElementById("scheduleEndDate").value;

    if (!startDateStr) return;

    const startDate = new Date(startDateStr);
    const endDate = endDateStr
      ? new Date(endDateStr)
      : new Date(startDate.getTime() + 30 * 24 * 60 * 60 * 1000);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    this.selectedDates.clear();
    this.individualTimes = {};

    for (
      let date = new Date(Math.max(startDate.getTime(), today.getTime()));
      date <= endDate;
      date.setDate(date.getDate() + 1)
    ) {
      if (dayFilter(date)) {
        const dateStr = toLocalDateString(date);
        this.selectedDates.add(dateStr);
        if (this.timeMode === "multiple") {
          this.individualTimes[dateStr] = "12:00";
        }
      }
    }

    this.renderCalendar();
    this.updateIndividualTimes();
    this.updatePreview();
  }

  updateSelectedDatesInfo() {
    const countElement = document.getElementById("selectedDatesCount");
    if (countElement) {
      countElement.textContent = this.selectedDates.size;
    }
  }

  handleTimeModeChange() {
    const selectedMode = document.querySelector(
      'input[name="timeMode"]:checked'
    );
    if (!selectedMode) return;

    this.timeMode = selectedMode.value;

    const singleTimeSetting = document.getElementById("singleTimeSetting");
    const multipleTimeSetting = document.getElementById("multipleTimeSetting");

    if (this.timeMode === "single") {
      singleTimeSetting.style.display = "block";
      multipleTimeSetting.style.display = "none";
      this.individualTimes = {};
    } else {
      singleTimeSetting.style.display = "none";
      multipleTimeSetting.style.display = "block";

      // Инициализируем времена для выбранных дат
      this.selectedDates.forEach((dateStr) => {
        if (!this.individualTimes[dateStr]) {
          this.individualTimes[dateStr] = "12:00";
        }
      });
      this.updateIndividualTimes();
    }

    this.updatePreview();
  }

  updateIndividualTimes() {
    const container = document.getElementById("individualTimesContainer");
    if (!container) return;

    if (this.selectedDates.size === 0) {
      container.innerHTML =
        '<div class="no-dates-selected"><i class="fa-solid fa-info-circle me-2"></i>Сначала выберите даты публикаций</div>';
      return;
    }

    const sortedDates = Array.from(this.selectedDates).sort();

    container.innerHTML = sortedDates
      .map((dateStr) => {
        const date = new Date(dateStr);
        const formattedDate = date.toLocaleDateString("ru-RU", {
          weekday: "short",
          day: "numeric",
          month: "short",
        });

        return `
                <div class="individual-time-item">
                    <div class="individual-time-date">${formattedDate}</div>
                    <input 
                        type="time" 
                        class="individual-time-input" 
                        value="${this.individualTimes[dateStr] || "12:00"}"
                        onchange="scheduleModal.updateIndividualTime('${dateStr}', this.value)"
                    >
                </div>
            `;
      })
      .join("");
  }

  updateIndividualTime(dateStr, time) {
    this.individualTimes[dateStr] = time;
    this.updatePreview();
  }

  updatePreview() {
    const previewContainer = document.getElementById("schedulePreview");
    if (!previewContainer) return;

    if (this.selectedDates.size === 0) {
      previewContainer.innerHTML =
        '<div class="no-schedule-preview"><i class="fa-solid fa-calendar-xmark me-2"></i>Выберите даты и время для отображения превью</div>';
      return;
    }

    const sortedDates = Array.from(this.selectedDates).sort();
    const globalTime = document.getElementById("globalTime")?.value || "12:00";

    const previewItems = sortedDates
      .map((dateStr) => {
        const date = new Date(dateStr);
        const formattedDate = date.toLocaleDateString("ru-RU", {
          weekday: "long",
          day: "numeric",
          month: "long",
          year: "numeric",
        });

        const time =
          this.timeMode === "single"
            ? globalTime
            : this.individualTimes[dateStr] || "12:00";

        return `
                <div class="schedule-preview-item">
                    <div class="schedule-preview-date">${formattedDate}</div>
                    <div class="schedule-preview-time">${time} UTC</div>
                </div>
            `;
      })
      .join("");

    previewContainer.innerHTML = previewItems;
  }

  validateSettings() {
    if (!this.validatePeriod()) {
      return false;
    }

    if (this.selectedDates.size === 0) {
      this.showNotification(
        "error",
        "Ошибка",
        "Необходимо выбрать хотя бы одну дату для публикации"
      );
      return false;
    }

    // Проверяем времена для множественного режима
    if (this.timeMode === "multiple") {
      for (const dateStr of this.selectedDates) {
        if (!this.individualTimes[dateStr]) {
          this.showNotification(
            "error",
            "Ошибка",
            "Не указано время для всех выбранных дат"
          );
          return false;
        }
      }
    }

    return true;
  }

  saveSettings() {
    console.log("Сохранение настроек расписания...");

    if (!this.validateSettings()) {
      return;
    }

    try {
      const startDate = document.getElementById("scheduleStartDate").value;
      const endDate = document.getElementById("scheduleEndDate").value;
      const globalTime =
        document.getElementById("globalTime")?.value || "12:00";

      const settings = {
        type: "schedule",
        startDate: startDate,
        endDate: endDate || null,
        selectedDates: Array.from(this.selectedDates),
        timeMode: this.timeMode,
        globalTime: globalTime,
        individualTimes: { ...this.individualTimes },
        createdAt: new Date().toISOString(),
      };

      this.currentSettings = settings;

      if (this.onSettingsChanged) {
        this.onSettingsChanged(settings);
      }

      // Закрываем модальное окно
      const modalInstance = bootstrap.Modal.getInstance(this.modal);
      if (modalInstance) {
        modalInstance.hide();
      }

      this.showNotification(
        "success",
        "Успех",
        "Расписание публикаций сохранено"
      );
    } catch (error) {
      console.error("Ошибка при сохранении настроек расписания:", error);
      this.showNotification(
        "error",
        "Ошибка",
        "Не удалось сохранить настройки расписания"
      );
    }
  }

  getCurrentSettings() {
    return this.currentSettings;
  }

  loadSettings(settings) {
    if (!settings || settings.type !== "schedule") return;

    try {
      // Загружаем основные настройки
      if (settings.startDate) {
        const startDateInput = document.getElementById("scheduleStartDate");
        if (startDateInput) startDateInput.value = settings.startDate;
      }

      if (settings.endDate) {
        const endDateInput = document.getElementById("scheduleEndDate");
        if (endDateInput) endDateInput.value = settings.endDate;
      }

      // Загружаем выбранные даты
      this.selectedDates = new Set(settings.selectedDates || []);

      // Загружаем режим времени
      this.timeMode = settings.timeMode || "single";
      const timeModeRadio = document.querySelector(
        `input[name="timeMode"][value="${this.timeMode}"]`
      );
      if (timeModeRadio) {
        timeModeRadio.checked = true;
      }

      // Загружаем глобальное время
      if (settings.globalTime) {
        const globalTimeInput = document.getElementById("globalTime");
        if (globalTimeInput) globalTimeInput.value = settings.globalTime;
      }

      // Загружаем индивидуальные времена
      this.individualTimes = { ...(settings.individualTimes || {}) };

      this.currentSettings = settings;

      // Обновляем интерфейс
      this.handleTimeModeChange();
      this.renderCalendar();
      this.updatePreview();
    } catch (error) {
      console.error("Ошибка при загрузке настроек расписания:", error);
    }
  }

  resetModal() {
    this.selectedDates.clear();
    this.individualTimes = {};
    this.timeMode = "single";
    this.currentSettings = null;
    this.currentDate = new Date();
    this.currentDate.setHours(0, 0, 0, 0);

    // Сбрасываем поля формы
    const inputs = this.modal.querySelectorAll("input");
    inputs.forEach((input) => {
      if (input.type === "radio" && input.value === "single") {
        input.checked = true;
      } else if (input.type === "radio") {
        input.checked = false;
      } else if (input.type === "time") {
        input.value = "12:00";
      } else {
        input.value = "";
      }
      input.classList.remove("is-invalid");
    });

    // Очищаем ошибки
    const errorElements = this.modal.querySelectorAll(".invalid-feedback");
    errorElements.forEach((element) => {
      element.textContent = "";
    });

    this.handleTimeModeChange();
    this.renderCalendar();
    this.updatePreview();
  }

  showError(input, errorElement, message) {
    input.classList.add("is-invalid");
    if (errorElement) {
      errorElement.textContent = message;
    }
  }

  clearError(input, errorElement) {
    input.classList.remove("is-invalid");
    if (errorElement) {
      errorElement.textContent = "";
    }
  }

  showNotification(type, title, message) {
    if (typeof Utils !== "undefined" && Utils.showNotification) {
      Utils.showNotification(type, title, message);
    } else {
      console.log(`${type.toUpperCase()}: ${title} - ${message}`);
    }
  }

  // Методы для внешнего использования
  show() {
    const modalInstance = new bootstrap.Modal(this.modal);
    modalInstance.show();
  }

  hide() {
    const modalInstance = bootstrap.Modal.getInstance(this.modal);
    if (modalInstance) {
      modalInstance.hide();
    }
  }

  setCallback(callback) {
    this.onSettingsChanged = callback;
  }

  getSettings() {
    return this.currentSettings;
  }

  clearSettings() {
    this.currentSettings = null;
    this.resetModal();
  }
}

// Инициализация при загрузке DOM
document.addEventListener("DOMContentLoaded", function () {
  window.scheduleModal = new ScheduleModal();
  console.log("ScheduleModal инициализирован");
});

// Добавляю функцию для локального форматирования даты
function toLocalDateString(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
