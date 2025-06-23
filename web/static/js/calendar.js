/**
 * JavaScript для страницы календаря кампаний
 * Переработан для работы с UTC временем
 */
class CalendarManager {
  constructor() {
    this.currentDate = new Date();
    this.selectedDate = null;
    this.events = [];
    this.utcTimeInterval = null;

    this.init();
  }

  init() {
    // Инициализация календаря
    this.initializeCalendar();

    // Загрузка статистики
    this.loadCalendarStats();

    // Загрузка событий
    this.loadCalendarEvents();

    // Загрузка сегодняшних кампаний
    this.loadTodayCampaigns();

    // Обрабатываем изменение состояния сайдбара
    document.addEventListener(
      "sidebarToggled",
      function (e) {
        setTimeout(() => {
          this.renderCalendar();
        }, 300);
      }.bind(this)
    );

    // Добавляем запуск UTC часов
    this.startUTCClock();

    // Добавляем обработчики для модальных окон
    this.setupModalClosers();
  }

  // Новый метод для запуска часов UTC
  startUTCClock() {
    this.updateUTCTime();
    this.utcTimeInterval = setInterval(() => {
      this.updateUTCTime();
    }, 1000);
  }

  // Обновляет отображение текущего UTC времени
  updateUTCTime() {
    const now = new Date();
    const utcTime = now.toLocaleTimeString("ru-RU", {
      timeZone: "UTC",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });

    const utcDate = now.toLocaleDateString("ru-RU", {
      timeZone: "UTC",
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });

    // Обновляем все элементы с UTC временем
    const utcElements = document.querySelectorAll(".utc-time");
    utcElements.forEach((el) => {
      el.textContent = `${utcDate}, ${utcTime}`;
    });
  }

  initializeCalendar() {
    this.renderCalendar();

    // Обработчики навигации
    document.getElementById("prevMonth").addEventListener("click", () => {
      this.currentDate.setMonth(this.currentDate.getMonth() - 1);
      this.renderCalendar();
      this.loadCalendarEvents();
    });

    document.getElementById("nextMonth").addEventListener("click", () => {
      this.currentDate.setMonth(this.currentDate.getMonth() + 1);
      this.renderCalendar();
      this.loadCalendarEvents();
    });

    document.getElementById("todayBtn").addEventListener("click", () => {
      this.currentDate = new Date();
      this.renderCalendar();
      this.loadCalendarEvents();
    });
  }

  renderCalendar() {
    const year = this.currentDate.getUTCFullYear();
    const month = this.currentDate.getUTCMonth();

    // Обновляем заголовок
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

    document.getElementById(
      "currentMonth"
    ).textContent = `${monthNames[month]} ${year}`;

    // Генерируем календарную сетку
    const firstDay = new Date(Date.UTC(year, month, 1));
    const lastDay = new Date(Date.UTC(year, month + 1, 0));
    const daysInMonth = lastDay.getUTCDate();
    const startingDayOfWeek =
      firstDay.getUTCDay() === 0 ? 7 : firstDay.getUTCDay(); // Понедельник = 1

    const calendarGrid = document.getElementById("calendarGrid");
    calendarGrid.innerHTML = "";

    // Добавляем заголовки дней недели
    const dayHeaders = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
    dayHeaders.forEach((dayName) => {
      const dayHeader = document.createElement("div");
      dayHeader.className = "calendar-day-header";
      dayHeader.textContent = dayName;
      calendarGrid.appendChild(dayHeader);
    });

    // Добавляем пустые ячейки для дней предыдущего месяца
    for (let i = 1; i < startingDayOfWeek; i++) {
      const emptyDay = document.createElement("div");
      emptyDay.className = "calendar-day empty";
      calendarGrid.appendChild(emptyDay);
    }

    // Добавляем дни текущего месяца
    const today = new Date();
    const todayDateStr = today.toISOString().split("T")[0];

    for (let day = 1; day <= daysInMonth; day++) {
      const dateObj = new Date(Date.UTC(year, month, day));
      const dateStr = dateObj.toISOString().split("T")[0];

      const dayEl = document.createElement("div");
      dayEl.className = "calendar-day";
      dayEl.dataset.date = dateStr;

      if (dateStr === todayDateStr) {
        dayEl.classList.add("today");
      }

      const dayNumber = document.createElement("div");
      dayNumber.className = "day-number";
      dayNumber.textContent = day;
      dayEl.appendChild(dayNumber);

      // Контейнер для событий
      const dayEvents = document.createElement("div");
      dayEvents.className = "day-events";
      dayEl.appendChild(dayEvents);

      // Обработчик нажатия на день
      dayEl.addEventListener("click", () =>
        this.showDayEvents(year, month + 1, day)
      );

      calendarGrid.appendChild(dayEl);
    }
  }

