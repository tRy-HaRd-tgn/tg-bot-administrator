/**
 * JavaScript для создания новой кампании
 */
class NewCampaignManager {
    constructor() {
        this.selectedChats = new Map();
        this.selectedFiles = [];
        this.buttons = [];
        this.isSubmitting = false;
        this.chats = [];
        this.utcTimeInterval = null;
        this.repeatSettings = null;
        
        this.init();
    }    init() {
        console.log('Инициализация NewCampaignManager...');
        this.bindEvents();
        this.loadChats();
        this.updateCharCounter();
        this.setDefaultDates();
        this.startUTCClock();
    }

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

    startUTCClock() {
        this.updateUTCTime();
        this.utcTimeInterval = setInterval(() => {
            this.updateUTCTime();
        }, 1000);
    }

    bindEvents() {
        // Форма
        const form = document.getElementById('campaignForm');
        if (form) {
            form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // Кнопки действий
        this.bindElement('cancelBtn', 'click', () => this.cancel());

        // Повторение
        this.bindElement('repeatEnabled', 'change', (e) => this.toggleRepeatOptions(e.target.checked));
        
        // Вкладки повторения
        document.querySelectorAll('.repeat-tab').forEach(tab => {
            tab.addEventListener('click', (e) => this.switchRepeatTab(e.target.dataset.tab));
        });

        // Поиск чатов
        this.bindElement('chatsSearch', 'input', (e) => this.searchChats(e.target.value));

        // Медиафайлы
        this.bindElement('mediaUploadArea', 'click', () => this.triggerFileInput());
        this.bindElement('mediaUploadArea', 'dragover', (e) => this.handleDragOver(e));
        this.bindElement('mediaUploadArea', 'drop', (e) => this.handleDrop(e));
        this.bindElement('mediaFiles', 'change', (e) => this.handleFileSelect(e));

        // Кнопки
        this.bindElement('addButton', 'click', () => this.addButton());

        // Предпросмотр
        this.bindElement('previewButton', 'click', () => this.showPreview());

        // Счетчик символов
        this.bindElement('messageText', 'input', () => this.updateCharCounter());

        // Валидация дат
        this.bindElement('startDate', 'change', () => this.validateDates());
        this.bindElement('endDate', 'change', () => this.validateDates());

        // Дни недели
        document.querySelectorAll('input[name="weekday"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.updateWeekdaysSelection());
        });

        // Обработчик для кнопки настройки повтора
        const repeatSettingsBtn = document.getElementById('configureRepeatBtn');
        if (repeatSettingsBtn) {
            repeatSettingsBtn.addEventListener('click', () => {
                if (!window.repeatModal) return;
                
                window.repeatModal.setCallback((settings) => {
                    this.repeatSettings = settings;
                    this.updateRepeatSettingsDisplay();
                });
                
                if (this.repeatSettings) {
                    window.repeatModal.loadSettings(this.repeatSettings);
                }
                
                window.repeatModal.show();
            });
        }

        // Переключатель автоповтора
        const repeatToggle = document.getElementById('repeatEnabled');
        if (repeatToggle) {
            repeatToggle.addEventListener('change', (e) => {
                this.toggleRepeatOptions(e.target.checked);
            });
        }
    }

