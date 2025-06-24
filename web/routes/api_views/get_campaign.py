from flask import jsonify, current_app
from loguru import logger
from flask_login import login_required

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