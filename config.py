import os
from dotenv import load_dotenv
from loguru import logger

class Config:
    def __init__(self):
        logger.debug("Инициализация конфигурации")
        
        # Загрузка .env файла
        load_dotenv()
        logger.debug(".env файл загружен")
        
        # Telegram Bot
        self.BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        logger.debug(f"BOT_TOKEN загружен: {'✅' if self.BOT_TOKEN else '❌'}")
        
        admin_ids = os.getenv("ADMIN_USER_IDS", "").split(",")
        self.ADMIN_IDS = [int(admin_id) for admin_id in admin_ids if admin_id.strip()]
        logger.debug(f"ADMIN_IDS загружены: {self.ADMIN_IDS}")
        
        # Web Server
        self.WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
        self.WEB_PORT = int(os.getenv("WEB_PORT", 8000))
        self.SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")
        self.SESSION_LIFETIME = int(os.getenv("SESSION_LIFETIME", 86400))
        logger.debug(f"Веб-сервер: {self.WEB_HOST}:{self.WEB_PORT}")
        
        # Admin Auth
        self.ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
        self.ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
        logger.debug(f"Админ логин: {self.ADMIN_USERNAME}")
        
        # Storage
        self.DATA_DIR = os.getenv("DATA_DIR", "data")
        self.UPLOADS_DIR = os.getenv("UPLOADS_DIR", "uploads")
        
        # Пути к файлам данных
        self.CAMPAIGNS_FILE = os.path.join(self.DATA_DIR, "campaigns.json")
        self.CHATS_FILE = os.path.join(self.DATA_DIR, "chats.json")
        self.USERS_FILE = os.path.join(self.DATA_DIR, "users.json")
        
        # Ngrok Configuration
        self.NGROK_ENABLED = os.getenv("NGROK_ENABLED", "true").lower() == "true"
        self.NGROK_PATH = os.getenv("NGROK_PATH", "ngrok")
        self.NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", "")
        self.NGROK_API_KEY = os.getenv("NGROK_API_KEY", "")
        self.NGROK_RESTART_INTERVAL = int(os.getenv("NGROK_RESTART_INTERVAL", "2"))
        
        logger.debug(f"Конфигурация Ngrok: Enabled={self.NGROK_ENABLED}, Path={self.NGROK_PATH}")
        
        logger.debug(f"Пути к файлам данных:")
        logger.debug(f"  - CAMPAIGNS_FILE: {self.CAMPAIGNS_FILE}")
        logger.debug(f"  - CHATS_FILE: {self.CHATS_FILE}")
        logger.debug(f"  - USERS_FILE: {self.USERS_FILE}")
        
        # Создаем JSON файлы с пустыми структурами если они не существуют
        self._ensure_data_files_exist()
        logger.info("Конфигурация успешно инициализирована")
    
    def _ensure_data_files_exist(self):
        """Создает пустые JSON файлы для данных если они не существуют"""
        logger.debug("Проверка существования файлов данных")
        
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.UPLOADS_DIR, exist_ok=True)
        logger.debug(f"Директории созданы: {self.DATA_DIR}, {self.UPLOADS_DIR}")
        
        default_files = {
            self.CAMPAIGNS_FILE: {"campaigns": []},
            self.CHATS_FILE: {"chats": []},
            self.USERS_FILE: {"users": []}
        }
        
        import json
        for file_path, default_content in default_files.items():
            if not os.path.exists(file_path):
                logger.debug(f"Создание файла: {file_path}")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(default_content, f, ensure_ascii=False, indent=2)
            else:
                logger.debug(f"Файл уже существует: {file_path}")
        
        logger.info("Все файлы данных проверены/созданы")
