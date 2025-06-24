import json
from flask import jsonify, current_app
from loguru import logger
from flask_login import login_required

def get_chats_statistics():
    """Получение статистики по чатам"""
    try:
        logger.debug("Получение статистики чатов")
        config = current_app.config_obj
        with open(config.CHATS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chats = data.get('chats', [])
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