    bindElement(id, event, handler) {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener(event, handler);
        }
    }

    setDefaultDates() {
        const today = new Date();
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        
        const nextWeek = new Date(today);
        nextWeek.setDate(nextWeek.getDate() + 7);

        const startDateInput = document.getElementById('startDate');
        const endDateInput = document.getElementById('endDate');

        if (startDateInput) {
            startDateInput.value = tomorrow.toISOString().split('T')[0];
        }
        if (endDateInput) {
            endDateInput.value = nextWeek.toISOString().split('T')[0];
        }
    }

    async loadChats() {
        try {
            Utils.showLoading(true, 'Загрузка чатов...');

            const response = await fetch('/api/chats');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            this.chats = data.chats || [];
            
            this.renderChats();
            
        } catch (error) {
            console.error('Ошибка загрузки чатов:', error);
            this.showChatsError('Не удалось загрузить список чатов');
        } finally {
            Utils.showLoading(false);
        }
    }

    renderChats() {
        const container = document.getElementById('chatsContainer');
        if (!container) return;

        if (this.chats.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-comments fa-3x"></i>
                    <h6>Нет доступных чатов</h6>
                    <p>Сначала добавьте чаты в систему</p>
                    <a href="/chats" class="btn btn-primary btn-sm">
                        <i class="fa-solid fa-plus me-1"></i>Добавить чаты
                    </a>
                </div>
            `;
            return;
        }

        container.innerHTML = this.chats.map(chat => this.renderChatItem(chat)).join('');
        this.bindChatEvents();
    }

    renderChatItem(chat) {
        const isSelected = this.selectedChats.has(chat.id);
        const typeConfig = this.getChatTypeConfig(chat);
        
        return `
            <div class="chat-item ${isSelected ? 'selected' : ''}" data-chat-id="${chat.id}">
                <div class="chat-item-content">
                    <div class="chat-avatar">
                        ${chat.avatar_url ? 
                            `<img src="${chat.avatar_url}" alt="Avatar">` : 
                            `<div class="chat-avatar-placeholder ${typeConfig.avatarClass}">
                                <i class="fa-solid ${typeConfig.icon}"></i>
                            </div>`
                        }
                    </div>
                    <div class="chat-info">
                        <h6 class="chat-title">${Utils.escapeHtml(chat.title)}</h6>
                        <div class="chat-badges">
                            <span class="chat-badge ${typeConfig.badgeClass}">${typeConfig.label}</span>
                            ${chat.bot_is_admin ? 
                                '<span class="chat-badge status-admin">Админ</span>' : 
                                '<span class="chat-badge status-member">Участник</span>'
                            }
                        </div>
                        <div class="chat-details">
                            <small>ID: ${chat.chat_id}</small>
                            ${chat.member_count ? `<small>• ${chat.member_count} участников</small>` : ''}
                        </div>
                    </div>
                </div>
                <div class="chat-actions">
                    <button type="button" class="chat-select-btn ${isSelected ? 'selected' : ''}" 
                            onclick="newCampaignManager.toggleChatSelection('${chat.id}')">
                        <i class="fa-solid ${isSelected ? 'fa-check' : 'fa-plus'}"></i>
                    </button>
                </div>
                ${chat.is_forum ? `
                    <div class="forum-topics" style="display: ${isSelected ? 'block' : 'none'};">
                        <div class="topics-header">
                            <small>Тема форума (опционально):</small>
                        </div>
                        <div class="topics-list">
                            <input type="number" placeholder="ID темы" class="topic-input" min="1">
                            <small>Оставьте пустым для общей темы</small>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    bindChatEvents() {
        document.querySelectorAll('.chat-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.chat-select-btn') && !e.target.closest('.topic-input')) {
                    const chatId = item.dataset.chatId;
                    this.toggleChatSelection(chatId);
                }
            });
        });
    }

    toggleChatSelection(chatId) {
        const chat = this.chats.find(c => c.id === chatId);
        if (!chat) return;

        if (this.selectedChats.has(chatId)) {
            this.selectedChats.delete(chatId);
        } else {
            let threadId = null;
            if (chat.is_forum) {
                const chatItem = document.querySelector(`[data-chat-id="${chatId}"]`);
                const topicInput = chatItem?.querySelector('.topic-input');
                if (topicInput && topicInput.value) {
                    threadId = parseInt(topicInput.value);
                }
            }

            this.selectedChats.set(chatId, {
                ...chat,
                thread_id: threadId,
                is_active: true
            });
        }

        this.updateChatUI(chatId);
        this.updateSelectedChatsDisplay();
    }

    updateChatUI(chatId) {
        const chatItem = document.querySelector(`[data-chat-id="${chatId}"]`);
        const selectBtn = chatItem?.querySelector('.chat-select-btn');
        
        if (!chatItem || !selectBtn) return;

        const isSelected = this.selectedChats.has(chatId);
        
        chatItem.classList.toggle('selected', isSelected);
        selectBtn.classList.toggle('selected', isSelected);
        selectBtn.innerHTML = `<i class="fa-solid ${isSelected ? 'fa-check' : 'fa-plus'}"></i>`;

        const forumTopics = chatItem.querySelector('.forum-topics');
        if (forumTopics) {
            forumTopics.style.display = isSelected ? 'block' : 'none';
        }
    }

    updateSelectedChatsDisplay() {
        const countElement = document.getElementById('selectedChatsCount');
        const listElement = document.getElementById('selectedChatsList');

        if (countElement) {
            countElement.textContent = this.selectedChats.size;
        }

        if (listElement) {
            if (this.selectedChats.size === 0) {
                listElement.innerHTML = '<p class="text-muted">Чаты не выбраны</p>';
            } else {
                listElement.innerHTML = Array.from(this.selectedChats.values())
                    .map(chat => `
                        <div class="selected-chat-item">
                            <span class="chat-name">${Utils.escapeHtml(chat.title)}</span>
                            ${chat.thread_id ? `<small class="thread-id">Тема: ${chat.thread_id}</small>` : ''}
                            <button type="button" class="remove-chat-btn" onclick="newCampaignManager.toggleChatSelection('${chat.id}')">
                                <i class="fa-solid fa-times"></i>
                            </button>
                        </div>
                    `).join('');
            }
        }
    }

    searchChats(query) {
        const filteredChats = this.chats.filter(chat => 
            chat.title.toLowerCase().includes(query.toLowerCase()) ||
            chat.chat_id.toString().includes(query)
        );

        const container = document.getElementById('chatsContainer');
        if (container) {
            container.innerHTML = filteredChats.map(chat => this.renderChatItem(chat)).join('');
            this.bindChatEvents();
        }
    }

    toggleRepeatOptions(enabled) {
        const options = document.getElementById('repeatOptions');
        if (options) {
            options.style.display = enabled ? 'block' : 'none';
        }
    }

    switchRepeatTab(tabName) {
        document.querySelectorAll('.repeat-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });

        document.querySelectorAll('.repeat-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tabName}Tab`);
        });
    }

    updateWeekdaysSelection() {
        const checkboxes = document.querySelectorAll('input[name="weekday"]:checked');
        // ...existing code...
    }

    triggerFileInput() {
        const input = document.getElementById('mediaFiles');
        if (input) {
            input.click();
        }
    }

    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('drag-over');
    }

    handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');
        
        const files = Array.from(e.dataTransfer.files);
        this.processFiles(files);
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.processFiles(files);
    }

    processFiles(files) {
        const validFiles = files.filter(file => this.validateFile(file));
        
        if (validFiles.length === 0) {
            Utils.showNotification('error', 'Ошибка', 'Не выбраны подходящие файлы');
            return;
        }

        const images = validFiles.filter(f => f.type.startsWith('image/'));
        const videos = validFiles.filter(f => f.type.startsWith('video/'));

        if (images.length > 8) {
            Utils.showNotification('error', 'Ошибка', 'Максимум 8 изображений');
            return;
        }

        if (videos.length > 1) {
            Utils.showNotification('error', 'Ошибка', 'Максимум 1 видео');
            return;
        }

        if (images.length > 0 && videos.length > 0) {
            Utils.showNotification('error', 'Ошибка', 'Нельзя одновременно загружать фото и видео');
            return;
        }

        this.selectedFiles = validFiles;
        this.renderMediaPreview();
    }

    validateFile(file) {
        const maxSize = 20 * 1024 * 1024; // 20MB
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'video/mp4', 'video/mov', 'video/avi'];

        if (file.size > maxSize) {
            Utils.showNotification('error', 'Ошибка', `Файл ${file.name} слишком большой (макс. 20MB)`);
            return false;
        }

        if (!allowedTypes.includes(file.type)) {
            Utils.showNotification('error', 'Ошибка', `Неподдерживаемый тип файла: ${file.type}`);
            return false;
        }

        return true;
    }

    renderMediaPreview() {
        const preview = document.getElementById('mediaPreview');
        if (!preview) return;

        if (this.selectedFiles.length === 0) {
            preview.innerHTML = '';
            return;
        }

        preview.innerHTML = `
            <div class="media-preview-header">
                <h6>Выбранные файлы: ${this.selectedFiles.length}</h6>
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="newCampaignManager.clearMedia()">
                    <i class="fa-solid fa-trash me-1"></i>Очистить
                </button>
            </div>
            <div class="media-preview-grid">
                ${this.selectedFiles.map((file, index) => this.renderMediaItem(file, index)).join('')}
            </div>
        `;
    }

    renderMediaItem(file, index) {
        const isImage = file.type.startsWith('image/');
        const fileUrl = URL.createObjectURL(file);
        
        return `
            <div class="media-item" data-index="${index}">
                ${isImage ? 
                    `<img src="${fileUrl}" alt="${file.name}" class="media-thumbnail">` :
                    `<video src="${fileUrl}" class="media-thumbnail" controls></video>`
                }
                <div class="media-info">
                    <div class="media-name">${file.name}</div>
                    <div class="media-size">${Utils.formatFileSize(file.size)}</div>
                </div>
                <button type="button" class="remove-media-btn" onclick="newCampaignManager.removeMedia(${index})">
                    <i class="fa-solid fa-times"></i>
                </button>
            </div>
        `;
    }

    removeMedia(index) {
        this.selectedFiles.splice(index, 1);
        this.renderMediaPreview();
    }

    clearMedia() {
        this.selectedFiles = [];
        this.renderMediaPreview();
        
        const input = document.getElementById('mediaFiles');
        if (input) {
            input.value = '';
        }
    }

    addButton() {
        const button = {
            id: Date.now(),
            text: '',
            url: ''
        };
        
        this.buttons.push(button);
        this.renderButtons();
        
        // Фокус на новом поле ввода после добавления кнопки
        setTimeout(() => {
            const lastButtonItem = document.querySelector(`.button-item[data-button-id="${button.id}"] input`);
            if (lastButtonItem) {
                lastButtonItem.focus();
            }
        }, 10);
    }

    renderButtons() {
        const container = document.getElementById('buttonsContainer');
        if (!container) return;

        if (this.buttons.length === 0) {
            container.innerHTML = '<p class="text-muted">Кнопки не добавлены</p>';
            return;
        }

        container.innerHTML = this.buttons.map((button) => `
            <div class="button-item" data-button-id="${button.id}">
                <div class="button-inputs">
                    <div class="form-group">
                        <label class="form-label">Текст кнопки</label>
                        <input type="text" class="form-input" placeholder="Текст кнопки" 
                               value="${Utils.escapeHtml(button.text)}" 
                               oninput="newCampaignManager.updateButton(${button.id}, 'text', this.value)">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Ссылка</label>
                        <input type="url" class="form-input" placeholder="https://example.com" 
                               value="${Utils.escapeHtml(button.url)}"
                               oninput="newCampaignManager.updateButton(${button.id}, 'url', this.value)">
                    </div>
                </div>
                <button type="button" class="remove-button-btn" onclick="newCampaignManager.removeButton(${button.id})">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </div>
        `).join('');
    }

    updateButton(id, field, value) {
        const button = this.buttons.find(b => b.id === id);
        if (button) {
            button[field] = value;
            
            // Обновляем предпросмотр, если он активен
            const previewContainer = document.getElementById('messagePreview');
            if (previewContainer && previewContainer.style.display !== 'none') {
                this.showPreview();
            }
        }
    }

    showPreview() {
        // Получаем текст из Telegram редактора
        const messageText = window.telegramEditor ? 
            window.telegramEditor.getValue() : 
            document.getElementById('messageText').value;
            
        if (!messageText.trim()) {
            Utils.showNotification('warning', 'Предупреждение', 'Введите текст сообщения для предпросмотра');
            return;
        }

        const previewContainer = document.getElementById('messagePreview');
        if (!previewContainer) return;

        const previewHtml = this.generatePreviewHtml(messageText);
        previewContainer.innerHTML = previewHtml;
        previewContainer.style.display = 'block';

        const previewButton = document.getElementById('previewButton');
        if (previewButton) {
            previewButton.innerHTML = '<i class="fa-solid fa-eye-slash me-2"></i>Скрыть предпросмотр';
            previewButton.onclick = () => this.hidePreview();
        }
    }

    hidePreview() {
        const previewContainer = document.getElementById('messagePreview');
        if (previewContainer) {
            previewContainer.style.display = 'none';
        }

        const previewButton = document.getElementById('previewButton');
        if (previewButton) {
            previewButton.innerHTML = '<i class="fa-solid fa-eye me-2"></i>Показать предпросмотр';
            previewButton.onclick = () => this.showPreview();
        }
    }

    generatePreviewHtml(messageText) {
        return `
            <div class="telegram-message-preview">
                <div class="telegram-message-header">
                    <div class="telegram-message-avatar">TG</div>
                    <span>AutoPosting Bot</span>
                </div>
                <div class="telegram-message-body">
                    ${this.selectedFiles.length > 0 ? this.generateMediaPreviewHtml() : ''}
                    <div class="telegram-message-text">${this.formatMessageText(messageText)}</div>
                    ${this.generateButtonsPreviewHtml()}
                    <div class="telegram-message-time">${new Date().toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'})}</div>
                </div>
            </div>
        `;
    }

    generateMediaPreviewHtml() {
        // ...existing code...
        if (this.selectedFiles.length === 0) return '';

        const isVideo = this.selectedFiles[0].type.startsWith('video/');
        
        if (isVideo) {
            const videoUrl = URL.createObjectURL(this.selectedFiles[0]);
            return `<div class="telegram-message-media"><video src="${videoUrl}" controls style="width: 100%; max-height: 200px; border-radius: 8px;"></video></div>`;
        }

        const photoUrls = this.selectedFiles.map(file => URL.createObjectURL(file));
        
        if (photoUrls.length === 1) {
            return `<div class="telegram-message-media"><img src="${photoUrls[0]}" style="width: 100%; max-height: 200px; object-fit: cover; border-radius: 8px;"></div>`;
        }

        return `<div class="telegram-message-media"><div class="telegram-message-media-group">${photoUrls.slice(0, 4).map(url => `<img src="${url}">`).join('')}</div></div>`;
    }

    generateButtonsPreviewHtml() {
        if (this.buttons.length === 0) return '';
        
        const validButtons = this.buttons.filter(button => button.text && button.url);
        
        if (validButtons.length === 0) return '';
        
        return `<div class="telegram-inline-buttons">
            ${validButtons.map(button => `
                <div class="telegram-inline-button-row">
                    <a href="${Utils.escapeHtml(button.url)}" class="telegram-inline-button" target="_blank">
                        ${Utils.escapeHtml(button.text)}
                    </a>
                </div>
            `).join('')}
        </div>`;
    }

    formatMessageText(text) {
        // Улучшенное форматирование с поддержкой всех Telegram тегов
        return text
            .replace(/\n/g, '<br>')
            // Экранируем HTML символы, но не наши теги
            .replace(/&(?!(?:amp|lt|gt|quot|#39|#x27|#x2F);)/g, '&amp;')
            // Обрабатываем Telegram теги
            .replace(/<b>(.*?)<\/b>/g, '<strong>$1</strong>')
            .replace(/<strong>(.*?)<\/strong>/g, '<strong>$1</strong>')
            .replace(/<i>(.*?)<\/i>/g, '<em>$1</em>')
            .replace(/<em>(.*?)<\/em>/g, '<em>$1</em>')
            .replace(/<u>(.*?)<\/u>/g, '<u>$1</u>')
            .replace(/<ins>(.*?)<\/ins>/g, '<u>$1</u>')
            .replace(/<s>(.*?)<\/s>/g, '<s>$1</s>')
            .replace(/<strike>(.*?)<\/strike>/g, '<s>$1</s>')
            .replace(/<del>(.*?)<\/del>/g, '<s>$1</s>')
            .replace(/<tg-spoiler>(.*?)<\/tg-spoiler>/g, '<span style="background: #666; color: #666; border-radius: 3px; padding: 2px 4px; cursor: pointer;" title="Нажмите чтобы показать">$1</span>')
            .replace(/<code>(.*?)<\/code>/g, '<code style="background: var(--apple-fill-secondary); padding: 2px 4px; border-radius: 3px; font-family: monospace; font-size: 14px;">$1</code>')
            .replace(/<pre>(.*?)<\/pre>/g, '<pre style="background: var(--apple-fill-secondary); padding: 8px; border-radius: 6px; font-family: monospace; white-space: pre-wrap; border-left: 4px solid var(--apple-blue);">$1</pre>')
            .replace(/<a href="([^"]*)">(.*?)<\/a>/g, '<a href="$1" style="color: var(--apple-blue); text-decoration: none;" target="_blank">$2</a>');
    }

    updateCharCounter() {
        // Используем счетчик из Telegram редактора
        if (window.telegramEditor) {
            window.telegramEditor.updateCounter();
        }
        
        // Сохраняем старую логику для совместимости
        const textarea = document.getElementById('messageText');
        const counter = document.getElementById('charCount');
        
        if (textarea && counter) {
            const length = textarea.value.length;
            counter.textContent = length;
            
            if (length > 4096) {
                counter.style.color = 'var(--apple-red)';
            } else if (length > 3500) {
                counter.style.color = 'var(--apple-orange)';
            } else {
                counter.style.color = 'var(--apple-label-secondary)';
            }
        }
    }

    validateDates() {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;

        if (startDate && endDate) {
            const start = new Date(startDate);
            const end = new Date(endDate);
            
            // Преобразуем текущую дату в UTC для сравнения с датами в UTC формате
            const today = new Date();
            const todayUTC = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()));
            todayUTC.setHours(0, 0, 0, 0);
            
            // Преобразуем даты начала и конца в объекты дат без времени для корректного сравнения
            const startDateObj = new Date(Date.UTC(start.getUTCFullYear(), start.getUTCMonth(), start.getUTCDate()));
            startDateObj.setHours(0, 0, 0, 0);

            if (startDateObj < todayUTC) {
                this.showFieldError('startDate', 'Дата начала не может быть в прошлом (UTC)');
                return false;
            }

            if (start > end) {
                this.showFieldError('endDate', 'Дата окончания не может быть раньше даты начала');
                return false;
            }

            this.clearFieldError('startDate');
            this.clearFieldError('endDate');
            return true;
        }

        return true;
    }

    showFieldError(fieldId, message) {
        const field = document.getElementById(fieldId);
        const feedback = field?.parentNode.querySelector('.form-feedback');
        
        if (field && feedback) {
            field.classList.add('error');
            feedback.textContent = message;
            feedback.style.display = 'block';
        }
    }

    clearFieldError(fieldId) {
        const field = document.getElementById(fieldId);
        const feedback = field?.parentNode.querySelector('.form-feedback');
        
        if (field && feedback) {
            field.classList.remove('error');
            feedback.style.display = 'none';
        }
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        if (this.isSubmitting) return;
        
        if (!this.validateForm()) {
            Utils.showNotification('error', 'Ошибка валидации', 'Пожалуйста, исправьте ошибки в форме');
            return;
        }

        // Всегда создаем активную компанию
        await this.submitCampaign('active');
    }

    async submitCampaign(status) {
        try {
            this.isSubmitting = true;
            Utils.showLoading(true, 'Создание кампании...');

            const formData = this.buildFormData(status);
            
            // Для отладки: логируем, что отправляется
            console.log('Отправляемые кнопки:', this.buttons.filter(b => b.text && b.url));
            
            const response = await fetch('/api/campaigns', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok && result.success) {
                Utils.showNotification('success', 'Успех', result.message);
                
                setTimeout(() => {
                    window.location.href = '/campaigns';
                }, 1500);
            } else {
                throw new Error(result.message || 'Неизвестная ошибка');
            }

        } catch (error) {
            console.error('Ошибка создания кампании:', error);
            Utils.showNotification('error', 'Ошибка', error.message);
        } finally {
            this.isSubmitting = false;
            Utils.showLoading(false);
        }
    }

    buildFormData(status) {
        const formData = new FormData();
        
        // Основные поля
        formData.append('name', document.getElementById('campaignName').value);
        formData.append('status', status);
        formData.append('description', document.getElementById('campaignDescription').value);
        
        // Расписание - все времена сохраняются как UTC
        formData.append('start_date', document.getElementById('startDate').value);
        formData.append('end_date', document.getElementById('endDate').value);
        
        // Время тоже в UTC
        const postTimeValue = document.getElementById('postTime').value;
        formData.append('post_time', postTimeValue); // Пользователь вводит UTC время
        formData.append('timezone', 'UTC'); // Всегда UTC
        
        // Повторение
        const repeatEnabled = document.getElementById('repeatEnabled').checked;
        formData.append('repeat_enabled', repeatEnabled);
        
        if (repeatEnabled && this.repeatSettings) {
            formData.append('repeat_settings', JSON.stringify(this.repeatSettings));
        }
        
        // Чаты
        const chatsArray = Array.from(this.selectedChats.values());
        formData.append('chats', JSON.stringify(chatsArray));
        
        // Текст сообщения из Telegram редактора
        const messageText = window.telegramEditor ? 
            window.telegramEditor.getValue() : 
            document.getElementById('messageText').value;
        formData.append('message_text', messageText);
        
        // Кнопки - преобразуем только валидные кнопки и отправляем как JSON
        const validButtons = this.buttons.filter(b => b.text && b.url);
        if (validButtons.length > 0) {
            formData.append('buttons', JSON.stringify(validButtons));
        }
        
        // Медиафайлы
        this.selectedFiles.forEach(file => {
            formData.append('media_files', file);
        });
        
        // Настройки
        formData.append('disable_preview', document.getElementById('disable_preview').checked);
        formData.append('disable_notification', document.getElementById('disable_notification').checked);
        formData.append('protect_content', document.getElementById('protect_content').checked);
        formData.append('pin_message', document.getElementById('pin_message').checked);
        
        // Настройки повтора уже были добавлены выше, поэтому убираем дублирование
        
        if (repeatEnabled && this.repeatSettings) {
            formData.append('repeat_settings', JSON.stringify(this.repeatSettings));
        }
        
        // Для отладки
        console.log('FormData кнопки:', JSON.stringify(validButtons));
        console.log('Текст сообщения:', messageText);
        
        return formData;
    }

    validateForm() {
        let isValid = true;

        const requiredFields = [
            { id: 'campaignName', message: 'Введите название кампании' },
            { id: 'startDate', message: 'Выберите дату начала' },
            { id: 'endDate', message: 'Выберите дату окончания' },
            { id: 'postTime', message: 'Укажите время публикации' }
        ];

        requiredFields.forEach(field => {
            const element = document.getElementById(field.id);
            if (!element || !element.value.trim()) {
                this.showFieldError(field.id, field.message);
                isValid = false;
            } else {
                this.clearFieldError(field.id);
            }
        });

        // Проверяем текст сообщения через Telegram редактор
        const messageText = window.telegramEditor ? 
            window.telegramEditor.getValue() : 
            document.getElementById('messageText').value;
            
        if (!messageText.trim()) {
            Utils.showNotification('error', 'Ошибка', 'Введите текст сообщения');
            isValid = false;
        }

        if (this.selectedChats.size === 0) {
            Utils.showNotification('error', 'Ошибка', 'Выберите хотя бы один чат для публикации');
            isValid = false;
        }

        if (!this.validateDates()) {
            isValid = false;
        }

        const repeatEnabled = document.getElementById('repeatEnabled').checked;
        if (repeatEnabled) {
            const weekdays = document.querySelectorAll('input[name="weekday"]:checked');
            const specificDates = document.getElementById('specificDates').value;
            
            if (weekdays.length === 0 && !specificDates) {
                Utils.showNotification('error', 'Ошибка', 'Укажите дни недели или конкретные даты для повторения');
                isValid = false;
            }
        }

        if (messageText.length > 4096) {
            Utils.showNotification('error', 'Ошибка', 'Текст сообщения слишком длинный (макс. 4096 символов)');
            isValid = false;
        }

        return isValid;
    }

    cancel() {
        if (confirm('Вы уверены, что хотите отменить создание кампании? Все несохраненные данные будут потеряны.')) {
            window.location.href = '/campaigns';
        }
    }

    showChatsError(message) {
        const container = document.getElementById('chatsContainer');
        if (container) {
            container.innerHTML = `
                <div class="error-state">
                    <i class="fa-solid fa-exclamation-triangle fa-3x"></i>
                    <h6>Ошибка загрузки</h6>
                    <p>${message}</p>
                    <button type="button" class="btn btn-primary btn-sm" onclick="newCampaignManager.loadChats()">
                        <i class="fa-solid fa-refresh me-1"></i>Повторить
                    </button>
                </div>
            `;
        }
    }

    getChatTypeConfig(chat) {
        if (chat.is_forum) {
            return {
                label: 'Форум',
                badgeClass: 'type-forum',
                avatarClass: 'forum-avatar',
                icon: 'fa-comments'
            };
        }

        switch (chat.type) {
            case 'group':
                return {
                    label: 'Группа',
                    badgeClass: 'type-group',
                    avatarClass: 'group-avatar',
                    icon: 'fa-users'
                };
            case 'supergroup':
                return {
                    label: 'Супергруппа',
                    badgeClass: 'type-supergroup',
                    avatarClass: 'supergroup-avatar',
                    icon: 'fa-user-group'
                };
            case 'channel':
                return {
                    label: 'Канал',
                    badgeClass: 'type-channel',
                    avatarClass: 'channel-avatar',
                    icon: 'fa-broadcast-tower'
                };
            default:
                return {
                    label: chat.type,
                    badgeClass: 'type-unknown',
                    avatarClass: 'unknown-avatar',
                    icon: 'fa-question'
                };
        }
    }

    updateRepeatSettingsDisplay() {
        const container = document.getElementById('repeatSettingsDisplay');
        if (!container) return;

        if (!this.repeatSettings || !this.repeatSettings.interval) {
            container.innerHTML = `
                <div class="no-repeat-settings">
                    <i class="fa-solid fa-info-circle me-2"></i>
                    Настройки повторения не заданы. Нажмите "Настроить" для выбора интервала и периода.
                </div>
            `;
            return;
        }

        const intervalLabels = {
            minutely: 'Каждую минуту',
            hourly: 'Каждый час',
            daily: 'Ежедневно',
            weekly: 'Еженедельно',
            monthly: 'Ежемесячно'
        };

        const settingsItem = this.createRepeatSettingsElement(this.repeatSettings);
        container.innerHTML = '';
        container.appendChild(settingsItem);
    }

    createRepeatSettingsElement(settings) {
        const item = document.createElement('div');
        item.className = 'repeat-settings-item';
        
        const intervalLabels = {
            minutely: 'Каждую минуту',
            hourly: 'Каждый час',
            daily: 'Ежедневно',
            weekly: 'Еженедельно',
            monthly: 'Ежемесячно'
        };

        const description = this.getRepeatSettingsDescription(settings);
        const title = intervalLabels[settings.interval] || 'Автоповтор';

        item.innerHTML = `
            <div class="repeat-settings-content">
                <div class="repeat-settings-icon">
                    <i class="fa-solid fa-repeat"></i>
                </div>
                <div class="repeat-settings-text">
                    <div class="repeat-settings-title">${title}</div>
                    <div class="repeat-settings-description">${description}</div>
                </div>
            </div>
            <div class="repeat-settings-actions">
                <button type="button" class="repeat-action-btn edit" onclick="newCampaignManager.editRepeatSettings()">
                    <i class="fa-solid fa-edit"></i>
                </button>
                <button type="button" class="repeat-action-btn remove" onclick="newCampaignManager.removeRepeatSettings()">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </div>
        `;

        return item;
    }

    getRepeatSettingsDescription(settings) {
        const startDate = new Date(settings.startDate).toLocaleDateString('ru-RU');
        const endDate = settings.endDate ? new Date(settings.endDate).toLocaleDateString('ru-RU') : 'бесконечно';
        
        let description = `С ${startDate} по ${endDate}`;
        
        // Добавляем детали в зависимости от типа
        if (settings.interval === 'weekly' && settings.weekDay) {
            const dayNames = ['', 'по понедельникам', 'по вторникам', 'по средам', 'по четвергам', 'по пятницам', 'по субботам', 'по воскресеньям'];
            description += ` • ${dayNames[settings.weekDay]}`;
        }
        
        if (settings.interval === 'monthly') {
            if (settings.monthlyType === 'date' && settings.monthlyDate) {
                description += ` • ${settings.monthlyDate} числа каждого месяца`;
            } else if (settings.monthlyType === 'weekday') {
                const weekNames = { '1': 'первый', '2': 'второй', '3': 'третий', '4': 'четвертый', '-1': 'последний' };
                const dayNames = ['', 'понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье'];
                description += ` • ${weekNames[settings.monthlyWeek]} ${dayNames[settings.monthlyWeekday]} месяца`;
            }
        }
        
        return description;
    }

    editRepeatSettings() {
        if (window.repeatModal) {
            if (this.repeatSettings) {
                window.repeatModal.loadSettings(this.repeatSettings);
            }
            window.repeatModal.show();
        }
    }

    removeRepeatSettings() {
        this.repeatSettings = null;
        this.updateRepeatSettingsDisplay();
        
        if (window.repeatModal) {
            window.repeatModal.clearSettings();
        }
    }    formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString('ru-RU');
    }
}

// Инициализация
window.newCampaignManager = new NewCampaignManager();
