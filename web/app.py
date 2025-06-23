import os
from datetime import timedelta

from loguru import logger
from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from werkzeug.utils import secure_filename

from web.models.user import User
from web.routes.api import api_bp
from web.routes.views import views_bp
from web.utils.auth import AuthManager

def create_app(bot, scheduler, config):
    """Создает экземпляр Flask приложения"""
    logger.debug("Создание Flask приложения")
    
    app = Flask(__name__, 
                static_folder='static', 
                template_folder='templates')
    
    # Конфигурация приложения
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=config.SESSION_LIFETIME)
    app.config['UPLOAD_FOLDER'] = config.UPLOADS_DIR
    app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB максимальный размер загрузки
    
    logger.debug(f"Flask config: SECRET_KEY={'***' if config.SECRET_KEY else 'NOT SET'}")
    logger.debug(f"Upload folder: {config.UPLOADS_DIR}")
    
    # Инициализация менеджера аутентификации
    auth_manager = AuthManager(config)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "views.login"
    
    @login_manager.user_loader
    def load_user(user_id):
        logger.debug(f"Загрузка пользователя: {user_id}")
        return auth_manager.get_user_by_id(user_id)
    
    # Регистрация blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(views_bp, url_prefix='/')
    logger.debug("Blueprints зарегистрированы")
    
    # Делаем бота и планировщик доступными в контексте приложения
    app.bot = bot
    app.scheduler = scheduler
    app.config_obj = config
    app.auth_manager = auth_manager
    
    # Обработчики ошибок
    @app.errorhandler(404)
    def page_not_found(e):
        logger.warning(f"404 ошибка: {request.url}")
        return render_template('error.html', 
                              error_code=404, 
                              error_message="Страница не найдена"), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"500 ошибка: {e}")
        return render_template('error.html', 
                              error_code=500, 
                              error_message="Внутренняя ошибка сервера"), 500
    
    # Запуск веб-сервера в отдельном потоке
    from threading import Thread
    def run_server():
        logger.info(f"🌐 Запуск веб-сервера на {config.WEB_HOST}:{config.WEB_PORT}")
        app.run(host=config.WEB_HOST, port=config.WEB_PORT, debug=False, use_reloader=False)
    
    Thread(target=run_server, daemon=True).start()
    logger.info("✅ Веб-сервер запущен в отдельном потоке")
    
    return app
