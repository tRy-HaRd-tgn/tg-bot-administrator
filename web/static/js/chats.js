/**
 * Современный JavaScript для управления чатами
 */
class ChatsManager {
    constructor() {
        this.chats = [];
        this.filteredChats = [];
        this.selectedChats = new Set();
        this.currentPage = 1;
        this.itemsPerPage = 12;
        this.searchQuery = '';
        this.activeFilter = 'all';
        this.loading = false;
        this.deleteModal = null;
        this.chatToDelete = null;
    }

    /**
     * Инициализация менеджера
     */
    async init() {
        console.log('Инициализация ChatsManager...');
        this.bindEvents();
        await this.loadChats();
        this.restoreFilterFromStorage();
    }

    /**
     * Привязка событий
     */
    bindEvents() {
        // Кнопки управления
        this.bindElement('addChatBtn', 'click', () => this.showAddChatModal());
        this.bindElement('addChatEmptyBtn', 'click', () => this.showAddChatModal());
        this.bindElement('refreshChatsBtn', 'click', () => this.loadChats());
        this.bindElement('updateAllChatsBtn', 'click', () => this.updateAllChatsInfo());
        this.bindElement('retryLoadBtn', 'click', () => this.loadChats());

        // Форма добавления чата
        this.bindElement('addChatForm', 'submit', (e) => this.handleAddChat(e));

        // Поиск
        this.bindElement('chatSearch', 'input', (e) => this.handleSearch(e.target.value));
        this.bindElement('clearSearch', 'click', () => this.clearSearch());

        // Фильтры чатов
        document.querySelectorAll('.filter-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                this.setActiveFilter(e.currentTarget.dataset.filter);
            });
        });

        // Сброс формы при закрытии модального окна
        this.bindElement('addChatModal', 'hidden.bs.modal', () => this.resetAddChatForm());

        // Модал удаления
        this.bindElement('confirmDeleteBtn', 'click', () => this.performDelete());
    }

    /**
     * Вспомогательный метод для привязки событий
     */
    bindElement(id, event, handler) {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener(event, handler);
        }
    }

    /**
     * Загрузка списка чатов
     */
    async loadChats() {
        if (this.loading) return;

        this.loading = true;
        this.showLoadingState();

        try {
            const response = await fetch('/api/chats');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            this.chats = data.chats || [];
            
            this.updateFilterCounts();
            this.applyFilters();
            this.renderChats();
            
            console.log(`Загружено ${this.chats.length} чатов`);

        } catch (error) {
            console.error('Ошибка загрузки чатов:', error);
            this.showErrorState();
        } finally {
            this.loading = false;
        }
    }

    /**
     * Обновление счетчиков в фильтрах
     */
    updateFilterCounts() {
        const counts = {
            all: this.chats.length,
            regular: this.chats.filter(chat => chat.type === 'group').length,
            supergroup: this.chats.filter(chat => chat.type === 'supergroup' && !chat.is_forum).length,
            forum: this.chats.filter(chat => chat.is_forum === true).length
        };

        Object.keys(counts).forEach(filter => {
            const countElement = document.getElementById(`count-${filter}`);
            if (countElement) {
                countElement.textContent = counts[filter];
            }
        });
    }

    /**
     * Применение активного фильтра
     */
    setActiveFilter(filter) {
        this.activeFilter = filter;
        this.currentPage = 1;
        
        // Обновляем активную кнопку
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });
        
        // Сохраняем в localStorage
        localStorage.setItem('chatsActiveFilter', filter);
        
        this.applyFilters();
        this.renderChats();
    }

    /**
     * Восстановление фильтра из localStorage
     */
    restoreFilterFromStorage() {
        const savedFilter = localStorage.getItem('chatsActiveFilter');
        if (savedFilter && savedFilter !== this.activeFilter) {
            this.setActiveFilter(savedFilter);
        }
    }

    /**
     * Применение фильтров и поиска
     */
    applyFilters() {
        let filtered = this.chats;

        // Фильтр по типу чата
        if (this.activeFilter !== 'all') {
            filtered = filtered.filter(chat => {
                switch(this.activeFilter) {
                    case 'regular':
                        return chat.type === 'group';
                    case 'supergroup':
                        return chat.type === 'supergroup' && !chat.is_forum;
                    case 'forum':
                        return chat.is_forum === true;
                    default:
                        return true;
                }
            });
        }

        // Поиск по тексту
        if (this.searchQuery) {
            const query = this.searchQuery.toLowerCase();
            filtered = filtered.filter(chat => 
                (chat.title && chat.title.toLowerCase().includes(query)) || 
                (chat.username && chat.username.toLowerCase().includes(query)) ||
                (chat.description && chat.description.toLowerCase().includes(query)) ||
                String(chat.chat_id).includes(query)
            );
        }

        this.filteredChats = filtered;
    }

    /**
     * Обработка поиска
     */
    handleSearch(query) {
        this.searchQuery = query.trim();
        this.currentPage = 1;
        this.applyFilters();
        this.renderChats();
    }

    /**
     * Очистка поиска
     */
    clearSearch() {
        const searchInput = document.getElementById('chatSearch');
        if (searchInput) {
            searchInput.value = '';
            this.handleSearch('');
        }
    }

    /**
     * Отображение чатов
     */
    renderChats() {
        const container = document.getElementById('chatsList');
        if (!container) return;

        // Скрываем все состояния
        this.hideAllStates();

        // Проверка на пустой список
        if (this.filteredChats.length === 0) {
            this.showEmptyState();
            return;
        }

        // Пагинация
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const paginatedChats = this.filteredChats.slice(startIndex, endIndex);

        // Генерация HTML
        container.innerHTML = paginatedChats.map(chat => this.renderChatCard(chat)).join('');

        // Привязываем события к карточкам
        this.bindChatEvents();

        // Обновление пагинации
        this.updatePagination();

        // Показываем контейнер с чатами
        document.getElementById('chatsContainer').style.display = 'block';
    }

    /**
     * Создание HTML карточки чата
     */
    renderChatCard(chat) {
        const typeConfig = this.getChatTypeConfig(chat);
        const statusConfig = this.getStatusConfig(chat.bot_status);
        
        return `
            <div class="chat-card" data-chat-id="${chat.id}">
                <div class="chat-header">
                    <div class="chat-avatar">
                        ${chat.avatar_url ? 
                            `<img src="${chat.avatar_url}" alt="Avatar">` : 
                            `<div class="chat-avatar-placeholder ${typeConfig.avatarClass}">
                                <i class="fa-solid ${typeConfig.icon}"></i>
                            </div>`
                        }
                    </div>
                    <div class="chat-info">
                        <h3 class="chat-title" title="${this.escapeHtml(chat.title)}">
                            ${this.escapeHtml(chat.title) || 'Без названия'}
                        </h3>
                        <div class="chat-badges">
                            <span class="chat-badge ${typeConfig.badgeClass}">${chat.is_forum ? 'Форум' : typeConfig.label}</span>
                            ${chat.bot_is_admin ? 
                                '<span class="chat-badge status-admin">Админ</span>' : 
                                '<span class="chat-badge status-member">Участник</span>'
                            }
                        </div>
                    </div>
                </div>
                
                <div class="chat-body">
                    <div class="chat-details">
                        <div class="chat-detail">
                            <i class="fa-solid fa-hashtag"></i>
                            <strong>ID:</strong>
                            <span class="chat-id-copy" onclick="Utils.copyToClipboard('${chat.chat_id}')" title="Нажмите для копирования">
                                ${chat.chat_id} <i class="fa-regular fa-copy"></i>
                            </span>
                        </div>

                        ${chat.username ? `
                            <div class="chat-detail">
                                <i class="fa-solid fa-at"></i>
                                <strong>Username:</strong> @${this.escapeHtml(chat.username)}
                            </div>
                        ` : ''}

                        <div class="chat-detail">
                            <i class="fa-solid fa-users"></i>
                            <strong>Участников:</strong> ${chat.member_count || 'Неизвестно'}
                        </div>

                        <div class="chat-detail">
                            <i class="fa-solid fa-clock"></i>
                            <strong>Обновлено:</strong> ${this.formatDate(chat.updated_at)}
                        </div>
                    </div>
                </div>
                
                <div class="chat-footer">
                    <div class="chat-actions">
                        <button class="chat-action-btn update" data-chat-id="${chat.id}" title="Обновить информацию">
                            <i class="fa-solid fa-sync"></i>
                        </button>
                        <button class="chat-action-btn test" data-chat-id="${chat.id}" title="Отправить тестовое сообщение">
                            <i class="fa-solid fa-paper-plane"></i>
                        </button>
                        <button class="chat-action-btn info" data-chat-id="${chat.id}" title="Подробная информация">
                            <i class="fa-solid fa-info"></i>
                        </button>
                        <button class="chat-action-btn delete" data-chat-id="${chat.id}" title="Удалить чат">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Форматирование прав бота
     */
    formatPermissions(permissions) {
        const importantPerms = ['can_delete_messages', 'can_pin_messages', 'can_manage_topics'];
        const activePerms = importantPerms.filter(perm => permissions[perm]);
        
        if (activePerms.length === 0) return 'Базовые';
        if (activePerms.length >= 3) return 'Полные';
        return `${activePerms.length} из 3`;
    }

    /**
     * Привязка событий к карточкам чатов
     */
    bindChatEvents() {
        // Обновление чата
        document.querySelectorAll('.chat-action-btn.update').forEach(button => {
            button.addEventListener('click', (e) => {
                const chatId = e.target.closest('[data-chat-id]').dataset.chatId;
                this.updateChatInfo(chatId);
            });
        });

        // Тестирование чата
        document.querySelectorAll('.chat-action-btn.test').forEach(button => {
            button.addEventListener('click', (e) => {
                const chatId = e.target.closest('[data-chat-id]').dataset.chatId;
                this.testChat(chatId);
            });
        });

        // Детали чата
        document.querySelectorAll('.chat-action-btn.info').forEach(button => {
            button.addEventListener('click', (e) => {
                const chatId = e.target.closest('[data-chat-id]').dataset.chatId;
                this.showChatDetails(chatId);
            });
        });

        // Удаление чата
        document.querySelectorAll('.chat-action-btn.delete').forEach(button => {
            button.addEventListener('click', (e) => {
                const chatId = e.target.closest('[data-chat-id]').dataset.chatId;
                this.confirmDeleteChat(chatId);
            });
        });
    }

    /**
     * Показ модального окна добавления чата
     */
    showAddChatModal() {
        const modal = document.getElementById('addChatModal');
        if (modal) {
            // Используем Bootstrap Modal
            const bsModal = bootstrap.Modal.getOrCreateInstance(modal);
            bsModal.show();
        }
    }

    /**
     * Обработка добавления чата
     */
    async handleAddChat(event) {
        event.preventDefault();
        const form = event.target;
        const input = form.querySelector('input[name="chat_id"]');
        if (!input || !input.value.trim()) {
            Utils.showNotification('error', 'Ошибка', 'Введите ID чата');
            return;
        }
        const chatId = input.value.trim();

        // Показываем загрузку
        Utils.showLoading(true, 'Добавление чата...');
        try {
            const response = await fetch('/api/chats', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ chat_id: chatId })
            });
            const data = await response.json();
            Utils.showLoading(false);

            if (response.ok && data.success) {
                Utils.showNotification('success', 'Чат добавлен', data.message || 'Чат успешно добавлен');
                // Закрываем модал
                const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('addChatModal'));
                modal.hide();
                // Обновляем список чатов
                await this.loadChats();
            } else {
                Utils.showNotification('error', 'Ошибка', data.error || data.message || 'Не удалось добавить чат');
            }
        } catch (error) {
            Utils.showLoading(false);
            Utils.showNotification('error', 'Ошибка', error.message || 'Ошибка сети');
        }
    }

    /**
     * Сброс формы добавления чата
     */
    resetAddChatForm() {
        const form = document.getElementById('addChatForm');
        if (form) {
            form.reset();
        }
    }

    /**
     * Обновление информации о чате
     */
    async updateChatInfo(chatId) {
        const button = document.querySelector(`[data-chat-id="${chatId}"] .chat-action-btn.update`);
        if (!button) return;

        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
        button.disabled = true;

        try {
            const response = await fetch(`/api/chats/${chatId}/update-info`, {
                method: 'POST'
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.showNotification('success', 'Успех', result.message);
                await this.loadChats();
            } else {
                throw new Error(result.error || 'Не удалось обновить информацию о чате');
            }

        } catch (error) {
            console.error('Ошибка обновления чата:', error);
            this.showNotification('error', 'Ошибка', error.message);
        } finally {
            button.innerHTML = originalHTML;
            button.disabled = false;
        }
    }

    /**
     * Тестирование чата (отправка тестового сообщения)
     */
    async testChat(chatId) {
        const chat = this.chats.find(c => c.id === chatId);
        if (!chat) return;

        const button = document.querySelector(`[data-chat-id="${chatId}"] .chat-action-btn.test`);
        if (!button) return;

        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
        button.disabled = true;

        try {
            const response = await fetch(`/api/chats/${chatId}/test`, {
                method: 'POST'
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.showNotification('success', 'Успех', result.message);
            } else {
                throw new Error(result.message || 'Не удалось отправить тестовое сообщение');
            }

        } catch (error) {
            console.error('Ошибка тестирования чата:', error);
            this.showNotification('error', 'Ошибка', error.message);
        } finally {
            button.innerHTML = originalHTML;
            button.disabled = false;
        }
    }

    /**
     * Показ деталей чата
     */
    showChatDetails(chatId) {
        const chat = this.chats.find(c => c.id === chatId);
        if (!chat) return;

        const formatPermissions = (permissions) => {
            if (!permissions) return 'Нет информации';
            return Object.entries(permissions)
                .filter(([_, value]) => value === true)
                .map(([key]) => key.replace('can_', '')
                    .split('_')
                    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(' ')
                )
                .join(', ');
        };

        const formatDate = (dateString) => {
            return new Date(dateString).toLocaleString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        };

        const modalContent = `
            <div class="modal fade" id="chatDetailsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title d-flex align-items-center gap-2">
                                <i class="fa-solid fa-circle-info text-primary"></i>
                                Информация о чате "${chat.title}"
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="chat-info-sections">
                                <!-- Основная информация -->
                                <div class="info-section mb-4">
                                    <h6 class="section-title">
                                        <i class="fa-solid fa-info-circle me-2"></i>
                                        Основная информация
                                    </h6>
                                    <div class="info-grid">
                                        <div class="info-item">
                                            <strong>ID чата:</strong>
                                            <span class="chat-id-copy" onclick="Utils.copyToClipboard('${chat.chat_id}')">
                                                ${chat.chat_id} <i class="fa-regular fa-copy ms-1"></i>
                                            </span>
                                        </div>
                                        <div class="info-item">
                                            <strong>Тип:</strong>
                                            <span>${chat.type === 'supergroup' ? 'Супергруппа' : chat.type}</span>
                                        </div>
                                        ${chat.username ? `
                                            <div class="info-item">
                                                <strong>Username:</strong>
                                                <span>@${chat.username}</span>
                                            </div>
                                        ` : ''}
                                        ${chat.invite_link ? `
                                            <div class="info-item">
                                                <strong>Ссылка:</strong>
                                                <a href="${chat.invite_link}" target="_blank">${chat.invite_link}</a>
                                            </div>
                                        ` : ''}
                                        <div class="info-item">
                                            <strong>Участников:</strong>
                                            <span>${chat.member_count || 'Неизвестно'}</span>
                                        </div>
                                        <div class="info-item">
                                            <strong>Создано:</strong>
                                            <span>${formatDate(chat.created_at)}</span>
                                        </div>
                                        <div class="info-item">
                                            <strong>Обновлено:</strong>
                                            <span>${formatDate(chat.updated_at)}</span>
                                        </div>
                                    </div>
                                </div>

                                <!-- Разрешения бота -->
                                <div class="info-section mb-4">
                                    <h6 class="section-title">
                                        <i class="fa-solid fa-robot me-2"></i>
                                        Разрешения бота
                                    </h6>
                                    <div class="permissions-box">
                                        ${formatPermissions(chat.bot_permissions)}
                                    </div>
                                </div>

                                <!-- Разрешения группы -->
                                <div class="info-section mb-4">
                                    <h6 class="section-title">
                                        <i class="fa-solid fa-users-gear me-2"></i>
                                        Разрешения группы
                                    </h6>
                                    <div class="permissions-box">
                                        ${formatPermissions(chat.permissions)}
                                    </div>
                                </div>

                                <!-- Дополнительные настройки -->
                                <div class="info-section">
                                    <h6 class="section-title">
                                        <i class="fa-solid fa-sliders me-2"></i>
                                        Дополнительные настройки
                                    </h6>
                                    <div class="info-grid">
                                        <div class="info-item">
                                            <strong>Форум:</strong>
                                            <span>${chat.is_forum ? 'Да' : 'Нет'}</span>
                                        </div>
                                        <div class="info-item">
                                            <strong>Защита контента:</strong>
                                            <span>${chat.has_protected_content ? 'Включена' : 'Отключена'}</span>
                                        </div>
                                        <div class="info-item">
                                            <strong>Медленный режим:</strong>
                                            <span>${chat.slow_mode_delay ? `${chat.slow_mode_delay} сек.` : 'Отключен'}</span>
                                        </div>
                                        <div class="info-item">
                                            <strong>Макс. реакций:</strong>
                                            <span>${chat.max_reaction_count || 'Не указано'}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Удаляем предыдущий модал если есть
        const existingModal = document.getElementById('chatDetailsModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Добавляем новый модал
        document.body.insertAdjacentHTML('beforeend', modalContent);
        
        // Показываем модал
        const modal = new bootstrap.Modal(document.getElementById('chatDetailsModal'));
        modal.show();
    }

    /**
     * Подтверждение удаления чата
     */
    confirmDeleteChat(chatId) {
        const chat = this.chats.find(c => c.id === chatId);
        if (!chat) return;

        if (confirm(`Вы действительно хотите удалить чат "${chat.title}"?\n\nЭто действие нельзя отменить.`)) {
            this.deleteChat(chatId);
        }
    }

    /**
     * Удаление чата
     */
    async deleteChat(chatId) {
        try {
            const response = await fetch(`/api/chats/${chatId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.showNotification('success', 'Успех', result.message);
                await this.loadChats();
            } else {
                throw new Error(result.error || 'Не удалось удалить чат');
            }

        } catch (error) {
            console.error('Ошибка удаления чата:', error);
            this.showNotification('error', 'Ошибка', error.message);
        }
    }

    /**
     * Массовое обновление информации о всех чатах
     */
    async updateAllChatsInfo() {
        if (this.loading) return;

        // Показываем модальное окно с прогрессом
        const modalHtml = `
            <div class="modal fade" id="updateAllChatsModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Обновление информации о чатах</h5>
                        </div>
                        <div class="modal-body text-center">
                            <div class="spinner-border text-primary mb-3" role="status"></div>
                            <p id="updateProgress">Обновление информации о чатах...</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modal = new bootstrap.Modal(document.getElementById('updateAllChatsModal'));
        modal.show();

        try {
            const response = await fetch('/api/chats/update-all-info', {
                method: 'POST'
            });

            const result = await response.json();

            const progressElement = document.getElementById('updateProgress');
            if (progressElement) {
                if (result.success) {
                    progressElement.innerHTML = `
                        <div class="alert alert-success mb-0">
                            <i class="fa-solid fa-check-circle me-2"></i>
                            ${result.message}
                        </div>
                    `;

                    setTimeout(() => {
                        modal.hide();
                        this.loadChats();
                    }, 2000);
                } else {
                    throw new Error(result.error || 'Ошибка при обновлении чатов');
                }
            }

        } catch (error) {
            console.error('Ошибка массового обновления:', error);
            this.showNotification('error', 'Ошибка', error.message);
            modal.hide();
        } finally {
            // Удаляем модал через 3 секунды
            setTimeout(() => {
                const modalElement = document.getElementById('updateAllChatsModal');
                if (modalElement) {
                    modalElement.remove();
                }
            }, 3000);
        }
    }

    /**
     * Обновление пагинации
     */
    updatePagination() {
        const container = document.getElementById('chatsPagination');
        if (!container) return;

        const totalPages = Math.ceil(this.filteredChats.length / this.itemsPerPage);

        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let paginationHTML = '';

        // Предыдущая страница
        paginationHTML += `
            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${this.currentPage - 1}">Назад</a>
            </li>
        `;

        // Страницы
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= this.currentPage - 2 && i <= this.currentPage + 2)) {
                paginationHTML += `
                    <li class="page-item ${i === this.currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" data-page="${i}">${i}</a>
                    </li>
                `;
            } else if (i === this.currentPage - 3 || i === this.currentPage + 3) {
                paginationHTML += '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }
        }

        // Следующая страница
        paginationHTML += `
            <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${this.currentPage + 1}">Вперед</a>
            </li>
        `;

        container.innerHTML = paginationHTML;

        // Привязываем события
        container.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.target.dataset.page);
                if (page && page !== this.currentPage && page >= 1 && page <= totalPages) {
                    this.currentPage = page;
                    this.renderChats();
                }
            });
        });
    }

    /**
     * Состояния интерфейса
     */
    showLoadingState() {
        this.hideAllStates();
        document.getElementById('loadingState').style.display = 'block';
    }

    showEmptyState() {
        this.hideAllStates();
        document.getElementById('emptyState').style.display = 'block';
        // Привязываем событие к кнопке в пустом состоянии
        this.bindElement('addChatEmptyBtn', 'click', () => this.showAddChatModal());
    }

    showErrorState() {
        this.hideAllStates();
        document.getElementById('errorState').style.display = 'block';
    }

    hideAllStates() {
        ['loadingState', 'emptyState', 'errorState', 'chatsContainer'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.style.display = 'none';
            }
        });
    }

    // Вспомогательные методы
    getChatTypeConfig(chat) {
        if (chat.is_forum) {
            return {
                icon: 'fa-comments',
                label: 'Форум',
                badgeClass: 'type-forum',
                avatarClass: 'type-forum'
            };
        }

        switch (chat.type) {
            case 'channel':
                return {
                    icon: 'fa-bullhorn',
                    label: 'Канал',
                    badgeClass: 'type-channel',
                    avatarClass: 'type-channel'
                };
            case 'group':
                return {
                    icon: 'fa-users',
                    label: 'Группа',
                    badgeClass: 'type-group',
                    avatarClass: 'type-group'
                };
            case 'supergroup':
                return {
                    icon: 'fa-user-group',
                    label: 'Супергруппа',
                    badgeClass: 'type-supergroup',
                    avatarClass: 'type-supergroup'
                };
            default:
                return {
                    icon: 'fa-comments',
                    label: 'Неизвестно',
                    badgeClass: 'type-group',
                    avatarClass: 'type-group'
                };
        }
    }

    getStatusConfig(status) {
        switch (status) {
            case 'creator':
                return { label: 'Создатель' };
            case 'administrator':
                return { label: 'Администратор' };
            case 'member':
                return { label: 'Участник' };
            case 'restricted':
                return { label: 'Ограничен' };
            case 'left':
                return { label: 'Покинул' };
            case 'kicked':
                return { label: 'Удалён' };
            default:
                return { label: 'Неизвестно' };
        }
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatDate(dateString) {
        if (!dateString) return 'Неизвестно';

        try {
            const date = new Date(dateString);
            return date.toLocaleString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return dateString;
        }
    }

    showNotification(type, title, message) {
        if (typeof Utils !== 'undefined' && Utils.showNotification) {
            Utils.showNotification(type, title, message);
        } else {
            alert(`${title}: ${message}`);
        }
    }
}

// Создаем глобальный экземпляр менеджера
const chatsManager = new ChatsManager();

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
    chatsManager.init();
});

// Экспорт для использования в других модулях
window.chatsManager = chatsManager;

// Добавляем стили для копируемого ID
document.addEventListener('DOMContentLoaded', () => {
    const style = document.createElement('style');
    style.textContent = `
        .chat-id-code {
            background-color: #f8f9fa;
            padding: 2px 5px;
            border-radius: 4px;
            border: 1px solid #e9ecef;
            font-family: monospace;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .chat-id-code:hover {
            background-color: #e9ecef;
        }
        .placeholder-avatar {
            flex-shrink: 0;
        }
        .chat-card {
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .chat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
    `;
    document.head.appendChild(style);
});

// Добавляем функцию показа уведомления о копировании
HTMLElement.prototype.showCopyNotification = function() {
    Utils.showNotification('success', 'Скопировано', 'ID чата скопирован в буфер обмена');
};
