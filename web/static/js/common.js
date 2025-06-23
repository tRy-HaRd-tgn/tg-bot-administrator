/**
 * Общие утилиты и функции для всего приложения
 */

// Глобальный объект утилит
window.Utils = {
    
    /**
     * Экранирование HTML
     * @param {string} str - Строка для экранирования
     * @returns {string} Экранированная строка
     */
    escapeHtml: function(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },
    
    /**
     * Форматирование даты
     * @param {string} dateString - Строка даты
     * @returns {string} Отформатированная дата
     */
    formatDate: function(dateString) {
        if (!dateString) return 'Не указано';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('ru-RU', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return dateString;
        }
    },
    
    /**
     * Показ уведомления
     * @param {string} type - Тип уведомления (success, error, warning, info)
     * @param {string} title - Заголовок
     * @param {string} message - Сообщение
     */
    showNotification: function(type, title, message) {
        // Создаем контейнер для уведомлений если его нет
        let container = document.getElementById('notifications-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notifications-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        
        // Определяем класс и иконку для типа уведомления
        const typeConfig = {
            success: { class: 'alert-success', icon: 'fa-check-circle' },
            error: { class: 'alert-danger', icon: 'fa-exclamation-circle' },
            warning: { class: 'alert-warning', icon: 'fa-exclamation-triangle' },
            info: { class: 'alert-info', icon: 'fa-info-circle' }
        };
        
        const config = typeConfig[type] || typeConfig.info;
        
        // Создаем элемент уведомления
        const notification = document.createElement('div');
        notification.className = `alert ${config.class} alert-dismissible fade show mb-3`;
        notification.style.cssText = `
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            border: none;
            border-radius: 10px;
        `;
        
        notification.innerHTML = `
            <div class="d-flex align-items-start">
                <i class="fa-solid ${config.icon} me-2 mt-1"></i>
                <div class="flex-grow-1">
                    <div class="fw-bold">${this.escapeHtml(title)}</div>
                    <div>${this.escapeHtml(message)}</div>
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Добавляем уведомление в контейнер
        container.appendChild(notification);
        
        // Автоматически удаляем через 5 секунд
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 150);
            }
        }, 5000);
    },
    
    /**
     * Показ модального окна подтверждения
     * @param {string} title - Заголовок
     * @param {string} message - Сообщение
     * @param {Function} onConfirm - Функция при подтверждении
     * @param {Function} onCancel - Функция при отмене
     */
    showConfirmModal: function(title, message, onConfirm, onCancel) {
        // Удаляем существующий модал если есть
        const existingModal = document.getElementById('confirmModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Создаем модальное окно
        const modalHtml = `
            <div class="modal fade" id="confirmModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${this.escapeHtml(title)}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>${this.escapeHtml(message)}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
                            <button type="button" class="btn btn-danger" id="confirmButton">Подтвердить</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
        const confirmButton = document.getElementById('confirmButton');
        
        confirmButton.addEventListener('click', () => {
            modal.hide();
            if (onConfirm) onConfirm();
        });
        
        document.getElementById('confirmModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
            if (onCancel) onCancel();
        });
        
        modal.show();
    },
    
    /**
     * Показ индикатора загрузки
     * @param {boolean} show - Показать или скрыть
     * @param {string} message - Сообщение загрузки
     */
    showLoading: function(show, message = 'Загрузка...') {
        let loader = document.getElementById('global-loader');
        
        if (show) {
            if (!loader) {
                loader = document.createElement('div');
                loader.id = 'global-loader';
                loader.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 10000;
                `;
                
                loader.innerHTML = `
                    <div class="bg-white p-4 rounded shadow text-center">
                        <div class="spinner-border text-primary mb-3" role="status">
                            <span class="visually-hidden">Загрузка...</span>
                        </div>
                        <div>${this.escapeHtml(message)}</div>
                    </div>
                `;
                
                document.body.appendChild(loader);
            }
            loader.style.display = 'flex';
        } else {
            if (loader) {
                loader.style.display = 'none';
            }
        }
    },
    
    /**
     * Копирование текста в буфер обмена
     * @param {string} text - Текст для копирования
     * @returns {Promise<boolean>} Результат операции
     */
    copyToClipboard: async function(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showNotification('success', 'Скопировано', 'Текст скопирован в буфер обмена');
            return true;
        } catch (err) {
            console.error('Ошибка копирования:', err);
            this.showNotification('error', 'Ошибка', 'Не удалось скопировать текст');
            return false;
        }
    },
    
    /**
     * Форматирование размера файла
     * @param {number} bytes - Размер в байтах
     * @returns {string} Отформатированный размер
     */
    formatFileSize: function(bytes) {
        if (!bytes) return '0 Б';
        
        const sizes = ['Б', 'КБ', 'МБ', 'ГБ'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    },
    
    /**
     * Валидация email
     * @param {string} email - Email для валидации
     * @returns {boolean} Результат валидации
     */
    validateEmail: function(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },
    
    /**
     * Валидация URL
     * @param {string} url - URL для валидации
     * @returns {boolean} Результат валидации
     */
    validateUrl: function(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    },
    
    /**
     * Дебаунсинг функции
     * @param {Function} func - Функция для дебаунсинга
     * @param {number} wait - Время ожидания в мс
     * @returns {Function} Дебаунснутая функция
     */
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('Common utilities loaded');
    
    // Обработчик для копирования при клике на элементы с data-copy
    document.addEventListener('click', function(e) {
        const copyElement = e.target.closest('[data-copy]');
        if (copyElement) {
            const textToCopy = copyElement.dataset.copy || copyElement.textContent;
            Utils.copyToClipboard(textToCopy);
        }
    });
    
    // Обработчик для всех форм с классом ajax-form
    document.addEventListener('submit', function(e) {
        if (e.target.classList.contains('ajax-form')) {
            e.preventDefault();
            // Логика для AJAX отправки форм может быть добавлена здесь
        }
    });
});

// Экспорт в глобальную область
window.showToast = Utils.showNotification;
window.showConfirmModal = Utils.showConfirmModal;
window.showLoading = Utils.showLoading;
