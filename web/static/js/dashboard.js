/**
 * Dashboard JavaScript
 * Управляет отображением и обновлением статистики на дашборде
 */
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация дашборда
    const dashboard = new Dashboard();
    dashboard.init();
});

class Dashboard {
    constructor() {
        // Статистические элементы - удаляем ненужные
        this.elements = {
            activeСampaigns: document.getElementById('activeСampaigns'),
            totalСampaigns: document.getElementById('totalСampaigns'),
            regularGroups: document.getElementById('regularGroups'),
            forumGroups: document.getElementById('forumGroups'),
            supergroups: document.getElementById('supergroups'),
            totalChats: document.getElementById('totalChats')
        };
        
        // Кнопка обновления статистики
        this.refreshBtn = document.getElementById('refreshStatsBtn');
        
        // Флаг загрузки
        this.isLoading = false;
    }
    
    /**
     * Инициализация дашборда
     */
    init() {
        // Загружаем статистику при загрузке страницы
        this.loadStatistics();
        
        // Обработчик кнопки обновления
        if (this.refreshBtn) {
            this.refreshBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.loadStatistics();
            });
        }
        
        // Автообновление каждые 5 минут
        setInterval(() => this.loadStatistics(), 300000);
    }
    
    /**
     * Загрузка статистических данных
     */
    async loadStatistics() {
        // Если уже идет загрузка, не делаем повторный запрос
        if (this.isLoading) return;
        
        // Показываем состояние загрузки
        this.showLoadingState();
        
        try {
            // Загружаем данные по кампаниям и чатам
            const [campaignData, chatData] = await Promise.all([
                this.fetchCampaignStatistics(),
                this.fetchChatStatistics()
            ]);
            
            // Обновляем данные на странице
            this.updateDashboard(campaignData, chatData);
        } catch (error) {
            console.error('Ошибка при загрузке статистики:', error);
            this.showErrorState();
        } finally {
            this.isLoading = false;
        }
    }
    
    /**
     * Запрос статистики по кампаниям
     */
    async fetchCampaignStatistics() {
        try {
            const response = await fetch('/api/statistics/campaigns');
            if (!response.ok) {
                throw new Error(`HTTP ошибка: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Ошибка при получении статистики кампаний:', error);
            // Возвращаем тестовые данные в случае ошибки
            return {
                active_campaigns: 0,
                total_campaigns: 0,
                total_messages: 0,
                scheduled_messages: 0
            };
        }
    }
    
    /**
     * Запрос статистики по чатам
     */
    async fetchChatStatistics() {
        try {
            const response = await fetch('/api/statistics/chats');
            if (!response.ok) {
                throw new Error(`HTTP ошибка: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Ошибка при получении статистики чатов:', error);
            // Возвращаем тестовые данные в случае ошибки
            return {
                regular_groups: 0,
                forum_groups: 0,
                supergroups: 0,
                total_chats: 0
            };
        }
    }
    
    /**
     * Обновление интерфейса дашборда полученными данными
     */
    updateDashboard(campaignData, chatData) {
        // Обновляем статистику кампаний (удаляем ненужные)
        this.updateElement(this.elements.activeСampaigns, campaignData.active_campaigns);
        this.updateElement(this.elements.totalСampaigns, campaignData.total_campaigns);
        
        // Обновляем статистику чатов
        this.updateElement(this.elements.regularGroups, chatData.regular_groups);
        this.updateElement(this.elements.forumGroups, chatData.forum_groups);
        this.updateElement(this.elements.supergroups, chatData.supergroups);
        this.updateElement(this.elements.totalChats, chatData.total_chats);
        
        // Обновляем время последнего обновления
        this.updateLastUpdatedTime();
    }
    
    /**
     * Обновление отдельного элемента статистики с анимацией
     */
    updateElement(element, value) {
        if (!element) return;
        
        // Убираем класс загрузки
        element.classList.remove('loading');
        
        // Если значение не изменилось, просто обновляем
        if (element.textContent === value.toString()) {
            return;
        }
        
        // Если значение изменилось, применяем анимацию
        element.style.transform = 'translateY(-10px)';
        element.style.opacity = '0';
        
        setTimeout(() => {
            element.textContent = value;
            element.style.transform = 'translateY(0)';
            element.style.opacity = '1';
        }, 200);
    }
    
    /**
     * Обновление времени последнего обновления
     */
    updateLastUpdatedTime() {
        const timeElements = document.querySelectorAll('.last-update-time');
        const now = new Date();
        const timeString = now.toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        timeElements.forEach(el => {
            el.textContent = timeString;
        });
    }
    
    /**
     * Показать состояние загрузки
     */
    showLoadingState() {
        this.isLoading = true;
        
        // Добавляем класс загрузки ко всем элементам статистики
        Object.values(this.elements).forEach(element => {
            if (element) {
                element.classList.add('loading');
            }
        });
        
        // Изменяем иконку кнопки обновления
        if (this.refreshBtn) {
            const icon = this.refreshBtn.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-sync-alt');
                icon.classList.add('fa-spinner');
                icon.classList.add('fa-spin');
            }
        }
    }
    
    /**
     * Сбросить состояние загрузки
     */
    resetLoadingState() {
        // Убираем класс загрузки со всех элементов статистики
        Object.values(this.elements).forEach(element => {
            if (element) {
                element.classList.remove('loading');
            }
        });
        
        // Восстанавливаем иконку кнопки обновления
        if (this.refreshBtn) {
            const icon = this.refreshBtn.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-spinner');
                icon.classList.remove('fa-spin');
                icon.classList.add('fa-sync-alt');
            }
        }
        
        this.isLoading = false;
    }
    
    /**
     * Показать состояние ошибки
     */
    showErrorState() {
        this.resetLoadingState();
        
        // Оповещаем пользователя об ошибке
        if (typeof Utils !== 'undefined' && Utils.showNotification) {
            Utils.showNotification('error', 'Ошибка', 'Не удалось загрузить статистику');
        } else {
            // Простое оповещение если нет утилиты
            const alertElement = document.createElement('div');
            alertElement.className = 'alert alert-danger mt-3';
            alertElement.textContent = 'Не удалось загрузить статистику. Пожалуйста, попробуйте позже.';
            
            const container = document.querySelector('.container-fluid');
            if (container) {
                container.prepend(alertElement);
                
                // Удаляем сообщение через 5 секунд
                setTimeout(() => {
                    alertElement.remove();
                }, 5000);
            }
        }
    }
}

function fetchChatsStats() {
    fetch('/api/statistics/chats')
        .then(response => {
            if (!response.ok) {
                throw new Error('Не удалось загрузить статистику чатов');
            }
            return response.json();
        })
        .then(data => {
            document.getElementById('total-chats-count').innerText = data.total_chats;
            document.getElementById('supergroups-count').innerText = data.supergroups || 0;
        })
        .catch(error => {
            console.error('Ошибка при получении статистики чатов:', error);
        });
}
