from flask import Blueprint, render_template, redirect, url_for, current_app, flash, request, jsonify, session
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from loguru import logger
from datetime import datetime

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    """Главная страница или перенаправление на логин/дашборд"""
    logger.debug(f"Переход на главную страницу. Аутентифицирован: {current_user.is_authenticated}")
    
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
    return redirect(url_for('views.login'))

@views_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа в систему"""
    logger.debug(f"Страница логина. Метод: {request.method}, Аутентифицирован: {current_user.is_authenticated}")
    
    if current_user.is_authenticated:
        logger.debug("Пользователь уже аутентифицирован, перенаправление на дашборд")
        return redirect(url_for('views.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        logger.debug(f"Попытка входа пользователя: {username}")
        
        # Проверяем учетные данные
        auth_manager = current_app.auth_manager
        user = auth_manager.authenticate(username, password)
        
        if user:
            login_user(user, remember=True)
            logger.info(f"Успешный вход пользователя: {username}")
            return redirect(url_for('views.dashboard'))
        else:
            logger.warning(f"Неудачная попытка входа для пользователя: {username}")
            flash('Неверное имя пользователя или пароль', 'danger')
    
    return render_template('login.html')

@views_bp.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    username = current_user.username
    logger.debug(f"Выход пользователя: {username}")
    
    logout_user()
    logger.info(f"Пользователь {username} вышел из системы")
    return redirect(url_for('views.login'))

@views_bp.route('/dashboard')
@login_required
def dashboard():
    """Панель управления"""
    logger.debug(f"Переход на дашборд пользователя: {current_user.username}")
    return render_template('dashboard.html')

@views_bp.route('/campaigns')
@login_required
def campaigns():
    """Список кампаний"""
    logger.debug(f"Просмотр кампаний пользователем: {current_user.username}")
    return render_template('campaigns.html')

@views_bp.route('/campaigns/new')
@login_required
def new_campaign():
    """Создание новой кампании"""
    logger.debug(f"Создание новой кампании пользователем {current_user.username}")
    return render_template('new_campaign.html', url_for=url_for)

@views_bp.route('/campaigns/<campaign_id>/edit')
@login_required
def edit_campaign(campaign_id):
    """Редактирование кампании"""
    logger.debug(f"Редактирование кампании {campaign_id} пользователем {current_user.username}")
    return render_template('edit_campaign.html', campaign_id=campaign_id)

@views_bp.route('/chats')
@login_required
def chats():
    """Управление чатами"""
    logger.debug(f"Управление чатами пользователем: {current_user.username}")
    return render_template('chats.html')

@views_bp.route('/calendar')
@login_required
def calendar():
    """Календарь кампаний"""
    logger.debug(f"Просмотр календаря пользователем: {current_user.username}")

    # Собираем статистику для календаря
    scheduler = current_app.scheduler
    campaigns = list(scheduler.campaigns.values())
    today = datetime.now().date()

    # Считаем события на сегодня и всего
    today_events = 0
    total_events = 0
    for campaign in campaigns:
        try:
            start_date = campaign.get('start_date')
            end_date = campaign.get('end_date')
            if start_date and end_date:
                start = datetime.fromisoformat(start_date).date()
                end = datetime.fromisoformat(end_date).date()
                if start <= today <= end:
                    today_events += 1
                total_events += 1
        except Exception:
            continue

    stats = {
        "today_events": today_events,
        "total_events": total_events
    }

    return render_template('calendar.html', stats=stats)

