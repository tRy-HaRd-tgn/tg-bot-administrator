import requests
from loguru import logger

def get_chat_info_sync(chat_id, token):
    """Синхронно получает информацию о чате через Telegram HTTP API"""
    logger.debug(f"Запрос информации о чате {chat_id} через HTTP API")
    try:
        api_url = f"https://api.telegram.org/bot{token}/getChat"
        response = requests.get(api_url, params={'chat_id': chat_id})
        data = response.json()
        if not data.get('ok'):
            logger.error(f"❌ API вернул ошибку: {data.get('description', 'Неизвестная ошибка')}")
            return None
        chat = data['result']
        bot_status = "member"
        bot_is_admin = False
        bot_permissions = {}
        try:
            bot_info_url = f"https://api.telegram.org/bot{token}/getMe"
            bot_response = requests.get(bot_info_url)
            bot_data = bot_response.json()
            bot_id = bot_data.get('result', {}).get('id', 0) if bot_data.get('ok') else 0
            chat_member_url = f"https://api.telegram.org/bot{token}/getChatMember"
            member_response = requests.get(chat_member_url, params={
                'chat_id': chat_id, 
                'user_id': bot_id
            })
            member_data = member_response.json()
            if member_data.get('ok'):
                member_result = member_data.get('result', {})
                bot_status = member_result.get('status', 'member')
                bot_is_admin = bot_status in ['administrator', 'creator']
                bot_permissions = {
                    'can_be_edited': member_result.get('can_be_edited', False),
                    'can_manage_chat': member_result.get('can_manage_chat', False),
                    'can_change_info': member_result.get('can_change_info', False),
                    'can_delete_messages': member_result.get('can_delete_messages', False),
                    'can_invite_users': member_result.get('can_invite_users', False),
                    'can_restrict_members': member_result.get('can_restrict_members', False),
                    'can_pin_messages': member_result.get('can_pin_messages', False),
                    'can_promote_members': member_result.get('can_promote_members', False),
                    'can_manage_video_chats': member_result.get('can_manage_video_chats', False),
                    'can_manage_topics': member_result.get('can_manage_topics', False),
                    'can_post_messages': member_result.get('can_post_messages', False),
                    'can_edit_messages': member_result.get('can_edit_messages', False),
                    'can_send_messages': member_result.get('can_send_messages', True),
                    'can_send_media_messages': member_result.get('can_send_media_messages', True),
                    'can_send_polls': member_result.get('can_send_polls', True),
                    'can_send_other_messages': member_result.get('can_send_other_messages', True),
                    'can_add_web_page_previews': member_result.get('can_add_web_page_previews', True)
                }
                logger.debug(f"Статус бота в чате: {bot_status}")
        except Exception as e:
            logger.error(f"Ошибка при получении статуса бота: {e}")
        avatar_url = None
        try:
            if chat.get('photo'):
                photo_id = chat.get('photo', {}).get('big_file_id')
                if photo_id:
                    avatar_url = f"/api/chat-photo/{photo_id}"
        except Exception as e:
            logger.error(f"Ошибка при получении аватара: {e}")
        chat_info = {
            "id": str(chat.get('id')),
            "chat_id": chat.get('id'),
            "type": chat.get('type'),
            "title": chat.get('title'),
            "username": chat.get('username'),
            "description": chat.get('description'),
            "member_count": None,
            "is_forum": chat.get('is_forum', False),
            "avatar_url": avatar_url,
            "bot_status": bot_status,
            "bot_is_admin": bot_is_admin,
            "bot_permissions": bot_permissions,
            "invite_link": chat.get('invite_link'),
            "has_visible_history": chat.get('has_visible_history', False),
            "join_to_send_messages": chat.get('join_to_send_messages', False),
            "max_reaction_count": chat.get('max_reaction_count', 0),
            "accent_color_id": chat.get('accent_color_id'),
            "permissions": chat.get('permissions', {}),
            "accepted_gift_types": chat.get('accepted_gift_types', {}),
            "photo_info": chat.get('photo', {}),
            "has_protected_content": chat.get('has_protected_content', False),
            "has_aggressive_anti_spam": chat.get('has_aggressive_anti_spam', False),
            "has_hidden_members": chat.get('has_hidden_members', False),
            "slow_mode_delay": chat.get('slow_mode_delay', 0),
            "message_auto_delete_time": chat.get('message_auto_delete_time', 0),
            "linked_chat_id": chat.get('linked_chat_id'),
            "location": chat.get('location', {}),
            "pinned_message": chat.get('pinned_message', {}),
            "sticker_set_name": chat.get('sticker_set_name'),
            "can_set_sticker_set": chat.get('can_set_sticker_set', False),
            "can_send_messages": True
        }
        try:
            member_count_url = f"https://api.telegram.org/bot{token}/getChatMemberCount"
            count_response = requests.get(member_count_url, params={'chat_id': chat_id})
            count_data = count_response.json()
            if count_data.get('ok'):
                chat_info["member_count"] = count_data['result']
        except Exception as e:
            logger.warning(f"Не удалось получить число участников: {e}")
        logger.info(f"✅ Информация о чате получена: {chat_info['title']}")
        return chat_info
    except requests.RequestException as e:
        logger.error(f"❌ Ошибка HTTP запроса: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        return None 