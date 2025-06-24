from datetime import datetime
from flask import jsonify, current_app
from loguru import logger
from flask_login import login_required

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