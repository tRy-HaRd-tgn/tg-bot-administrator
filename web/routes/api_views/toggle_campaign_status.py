from flask import jsonify, current_app
from loguru import logger
from flask_login import login_required

def toggle_campaign_status(campaign_id):
    """Переключение статуса кампании (активна/приостановлена)"""
    try:
        scheduler = current_app.scheduler
        if campaign_id not in scheduler.campaigns:
            return jsonify({"error": "Кампания не найдена"}), 404
        new_status = scheduler.toggle_campaign_status_sync(campaign_id)
        if new_status:
            status_text = "активирована" if new_status == "active" else "приостановлена"
            return jsonify({
                "success": True,
                "message": f"Кампания успешно {status_text}",
                "status": new_status
            })
        else:
            return jsonify({"error": "Не удалось изменить статус кампании"}), 500
    except Exception as e:
        logger.error(f"❌ Ошибка при изменении статуса кампании: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера", "detail": str(e)}), 500 