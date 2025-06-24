import json
import uuid
from datetime import datetime
from flask import request, jsonify, current_app
from loguru import logger
from flask_login import login_required
from .get_chat_info_sync import get_chat_info_sync

def add_chat():
    try:
        data = request.get_json()
        chat_id = data.get('chat_id')
        if not chat_id:
            return jsonify({"error": "Не указан ID чата"}), 400
        token = current_app.config_obj.BOT_TOKEN
        chat_info = get_chat_info_sync(chat_id, token)
        if not chat_info:
            return jsonify({"error": "Не удалось получить информацию о чате"}), 404
        chat_info["id"] = str(uuid.uuid4())
        chat_info["created_at"] = datetime.now().isoformat()
        chat_info["updated_at"] = datetime.now().isoformat()
        config = current_app.config_obj
        with open(config.CHATS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chats = data.get('chats', [])
        for chat in chats:
            if chat.get('chat_id') == chat_info.get('chat_id'):
                return jsonify({"error": "Этот чат уже добавлен"}), 400
        chats.append(chat_info)
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