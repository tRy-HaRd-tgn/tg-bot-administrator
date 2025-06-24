import requests
from io import BytesIO
from flask import jsonify, current_app, send_file
from flask_login import login_required
from loguru import logger

def get_chat_photo(file_id):
    """Проксирует фото чата, скрывая токен бота"""
    try:
        token = current_app.config_obj.BOT_TOKEN
        file_info_url = f"https://api.telegram.org/bot{token}/getFile"
        file_info_resp = requests.get(file_info_url, params={'file_id': file_id})
        file_info = file_info_resp.json()
        if not file_info.get('ok'):
            return jsonify({"error": "Не удалось получить информацию о файле"}), 404
        file_path = file_info['result']['file_path']
        file_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
        file_resp = requests.get(file_url)
        if file_resp.status_code != 200:
            return jsonify({"error": "Не удалось скачать файл"}), 404
        return send_file(BytesIO(file_resp.content), mimetype='image/jpeg')
    except Exception as e:
        logger.error(f"Ошибка при проксировании фото чата: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500 