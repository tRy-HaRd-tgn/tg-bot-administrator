import os
import json
import uuid
from datetime import datetime, timezone
from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
from loguru import logger
from flask_login import login_required
from .allowed_file import allowed_file

def create_campaign():
    """Создание новой кампании"""
    try:
        logger.debug("Создание новой кампании")
        logger.debug(f"Полученные данные формы: {dict(request.form)}")
        logger.debug(f"Полученные файлы: {list(request.files.keys())}")
        
        scheduler = current_app.scheduler
        name = request.form.get('name')
        message_text = request.form.get('message_text')
        status = request.form.get('status', 'draft')
        logger.debug(f"Данные кампании: name={name}, status={status}")
        if not name or not message_text:
            logger.warning("Отсутствуют обязательные поля")
            return jsonify({"error": "Необходимо указать название и текст сообщения"}), 400
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
            "disable_preview": request.form.get('disable_preview') in ['true', 'on', '1'],
            "disable_notification": request.form.get('disable_notification') in ['true', 'on', '1'],
            "protect_content": request.form.get('protect_content') in ['true', 'on', '1'],
            "pin_message": request.form.get('pin_message') in ['true', 'on', '1'],
            "description": request.form.get('description', ''),
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "utc_offset": datetime.now().astimezone().utcoffset().total_seconds() / 3600
        }
        repeat_settings_json = request.form.get('repeat_settings')
        if repeat_settings_json:
            try:
                campaign_data['repeat_settings'] = json.loads(repeat_settings_json)
                logger.debug(f"Добавлены repeat_settings: {campaign_data['repeat_settings']}")
            except Exception as e:
                logger.warning(f"Ошибка парсинга repeat_settings: {e}")
        logger.info(f"Настройки публикации для кампании '{name}':")
        logger.info(f"  - disable_preview: {campaign_data['disable_preview']} (исходное: '{request.form.get('disable_preview')}')")
        logger.info(f"  - disable_notification: {campaign_data['disable_notification']} (исходное: '{request.form.get('disable_notification')}')")
        logger.info(f"  - protect_content: {campaign_data['protect_content']} (исходное: '{request.form.get('protect_content')}')")
        logger.info(f"  - pin_message: {campaign_data['pin_message']} (исходное: '{request.form.get('pin_message')}')")
        chats_json = request.form.get('chats', '[]')
        try:
            chats = json.loads(chats_json)
            campaign_data["chats"] = chats
            logger.debug(f"Выбрано чатов: {len(chats)}")
            logger.debug(f"Данные чатов: {json.dumps(chats, indent=2)}")
        except json.JSONDecodeError as e:
            campaign_data["chats"] = []
            logger.warning(f"Ошибка парсинга JSON чатов: {e}")
            logger.warning(f"Полученные данные чатов: {chats_json}")
        except Exception as e:
            campaign_data["chats"] = []
            logger.error(f"Неожиданная ошибка при обработке чатов: {e}")
            logger.error(f"Полученные данные чатов: {chats_json}")
        buttons_json = request.form.get('buttons', '[]')
        try:
            buttons = json.loads(buttons_json)
            campaign_data["buttons"] = buttons
            logger.debug(f"Добавлено кнопок: {len(buttons)}")
        except json.JSONDecodeError:
            campaign_data["buttons"] = []
            logger.warning("Ошибка парсинга JSON кнопок")
        media_files = []
        if 'media_files' in request.files:
            files = request.files.getlist('media_files')
            logger.debug(f"Получено файлов: {len(files)}")
            for file in files:
                if file and allowed_file(file.filename):
                    try:
                        ext = file.filename.rsplit('.', 1)[1].lower()
                        filename = f"{uuid.uuid4().hex}.{ext}"
                        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                        file.save(file_path)
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
        campaign_id = scheduler.add_campaign_sync(campaign_data)
        logger.info(f"✅ Создана кампания: {campaign_id} - {name}")
        return jsonify({
            "success": True,
            "message": f"Кампания \"{name}\" успешно создана",
            "campaign_id": campaign_id
        })
    except Exception as e:
        logger.error(f"❌ Ошибка при создании кампании: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера", "detail": str(e)}), 500 