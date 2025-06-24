import os
from flask import jsonify, current_app
from loguru import logger
from flask_login import login_required

def delete_campaign(campaign_id):
    """Удаление кампании"""
    try:
        scheduler = current_app.scheduler
        if campaign_id not in scheduler.campaigns:
            return jsonify({"error": "Кампания не найдена"}), 404
        campaign = scheduler.campaigns[campaign_id]
        for media in campaign.get('media_files', []):
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media.get('filename', ''))
            if os.path.exists(file_path):
                os.remove(file_path)
        success = scheduler.delete_campaign(campaign_id)
        if success:
            return jsonify({
                "success": True,
                "message": "Кампания успешно удалена"
            })
        else:
            return jsonify({"error": "Не удалось удалить кампанию"}), 500
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении кампании: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера", "detail": str(e)}), 500 