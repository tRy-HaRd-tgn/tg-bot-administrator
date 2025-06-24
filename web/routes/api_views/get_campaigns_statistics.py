from flask import jsonify, current_app
from loguru import logger
from flask_login import login_required

def get_campaigns_statistics():
    """Получение статистики по кампаниям"""
    try:
        logger.debug("Получение статистики кампаний")
        scheduler = current_app.scheduler
        campaigns = list(scheduler.campaigns.values())
        active_campaigns = sum(1 for c in campaigns if c.get('status') == 'active')
        total_campaigns = len(campaigns)
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