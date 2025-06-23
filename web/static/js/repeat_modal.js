/**
 * Модуль для работы с настройками автоповтора публикации
 */
class RepeatModal {
    constructor() {
        this.modal = null;
        this.currentSettings = null;
        this.onSettingsChanged = null;
        this.init();
    }

    init() {
        this.modal = document.getElementById('repeatModal');
        if (!this.modal) {
            console.error('Модальное окно repeatModal не найдено');
            return;
        }

        this.setupMonthlyDateOptions();
        this.bindEvents();
        this.updatePreview();
    }

    setupMonthlyDateOptions() {
        const monthlyDateSelect = document.getElementById('monthlyDate');
        if (monthlyDateSelect) {
            monthlyDateSelect.innerHTML = '';
            for (let i = 1; i <= 31; i++) {
                const option = document.createElement('option');
                option.value = i;
                option.textContent = i;
                if (i === 1) option.selected = true;
                monthlyDateSelect.appendChild(option);
            }
        }
    }

    bindEvents() {
        // Изменение интервала повторения
        document.querySelectorAll('input[name="repeat_interval"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.handleIntervalChange();
                this.updatePreview();
            });
        });

        // Изменение дат периода
        ['repeatStartDate', 'repeatEndDate'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => {
                    this.validateDates();
                    this.updatePreview();
                });
            }
        });

        // Изменение дня недели для еженедельного повторения
        document.querySelectorAll('input[name="weekly_day"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.validateWeeklySettings();
                this.updatePreview();
            });
        });

        // Изменение типа месячного повторения
        document.querySelectorAll('input[name="monthly_type"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.handleMonthlyTypeChange();
                this.updatePreview();
            });
        });

        // Изменение настроек месячного повторения
        ['monthlyDate', 'monthlyWeek', 'monthlyWeekday'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => {
                    this.updatePreview();
                });
            }
        });

        // Кнопка сохранения - ИСПРАВЛЕНО
        const saveBtn = document.getElementById('saveRepeatSettings');
        if (saveBtn) {
            saveBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Нажата кнопка сохранения настроек повтора');
                this.saveSettings();
            });
        } else {
            console.error('Кнопка saveRepeatSettings не найдена');
        }

        // Сброс при закрытии модала
        if (this.modal) {
            this.modal.addEventListener('hidden.bs.modal', () => this.resetModal());
        }
    }

    handleIntervalChange() {
        const selectedInterval = document.querySelector('input[name="repeat_interval"]:checked');
        if (!selectedInterval) return;
        
        const intervalValue = selectedInterval.value;
        
        // Скрываем все дополнительные настройки
        document.querySelectorAll('.interval-specific-settings').forEach(settings => {
            settings.style.display = 'none';
        });

        // Показываем настройки для выбранного интервала
        const settingsElement = document.getElementById(`${intervalValue}-settings`);
        if (settingsElement) {
            settingsElement.style.display = 'block';
        }

        // Обновляем визуальное выделение карточек
        document.querySelectorAll('.interval-option').forEach(option => {
            option.classList.remove('active');
        });
        
        selectedInterval.closest('.interval-option').classList.add('active');
    }

    handleMonthlyTypeChange() {
        const selectedType = document.querySelector('input[name="monthly_type"]:checked');
        if (!selectedType) return;
        
        // Обновляем визуальное выделение опций
        document.querySelectorAll('.monthly-option').forEach(option => {
            option.classList.remove('selected');
        });
        
        selectedType.closest('.monthly-option').classList.add('selected');
    }

    validateDates() {
        const startDate = document.getElementById('repeatStartDate');
        const endDate = document.getElementById('repeatEndDate');
        const startError = document.getElementById('repeatStartDateError');
        const endError = document.getElementById('repeatEndDateError');

        let isValid = true;

        this.clearError(startDate, startError);
        this.clearError(endDate, endError);

        if (!startDate.value) {
            this.showError(startDate, startError, 'Дата начала обязательна');
            isValid = false;
        }

        if (startDate.value && endDate.value) {
            const start = new Date(startDate.value);
            const end = new Date(endDate.value);
            
            if (start >= end) {
                this.showError(endDate, endError, 'Дата окончания должна быть позже даты начала');
                isValid = false;
            }
        }

        return isValid;
    }

    validateWeeklySettings() {
        const selectedInterval = document.querySelector('input[name="repeat_interval"]:checked');
        
        if (selectedInterval && selectedInterval.value === 'weekly') {
            const selectedDay = document.querySelector('input[name="weekly_day"]:checked');
            const error = document.getElementById('weeklyDayError');
            
            if (!selectedDay) {
                this.showError(null, error, 'Выберите день недели');
                return false;
            }
            
            this.clearError(null, error);
        }
        
        return true;
    }

    updatePreview() {
        const intervalElement = document.getElementById('previewInterval');
        const periodElement = document.getElementById('previewPeriod');
        const nextElement = document.getElementById('previewNext');

        if (!intervalElement || !periodElement || !nextElement) return;

        // Обновляем интервал
        const selectedInterval = document.querySelector('input[name="repeat_interval"]:checked');
        if (selectedInterval) {
            intervalElement.textContent = this.getIntervalDescription(selectedInterval.value);
        }

        // Обновляем период
        const startDate = document.getElementById('repeatStartDate').value;
        const endDate = document.getElementById('repeatEndDate').value;
        
        if (startDate) {
            let periodText = `с ${new Date(startDate).toLocaleDateString('ru-RU')}`;
            if (endDate) {
                periodText += ` по ${new Date(endDate).toLocaleDateString('ru-RU')}`;
            } else {
                periodText += ' (без ограничений)';
            }
            periodElement.textContent = periodText;
        } else {
            periodElement.textContent = 'Не указан';
        }

        // Обновляем следующую публикацию
        if (startDate && selectedInterval) {
            const nextDate = this.calculateNextPublication();
            if (nextDate) {
                nextElement.textContent = nextDate.toLocaleDateString('ru-RU') + ' ' + nextDate.toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'});
            } else {
                nextElement.textContent = 'Не определена';
            }
        } else {
            nextElement.textContent = 'Не определена';
        }
    }

    getIntervalDescription(interval) {
        const descriptions = {
            minutely: 'Каждую минуту',
            hourly: 'Каждый час',
            daily: 'Ежедневно',
            weekly: 'Раз в неделю',
            monthly: 'Раз в месяц'
        };

        let description = descriptions[interval] || 'Неизвестно';

        // Добавляем детали для еженедельного повторения
        if (interval === 'weekly') {
            const selectedDay = document.querySelector('input[name="weekly_day"]:checked');
            if (selectedDay) {
                const dayNames = {
                    '1': 'по понедельникам',
                    '2': 'по вторникам',
                    '3': 'по средам',
                    '4': 'по четвергам',
                    '5': 'по пятницам',
                    '6': 'по субботам',
                    '7': 'по воскресеньям'
                };
                description += ` (${dayNames[selectedDay.value]})`;
            }
        }

        // Добавляем детали для ежемесячного повторения
        if (interval === 'monthly') {
            const monthlyType = document.querySelector('input[name="monthly_type"]:checked');
            if (monthlyType && monthlyType.value === 'date') {
                const date = document.getElementById('monthlyDate').value;
                if (date) {
                    description += ` (${date} числа)`;
                }
            } else if (monthlyType && monthlyType.value === 'weekday') {
                const week = document.getElementById('monthlyWeek').value;
                const weekday = document.getElementById('monthlyWeekday').value;
                if (week && weekday) {
                    const weekNames = {
                        '1': 'первый',
                        '2': 'второй', 
                        '3': 'третий',
                        '4': 'четвертый',
                        '-1': 'последний'
                    };
                    const dayNames = {
                        '1': 'понедельник',
                        '2': 'вторник',
                        '3': 'среда',
                        '4': 'четверг',
                        '5': 'пятница',
                        '6': 'суббота',
                        '7': 'воскресенье'
                    };
                    description += ` (${weekNames[week]} ${dayNames[weekday]})`;
                }
            }
        }

        return description;
    }

    calculateNextPublication() {
        const startDate = document.getElementById('repeatStartDate').value;
        const selectedInterval = document.querySelector('input[name="repeat_interval"]:checked');
        
        if (!startDate || !selectedInterval) return null;

        const start = new Date(startDate);
        const now = new Date();
        let next = new Date(start);

        // Если дата начала в будущем, возвращаем её
        if (start > now) return start;

        // Вычисляем следующую дату в зависимости от интервала
        switch (selectedInterval.value) {
            case 'minutely':
                while (next <= now) {
                    next.setMinutes(next.getMinutes() + 1);
                }
                break;
            case 'hourly':
                while (next <= now) {
                    next.setHours(next.getHours() + 1);
                }
                break;
            case 'daily':
                while (next <= now) {
                    next.setDate(next.getDate() + 1);
                }
                break;
            case 'weekly':
                while (next <= now) {
                    next.setDate(next.getDate() + 7);
                }
                break;
            case 'monthly':
                while (next <= now) {
                    next.setMonth(next.getMonth() + 1);
                }
                break;
            default:
                return null;
        }

        return next;
    }

    validateSettings() {
        const selectedInterval = document.querySelector('input[name="repeat_interval"]:checked');
        if (!selectedInterval) {
            alert('Выберите интервал повторения');
            return false;
        }

        if (!this.validateDates()) {
            return false;
        }

        // Валидация для еженедельного повтора
        if (selectedInterval.value === 'weekly') {
            return this.validateWeeklySettings();
        }

        return true;
    }

    saveSettings() {
        console.log('Сохранение настроек повтора...');
        
        try {
            if (!this.validateSettings()) {
                console.error('Валидация не прошла');
                return false;
            }

            const settings = this.getCurrentSettings();
            console.log('Настройки для сохранения:', settings);
            
            this.currentSettings = settings;
            
            if (this.onSettingsChanged && typeof this.onSettingsChanged === 'function') {
                this.onSettingsChanged(settings);
                console.log('Callback вызван успешно');
            } else {
                console.warn('Callback не установлен');
            }
            
            // Закрываем модальное окно
            this.hide();
            
            console.log('Настройки повтора сохранены успешно');
            return true;
        } catch (error) {
            console.error('Ошибка при сохранении настроек:', error);
            return false;
        }
    }

    getCurrentSettings() {
        const selectedInterval = document.querySelector('input[name="repeat_interval"]:checked');
        if (!selectedInterval) return null;

        const settings = {
            interval: selectedInterval.value,
            startDate: document.getElementById('repeatStartDate').value,
            endDate: document.getElementById('repeatEndDate').value || null
        };

        // Добавляем специфичные настройки для еженедельного повторения
        if (selectedInterval.value === 'weekly') {
            const selectedDay = document.querySelector('input[name="weekly_day"]:checked');
            if (selectedDay) {
                settings.weekDay = parseInt(selectedDay.value);
            }
        }

        // Добавляем специфичные настройки для ежемесячного повторения
        if (selectedInterval.value === 'monthly') {
            const monthlyType = document.querySelector('input[name="monthly_type"]:checked');
            if (monthlyType) {
                settings.monthlyType = monthlyType.value;
                
                if (monthlyType.value === 'date') {
                    settings.monthlyDate = parseInt(document.getElementById('monthlyDate').value);
                } else if (monthlyType.value === 'weekday') {
                    settings.monthlyWeek = parseInt(document.getElementById('monthlyWeek').value);
                    settings.monthlyWeekday = parseInt(document.getElementById('monthlyWeekday').value);
                }
            }
        }

        return settings;
    }

    loadSettings(settings) {
        if (!settings) return;

        // Загружаем интервал
        const intervalRadio = document.querySelector(`input[name="repeat_interval"][value="${settings.interval}"]`);
        if (intervalRadio) {
            intervalRadio.checked = true;
            this.handleIntervalChange();
        }

        // Загружаем даты
        if (settings.startDate) {
            document.getElementById('repeatStartDate').value = settings.startDate;
        }
        if (settings.endDate) {
            document.getElementById('repeatEndDate').value = settings.endDate;
        }

        // Загружаем настройки для еженедельного повторения
        if (settings.interval === 'weekly' && settings.weekDay) {
            const dayRadio = document.querySelector(`input[name="weekly_day"][value="${settings.weekDay}"]`);
            if (dayRadio) {
                dayRadio.checked = true;
            }
        }

        // Загружаем настройки для ежемесячного повторения
        if (settings.interval === 'monthly') {
            if (settings.monthlyType) {
                const typeRadio = document.querySelector(`input[name="monthly_type"][value="${settings.monthlyType}"]`);
                if (typeRadio) {
                    typeRadio.checked = true;
                    this.handleMonthlyTypeChange();
                }
            }

            if (settings.monthlyDate) {
                document.getElementById('monthlyDate').value = settings.monthlyDate;
            }

            if (settings.monthlyWeek) {
                document.getElementById('monthlyWeek').value = settings.monthlyWeek;
            }

            if (settings.monthlyWeekday) {
                document.getElementById('monthlyWeekday').value = settings.monthlyWeekday;
            }
        }

        this.currentSettings = settings;
        this.updatePreview();
    }

    resetModal() {
        // Сбрасываем выбор интервала на ежедневный
        const dailyRadio = document.querySelector('input[name="repeat_interval"][value="daily"]');
        if (dailyRadio) {
            dailyRadio.checked = true;
        }

        // Скрываем все дополнительные настройки
        document.querySelectorAll('.interval-specific-settings').forEach(settings => {
            settings.style.display = 'none';
        });

        // Очищаем поля
        document.getElementById('repeatStartDate').value = '';
        document.getElementById('repeatEndDate').value = '';

        // Сбрасываем ошибки
        document.querySelectorAll('.invalid-feedback').forEach(error => {
            error.style.display = 'none';
        });

        // Обновляем превью
        this.updatePreview();
    }

    showError(input, errorElement, message) {
        if (input) {
            input.classList.add('is-invalid');
        }
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    }

    clearError(input, errorElement) {
        if (input) {
            input.classList.remove('is-invalid');
        }
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    }

    // Методы для внешнего использования
    show() {
        if (this.modal) {
            const modal = new bootstrap.Modal(this.modal);
            modal.show();
        }
    }

    hide() {
        if (this.modal) {
            const modal = bootstrap.Modal.getInstance(this.modal);
            if (modal) {
                modal.hide();
            }
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
document.addEventListener('DOMContentLoaded', function() {
    window.repeatModal = new RepeatModal();
    console.log('RepeatModal инициализирован');
});
