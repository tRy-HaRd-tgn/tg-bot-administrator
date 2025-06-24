import json
from flask import jsonify, current_app
from loguru import logger
from flask_login import login_required

def delete_chat(chat_id):
    """Удаление чата"""
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
        chats.pop(chat_index)
        with open(config.CHATS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"chats": chats}, f, ensure_ascii=False, indent=2)
        return jsonify({
            "success": True,
            "message": f"Чат \"{chat_data.get('title')}\" успешно удален"
        })
    except Exception as e:
        logger.error(f"Ошибка при удалении чата: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера", "detail": str(e)}), 500 