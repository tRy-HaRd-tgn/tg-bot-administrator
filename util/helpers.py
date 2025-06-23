"""
Вспомогательные функции
"""
import os
import json
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional

class FileManager:
    """Менеджер файлов"""
    
    @staticmethod
    def save_uploaded_file(file, upload_dir: str) -> Dict[str, Any]:
        """Сохранение загруженного файла"""
        # Генерируем уникальное имя файла
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Создаем директорию если не существует
        os.makedirs(upload_dir, exist_ok=True)
        
        # Сохраняем файл
        file.save(file_path)
        
        # Получаем информацию о файле
        file_info = {
            "filename": unique_filename,
            "original_filename": file.filename,
            "type": file.content_type,
            "size": os.path.getsize(file_path),
            "uploaded_at": datetime.now().isoformat(),
            "path": file_path
        }
        
        return file_info
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Удаление файла"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    @staticmethod
    def get_file_hash(file_path: str) -> Optional[str]:
        """Получение хеша файла"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            return file_hash
        except Exception:
            return None

class DataManager:
    """Менеджер данных JSON"""
    
    @staticmethod
    def load_json(file_path: str) -> Dict[str, Any]:
        """Загрузка данных из JSON файла"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}
    
    @staticmethod
    def save_json(data: Dict[str, Any], file_path: str) -> bool:
        """Сохранение данных в JSON файл"""
        try:
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    @staticmethod
    def backup_json(file_path: str) -> bool:
        """Создание резервной копии JSON файла"""
        try:
            if os.path.exists(file_path):
                backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                with open(file_path, 'r', encoding='utf-8') as source:
                    with open(backup_path, 'w', encoding='utf-8') as backup:
                        backup.write(source.read())
                return True
            return False
        except Exception:
            return False

class TimeHelper:
    """Помощник для работы с временем"""
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = '%d.%m.%Y %H:%M') -> str:
        """Форматирование даты и времени"""
        return dt.strftime(format_str)
    
    @staticmethod
    def parse_time(time_str: str) -> Optional[tuple[int, int]]:
        """Парсинг времени из строки HH:MM"""
        try:
            parts = time_str.split(':')
            if len(parts) == 2:
                hour = int(parts[0])
                minute = int(parts[1])
                
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return hour, minute
            return None
        except Exception:
            return None
    
    @staticmethod
    def get_weekday_name(weekday: int) -> str:
        """Получение названия дня недели"""
        days = {
            1: 'Понедельник',
            2: 'Вторник', 
            3: 'Среда',
            4: 'Четверг',
            5: 'Пятница',
            6: 'Суббота',
            7: 'Воскресенье'
        }
        return days.get(weekday, 'Неизвестно')

class SecurityHelper:
    """Помощник для безопасности"""
    HTML_FORMAT_WARNING = """⚠️ Правильное HTML форматирование для Telegram:

📌 Основные теги:
• <b>жирный</b> или <strong>жирный</strong>
• <i>курсив</i> или <em>курсив</em>
• <u>подчеркнутый</u> или <ins>подчеркнутый</ins>
• <s>зачеркнутый</s>, <strike>зачеркнутый</strike> или <del>зачеркнутый</del>
• <span class="tg-spoiler">спойлер</span> или <tg-spoiler>спойлер</tg-spoiler>
• <code>моноширинный текст</code>
• <pre>блок кода</pre>

📱 Пример вложенных тегов:
<b>жирный <i>жирный курсив <s>зачеркнутый жирный курсив</s></i></b>

🔗 Ссылки:
<a href="http://example.com/">текст ссылки</a>

❌ Неправильное использование HTML тегов приведет к ошибке отправки сообщения!"""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Очистка имени файла от опасных символов"""
        # Удаляем опасные символы
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
        sanitized = ''.join(c for c in filename if c in safe_chars)
        
        # Ограничиваем длину
        if len(sanitized) > 100:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:90] + ext
        
        return sanitized or 'unnamed_file'
    
    @staticmethod
    def validate_admin_id(user_id: int, admin_ids: List[int]) -> bool:
        """Проверка является ли пользователь администратором"""
        return user_id in admin_ids
    
    @staticmethod
    def escape_html(text: str) -> str:
        """Экранирование HTML символов"""
        if not text:
            return ""
        
        escape_chars = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;'
        }
        
        for char, escape in escape_chars.items():
            text = text.replace(char, escape)
        
        return text

class LogHelper:
    """Помощник для логирования"""
    
    @staticmethod
    def setup_logger(name: str, log_file: str, level: str = 'INFO') -> Any:
        """Настройка логгера"""
        import logging
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # Создаем директорию для логов
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Форматтер
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Обработчик файла
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Обработчик консоли
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
