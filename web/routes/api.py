import os
import json
import uuid
from datetime import datetime, timezone, timedelta
import logging
from typing import Dict, List, Any, Optional
import asyncio
import requests
from io import BytesIO
from PIL import Image

from flask import Blueprint, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from loguru import logger

api_bp = Blueprint('api', __name__)

# Проверка разрешенных типов файлов
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Функция для безопасного запуска асинхронных функций из синхронного кода
def run_async(coro):
    """Безопасно запускает асинхронную функцию из синхронного кода"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Внутри уже работающего event loop (например, Flask с gevent/threading)
            # Используем asyncio.ensure_future и loop.run_until_complete через новый loop
            # Но в большинстве случаев лучше использовать nest_asyncio, но здесь делаем просто:
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # Нет текущего event loop
        return asyncio.run(coro)

# Улучшенная синхронная функция для получения информации о чате через Telegram API
def get_chat_info_sync(chat_id, token):
    """Синхронно получает информацию о чате через Telegram HTTP API"""
    logger.debug(f"Запрос информации о чате {chat_id} через HTTP API")
    
    try:
        api_url = f"https://api.telegram.org/bot{token}/getChat"
        response = requests.get(api_url, params={'chat_id': chat_id})
        data = response.json()
        
        if not data.get('ok'):
            logger.error(f"❌ API вернул ошибку: {data.get('description', 'Неизвестная ошибка')}")
            return None
        
        chat = data['result']
        
        # Проверяем, является ли бот админом
        bot_status = "member"
        bot_is_admin = False
        bot_permissions = {}
        try:
            # Получаем информацию о боте
            bot_info_url = f"https://api.telegram.org/bot{token}/getMe"
            bot_response = requests.get(bot_info_url)
            bot_data = bot_response.json()
            bot_id = bot_data.get('result', {}).get('id', 0) if bot_data.get('ok') else 0
            
            # Получаем статус бота в чате
            chat_member_url = f"https://api.telegram.org/bot{token}/getChatMember"
            member_response = requests.get(chat_member_url, params={
                'chat_id': chat_id, 
                'user_id': bot_id
            })
            member_data = member_response.json()
            
            if member_data.get('ok'):
                member_result = member_data.get('result', {})
                bot_status = member_result.get('status', 'member')
                bot_is_admin = bot_status in ['administrator', 'creator']
                
                # Собираем права бота
                bot_permissions = {
                    'can_be_edited': member_result.get('can_be_edited', False),
                    'can_manage_chat': member_result.get('can_manage_chat', False),
                    'can_change_info': member_result.get('can_change_info', False),
                    'can_delete_messages': member_result.get('can_delete_messages', False),
                    'can_invite_users': member_result.get('can_invite_users', False),
                    'can_restrict_members': member_result.get('can_restrict_members', False),
                    'can_pin_messages': member_result.get('can_pin_messages', False),
                    'can_promote_members': member_result.get('can_promote_members', False),
                    'can_manage_video_chats': member_result.get('can_manage_video_chats', False),
                    'can_manage_topics': member_result.get('can_manage_topics', False),
                    'can_post_messages': member_result.get('can_post_messages', False),
                    'can_edit_messages': member_result.get('can_edit_messages', False),
                    'can_send_messages': member_result.get('can_send_messages', True),
                    'can_send_media_messages': member_result.get('can_send_media_messages', True),
                    'can_send_polls': member_result.get('can_send_polls', True),
                    'can_send_other_messages': member_result.get('can_send_other_messages', True),
                    'can_add_web_page_previews': member_result.get('can_add_web_page_previews', True)
                }
                
                logger.debug(f"Статус бота в чате: {bot_status}")
        except Exception as e:
            logger.error(f"Ошибка при получении статуса бота: {e}")
        
        # Получаем аватар чата если он есть
        avatar_url = None
        try:
            if chat.get('photo'):
                photo_id = chat.get('photo', {}).get('big_file_id')
                if photo_id:
                    photo_url = f"https://api.telegram.org/bot{token}/getFile"
                    photo_response = requests.get(photo_url, params={'file_id': photo_id})
                    photo_data = photo_response.json()
                    
                    if photo_data.get('ok'):
                        file_path = photo_data.get('result', {}).get('file_path')
                        if file_path:
                            avatar_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
        except Exception as e:
            logger.error(f"Ошибка при получении аватара: {e}")
        
        # Формируем расширенную структуру ответа
        chat_info = {
            "id": str(chat.get('id')),
            "chat_id": chat.get('id'),
            "type": chat.get('type'),
            "title": chat.get('title'),
            "username": chat.get('username'),
            "description": chat.get('description'),
            "member_count": None,  # Получаем отдельно
            "is_forum": chat.get('is_forum', False),
            "avatar_url": avatar_url,
            "bot_status": bot_status,
            "bot_is_admin": bot_is_admin,
            "bot_permissions": bot_permissions,
            
            # Расширенная информация о чате
            "invite_link": chat.get('invite_link'),
            "has_visible_history": chat.get('has_visible_history', False),
            "join_to_send_messages": chat.get('join_to_send_messages', False),
            "max_reaction_count": chat.get('max_reaction_count', 0),
            "accent_color_id": chat.get('accent_color_id'),
            
            # Права участников чата
            "permissions": chat.get('permissions', {}),
            
            # Информация о подарках (если есть)
            "accepted_gift_types": chat.get('accepted_gift_types', {}),
            
            # Информация о фото
            "photo_info": chat.get('photo', {}),
            
            # Дополнительные поля для различных типов чатов
            "has_protected_content": chat.get('has_protected_content', False),
            "has_aggressive_anti_spam": chat.get('has_aggressive_anti_spam', False),
            "has_hidden_members": chat.get('has_hidden_members', False),
            "slow_mode_delay": chat.get('slow_mode_delay', 0),
            "message_auto_delete_time": chat.get('message_auto_delete_time', 0),
            "linked_chat_id": chat.get('linked_chat_id'),
            "location": chat.get('location', {}),
            "pinned_message": chat.get('pinned_message', {}),
            "sticker_set_name": chat.get('sticker_set_name'),
            "can_set_sticker_set": chat.get('can_set_sticker_set', False),
            
            # Системные поля
            "can_send_messages": True
        }
        
        # Пробуем получить число участников
        try:
            member_count_url = f"https://api.telegram.org/bot{token}/getChatMemberCount"
            count_response = requests.get(member_count_url, params={'chat_id': chat_id})
            count_data = count_response.json()
            
            if count_data.get('ok'):
                chat_info["member_count"] = count_data['result']
        except Exception as e:
            logger.warning(f"Не удалось получить число участников: {e}")
        
        logger.info(f"✅ Информация о чате получена: {chat_info['title']}")
        return chat_info
    
    except requests.RequestException as e:
        logger.error(f"❌ Ошибка HTTP запроса: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        return None

# API для кампаний
@api_bp.route('/campaigns', methods=['GET'])
@api_bp.route('/campaigns/', methods=['GET'])  # Добавляем обработку URL со слешем
@login_required
def get_campaigns():
    """Получение списка кампаний"""
    try:
        logger.debug("🔄 Получение списка кампаний...")
        scheduler = current_app.scheduler
        
        if not scheduler:
            logger.error("❌ Планировщик не инициализирован")
            return jsonify({
                "error": "Система не готова, попробуйте позже",
                "details": "Планировщик не инициализирован"
            }), 500

        campaigns = list(scheduler.campaigns.values())
        
        # Сортировка по дате создания (сначала новые)
        campaigns.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        logger.info(f"✅ Успешно получено {len(campaigns)} кампаний")
        return jsonify(campaigns)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при получении списка кампаний: {e}")
        return jsonify({
            "error": "Внутренняя ошибка сервера",
            "details": str(e)
        }), 500

@api_bp.route('/campaigns/<campaign_id>', methods=['GET'])
@login_required
def get_campaign(campaign_id):
    """Получение информации о кампании"""
    try:
        scheduler = current_app.scheduler
        campaign = scheduler.campaigns.get(campaign_id)
        
        if not campaign:
            return jsonify({"error": "Кампания не найдена"}), 404
        
        return jsonify(campaign)
    except Exception as e:
        logger.error(f"Ошибка при получении информации о кампании: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@api_bp.route('/campaigns', methods=['POST'])
@login_required
def create_campaign():
    """Создание новой кампании"""
    try:
        logger.debug("Создание новой кампании")
        scheduler = current_app.scheduler
        
        # Получаем данные формы
        name = request.form.get('name')
        message_text = request.form.get('message_text')
        status = request.form.get('status', 'draft')
        
        logger.debug(f"Данные кампании: name={name}, status={status}")
        
        if not name or not message_text:
            logger.warning("Отсутствуют обязательные поля")
            return jsonify({"error": "Необходимо указать название и текст сообщения"}), 400
        
        # Создаем базовую структуру кампании
        campaign_data = {
            "name": name,
            "message_text": message_text,
            "status": status,
            "start_date": request.form.get('start_date'),
            "end_date": request.form.get('end_date'),
            "post_time": request.form.get('post_time', '12:00'),
            "repeat_enabled": request.form.get('repeat_enabled') == 'true',
            "days_of_week": request.form.get('days_of_week', ''),
            "specific_dates": request.form.get('specific_dates', ''),
            "timezone": request.form.get('timezone', 'UTC'),
            
            # Исправляем обработку переключателей - проверяем точные значения
            "disable_preview": request.form.get('disable_preview') in ['true', 'on', '1'],
            "disable_notification": request.form.get('disable_notification') in ['true', 'on', '1'],
            "protect_content": request.form.get('protect_content') in ['true', 'on', '1'],
            "pin_message": request.form.get('pin_message') in ['true', 'on', '1'],
            
            "description": request.form.get('description', ''),
            # Добавляем UTC время создания
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "utc_offset": datetime.now().astimezone().utcoffset().total_seconds() / 3600
        }
        
        # Логируем настройки для отладки
        logger.info(f"Настройки публикации для кампании '{name}':")
        logger.info(f"  - disable_preview: {campaign_data['disable_preview']} (исходное: '{request.form.get('disable_preview')}')")
        logger.info(f"  - disable_notification: {campaign_data['disable_notification']} (исходное: '{request.form.get('disable_notification')}')")
        logger.info(f"  - protect_content: {campaign_data['protect_content']} (исходное: '{request.form.get('protect_content')}')")
        logger.info(f"  - pin_message: {campaign_data['pin_message']} (исходное: '{request.form.get('pin_message')}')")
        
        # Обработка чатов
        chats_json = request.form.get('chats', '[]')
        try:
            chats = json.loads(chats_json)
            campaign_data["chats"] = chats
            logger.debug(f"Выбрано чатов: {len(chats)}")
        except json.JSONDecodeError:
            campaign_data["chats"] = []
            logger.warning("Ошибка парсинга JSON чатов")
        
        # Обработка кнопок
        buttons_json = request.form.get('buttons', '[]')
        try:
            buttons = json.loads(buttons_json)
            campaign_data["buttons"] = buttons
            logger.debug(f"Добавлено кнопок: {len(buttons)}")
        except json.JSONDecodeError:
            campaign_data["buttons"] = []
            logger.warning("Ошибка парсинга JSON кнопок")
        
        # Обработка медиафайлов
        media_files = []
        if 'media_files' in request.files:
            files = request.files.getlist('media_files')
            logger.debug(f"Получено файлов: {len(files)}")
            
            for file in files:
                if file and allowed_file(file.filename):
                    try:
                        # Генерируем уникальное имя файла
                        ext = file.filename.rsplit('.', 1)[1].lower()
                        filename = f"{uuid.uuid4().hex}.{ext}"
                        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        
                        # Создаем директорию если не существует
                        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                        
                        # Сохраняем файл
                        file.save(file_path)
                        
                        # Добавляем в список медиа
                        media_files.append({
                            "filename": filename,
                            "original_filename": secure_filename(file.filename),
                            "type": file.content_type,
                            "size": os.path.getsize(file_path)
                        })
                        
                        logger.debug(f"Сохранен файл: {filename}")
                        
                    except Exception as e:
                        logger.error(f"❌ Ошибка при сохранении файла {file.filename}: {e}")
                        continue
        
        campaign_data["media_files"] = media_files
        
        # Создаем кампанию через планировщик (убираем await для синхронного вызова)
        campaign_id = scheduler.add_campaign(campaign_data)
        
        logger.info(f"✅ Создана кампания: {campaign_id} - {name}")
        
        return jsonify({
            "success": True,
            "message": f"Кампания \"{name}\" успешно создана",
            "campaign_id": campaign_id
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании кампании: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера", "detail": str(e)}), 500

@api_bp.route('/campaigns/<campaign_id>', methods=['DELETE'])
@login_required
def delete_campaign(campaign_id):
    """Удаление кампании"""
    try:
        scheduler = current_app.scheduler
        
        # Проверяем существование кампании
        if campaign_id not in scheduler.campaigns:
            return jsonify({"error": "Кампания не найдена"}), 404
        
        # Получаем кампанию для удаления файлов
        campaign = scheduler.campaigns[campaign_id]
        
        # Удаляем файлы кампании
        for media in campaign.get('media_files', []):
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media.get('filename', ''))
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Удаляем кампанию через планировщик (убираем await)
        success = scheduler.delete_campaign(campaign_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Кампания успешно удалена"
            })
        else:
            return jsonify({"error": "Не удалось удалить кампанию"}), 500
        
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении кампании: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера", "detail": str(e)}), 500

@api_bp.route('/campaigns/<campaign_id>/toggle-status', methods=['POST'])
@login_required
def toggle_campaign_status(campaign_id):
    """Переключение статуса кампании (активна/приостановлена)"""
    try:
        scheduler = current_app.scheduler
        
        # Проверяем существование кампании
        if campaign_id not in scheduler.campaigns:
            return jsonify({"error": "Кампания не найдена"}), 404
        
        # Изменяем статус кампании (убираем await)
        new_status = scheduler.toggle_campaign_status(campaign_id)
        
        if new_status:
            status_text = "активирована" if new_status == "active" else "приостановлена"
            return jsonify({
                "success": True,
                "message": f"Кампания успешно {status_text}",
                "status": new_status
            })
        else:
            return jsonify({"error": "Не удалось изменить статус кампании"}), 500
        
    except Exception as e:
        logger.error(f"❌ Ошибка при изменении статуса кампании: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера", "detail": str(e)}), 500

@api_bp.route('/campaigns/<campaign_id>/complete', methods=['POST'])
@login_required
def complete_campaign(campaign_id):
    """Досрочное завершение компании"""
    try:
        scheduler = current_app.scheduler
        
        if campaign_id not in scheduler.campaigns:
            return jsonify({
                "success": False,
                "message": "Компания не найдена"
            }), 404
        
        campaign = scheduler.campaigns[campaign_id]
        campaign["status"] = "completed"
        campaign["updated_at"] = datetime.now().isoformat()
        
        # Сохраняем изменения
        scheduler._save_campaigns_sync()
        
        return jsonify({
            "success": True,
            "message": "Компания успешно завершена",
            "status": "completed"
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка при завершении компании: {e}")
        return jsonify({
            "success": False,
            "message": f"Внутренняя ошибка сервера: {str(e)}"
        }), 500

# API для чатов
@api_bp.route('/chats', methods=['GET'])
@login_required
def get_chats():
    """Получение списка чатов"""
    try:
        # Загружаем чаты из JSON
        config = current_app.config_obj
        
        with open(config.CHATS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chats = data.get('chats', [])
        
        return jsonify({"chats": chats})
    except Exception as e:
        logger.error(f"Ошибка при получении списка чатов: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера", "detail": str(e)}), 500

@api_bp.route('/chats', methods=['POST'])
@login_required
def add_chat():
    try:
        # Получаем ID чата из запроса
        data = request.get_json()
        chat_id = data.get('chat_id')

        if not chat_id:
            return jsonify({"error": "Не указан ID чата"}), 400

        # Получаем токен бота
        token = current_app.config_obj.BOT_TOKEN
        
        # Синхронно получаем информацию о чате через HTTP API
        chat_info = get_chat_info_sync(chat_id, token)

        if not chat_info:
            return jsonify({"error": "Не удалось получить информацию о чате"}), 404

        # Генерируем уникальный ID для чата в нашей системе
        chat_info["id"] = str(uuid.uuid4())
        chat_info["created_at"] = datetime.now().isoformat()
        chat_info["updated_at"] = datetime.now().isoformat()

        config = current_app.config_obj
        
        # Загружаем существующие чаты
        with open(config.CHATS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chats = data.get('chats', [])

        # Проверяем, не существует ли уже такой чат
        for chat in chats:
            if chat.get('chat_id') == chat_info.get('chat_id'):
                return jsonify({"error": "Этот чат уже добавлен"}), 400

        # Добавляем новый чат
        chats.append(chat_info)

        # Сохраняем обновленный список
        with open(config.CHATS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"chats": chats}, f, ensure_ascii=False, indent=2)

        return jsonify({
            "success": True,
            "message": f"Чат \"{chat_info.get('title')}\" успешно добавлен",
            **chat_info
        })

    except Exception as e:
        logger.error(f"Ошибка при добавлении чата: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера", "detail": str(e)}), 500

@api_bp.route('/chats/<chat_id>', methods=['DELETE'])
@login_required
def delete_chat(chat_id):
    """Удаление чата"""
    try:
        config = current_app.config_obj
        
        # Загружаем существующие чаты
        with open(config.CHATS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chats = data.get('chats', [])
        
        # Ищем чат по ID
        chat_index = None
        chat_data = None
        
        for i, chat in enumerate(chats):
            if chat.get('id') == chat_id:
                chat_index = i
                chat_data = chat
                break
        
        if chat_index is None:
            return jsonify({"error": "Чат не найден"}), 404
        
        # Удаляем чат из списка
        chats.pop(chat_index)
        
        # Сохраняем обновленный список
        with open(config.CHATS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"chats": chats}, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            "success": True,
            "message": f"Чат \"{chat_data.get('title')}\" успешно удален"
        })
        
    except Exception as e:
        logger.error(f"Ошибка при удалении чата: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера", "detail": str(e)}), 500

@api_bp.route('/chats/<chat_id>/update-info', methods=['POST'])
@login_required
def update_chat_info(chat_id):
    try:
        config = current_app.config_obj

        # Загружаем существующие чаты
        with open(config.CHATS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chats = data.get('chats', [])

        # Ищем чат по ID
        chat_index = None
        chat_data = None

        for i, chat in enumerate(chats):
            if chat.get('id') == chat_id:
                chat_index = i
                chat_data = chat
                break

        if chat_index is None:
            return jsonify({"error": "Чат не найден"}), 404

        # Получаем текущий chat_id для Telegram API
        telegram_chat_id = chat_data.get('chat_id')
        token = config.BOT_TOKEN

        # Синхронно получаем актуальную информацию о чате через HTTP API
        new_chat_info = get_chat_info_sync(telegram_chat_id, token)

        if not new_chat_info:
            return jsonify({"error": "Не удалось получить информацию о чате"}), 404

        # Сохраняем ID в нашей системе и дату создания
        new_chat_info["id"] = chat_id
        new_chat_info["created_at"] = chat_data.get('created_at')
        new_chat_info["updated_at"] = datetime.now().isoformat()

        # Обновляем чат в списке
        chats[chat_index] = new_chat_info

        # Сохраняем обновленный список
        with open(config.CHATS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"chats": chats}, f, ensure_ascii=False, indent=2)

        return jsonify({
            "success": True,
            "message": f"Информация о чате \"{new_chat_info.get('title')}\" обновлена"
        })

    except Exception as e:
        logger.error(f"Ошибка при обновлении информации о чате: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера", "detail": str(e)}), 500

# API для статистики
@api_bp.route('/statistics/campaigns', methods=['GET'])
@login_required
def get_campaigns_statistics():
    """Получение статистики по кампаниям"""
    try:
        logger.debug("Получение статистики кампаний")
        scheduler = current_app.scheduler
        campaigns = list(scheduler.campaigns.values())
        
        # Собираем статистику
        active_campaigns = sum(1 for c in campaigns if c.get('status') == 'active')
        total_campaigns = len(campaigns)
        
        # Дополнительная статистика
        scheduled_messages = sum(c.get('run_count', 0) for c in campaigns)
        
        stats = {
            "active_campaigns": active_campaigns,
            "total_campaigns": total_campaigns,
            "scheduled_messages": scheduled_messages
        }
        
        logger.debug(f"Статистика кампаний: {stats}")
        return jsonify(stats)
    except Exception as e:
        logger.error(f"❌ Ошибка при получении статистики кампаний: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@api_bp.route('/statistics/chats', methods=['GET'])
@login_required
def get_chats_statistics():
    """Получение статистики по чатам"""
    try:
        logger.debug("Получение статистики чатов")
        config = current_app.config_obj
        
        with open(config.CHATS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chats = data.get('chats', [])
        
        # Собираем статистику
        regular_groups = sum(1 for c in chats if str(c.get('type')) == 'group')
        forum_groups = sum(1 for c in chats if c.get('is_forum', False))
        supergroups = sum(1 for c in chats if str(c.get('type')) == 'supergroup' and not c.get('is_forum', False))
        total_chats = len(chats)
        
        stats = {
            "regular_groups": regular_groups,
            "forum_groups": forum_groups,
            "supergroups": supergroups,
            "total_chats": total_chats
        }
        
        logger.debug(f"Статистика чатов: {stats}")
        return jsonify(stats)
    except Exception as e:
        logger.error(f"❌ Ошибка при получении статистики чатов: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

# API для календаря
@api_bp.route('/calendar/events', methods=['GET'])
@login_required
def get_calendar_events():
    """Получение событий для календаря"""
    try:
        # Получаем список кампаний
        scheduler = current_app.scheduler
        campaigns = list(scheduler.campaigns.values())
        
        events = []
        for campaign in campaigns:
            try:
                # Пропускаем кампании без дат
                if not campaign.get('start_date') or not campaign.get('end_date'):
                    continue
                
                # Статус кампании
                status = campaign.get('status', 'draft')
                
                # Информация о времени публикации
                post_time = campaign.get('post_time', '12:00')
                
                # Проверяем расписание публикации
                start_date = datetime.fromisoformat(campaign['start_date']).date()
                end_date = datetime.fromisoformat(campaign['end_date']).date()
                
                # Определяем дни публикации
                publication_dates = []
                
                # Если есть указанные дни недели
                days_of_week = campaign.get('days_of_week', '')
                if days_of_week:
                    # Преобразуем строку дней недели в список чисел
                    weekdays = [int(day) for day in days_of_week.split(',') if day.isdigit()]
                    
                    # Генерируем даты для каждого дня недели в диапазоне дат
                    current_date = start_date
                    while current_date <= end_date:
                        # В Python понедельник=0, в JS понедельник=1
                        if (current_date.weekday() + 1) % 7 + 1 in weekdays:
                            publication_dates.append(current_date)
                        current_date += timedelta(days=1)
                
                # Если есть конкретные даты
                specific_dates = campaign.get('specific_dates', '')
                if specific_dates:
                    dates = specific_dates.split(',')
                    for date_str in dates:
                        try:
                            date_obj = datetime.fromisoformat(date_str).date()
                            if start_date <= date_obj <= end_date:
                                publication_dates.append(date_obj)
                        except:
                            continue
                
                # Если нет особых указаний дат, используем весь диапазон
                if not publication_dates:
                    current_date = start_date
                    while current_date <= end_date:
                        publication_dates.append(current_date)
                        current_date += timedelta(days=1)
                
                # Удаляем дубликаты дат
                publication_dates = list(set(publication_dates))
                
                # Создаем события для каждой даты публикации
                for pub_date in publication_dates:
                    events.append({
                        'title': campaign.get('name', 'Без названия'),
                        'date': pub_date.isoformat(),
                        'time': post_time,
                        'type': 'campaign',
                        'description': campaign.get('message_text', '')[:100] + '...' if len(campaign.get('message_text', '')) > 100 else campaign.get('message_text', ''),
                        'campaign_id': campaign.get('id'),
                        'campaign_name': campaign.get('name'),
                        'status': status,
                        'chats': campaign.get('chats', []),
                        'media_files': campaign.get('media_files', []),
                        'buttons': campaign.get('buttons', [])
                    })
            except Exception as e:
                logger.error(f"Ошибка при обработке кампании для календаря: {e}")
                continue
        
        return jsonify({'events': events})
    except Exception as e:
        logger.error(f"Ошибка при получении событий календаря: {e}")
        return jsonify({'error': str(e)}), 500

# Добавляем новый эндпоинт для массового обновления информации о чатах
@api_bp.route('/chats/update-all-info', methods=['POST'])
@login_required
def update_all_chats_info():
    """Массовое обновление информации о чатах"""
    try:
        config = current_app.config_obj
        token = config.BOT_TOKEN
        
        # Загружаем существующие чаты
        with open(config.CHATS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chats = data.get('chats', [])
        
        updated_chats = []
        failed_chats = []
        
        # Обновляем каждый чат по очереди
        for chat in chats:
            try:
                chat_id = chat.get('chat_id')
                if not chat_id:
                    failed_chats.append(chat)
                    continue
                
                # Получаем свежую информацию о чате
                new_chat_info = get_chat_info_sync(chat_id, token)
                
                if not new_chat_info:
                    failed_chats.append(chat)
                    continue
                
                # Сохраняем ID и даты
                new_chat_info["id"] = chat.get('id')
                new_chat_info["created_at"] = chat.get('created_at')
                new_chat_info["updated_at"] = datetime.now().isoformat()
                
                updated_chats.append(new_chat_info)
                
            except Exception as e:
                logger.error(f"Ошибка при обновлении чата {chat.get('id')}: {e}")
                failed_chats.append(chat)
        
        # Собираем все чаты вместе (обновленные + не обновленные)
        all_chats = updated_chats + failed_chats
        
        # Сохраняем обновленные данные
        with open(config.CHATS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"chats": all_chats}, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            "success": True,
            "message": f"Обновлено {len(updated_chats)} из {len(chats)} чатов",
            "updated_count": len(updated_chats),
            "failed_count": len(failed_chats)
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка при массовом обновлении чатов: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера", "detail": str(e)}), 500

# Добавляем новый эндпоинт для отправки тестового сообщения в чат
@api_bp.route('/chats/<chat_id>/test', methods=['POST'])
@login_required
def test_chat(chat_id):
    """Отправка тестового сообщения в чат"""
    try:
        # Находим чат в списке по ID
        config = current_app.config_obj
        
        # Загружаем существующие чаты
        with open(config.CHATS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chats = data.get('chats', [])
        
        # Ищем чат по ID
        chat_data = None
        for chat in chats:
            if chat.get('id') == chat_id:
                chat_data = chat
                break
        
        if not chat_data:
            return jsonify({"error": "Чат не найден"}), 404
        
        # Отправляем тестовое сообщение в чат
        telegram_chat_id = chat_data.get('chat_id')
        token = config.BOT_TOKEN
        
        # Готовим текст тестового сообщения
        test_message = f"🔄 <b>Тестовое сообщение</b>\n\n"
        test_message += f"📊 <b>Информация о чате:</b>\n"
        test_message += f"• Название: {chat_data.get('title')}\n"
        test_message += f"• Тип: {chat_data.get('type')}\n"
        test_message += f"• Участников: {chat_data.get('member_count') or '?'}\n"
        test_message += f"• Статус бота: {chat_data.get('bot_status')}\n\n"
        test_message += f"✅ <i>Отправлено из веб-интерфейса администратором {current_user.username}</i>\n"
        test_message += f"⏱ <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        
        # Отправляем через Telegram API
        api_url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': telegram_chat_id,
            'text': test_message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(api_url, json=payload)
        data = response.json()
        
        if data.get('ok'):
            message_id = data.get('result', {}).get('message_id')
            return jsonify({
                "success": True,
                "message": f"Тестовое сообщение отправлено в чат '{chat_data.get('title')}'",
                "message_id": message_id
            })
        else:
            error_description = data.get('description', 'Неизвестная ошибка')
            return jsonify({
                "success": False,
                "message": f"Не удалось отправить сообщение: {error_description}",
                "error_code": data.get('error_code')
            }), 400
        
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке тестового сообщения: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера", "detail": str(e)}), 500

# Добавляем новый эндпоинт для тестирования параметров публикации
@api_bp.route('/chats/<chat_id>/test-parameters', methods=['POST'])
@login_required
def test_chat_parameters(chat_id):
    """Тестирует параметры публикации в чате"""
    try:
        # Находим чат в списке по ID
        config = current_app.config_obj
        
        # Загружаем существующие чаты
        with open(config.CHATS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chats = data.get('chats', [])
        
        # Ищем чат по ID
        chat_data = None
        for chat in chats:
            if chat.get('id') == chat_id:
                chat_data = chat
                break
        
        if not chat_data:
            return jsonify({"error": "Чат не найден"}), 404
        
        # Получаем параметры из запроса
        request_data = request.get_json()
        disable_preview = request_data.get('disable_preview', False)
        disable_notification = request_data.get('disable_notification', False)
        protect_content = request_data.get('protect_content', False)
        pin_message = request_data.get('pin_message', False)
        
        logger.info(f"🧪 Тестирование параметров публикации для чата {chat_id}:")
        logger.info(f"   disable_preview: {disable_preview}")
        logger.info(f"   disable_notification: {disable_notification}")
        logger.info(f"   protect_content: {protect_content}")
        logger.info(f"   pin_message: {pin_message}")
        
        # Отправляем тестовое сообщение в чат
        telegram_chat_id = chat_data.get('chat_id')
        token = config.BOT_TOKEN
        
        # Готовим текст тестового сообщения с информацией о параметрах
        test_message = f"🧪 <b>Тест параметров публикации</b>\n\n"
        test_message += f"📊 <b>Применённые настройки:</b>\n"
        test_message += f"🔗 Предпросмотр ссылок: {'❌ отключён' if disable_preview else '✅ включён'}\n"
        test_message += f"🔔 Уведомления: {'❌ отключены' if disable_notification else '✅ включены'}\n"
        test_message += f"🛡️ Защищённый контент: {'✅ включён' if protect_content else '❌ отключён'}\n"
        test_message += f"📌 Закрепление: {'✅ будет закреплено' if pin_message else '❌ не будет закреплено'}\n\n"
        
        # Добавляем ссылку для тестирования предпросмотра
        test_message += f"🔗 <b>Тест ссылки:</b> https://github.com/\n\n"
        test_message += f"✅ <i>Отправлено из веб-интерфейса администратором {current_user.username}</i>\n"
        test_message += f"⏱ <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        
        # Отправляем через Telegram API с применением параметров
        api_url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': telegram_chat_id,
            'text': test_message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': disable_preview,
            'disable_notification': disable_notification,
            'protect_content': protect_content
        }
        
        response = requests.post(api_url, json=payload)
        data = response.json()
        
        if data.get('ok'):
            message_id = data.get('result', {}).get('message_id')
            
            # Пытаемся закрепить сообщение, если нужно
            if pin_message and message_id:
                pin_url = f"https://api.telegram.org/bot{token}/pinChatMessage"
                pin_payload = {
                    'chat_id': telegram_chat_id,
                    'message_id': message_id,
                    'disable_notification': disable_notification
                }
                
                pin_response = requests.post(pin_url, json=pin_payload)
                pin_data = pin_response.json()
                
                if pin_data.get('ok'):
                    logger.info(f"📌 Сообщение {message_id} успешно закреплено")
                else:
                    logger.warning(f"⚠️ Не удалось закрепить сообщение: {pin_data.get('description')}")
            
            return jsonify({
                "success": True,
                "message": f"Тестовое сообщение с параметрами отправлено в чат '{chat_data.get('title')}'",
                "message_id": message_id,
                "applied_parameters": {
                    "disable_preview": disable_preview,
                    "disable_notification": disable_notification,
                    "protect_content": protect_content,
                    "pin_message": pin_message
                }
            })
        else:
            error_description = data.get('description', 'Неизвестная ошибка')
            return jsonify({
                "success": False,
                "message": f"Не удалось отправить сообщение: {error_description}",
                "error_code": data.get('error_code')
            }), 400
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании параметров: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера", "detail": str(e)}), 500