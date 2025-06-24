import json
from datetime import datetime
from flask import jsonify, current_app
from loguru import logger
from flask_login import login_required
from .get_chat_info_sync import get_chat_info_sync

def update_chat_info(chat_id):
    try:
        config = current_app.config_obj
        with open(config.CHATS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chats = data.get('chats', [])
        chat_index = None
        chat_data = None
        for i, chat in enumerate(chats):
            if chat.get('id') == chat_id:
                chat_index = i
                chat_data = chat
                break
        if chat_index is None:
            return jsonify({"error": "Чат не найден"}), 404
        telegram_chat_id = chat_data.get('chat_id')
        token = config.BOT_TOKEN
        new_chat_info = get_chat_info_sync(telegram_chat_id, token)
        if not new_chat_info:
            return jsonify({"error": "Не удалось получить информацию о чате"}), 404
        new_chat_info["id"] = chat_id
        new_chat_info["created_at"] = chat_data.get('created_at')
        new_chat_info["updated_at"] = datetime.now().isoformat()
        chats[chat_index] = new_chat_info
        with open(config.CHATS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"chats": chats}, f, ensure_ascii=False, indent=2)
        return jsonify({
            "success": True,
            "message": f"Информация о чате \"{new_chat_info.get('title')}\" обновлена"
        })
    except Exception as e:
        logger.error(f"Ошибка при обновлении информации о чате: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера", "detail": str(e)}), 500 