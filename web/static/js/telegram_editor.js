/**
 * Telegram HTML Editor
 * Визуальный редактор для создания HTML-форматированного текста для Telegram
 */
class TelegramEditor {
    constructor() {
        this.editor = null;
        this.textarea = null;
        this.isHtmlMode = false;
        this.maxLength = 4096;
        
        this.init();
    }

    init() {
        this.editor = document.getElementById('telegramEditor');
        this.textarea = document.getElementById('messageText');
        
        if (!this.editor || !this.textarea) {
            console.error('TelegramEditor: Не найдены необходимые элементы');
            return;
        }

        this.bindEvents();
        this.updateCounter();
        
        // Устанавливаем начальный текст
        this.editor.innerHTML = this.textarea.value || '';
        
        console.log('TelegramEditor инициализирован');
    }

    bindEvents() {
        // Обработчики для кнопок форматирования
        document.querySelectorAll('.toolbar-btn[data-command]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const command = btn.dataset.command;
                this.execCommand(command);
            });
        });

        // Обработчики клавиатуры
        this.editor.addEventListener('keydown', (e) => {
            // Ctrl+B - жирный
            if (e.ctrlKey && e.key === 'b') {
                e.preventDefault();
                this.execCommand('bold');
            }
            // Ctrl+I - курсив
            else if (e.ctrlKey && e.key === 'i') {
                e.preventDefault();
                this.execCommand('italic');
            }
            // Ctrl+U - подчеркнутый
            else if (e.ctrlKey && e.key === 'u') {
                e.preventDefault();
                this.execCommand('underline');
            }
            // Enter - разрыв строки
            else if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.insertHtml('<br>');
            }
        });

        // Обработка вставки текста
        this.editor.addEventListener('paste', (e) => {
            e.preventDefault();
            const text = e.clipboardData.getData('text/plain');
            this.insertText(text);
        });
    }

    execCommand(command) {
        this.editor.focus();
        
        try {
            const success = document.execCommand(command, false, null);
            if (!success) {
                console.warn(`Команда ${command} не выполнена`);
            }
        } catch (error) {
            console.error(`Ошибка выполнения команды ${command}:`, error);
        }
        
        this.updateButtonStates();
        this.syncWithTextarea();
        this.updateCounter();
    }

    insertHtml(html) {
        this.editor.focus();
        
        const selection = window.getSelection();
        if (!selection.rangeCount) return;
        
        const range = selection.getRangeAt(0);
        range.deleteContents();
        
        const temp = document.createElement('div');
        temp.innerHTML = html;
        const fragment = document.createDocumentFragment();
        
        let node;
        while ((node = temp.firstChild)) {
            fragment.appendChild(node);
        }
        
        range.insertNode(fragment);
        
        // Перемещаем курсор после вставленного контента
        range.collapse(false);
        selection.removeAllRanges();
        selection.addRange(range);
        
        this.syncWithTextarea();
        this.updateCounter();
    }

    insertText(text) {
        this.editor.focus();
        
        const selection = window.getSelection();
        if (!selection.rangeCount) return;
        
        const range = selection.getRangeAt(0);
        range.deleteContents();
        
        const textNode = document.createTextNode(text);
        range.insertNode(textNode);
        
        // Перемещаем курсор после вставленного текста
        range.setStartAfter(textNode);
        range.collapse(true);
        selection.removeAllRanges();
        selection.addRange(range);
        
        this.syncWithTextarea();
        this.updateCounter();
    }

    insertCode() {
        const selectedText = this.getSelectedText();
        const codeText = selectedText || 'код';
        this.insertHtml(`<code>${codeText}</code>`);
    }

    insertPre() {
        const selectedText = this.getSelectedText();
        const preText = selectedText || 'блок кода';
        this.insertHtml(`<pre>${preText}</pre>`);
    }

    insertSpoiler() {
        const selectedText = this.getSelectedText();
        const spoilerText = selectedText || 'скрытый текст';
        this.insertHtml(`<span class="tg-spoiler">${spoilerText}</span>`);
    }

    insertLink() {
        const selectedText = this.getSelectedText();
        const url = prompt('Введите URL:');
        
        if (url) {
            const linkText = selectedText || url;
            this.insertHtml(`<a href="${url}">${linkText}</a>`);
        }
    }

    insertEmoji() {
        const emojis = ['😊', '😂', '❤️', '👍', '🔥', '💯', '🎉', '👏', '😍', '🤔', '😎', '👌'];
        const emoji = emojis[Math.floor(Math.random() * emojis.length)];
        this.insertText(emoji);
    }

    getSelectedText() {
        const selection = window.getSelection();
        return selection.toString();
    }

    updateButtonStates() {
        document.querySelectorAll('.toolbar-btn[data-command]').forEach(btn => {
            const command = btn.dataset.command;
            try {
                const isActive = document.queryCommandState(command);
                btn.classList.toggle('active', isActive);
            } catch (error) {
                // Игнорируем ошибки для неподдерживаемых команд
            }
        });
    }

    syncWithTextarea() {
        if (this.isHtmlMode) {
            this.textarea.value = this.editor.textContent;
        } else {
            this.textarea.value = this.convertToTelegramHtml(this.editor.innerHTML);
        }
        
        // Триггерим событие input для других обработчиков
        this.textarea.dispatchEvent(new Event('input', { bubbles: true }));
    }

    convertToTelegramHtml(html) {
        // Преобразуем HTML в формат, поддерживаемый Telegram
        return html
            .replace(/<div><br><\/div>/g, '\n')
            .replace(/<div>/g, '\n')
            .replace(/<\/div>/g, '')
            .replace(/<br\s*\/?>/g, '\n')
            .replace(/<span class="tg-spoiler">(.*?)<\/span>/g, '<tg-spoiler>$1</tg-spoiler>')
            .trim();
    }

    updateCounter() {
        const text = this.editor.textContent || '';
        const length = text.length;
        const counter = document.getElementById('telegramCharCount');
        
        if (counter) {
            counter.textContent = length;
            
            const counterParent = counter.parentElement;
            counterParent.classList.remove('warning', 'error');
            
            if (length > this.maxLength) {
                counterParent.classList.add('error');
            } else if (length > this.maxLength * 0.9) {
                counterParent.classList.add('warning');
            }
        }
    }

    toggleMode() {
        this.isHtmlMode = !this.isHtmlMode;
        const modeBtn = document.getElementById('modeToggle');
        
        if (this.isHtmlMode) {
            // Переключение в HTML режим
            const html = this.convertToTelegramHtml(this.editor.innerHTML);
            this.editor.textContent = html;
            this.editor.classList.add('html-mode');
            modeBtn.innerHTML = '<i class="fa-solid fa-eye me-1"></i>Визуальный режим';
            modeBtn.classList.add('active');
        } else {
            // Переключение в визуальный режим
            const text = this.editor.textContent;
            this.editor.innerHTML = this.parseToHtml(text);
            this.editor.classList.remove('html-mode');
            modeBtn.innerHTML = '<i class="fa-solid fa-code me-1"></i>HTML режим';
            modeBtn.classList.remove('active');
        }
        
        this.syncWithTextarea();
        this.updateCounter();
    }

    parseToHtml(text) {
        // Преобразуем текст с HTML тегами в визуальное представление
        return text
            .replace(/\n/g, '<br>')
            .replace(/<tg-spoiler>(.*?)<\/tg-spoiler>/g, '<span class="tg-spoiler">$1</span>');
    }

    clearFormatting() {
        if (confirm('Очистить все форматирование? Текст останется, но форматирование будет удалено.')) {
            const text = this.editor.textContent;
            this.editor.innerHTML = text.replace(/\n/g, '<br>');
            this.syncWithTextarea();
            this.updateCounter();
        }
    }

    showSource() {
        const html = this.convertToTelegramHtml(this.editor.innerHTML);
        
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        `;
        
        modal.innerHTML = `
            <div style="background: white; padding: 20px; border-radius: 12px; max-width: 600px; width: 90%;">
                <h3 style="margin-top: 0;">HTML код для Telegram</h3>
                <textarea readonly style="width: 100%; height: 200px; font-family: monospace; padding: 10px; border: 1px solid #ccc; border-radius: 6px;">${html}</textarea>
                <div style="text-align: right; margin-top: 15px;">
                    <button onclick="navigator.clipboard.writeText(this.parentElement.parentElement.querySelector('textarea').value); alert('Скопировано!');" style="margin-right: 10px; padding: 8px 16px; background: #0078d7; color: white; border: none; border-radius: 6px; cursor: pointer;">Копировать</button>
                    <button onclick="this.closest('div[style*=fixed]').remove()" style="padding: 8px 16px; background: #ccc; border: none; border-radius: 6px; cursor: pointer;">Закрыть</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    setValue(value) {
        this.editor.innerHTML = this.parseToHtml(value);
        this.syncWithTextarea();
        this.updateCounter();
    }

    getValue() {
        return this.convertToTelegramHtml(this.editor.innerHTML);
    }
}

// Создаем глобальный экземпляр
window.telegramEditor = new TelegramEditor();
