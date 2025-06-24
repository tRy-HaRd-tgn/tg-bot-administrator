import json
from datetime import datetime
from flask import jsonify, current_app
from loguru import logger
from flask_login import login_required
from .get_chat_info_sync import get_chat_info_sync

def update_all_chats_info():
    """Массовое обновление информации о чатах"""
    try:
        config = current_app.config_obj
        token = config.BOT_TOKEN
        with open(config.CHATS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chats = data.get('chats', [])
        updated_chats = []
        failed_chats = []
        for chat in chats:
            try:
                chat_id = chat.get('chat_id')
                if not chat_id:
                    failed_chats.append(chat)
                    continue
                new_chat_info = get_chat_info_sync(chat_id, token)
                if not new_chat_info:
                    failed_chats.append(chat)
                    continue
                new_chat_info["id"] = chat.get('id')
                new_chat_info["created_at"] = chat.get('created_at')
                new_chat_info["updated_at"] = datetime.now().isoformat()
                updated_chats.append(new_chat_info)
            except Exception as e:
                logger.error(f"Ошибка при обновлении чата {chat.get('id')}: {e}")
                failed_chats.append(chat)
        all_chats = updated_chats + failed_chats
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