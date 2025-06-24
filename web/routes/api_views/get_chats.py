import json
from flask import jsonify, current_app
from loguru import logger
from flask_login import login_required

def get_chats():
    """Получение списка чатов"""
    try:
        config = current_app.config_obj
        with open(config.CHATS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chats = data.get('chats', [])
        return jsonify({"chats": chats})
    except Exception as e:
        logger.error(f"Ошибка при получении списка чатов: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера", "detail": str(e)}), 500 