  loadCalendarStats() {
    this.showLoading("calendar-stats", true);

    fetch("/api/statistics/campaigns")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Ошибка загрузки статистики");
        }
        return response.json();
      })
      .then((stats) => {
        document.getElementById("active-campaigns").textContent =
          stats.active_campaigns || 0;
        document.getElementById("total-campaigns").textContent =
          stats.total_campaigns || 0;
        this.showLoading("calendar-stats", false);
      })
      .catch((error) => {
        console.error("Ошибка загрузки статистики:", error);
        this.showLoading("calendar-stats", false);
      });
  }
  loadCalendarEvents() {
    this.showLoading("calendar-content", true);

    fetch("/api/calendar/events")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Ошибка загрузки событий");
        }
        return response.json();
      })
      .then((data) => {
        this.showLoading("calendar-content", false);
        this.events = data.events || [];
        console.log("Загружены события календаря:", this.events);

        // Сортируем события по времени
        this.events.sort((a, b) => {
          const timeA = a.time || "00:00";
          const timeB = b.time || "00:00";
          return timeA.localeCompare(timeB);
        });

        this.renderEvents(); // Отрисовываем события
        this.renderTodayCampaigns(); // Отображаем сегодняшние кампании
      })
      .catch((error) => {
        console.error("Ошибка при загрузке событий календаря:", error);
        this.showLoading("calendar-content", false);
        this.showError(
          "calendar-content",
          "Не удалось загрузить события календаря"
        );
      });
  } // Загрузка сегодняшних кампаний
  loadTodayCampaigns() {
    const todayContent = document.getElementById("todayCampaignsContent");

    // Получаем текущую дату в формате YYYY-MM-DD
    const today = new Date();
    const year = today.getUTCFullYear();
    const month = today.getUTCMonth() + 1;
    const day = today.getUTCDate();
    const dateStr = `${year}-${month.toString().padStart(2, "0")}-${day
      .toString()
      .padStart(2, "0")}`;

    // Если события уже загружены
    if (this.events && this.events.length > 0) {
      this.renderTodayCampaigns();
    } else {
      // Ждем загрузки событий
      setTimeout(() => this.loadTodayCampaigns(), 1000);
    }
  }

  // Отображение кампаний на сегодня
  renderTodayCampaigns() {
    const todayContent = document.getElementById("todayCampaignsContent");

    // Получаем текущую дату в формате YYYY-MM-DD
    const today = new Date();
    const year = today.getUTCFullYear();
    const month = today.getUTCMonth() + 1;
    const day = today.getUTCDate();
    const dateStr = `${year}-${month.toString().padStart(2, "0")}-${day
      .toString()
      .padStart(2, "0")}`;

    // Фильтруем события на сегодня
    const todayEvents = this.events.filter((event) => {
      const eventDate = new Date(event.date);
      const eventYear = eventDate.getUTCFullYear();
      const eventMonth = eventDate.getUTCMonth() + 1;
      const eventDay = eventDate.getUTCDate();
      const eventDateStr = `${eventYear}-${eventMonth
        .toString()
        .padStart(2, "0")}-${eventDay.toString().padStart(2, "0")}`;
      return eventDateStr === dateStr;
    });

    // Сортируем события по времени
    todayEvents.sort((a, b) => {
      const timeA = a.time || "00:00";
      const timeB = b.time || "00:00";
      return timeA.localeCompare(timeB);
    });

    // Отображаем события
    if (todayEvents.length === 0) {
      todayContent.innerHTML =
        '<div class="no-campaigns-today">На сегодня нет запланированных кампаний</div>';
    } else {
      let html = "";

      todayEvents.forEach((event) => {
        // Определение класса статуса
        const statusClass =
          {
            active: "bg-success",
            paused: "bg-warning",
            completed: "bg-secondary",
            draft: "bg-light text-dark",
          }[event.status] || "bg-primary";

        html += `
                    <div class="today-campaign-item" onclick="calendarManager.showEventDetails(${JSON.stringify(
                      event
                    ).replace(/"/g, "&quot;")})">
                        <div class="today-campaign-time">
                            <i class="fas fa-clock"></i>
                            ${event.time || "00:00"}
                        </div>
                        <div class="today-campaign-details">
                            <div class="today-campaign-title">${
                              event.title
                            }</div>
                            <div class="today-campaign-info">
                                <div class="today-campaign-status">
                                    <i class="fas fa-circle" style="font-size: 8px; color: ${
                                      event.status === "active"
                                        ? "var(--apple-green)"
                                        : "var(--apple-gray-1)"
                                    }"></i>
                                    <span class="badge ${statusClass}">${
          event.status || "Активна"
        }</span>
                                </div>
                                ${
                                  event.chats
                                    ? `<div class="today-campaign-chats">
                                    <i class="fas fa-users"></i>
                                    ${event.chats.length} чат(ов)
                                </div>`
                                    : ""
                                }
                            </div>
                        </div>
                        <div class="today-campaign-actions">
                            <button class="today-campaign-button" onclick="window.location.href='/campaigns/${
                              event.campaign_id
                            }/edit'; event.stopPropagation();">
                                <i class="fas fa-edit"></i>
                            </button>
                        </div>
                    </div>
                `;
      });

      todayContent.innerHTML = html;
    }
  }

  renderEvents() {
    // Очищаем все события
    document.querySelectorAll(".day-events").forEach((el) => {
      el.innerHTML = "";
    });

    if (!this.events || this.events.length === 0) {
      console.log("Нет событий для отображения");
      return;
    }

    // Группировка событий по дате
    const eventsByDate = {};

    // Отображаем события на календаре
    this.events.forEach((event) => {
      try {
        const eventDate = new Date(event.date);
        const year = eventDate.getUTCFullYear();
        const month = eventDate.getUTCMonth() + 1;
        const day = eventDate.getUTCDate();
        const dateKey = `${year}-${month}-${day}`;

        // Группируем события по дате
        if (!eventsByDate[dateKey]) {
          eventsByDate[dateKey] = [];
        }
        eventsByDate[dateKey].push(event);

        // Проверяем, что событие относится к текущему месяцу
        if (
          year === this.currentDate.getUTCFullYear() &&
          month === this.currentDate.getUTCMonth() + 1
        ) {
          const dayCell = document.querySelector(
            `.calendar-day[data-date="${dateKey}"]`
          );
          if (dayCell) {
            let dayEvents = dayCell.querySelector(".day-events");
            if (!dayEvents) {
              dayEvents = document.createElement("div");
              dayEvents.className = "day-events";
              dayCell.appendChild(dayEvents);
            }

            const eventDot = document.createElement("div");
            eventDot.className = `event-item ${this.getEventClass(event.type)}`;

            const timeEl = document.createElement("span");
            timeEl.className = "event-time";
            timeEl.textContent = event.time || "00:00";

            const titleEl = document.createElement("span");
            titleEl.className = "event-title";
            titleEl.textContent = event.title;

            eventDot.appendChild(timeEl);
            eventDot.appendChild(titleEl);

            eventDot.addEventListener("click", (e) => {
              e.stopPropagation();
              this.showEventDetails(event);
            });

            // Если событий много, добавляем только первые 3 и счетчик
            if (dayEvents.children.length < 3) {
              dayEvents.appendChild(eventDot);
            } else if (dayEvents.children.length === 3) {
              // Добавляем счетчик дополнительных событий
              const moreEvents = document.createElement("div");
              moreEvents.className = "more-events";
              moreEvents.textContent = `+${eventsByDate[dateKey].length - 2}`;
              moreEvents.addEventListener("click", (e) => {
                e.stopPropagation();
                this.showDayEvents(year, month, day);
              });
              dayEvents.appendChild(moreEvents);
            }
          }
        }
      } catch (err) {
        console.error("Ошибка при отображении события", event, err);
      }
    });
  }

  getEventClass(eventType) {
    switch (eventType) {
      case "campaign":
        return "campaign-event";
      case "message":
        return "message-event";
      case "reminder":
        return "reminder-event";
      default:
        return "default-event";
    }
  }

  getEventTypeName(eventType) {
    switch (eventType) {
      case "campaign":
        return "Кампания";
      case "message":
        return "Сообщение";
      case "reminder":
        return "Напоминание";
      default:
        return "Событие";
    }
  }

  showDayEvents(year, month, day) {
    const dateStr = `${year}-${month.toString().padStart(2, "0")}-${day
      .toString()
      .padStart(2, "0")}`;
    const dayEvents = this.events.filter((event) => {
      const eventDate = new Date(event.date);
      const eventDateStr = eventDate.toISOString().split("T")[0];
      return eventDateStr === dateStr;
    });

    // Сортировка событий по времени
    dayEvents.sort((a, b) => {
      const timeA = a.time || "00:00";
      const timeB = b.time || "00:00";
      return timeA.localeCompare(timeB);
    });

    const modal = document.getElementById("dayEventsModal");
    const modalTitle = document.getElementById("dayEventsTitle");
    const modalBody = document.getElementById("dayEventsBody");

    modalTitle.textContent = `События на ${day} ${this.getMonthName(
      month - 1
    )} ${year}`;

    if (dayEvents.length === 0) {
      modalBody.innerHTML =
        '<div class="no-events">На этот день нет запланированных событий</div>';
    } else {
      // Создаем более подробное отображение событий
      modalBody.innerHTML = dayEvents
        .map(
          (event) => `
                <div class="day-event-item ${this.getEventClass(
                  event.type
                )}" onclick="calendarManager.showEventDetails(${JSON.stringify(
            event
          ).replace(/"/g, "&quot;")})">
                    <div class="event-time">${this.formatTime(
                      event.time || "00:00"
                    )} UTC</div>
                    <div class="event-details">
                        <div class="event-title">${event.title}</div>
                        <div class="event-type">Тип: ${this.getEventTypeName(
                          event.type
                        )}</div>
                        <div class="event-description">${
                          event.description || "Нет описания"
                        }</div>
                        <div class="event-campaign">
                            <span class="event-campaign-label">Кампания:</span> 
                            <span class="event-campaign-name">${
                              event.campaign_name || event.title
                            }</span>
                        </div>
                        ${
                          event.chats
                            ? `<div class="event-chats">
                            <span class="event-chats-label">Чаты:</span> 
                            <span class="event-chats-count">${event.chats.length} чат(ов)</span>
                        </div>`
                            : ""
                        }
                    </div>
                </div>
            `
        )
        .join("");
    }

    modal.style.display = "flex";
  }
  showEventDetails(event) {
    const modal = document.getElementById("eventDetailsModal");
    const modalTitle = document.getElementById("eventDetailsTitle");
    const modalBody = document.getElementById("eventDetailsBody");

    modalTitle.textContent = event.title;

    // Собираем более полную информацию о событии
    let chatInfo = "";
    if (event.chats && event.chats.length > 0) {
      chatInfo = `
                <div class="event-detail-section">
                    <strong>Чаты:</strong>
                    <div class="event-chats-list">
                        <span class="badge bg-info">${event.chats.length} чат(ов)</span>
                    </div>
                </div>
            `;
    }

    // Информация о медиа, если есть
    let mediaInfo = "";
    if (event.media_files && event.media_files.length > 0) {
      mediaInfo = `
                <div class="event-detail-section">
                    <strong>Медиа:</strong>
                    <div class="event-media-info">
                        <span class="badge bg-success">${event.media_files.length} файл(ов)</span>
                    </div>
                </div>
            `;
    }

    // Информация о кнопках, если есть
    let buttonsInfo = "";
    if (event.buttons && event.buttons.length > 0) {
      buttonsInfo = `
                <div class="event-detail-section">
                    <strong>Кнопки:</strong>
                    <div class="event-buttons-info">
                        <span class="badge bg-primary">${event.buttons.length} кнопок</span>
                    </div>
                </div>
            `;
    }

    // Статус кампании
    let statusInfo = "";
    if (event.status) {
      const statusClass =
        {
          active: "bg-success",
          paused: "bg-warning",
          completed: "bg-secondary",
          draft: "bg-light text-dark",
        }[event.status] || "bg-primary";

      statusInfo = `
                <div class="event-detail-section">
                    <strong>Статус:</strong>
                    <div class="event-status">
                        <span class="badge ${statusClass}">${event.status}</span>
                    </div>
                </div>
            `;
    }

    modalBody.innerHTML = `
            <div class="event-detail-section">
                <strong>Дата и время (UTC):</strong> ${this.formatDate(
                  event.date
                )} в ${event.time || "00:00"}
            </div>
            <div class="event-detail-section">
                <strong>Тип:</strong> ${this.getEventTypeName(event.type)}
            </div>
            <div class="event-detail-section">
                <strong>Кампания:</strong> ${event.campaign_name || event.title}
            </div>
            ${statusInfo}
            <div class="event-detail-section">
                <strong>Описание:</strong>
                <div class="event-description">${
                  event.description || "Нет описания"
                }</div>
            </div>
            ${chatInfo}
            ${mediaInfo}
            ${buttonsInfo}
            <div class="event-detail-section">
                <strong>ID кампании:</strong> ${
                  event.campaign_id || "Не указан"
                }
            </div>
            <div class="event-detail-actions">
                <button class="btn btn-sm btn-outline-primary" onclick="window.location.href='/campaigns/${
                  event.campaign_id
                }/edit'">
                    <i class="fas fa-edit me-1"></i>Редактировать кампанию
                </button>
            </div>
        `;

    modal.style.display = "flex";
  }

  getMonthName(monthIndex) {
    const monthNames = [
      "января",
      "февраля",
      "марта",
      "апреля",
      "мая",
      "июня",
      "июля",
      "августа",
      "сентября",
      "октября",
      "ноября",
      "декабря",
    ];
    return monthNames[monthIndex];
  }

  formatTime(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleTimeString("ru-RU", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  formatEventTimeUTC(event) {
    const dateOptions = { day: "2-digit", month: "2-digit", year: "numeric" };
    const timeOptions = { hour: "2-digit", minute: "2-digit" };

    const startDate = new Date(event.start);
    const formattedDate = startDate.toLocaleDateString("ru-RU", dateOptions);
    const formattedTime = startDate.toLocaleTimeString("ru-RU", timeOptions);

    return `${formattedDate} ${formattedTime} UTC`;
  }

  formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString("ru-RU", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }

  showLoading(elementId, show) {
    const element = document.getElementById(elementId);
    if (show) {
      element.classList.add("loading");
    } else {
      element.classList.remove("loading");
    }
  }

  showError(elementId, message) {
    const element = document.getElementById(elementId);
    element.innerHTML = `
            <div class="error-state">
                <div class="state-icon error">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <h5>Ошибка загрузки</h5>
                <p>${message}</p>
            </div>
        `;
  }

  // Закрытие модальных окон
  closeModals() {
    document.querySelectorAll(".modal").forEach((modal) => {
      modal.style.display = "none";
    });
  }

  // Настройка обработчиков для закрытия модальных окон
  setupModalClosers() {
    // Добавляем обработчики на все кнопки закрытия
    document.querySelectorAll(".modal-close").forEach((closeBtn) => {
      closeBtn.addEventListener("click", () => this.closeModals());
    });

    // Закрытие по клику на фон
    document.querySelectorAll(".modal").forEach((modal) => {
      modal.addEventListener("click", (event) => {
        if (event.target === modal) {
          this.closeModals();
        }
      });
    });

    // Закрытие по клавише Escape
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        this.closeModals();
      }
    });
  }

  // Обновление календаря при изменении месяца
  refreshCalendarView() {
    console.log("Обновление представления календаря");
    // Перерисовываем календарь
    this.renderCalendar();
    // Загружаем события заново
    this.loadCalendarEvents();
  }
}

// Создаем экземпляр менеджера календаря при загрузке страницы
document.addEventListener("DOMContentLoaded", function () {
  window.calendarManager = new CalendarManager();
});
