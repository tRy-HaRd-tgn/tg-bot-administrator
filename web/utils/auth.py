import json
import os
import uuid
import time
from loguru import logger
from werkzeug.security import generate_password_hash, check_password_hash
from web.models.user import User

class AuthManager:
    """Менеджер аутентификации для работы с пользователями"""
    
    def __init__(self, config):
        logger.debug("Инициализация AuthManager")
        self.config = config
        self.users_file = config.USERS_FILE
        self._ensure_admin_user()
        logger.info("AuthManager инициализирован")
    
    def _ensure_admin_user(self):
        """Проверяет наличие администратора в системе и создает его при необходимости"""
        logger.debug("Проверка наличия администратора в системе")
        
        try:
            # Загружаем пользователей из файла
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    users = data.get('users', [])
            else:
                users = []
            
            # Проверяем наличие администратора
            admin_exists = False
            for user in users:
                if user.get('is_admin', False):
                    admin_exists = True
                    logger.debug(f"Найден администратор: {user.get('username')}")
                    break
            
            # Если администратора нет, создаем его
            if not admin_exists:
                logger.info("Администратор не найден, создаем нового")
                admin_user = {
                    'id': str(uuid.uuid4()),
                    'username': self.config.ADMIN_USERNAME,
                    'password_hash': generate_password_hash(self.config.ADMIN_PASSWORD),
                    'is_admin': True,
                    'created_at': time.time()
                }
                users.append(admin_user)
                
                # Сохраняем обновленный список пользователей
                with open(self.users_file, 'w', encoding='utf-8') as f:
                    json.dump({'users': users}, f, ensure_ascii=False, indent=2)
                
                logger.info(f"✅ Создан администратор: {self.config.ADMIN_USERNAME}")
            else:
                logger.debug("Администратор уже существует")
        
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке/создании администратора: {e}")
    
    def authenticate(self, username, password):
        """Аутентификация пользователя по логину и паролю"""
        logger.debug(f"Попытка аутентификации пользователя: {username}")
        
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    users = data.get('users', [])
                
                for user_data in users:
                    if user_data.get('username') == username:
                        if check_password_hash(user_data.get('password_hash', ''), password):
                            logger.info(f"✅ Успешная аутентификация пользователя: {username}")
                            return User(
                                id=user_data.get('id'),
                                username=username,
                                is_admin=user_data.get('is_admin', False)
                            )
                        else:
                            logger.warning(f"⚠️ Неверный пароль для пользователя: {username}")
                            break
                
                logger.warning(f"⚠️ Пользователь не найден: {username}")
            
            return None
        
        except Exception as e:
            logger.error(f"❌ Ошибка при аутентификации пользователя: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """Получение пользователя по ID"""
        logger.debug(f"Получение пользователя по ID: {user_id}")
        
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    users = data.get('users', [])
                
                for user_data in users:
                    if user_data.get('id') == user_id:
                        logger.debug(f"✅ Пользователь найден: {user_data.get('username')}")
                        return User(
                            id=user_id,
                            username=user_data.get('username'),
                            is_admin=user_data.get('is_admin', False)
                        )
            
            logger.debug(f"⚠️ Пользователь с ID {user_id} не найден")
            return None
        
        except Exception as e:
            logger.error(f"❌ Ошибка при получении пользователя по ID: {e}")
            return None
    
    def create_user(self, username, password, is_admin=False):
        """Создание нового пользователя"""
        logger.debug(f"Создание нового пользователя: {username}")
        
        try:
            # Загружаем существующих пользователей
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    users = data.get('users', [])
            else:
                users = []
            
            # Проверяем, существует ли пользователь с таким именем
            for user in users:
                if user.get('username') == username:
                    logger.warning(f"⚠️ Пользователь {username} уже существует")
                    return False, "Пользователь с таким именем уже существует"
            
            # Создаем нового пользователя
            new_user = {
                'id': str(uuid.uuid4()),
                'username': username,
                'password_hash': generate_password_hash(password),
                'is_admin': is_admin,
                'created_at': time.time()
            }
            users.append(new_user)
            
            # Сохраняем обновленный список пользователей
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump({'users': users}, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Пользователь {username} успешно создан")
            return True, "Пользователь успешно создан"
        
        except Exception as e:
            logger.error(f"❌ Ошибка при создании пользователя: {e}")
            return False, str(e)
