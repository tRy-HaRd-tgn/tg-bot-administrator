"""
Валидаторы для проверки данных
"""
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, date

class CampaignValidator:
    """Валидатор для кампаний"""
    
    @staticmethod
    def validate_campaign_data(data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Валидация данных кампании"""
        errors = []
        
        # Проверка обязательных полей
        if not data.get('name', '').strip():
            errors.append("Название кампании обязательно")
        
        if not data.get('message_text', '').strip():
            errors.append("Текст сообщения обязателен")
        
        # Проверка дат
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date).date()
                end = datetime.fromisoformat(end_date).date()
                
                if start > end:
                    errors.append("Дата начала не может быть позже даты окончания")
                
                if start < date.today():
                    errors.append("Дата начала не может быть в прошлом")
                    
            except ValueError:
                errors.append("Некорректный формат даты")
        
        # Проверка времени
        post_time = data.get('post_time')
        if post_time:
            try:
                datetime.strptime(post_time, '%H:%M')
            except ValueError:
                errors.append("Некорректный формат времени (используйте HH:MM)")
        
        # Проверка чатов
        chats = data.get('chats', [])
        if not chats:
            errors.append("Необходимо выбрать хотя бы один чат")
        
        # Проверка дней недели или конкретных дат
        days_of_week = data.get('days_of_week', '')
        specific_dates = data.get('specific_dates', '')
        
        if not days_of_week and not specific_dates:
            errors.append("Необходимо указать дни недели или конкретные даты")
        
        # Проверка кнопок
        buttons = data.get('buttons', [])
        for i, button in enumerate(buttons):
            if not button.get('text', '').strip():
                errors.append(f"Текст кнопки #{i+1} не может быть пустым")
            
            url = button.get('url', '')
            if not CampaignValidator.validate_url(url):
                errors.append(f"Некорректная ссылка в кнопке #{i+1}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Валидация URL"""
        if not url:
            return False
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return url_pattern.match(url) is not None

class ChatValidator:
    """Валидатор для чатов"""
    
    @staticmethod
    def validate_chat_id(chat_id: str) -> bool:
        """Валидация ID чата"""
        if not chat_id:
            return False
        
        # Чат ID должен быть числом (может быть отрицательным)
        try:
            int(chat_id)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_thread_id(thread_id: Optional[str]) -> bool:
        """Валидация ID темы форума"""
        if not thread_id:
            return True  # thread_id опциональный
        
        try:
            thread_id_int = int(thread_id)
            return thread_id_int > 0
        except ValueError:
            return False

class MediaValidator:
    """Валидатор для медиафайлов"""
    
    ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/jpg', 'image/png', 'image/gif'}
    ALLOWED_VIDEO_TYPES = {'video/mp4', 'video/avi', 'video/mov'}
    MAX_PHOTOS = 8
    MAX_VIDEOS = 1
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
    
    @staticmethod
    def validate_media_files(files: List[Dict[str, Any]]) -> tuple[bool, List[str]]:
        """Валидация медиафайлов"""
        errors = []
        
        if not files:
            return True, []
        
        photo_count = 0
        video_count = 0
        
        for file_info in files:
            file_type = file_info.get('type', '')
            file_size = file_info.get('size', 0)
            
            # Проверка размера файла
            if file_size > MediaValidator.MAX_FILE_SIZE:
                errors.append(f"Файл {file_info.get('name', 'неизвестный')} слишком большой (макс. 20MB)")
            
            # Проверка типа файла
            if file_type in MediaValidator.ALLOWED_IMAGE_TYPES:
                photo_count += 1
            elif file_type in MediaValidator.ALLOWED_VIDEO_TYPES:
                video_count += 1
            else:
                errors.append(f"Неподдерживаемый тип файла: {file_type}")
        
        # Проверка количества файлов
        if photo_count > MediaValidator.MAX_PHOTOS:
            errors.append(f"Слишком много фото (макс. {MediaValidator.MAX_PHOTOS})")
        
        if video_count > MediaValidator.MAX_VIDEOS:
            errors.append(f"Слишком много видео (макс. {MediaValidator.MAX_VIDEOS})")
        
        # Нельзя одновременно загружать фото и видео
        if photo_count > 0 and video_count > 0:
            errors.append("Нельзя одновременно загружать фото и видео")
        
        return len(errors) == 0, errors
