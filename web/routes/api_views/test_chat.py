import json
from datetime import datetime
import requests
from flask import jsonify, current_app
from flask_login import login_required, current_user
from loguru import logger

def test_chat(chat_id):
    """Отправка тестового сообщения в чат"""
    try:
        config = current_app.config_obj
        with open(config.CHATS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chats = data.get('chats', [])
        chat_data = None
        for chat in chats:
            if chat.get('id') == chat_id:
                chat_data = chat
                break
        if not chat_data:
            return jsonify({"error": "Чат не найден"}), 404
        telegram_chat_id = chat_data.get('chat_id')
        token = config.BOT_TOKEN
        test_message = f"🔄 <b>Тестовое сообщение</b>\n\n"
        test_message += f"📊 <b>Информация о чате:</b>\n"
        test_message += f"• Название: {chat_data.get('title')}\n"
        test_message += f"• Тип: {chat_data.get('type')}\n"
        test_message += f"• Участников: {chat_data.get('member_count') or '?'}\n"
        test_message += f"• Статус бота: {chat_data.get('bot_status')}\n\n"
        test_message += f"✅ <i>Отправлено из веб-интерфейса администратором {current_user.username}</i>\n"
        test_message += f"⏱ <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        api_url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': telegram_chat_id,
            'text': test_message,
            'parse_mode': 'HTML'
        }
        response = requests.post(api_url, json=payload)
        data = response.json()
        if data.get('ok'):
            message_id = data.get('result', {}).get('message_id')
            return jsonify({
                "success": True,
                "message": f"Тестовое сообщение отправлено в чат '{chat_data.get('title')}'",
                "message_id": message_id
            })
        else:
            error_description = data.get('description', 'Неизвестная ошибка')
            return jsonify({
                "success": False,
                "message": f"Не удалось отправить сообщение: {error_description}",
                "error_code": data.get('error_code')
            }), 400
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке тестового сообщения: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера", "detail": str(e)}), 500 