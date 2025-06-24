import json
from datetime import datetime
import requests
from flask import jsonify, current_app, request
from flask_login import login_required, current_user
from loguru import logger

def test_chat_parameters(chat_id):
    """Тестирует параметры публикации в чате"""
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
        request_data = request.get_json()
        disable_preview = request_data.get('disable_preview', False)
        disable_notification = request_data.get('disable_notification', False)
        protect_content = request_data.get('protect_content', False)
        pin_message = request_data.get('pin_message', False)
        logger.info(f"🧪 Тестирование параметров публикации для чата {chat_id}:")
        logger.info(f"   disable_preview: {disable_preview}")
        logger.info(f"   disable_notification: {disable_notification}")
        logger.info(f"   protect_content: {protect_content}")
        logger.info(f"   pin_message: {pin_message}")
        telegram_chat_id = chat_data.get('chat_id')
        token = config.BOT_TOKEN
        test_message = f"🧪 <b>Тест параметров публикации</b>\n\n"
        test_message += f"📊 <b>Применённые настройки:</b>\n"
        test_message += f"🔗 Предпросмотр ссылок: {'❌ отключён' if disable_preview else '✅ включён'}\n"
        test_message += f"🔔 Уведомления: {'❌ отключены' if disable_notification else '✅ включены'}\n"
        test_message += f"🛡️ Защищённый контент: {'✅ включён' if protect_content else '❌ отключён'}\n"
        test_message += f"📌 Закрепление: {'✅ будет закреплено' if pin_message else '❌ не будет закреплено'}\n\n"
        test_message += f"🔗 <b>Тест ссылки:</b> https://github.com/\n\n"
        test_message += f"✅ <i>Отправлено из веб-интерфейса администратором {current_user.username}</i>\n"
        test_message += f"⏱ <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        api_url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': telegram_chat_id,
            'text': test_message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': disable_preview,
            'disable_notification': disable_notification,
            'protect_content': protect_content
        }
        response = requests.post(api_url, json=payload)
        data = response.json()
        if data.get('ok'):
            message_id = data.get('result', {}).get('message_id')
            if pin_message and message_id:
                pin_url = f"https://api.telegram.org/bot{token}/pinChatMessage"
                pin_payload = {
                    'chat_id': telegram_chat_id,
                    'message_id': message_id,
                    'disable_notification': disable_notification
                }
                pin_response = requests.post(pin_url, json=pin_payload)
                pin_data = pin_response.json()
                if pin_data.get('ok'):
                    logger.info(f"📌 Сообщение {message_id} успешно закреплено")
                else:
                    logger.warning(f"⚠️ Не удалось закрепить сообщение: {pin_data.get('description')}")
            return jsonify({
                "success": True,
                "message": f"Тестовое сообщение с параметрами отправлено в чат '{chat_data.get('title')}'",
                "message_id": message_id,
                "applied_parameters": {
                    "disable_preview": disable_preview,
                    "disable_notification": disable_notification,
                    "protect_content": protect_content,
                    "pin_message": pin_message
                }
            })
        else:
            error_description = data.get('description', 'Неизвестная ошибка')
            return jsonify({
                "success": False,
                "message": f"Не удалось отправить сообщение: {error_description}",
                "error_code": data.get('error_code')
            }), 400
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании параметров: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера", "detail": str(e)}), 500 