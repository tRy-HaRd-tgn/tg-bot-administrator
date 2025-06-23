/**
 * Современный JavaScript для управления кампаниями
 */
class CampaignsManager {
    constructor() {
        this.campaigns = [];
        this.filteredCampaigns = [];
        this.currentFilter = 'all';
        this.searchQuery = '';
        this.utcTimeInterval = null;
        this.init();
    }

    async init() {
        console.log('Инициализация CampaignsManager...');
        this.bindEvents();
        await this.loadCampaigns();
        this.startUTCClock();
    }

    bindEvents() {
        // Поиск
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
        }

        // Фильтры
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => this.setFilter(btn.dataset.filter));
        });
    }

    async loadCampaigns() {
        try {
            Utils.showLoading(true, 'Загрузка кампаний...');
            
            const response = await fetch('/api/campaigns', {
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP error: ${response.status}`);
            }

            const campaigns = await response.json();
            console.log('Загруженные кампании:', campaigns);
            
            if (!Array.isArray(campaigns)) {
                throw new Error('Некорректный формат данных');
            }

            this.campaigns = campaigns;
            this.filterCampaigns();
            this.updateStatistics();

        } catch (error) {
            console.error('Ошибка загрузки кампаний:', error);
            this.showError('Не удалось загрузить список кампаний: ' + error.message);
        } finally {
            Utils.showLoading(false);
        }
    }

    filterCampaigns() {
        let filtered = this.campaigns;

        // Фильтр по статусу
        if (this.currentFilter !== 'all') {
            filtered = filtered.filter(campaign => campaign.status === this.currentFilter);
        }

        // Поиск
        if (this.searchQuery) {
            const query = this.searchQuery.toLowerCase();
            filtered = filtered.filter(campaign => 
                campaign.name.toLowerCase().includes(query) ||
                campaign.message_text.toLowerCase().includes(query) ||
                campaign.description?.toLowerCase().includes(query)
            );
        }

        this.filteredCampaigns = filtered;
        this.renderCampaigns();
    }

    renderCampaigns() {
        const container = document.getElementById('campaignsGrid');
        if (!container) return;

        if (this.filteredCampaigns.length === 0) {
            this.showEmptyState();
            return;
        }

        container.innerHTML = this.filteredCampaigns.map(campaign => 
            this.createCampaignCard(campaign)
        ).join('');
        
        this.bindCampaignEvents();
    }

    createCampaignCard(campaign) {
        const statusConfig = this.getStatusConfig(campaign.status);
        const createdDate = new Date(campaign.created_at).toLocaleDateString('ru-RU');
        const lastRun = campaign.last_run ? 
            new Date(campaign.last_run).toLocaleDateString('ru-RU') : 'Никогда';
        
        const chatsCount = campaign.chats?.length || 0;
        const buttonsCount = campaign.buttons?.length || 0;
        const mediaCount = campaign.media_files?.length || 0;
        
        return `
            <div class="campaign-card status-${campaign.status}" data-campaign-id="${campaign.id}">
                <div class="campaign-header">
                    <div class="campaign-title-section">
                        <h6 class="campaign-title">${Utils.escapeHtml(campaign.name)}</h6>
                        <span class="campaign-status ${campaign.status}">${statusConfig.text}</span>
                    </div>
                </div>
                
                <div class="campaign-body">
                    <div class="campaign-info">
                        <div class="campaign-detail">
                            <i class="fa-solid fa-calendar-days"></i>
                            <strong>Период:</strong> ${campaign.start_date} — ${campaign.end_date}
                        </div>
                        <div class="campaign-detail">
                            <i class="fa-solid fa-clock"></i>
                            <strong>Время:</strong> ${campaign.post_time}
                        </div>
                        <div class="campaign-detail">
                            <i class="fa-solid fa-comments"></i>
                            <strong>Чатов:</strong> ${chatsCount}
                        </div>
                        <div class="campaign-detail">
                            <i class="fa-solid fa-play"></i>
                            <strong>Запусков:</strong> ${campaign.run_count || 0}
                        </div>
                        <div class="campaign-detail">
                            <i class="fa-solid fa-calendar-check"></i>
                            <strong>Последний запуск:</strong> ${lastRun}
                        </div>
                    </div>
                    
                    <div class="campaign-message">
                        <div class="campaign-message-text">
                            ${Utils.escapeHtml(campaign.message_text)}
                        </div>
                    </div>
                    
                    <div class="campaign-meta">
                        ${mediaCount > 0 ? `<span class="campaign-badge media">📁 ${mediaCount} файлов</span>` : ''}
                        ${buttonsCount > 0 ? `<span class="campaign-badge buttons">🔘 ${buttonsCount} кнопок</span>` : ''}
                        ${campaign.repeat_enabled ? '<span class="campaign-badge repeat">🔄 Повторение</span>' : ''}
                        ${campaign.pin_message ? '<span class="campaign-badge pin">📌 Закрепление</span>' : ''}
                    </div>
                </div>
                
                <div class="campaign-footer">
                    <div class="campaign-actions">
                        <button class="campaign-action-btn view" onclick="campaignsManager.viewCampaign('${campaign.id}')" title="Просмотр">
                            <i class="fa-solid fa-eye"></i>
                        </button>
                        <button class="campaign-action-btn toggle" onclick="campaignsManager.toggleCampaignStatus('${campaign.id}')" 
                                title="${this.getStatusActionTitle(campaign.status)}">
                            <i class="fa-solid ${this.getStatusIcon(campaign.status)}"></i>
                        </button>
                        ${campaign.status !== 'completed' ? `
                            <button class="campaign-action-btn complete" onclick="campaignsManager.completeCampaign('${campaign.id}')" title="Завершить">
                                <i class="fa-solid fa-check-circle"></i>
                            </button>
                        ` : ''}
                        <button class="campaign-action-btn delete" onclick="campaignsManager.deleteCampaign('${campaign.id}')" title="Удалить">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    getStatusActionTitle(status) {
        switch (status) {
            case 'active': return 'Приостановить';
            case 'paused': return 'Активировать';
            case 'completed': return 'Перезапустить';
            default: return 'Изменить статус';
        }
    }

    getStatusIcon(status) {
        switch (status) {
            case 'active': return 'fa-pause';
            case 'paused': return 'fa-play';
            case 'completed': return 'fa-rotate';
            default: return 'fa-play';
        }
    }

    bindCampaignEvents() {
        // События уже привязаны через onclick в HTML
    }

    getStatusConfig(status) {
        const configs = {
            active: { text: 'Активна', class: 'success' },
            paused: { text: 'Приостановлена', class: 'warning' },
            draft: { text: 'Черновик', class: 'secondary' },
            completed: { text: 'Завершена', class: 'info' }
        };
        return configs[status] || { text: 'Неизвестно', class: 'secondary' };
    }

    updateStatistics() {
        const stats = {
            all: this.campaigns.length,
            active: this.campaigns.filter(c => c.status === 'active').length,
            paused: this.campaigns.filter(c => c.status === 'paused').length,
            draft: this.campaigns.filter(c => c.status === 'draft').length,
            completed: this.campaigns.filter(c => c.status === 'completed').length
        };

        // Обновляем счетчики в фильтрах
        Object.keys(stats).forEach(key => {
            const element = document.getElementById(`${key}Count`);
            if (element) {
                element.textContent = stats[key];
            }
        });

        // Обновляем общую статистику
        const campaignsCount = document.getElementById('campaignsCount');
        if (campaignsCount) {
            campaignsCount.textContent = `Всего кампаний: ${stats.all}`;
        }
    }

    setFilter(filter) {
        this.currentFilter = filter;
        
        // Обновляем активную кнопку
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });
        
        this.filterCampaigns();
    }

    handleSearch(query) {
        this.searchQuery = query.trim();
        
        // Показываем/скрываем кнопку очистки
        const clearBtn = document.querySelector('.search-clear');
        if (clearBtn) {
            clearBtn.style.display = this.searchQuery ? 'block' : 'none';
        }
        
        this.filterCampaigns();
    }

    clearSearch() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.value = '';
        }
        this.handleSearch('');
    }

    showEmptyState() {
        const container = document.getElementById('campaignsGrid');
        if (!container) return;

        const message = this.searchQuery || this.currentFilter !== 'all' 
            ? 'По заданным критериям кампании не найдены' 
            : 'Нет созданных кампаний';

        container.innerHTML = `
            <div class="content-state">
                <div class="state-icon">
                    <i class="fa-solid fa-rocket"></i>
                </div>
                <h5>Кампании не найдены</h5>
                <p>${message}</p>
                ${!this.searchQuery && this.currentFilter === 'all' ? `
                    <a href="/campaigns/new" class="btn btn-primary">
                        <i class="fa-solid fa-plus me-2"></i>Создать первую кампанию
                    </a>
                ` : `
                    <button class="btn btn-outline-primary" onclick="campaignsManager.clearFilters()">
                        <i class="fa-solid fa-filter-circle-xmark me-2"></i>Сбросить фильтры
                    </button>
                `}
            </div>
        `;
    }

    showError(message) {
        const container = document.getElementById('campaignsGrid');
        if (!container) return;

        container.innerHTML = `
            <div class="content-state">
                <div class="state-icon error">
                    <i class="fa-solid fa-exclamation-triangle"></i>
                </div>
                <h5>Ошибка загрузки</h5>
                <p>${message}</p>
                <button class="btn btn-primary" onclick="campaignsManager.loadCampaigns()">
                    <i class="fa-solid fa-refresh me-2"></i>Повторить
                </button>
            </div>
        `;
    }

    clearFilters() {
        this.setFilter('all');
        this.clearSearch();
    }

    async viewCampaign(campaignId) {
        const campaign = this.campaigns.find(c => c.id === campaignId);
        if (!campaign) return;

        // Показываем модальное окно с деталями
        this.showCampaignDetails(campaign);
    }

    showCampaignDetails(campaign) {
        const modal = document.getElementById('campaignDetailModal');
        const content = document.getElementById('campaignDetailContent');
        
        if (!modal || !content) return;

        const statusConfig = this.getStatusConfig(campaign.status);
        const chatsCount = campaign.chats?.length || 0;
        const buttonsCount = campaign.buttons?.length || 0;
        const mediaCount = campaign.media_files?.length || 0;

        content.innerHTML = `
            <div class="campaign-details">
                <div class="detail-section">
                    <h6>Основная информация</h6>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <strong>Название:</strong> ${Utils.escapeHtml(campaign.name)}
                        </div>
                        <div class="detail-item">
                            <strong>Статус:</strong> <span class="badge bg-${statusConfig.class}">${statusConfig.text}</span>
                        </div>
                        <div class="detail-item">
                            <strong>Описание:</strong> ${Utils.escapeHtml(campaign.description || 'Не указано')}
                        </div>
                    </div>
                </div>

                <div class="detail-section">
                    <h6>Расписание</h6>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <strong>Период:</strong> ${campaign.start_date} — ${campaign.end_date}
                        </div>
                        <div class="detail-item">
                            <strong>Время:</strong> ${campaign.post_time}
                        </div>
                        <div class="detail-item">
                            <strong>Повторение:</strong> ${campaign.repeat_enabled ? 'Включено' : 'Отключено'}
                        </div>
                        ${campaign.days_of_week ? `
                            <div class="detail-item">
                                <strong>Дни недели:</strong> ${campaign.days_of_week}
                            </div>
                        ` : ''}
                    </div>
                </div>

                <div class="detail-section">
                    <h6>Содержимое</h6>
                    <div class="detail-item">
                        <strong>Текст сообщения:</strong>
                        <div class="message-preview">${Utils.escapeHtml(campaign.message_text)}</div>
                    </div>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <strong>Чатов:</strong> ${chatsCount}
                        </div>
                        <div class="detail-item">
                            <strong>Медиафайлов:</strong> ${mediaCount}
                        </div>
                        <div class="detail-item">
                            <strong>Кнопок:</strong> ${buttonsCount}
                        </div>
                    </div>
                </div>

                <div class="detail-section">
                    <h6>Статистика</h6>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <strong>Запусков:</strong> ${campaign.run_count || 0}
                        </div>
                        <div class="detail-item">
                            <strong>Создана:</strong> ${new Date(campaign.created_at).toLocaleString('ru-RU')}
                        </div>
                        <div class="detail-item">
                            <strong>Последний запуск:</strong> ${campaign.last_run ? new Date(campaign.last_run).toLocaleString('ru-RU') : 'Никогда'}
                        </div>
                    </div>
                </div>
            </div>
        `;

        new bootstrap.Modal(modal).show();
    }

    editCampaign(campaignId) {
        window.location.href = `/campaigns/${campaignId}/edit`;
    }

    async toggleCampaignStatus(campaignId) {
        try {
            const campaign = this.campaigns.find(c => c.id === campaignId);
            if (!campaign) return;

            const action = campaign.status === 'completed' ? 'restart' : 
                         (campaign.status === 'active' ? 'pause' : 'activate');

            const response = await fetch(`/api/campaigns/${campaignId}/toggle-status`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ action })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                Utils.showNotification('success', 'Успех', result.message);
                await this.loadCampaigns();
            } else {
                throw new Error(result.message || 'Не удалось изменить статус');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            Utils.showNotification('error', 'Ошибка', error.message);
        }
    }

    // Добавляем метод для завершения компании
    async completeCampaign(campaignId) {
        try {
            const response = await fetch(`/api/campaigns/${campaignId}/complete`, {
                method: 'POST'
            });

            const result = await response.json();

            if (response.ok && result.success) {
                Utils.showNotification('success', 'Успех', 'Компания успешно завершена');
                await this.loadCampaigns();
            } else {
                throw new Error(result.message || 'Не удалось завершить компанию');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            Utils.showNotification('error', 'Ошибка', error.message);
        }
    }

    deleteCampaign(campaignId, campaignName) {
        const modal = document.getElementById('deleteConfirmModal');
        const nameElement = document.getElementById('deleteCampaignName');
        const confirmBtn = document.getElementById('confirmDeleteBtn');
        
        if (!modal || !nameElement || !confirmBtn) return;

        nameElement.textContent = campaignName;
        
        // Удаляем старые обработчики и добавляем новый
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
        
        newConfirmBtn.addEventListener('click', async () => {
            try {
                Utils.showLoading(true, 'Удаление кампании...');

                const response = await fetch(`/api/campaigns/${campaignId}`, {
                    method: 'DELETE',
                    credentials: 'same-origin'
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    Utils.showNotification('success', 'Успех', result.message);
                    bootstrap.Modal.getInstance(modal).hide();
                    await this.loadCampaigns();
                } else {
                    throw new Error(result.message || 'Не удалось удалить кампанию');
                }

            } catch (error) {
                console.error('Ошибка удаления:', error);
                Utils.showNotification('error', 'Ошибка', error.message);
            } finally {
                Utils.showLoading(false);
            }
        });

        new bootstrap.Modal(modal).show();
    }

    // Добавленный метод для отображения UTC времени
    startUTCClock() {
        this.updateUTCTime();
        this.utcTimeInterval = setInterval(() => {
            this.updateUTCTime();
        }, 1000);
    }

    // Обновляет отображение текущего UTC времени
    updateUTCTime() {
        const now = new Date();
        const utcTime = now.toLocaleTimeString('ru-RU', { 
            timeZone: 'UTC',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });

        const utcDate = now.toLocaleDateString('ru-RU', {
            timeZone: 'UTC',
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });

        // Обновляем все элементы с UTC временем
        const utcElements = document.querySelectorAll('.utc-time');
        utcElements.forEach(el => {
            el.textContent = `${utcDate}, ${utcTime}`;
        });
    }

    // Дополняем метод для форматирования дат с указанием UTC
    formatSchedule(campaign) {
        const startDate = new Date(campaign.start_date).toLocaleString('ru-RU', { timeZone: 'UTC' });
        const endDate = new Date(campaign.end_date).toLocaleString('ru-RU', { timeZone: 'UTC' });
        const postTime = new Date(`1970-01-01T${campaign.post_time}Z`).toLocaleString('ru-RU', { timeZone: 'UTC' });

        // Добавляем пометку UTC к отображаемому времени публикации
        return `${startDate} - ${endDate} в ${postTime} UTC`;
    }
}

// Создаем глобальный экземпляр менеджера
const campaignsManager = new CampaignsManager();

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM загружен, инициализация CampaignsManager');
    // Инициализация уже произошла в конструкторе
});

// Экспорт для использования в других модулях
window.campaignsManager = campaignsManager;

// Экспорт для использования в других модулях
window.campaignsManager = campaignsManager;

