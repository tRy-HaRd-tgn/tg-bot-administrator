from flask_login import UserMixin
from loguru import logger

class User(UserMixin):
    """Класс пользователя для системы аутентификации Flask-Login"""
    
    def __init__(self, id, username, is_admin=False):
        logger.debug(f"Создание объекта пользователя: {username}")
        self.id = id
        self.username = username
        self.is_admin = is_admin
    
    def __repr__(self):
        return f"<User {self.username}>"
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)
