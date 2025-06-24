from flask import jsonify, current_app
from loguru import logger
from flask_login import login_required

def get_campaigns():
    """Получение списка кампаний"""
    try:
        logger.debug("🔄 Получение списка кампаний...")
        scheduler = current_app.scheduler
        if not scheduler:
            logger.error("❌ Планировщик не инициализирован")
            return jsonify({
                "error": "Система не готова, попробуйте позже",
                "details": "Планировщик не инициализирован"
            }), 500
        campaigns = list(scheduler.campaigns.values())
        campaigns.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        logger.info(f"✅ Успешно получено {len(campaigns)} кампаний")
        return jsonify(campaigns)
    except Exception as e:
        logger.error(f"❌ Ошибка при получении списка кампаний: {e}")
        return jsonify({
            "error": "Внутренняя ошибка сервера",
            "details": str(e)
        }), 500 