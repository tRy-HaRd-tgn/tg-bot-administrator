import logging
import asyncio
from typing import List, Dict, Any, Optional, Union
import json

from loguru import logger
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
    InputMediaVideo,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)

class TelegramBot:
    def __init__(self, config):
        logger.debug("Инициализация TelegramBot")
        self.config = config
        # Исправленная инициализация бота для aiogram 3.7+
        self.bot = Bot(
            token=config.BOT_TOKEN, 
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.dp = Dispatcher()
        
        # Добавляем переменные для хранения информации о хосте, порте и ngrok
        self.host = "0.0.0.0"
        self.port = 8000
        self.ngrok_url = None
        
        # Регистрируем обработчики сообщений
        self._register_handlers()
        logger.info("TelegramBot инициализирован")
    
    def _register_handlers(self):
        """Регистрация обработчиков сообщений"""
        logger.debug("Регистрация обработчиков сообщений")
        
        # Обработка команды /start
        @self.dp.message(Command("start"))
        async def cmd_start(message: types.Message):
            user_id = message.from_user.id
            logger.debug(f"Получена команда /start от пользователя {user_id}")
            
            # Проверяем, является ли пользователь админом
            if user_id in self.config.ADMIN_IDS:
                logger.info(f"Админ {user_id} запустил бота")
                # Создаем клавиатуру с кнопкой статуса
                keyboard = ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="📊 Получить статус системы")]],
                    resize_keyboard=True
                )
                await message.answer(
                    "👋 <b>Добро пожаловать в систему автопостинга!</b>\n\n"
                    "Бот создан для автоматической публикации сообщений в группы и каналы.\n"
                    "Для управления используйте веб-панель или кнопку ниже для получения статуса.",
                    reply_markup=keyboard
                )
            else:
                logger.warning(f"Неавторизованный пользователь {user_id} пытался запустить бота")
                # Игнорируем сообщения от не-админов
                pass
        
        # Обработчик для кнопки статуса - используем F.text вместо Text
        @self.dp.message(F.text == "📊 Получить статус системы")
        async def status_button_handler(message: types.Message):
            user_id = message.from_user.id
            logger.debug(f"Получен запрос статуса от пользователя {user_id}")
            
            # Проверяем, является ли пользователь админом
            if user_id in self.config.ADMIN_IDS:
                logger.info(f"Отправка статуса системы админу {user_id}")
                await self.send_status_message(user_id)
            else:
                logger.warning(f"Неавторизованный пользователь {user_id} запросил статус системы")
          # Обработчик всех остальных сообщений
        @self.dp.message()
        async def echo_message(message: types.Message):
            user_id = message.from_user.id
            chat_type = message.chat.type
            logger.debug(f"Получено сообщение от пользователя {user_id}: {message.text if message.text else 'без текста'}")
            logger.debug(f"Тип чата: {chat_type}")
            
            # Отвечаем только в личных сообщениях и только админам
            if chat_type == "private" and user_id in self.config.ADMIN_IDS:
                logger.debug(f"Отправка ответа админу {user_id} в личном чате")
                # Создаем клавиатуру с кнопкой статуса, если её ещё нет
                keyboard = ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="📊 Получить статус системы")]],
                    resize_keyboard=True
                )
                await message.answer("Используйте веб-панель для управления ботом или кнопку ниже для получения статуса.", reply_markup=keyboard)
            else:
                # В группах и каналах бот молчит
                if chat_type != "private":
                    logger.debug(f"Бот добавлен в группу/канал {message.chat.id}, никаких действий не требуется")
                else:
                    logger.warning(f"Игнорируем сообщение от неавторизованного пользователя {user_id}")
        
        logger.info("Обработчики сообщений зарегистрированы")
    
    async def setup(self):
        """Инициализация бота"""
        logger.debug("Настройка бота")
        
        try:
            # Получаем информацию о боте
            bot_info = await self.bot.get_me()
            logger.info(f"Инициализация бота @{bot_info.username} (ID: {bot_info.id})")
            
            # Запуск опроса обновлений
            await self._start_polling()
            logger.info("Бот настроен и запущен")
        except Exception as e:
            logger.error(f"Ошибка при настройке бота: {e}")
            raise
    
    async def _start_polling(self):
        """Запускает опрос новых сообщений"""
        logger.debug("Запуск polling для получения обновлений")
        
        try:
            # Запускаем в отдельной задаче, чтобы не блокировать основной поток
            loop = asyncio.get_event_loop()
            task = loop.create_task(self.dp.start_polling(self.bot))
            logger.info("Polling запущен")
            return task
        except Exception as e:
            logger.error(f"Ошибка при запуске polling: {e}")
            raise
    
    async def stop(self):
        """Останавливает бота"""
        logger.debug("Остановка бота")
        try:
            await self.bot.session.close()
            logger.info("Бот остановлен")
        except Exception as e:
            logger.error(f"Ошибка при остановке бота: {e}")
    
    async def notify_admin_startup(self, host, port, ngrok_url=None):
        """Уведомляет админов о запуске системы"""
        logger.debug(f"Отправка уведомлений о запуске {len(self.config.ADMIN_IDS)} админам")
        
        # Сохраняем информацию о системе для последующего использования
        self.host = host
        self.port = port
        self.ngrok_url = ngrok_url
        
        for admin_id in self.config.ADMIN_IDS:
            try:
                logger.debug(f"Отправка уведомления админу {admin_id}")
                
                # Формируем текст уведомления
                message = self._get_status_message()
                
                # Создаем обычную клавиатуру с кнопкой статуса
                keyboard = ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="📊 Получить статус системы")]],
                    resize_keyboard=True
                )
                
                # Создаем инлайн-кнопки с ссылками
                inline_buttons = []
                
                # Кнопка для локального доступа
                local_url = f"http://{self.host}:{self.port}"
                inline_buttons.append([InlineKeyboardButton(text="🌐 Открыть локальный интерфейс", url=local_url)])
                
                # Кнопка для внешнего доступа (если есть)
                if self.ngrok_url:
                    inline_buttons.append([InlineKeyboardButton(text="🔗 Открыть внешний доступ", url=self.ngrok_url)])
                
                # Создаем разметку с инлайн-кнопками
                inline_markup = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
                
                await self.bot.send_message(
                    admin_id,
                    message,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                
                # Отправляем второе сообщение с инлайн-кнопками для переходов
                await self.bot.send_message(
                    admin_id,
                    "Используйте кнопки ниже для быстрого доступа:",
                    reply_markup=inline_markup
                )
                
                logger.info(f"✅ Уведомление отправлено администратору {admin_id}")
            except TelegramAPIError as e:
                logger.error(f"❌ Ошибка при отправке уведомления администратору {admin_id}: {e}")
            except Exception as e:
                logger.error(f"❌ Неожиданная ошибка при отправке уведомления администратору {admin_id}: {e}")
    async def send_status_message(self, user_id):
        """Отправляет сообщение со статусом системы"""
        try:
            # Формируем текст сообщения
            message = self._get_status_message()
            
            # Создаем инлайн-кнопки с ссылками
            buttons = []
            
            # Кнопка для локального доступа
            local_url = f"http://{self.host}:{self.port}"
            buttons.append([InlineKeyboardButton(text="🌐 Открыть локальный интерфейс", url=local_url)])
            
            # Кнопка для внешнего доступа (если есть)
            if self.ngrok_url:
                buttons.append([InlineKeyboardButton(text="🔗 Открыть внешний доступ", url=self.ngrok_url)])
            
            # Создаем разметку с кнопками
            markup = InlineKeyboardMarkup(inline_keyboard=buttons)
            
            # Отправляем сообщение с инлайн-кнопками
            await self.bot.send_message(
                user_id,
                message,
                parse_mode="HTML",
                reply_markup=markup
            )
            logger.info(f"✅ Сообщение со статусом отправлено пользователю {user_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке статуса пользователю {user_id}: {e}")
    def _get_status_message(self):
        """Формирует текст сообщения со статусом системы"""
        message = f"🚀 <b>TG AutoPosting запущен!</b>\n\n"
        
        # Добавляем локальную ссылку
        message += f"🌐 Локальная веб-панель: <code>http://{self.host}:{self.port}</code>\n"
        
        # Добавляем Ngrok ссылку если она есть
        if self.ngrok_url:
            message += f"🔗 Внешний доступ: <code>{self.ngrok_url}</code>\n"
            
            # Добавляем информацию об обновлении в UTC формате
            from utils.time_helper import get_future_utc_time_str
            next_restart_str = get_future_utc_time_str(hours=self.config.NGROK_RESTART_INTERVAL)
            
            message += f"⏱️ Ссылка обновится в <b>{next_restart_str}</b>\n"
            message += f"⌛ Осталось: {self.config.NGROK_RESTART_INTERVAL} ч. 0 мин.\n"
        
        message += f"👤 Логин: <code>{self.config.ADMIN_USERNAME}</code>\n"
        message += f"🔑 Пароль: <code>{self.config.ADMIN_PASSWORD}</code>\n\n"
        message += f"✅ Система готова к работе!"
        
        return message
    
    async def send_message(self, chat_id: Union[int, str], text: str, 
                          thread_id: Optional[int] = None,
                          buttons: Optional[List[Dict]] = None,
                          disable_preview: bool = False,
                          disable_notification: bool = False,
                          protect_content: bool = False,
                          **kwargs) -> Optional[types.Message]:
        """Отправляет сообщение в указанный чат"""
        logger.debug(f"Отправка сообщения в чат {chat_id}, thread_id: {thread_id}")
        logger.debug(f"Параметры: disable_preview={disable_preview}, disable_notification={disable_notification}, protect_content={protect_content}")
        
        try:
            # Создаем клавиатуру с кнопками если они указаны
            reply_markup = None
            if buttons:
                logger.debug(f"Создание клавиатуры с {len(buttons)} кнопками")
                keyboard_buttons = []
                for button in buttons:
                    keyboard_buttons.append([
                        types.InlineKeyboardButton(
                            text=button.get("text", ""), 
                            url=button.get("url", "")
                        )
                    ])
                reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            
            # Отправляем сообщение с правильными параметрами
            message = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                message_thread_id=thread_id,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_preview,  # Отключение предпросмотра ссылок
                disable_notification=disable_notification,  # Тихая отправка
                protect_content=protect_content,           # Защищённый контент
                parse_mode="HTML",  # Явно указываем режим парсинга
                **kwargs
            )
            
            logger.info(f"✅ Сообщение отправлено в чат {chat_id}, ID сообщения: {message.message_id}")
            logger.info(f"   Применённые параметры: preview={not disable_preview}, notification={not disable_notification}, protected={protect_content}")
            return message
            
        except TelegramAPIError as e:
            logger.error(f"❌ Ошибка при отправке сообщения в чат {chat_id}: {e}")
            logger.error(f"   Код ошибки: {e.error_code if hasattr(e, 'error_code') else 'неизвестен'}")
            return None
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при отправке сообщения в чат {chat_id}: {e}")
            return None
    
    async def send_media_group(self, chat_id: Union[int, str], media: List[Any], 
                              thread_id: Optional[int] = None,
                              disable_notification: bool = False,
                              protect_content: bool = False) -> Optional[List[types.Message]]:
        """Отправляет группу медиафайлов в указанный чат"""
        logger.debug(f"Отправка медиа-группы в чат {chat_id}, файлов: {len(media)}")
        
        try:
            messages = await self.bot.send_media_group(
                chat_id=chat_id,
                media=media,
                message_thread_id=thread_id,
                disable_notification=disable_notification,
                protect_content=protect_content
            )
            
            logger.info(f"✅ Медиа-группа отправлена в чат {chat_id}, сообщений: {len(messages)}")
            return messages
        except TelegramAPIError as e:
            logger.error(f"❌ Ошибка при отправке медиа в чат {chat_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при отправке медиа в чат {chat_id}: {e}")
            return None
    
    async def send_media_group_with_buttons(
        self,
        chat_id: Union[int, str],
        media: List[Dict],
        buttons: Optional[List[Dict]] = None,
        thread_id: Optional[int] = None,
        disable_notification: bool = False,
        protect_content: bool = False
    ) -> Optional[List[types.Message]]:
        """Отправляет группу медиафайлов с кнопками"""
        logger.debug(f"Отправка медиа-группы в чат {chat_id}")
        logger.debug(f"Параметры: disable_notification={disable_notification}, protect_content={protect_content}")
        
        try:
            # Подготавливаем медиа группу
            media_group = []
            
            for item in media:
                file_path = item.get("path")
                file_type = item.get("type")
                caption = item.get("caption", "")
                
                if not file_path:
                    continue
                    
                file = FSInputFile(file_path)
                
                if file_type.startswith("image/"):
                    media_item = InputMediaPhoto(media=file, caption=caption, parse_mode="HTML")
                elif file_type.startswith("video/") or file_type.endswith("/gif"):
                    media_item = InputMediaVideo(media=file, caption=caption, parse_mode="HTML")
                else:
                    continue
                    
                media_group.append(media_item)

            if not media_group:
                logger.warning("Нет валидных медиафайлов для отправки")
                return None

            # Отправляем медиа группу с правильными параметрами
            logger.info(f"📸 Отправка {len(media_group)} медиафайлов с параметрами: notification={not disable_notification}, protected={protect_content}")
            
            messages = await self.bot.send_media_group(
                chat_id=chat_id,
                media=media_group,
                message_thread_id=thread_id,
                disable_notification=disable_notification,  # Тихая отправка
                protect_content=protect_content             # Защищённый контент
            )
            
            # Если есть кнопки, добавляем их к первому сообщению медиа-группы
            if buttons and messages:
                keyboard = []
                for button in buttons:
                    keyboard.append([
                        InlineKeyboardButton(
                            text=button.get("text", ""),
                            url=button.get("url", "")
                        )
                    ])
                    
                markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
                
                logger.debug("Добавление кнопок к первому сообщению медиа-группы")
                
                # Редактируем первое сообщение медиа-группы, добавляя кнопки
                try:
                    await self.bot.edit_message_reply_markup(
                        chat_id=chat_id,
                        message_id=messages[0].message_id,
                        reply_markup=markup
                    )
                    logger.debug("Кнопки успешно добавлены к медиа-сообщению")
                except Exception as e:
                    logger.warning(f"Не удалось добавить кнопки к медиа-сообщению: {e}")
                    # Если не удалось добавить кнопки к медиа, отправляем их отдельным сообщением
                    logger.debug("Отправка кнопок отдельным сообщением")
                    
                    button_message = await self.bot.send_message(
                        chat_id=chat_id,
                        text="⚡ Дополнительные действия:",
                        reply_markup=markup,
                        message_thread_id=thread_id,
                        disable_notification=disable_notification,
                        protect_content=protect_content
                    )
                    
                    if button_message:
                        messages.append(button_message)
            
            logger.info(f"✅ Медиа-группа отправлена в чат {chat_id}, сообщений: {len(messages)}")
            return messages
            
        except TelegramAPIError as e:
            logger.error(f"❌ Ошибка при отправке медиа группы в чат {chat_id}: {e}")
            logger.error(f"   Код ошибки: {e.error_code if hasattr(e, 'error_code') else 'неизвестен'}")
            return None
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при отправке медиа группы в чат {chat_id}: {e}")
            return None
    
    async def delete_message(self, chat_id: Union[int, str], message_id: int) -> bool:
        """Удаляет сообщение из указанного чата"""
        logger.debug(f"Удаление сообщения {message_id} из чата {chat_id}")
        
        try:
            await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
            logger.info(f"✅ Сообщение {message_id} удалено из чата {chat_id}")
            return True
        except TelegramAPIError as e:
            logger.error(f"❌ Ошибка при удалении сообщения {message_id} из чата {chat_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при удалении сообщения {message_id} из чата {chat_id}: {e}")
            return False
    
    async def get_chat_info(self, chat_id: Union[int, str]) -> Optional[Dict]:
        """Получает информацию о чате"""
        logger.debug(f"Получение информации о чате {chat_id}")
        
        try:
            chat = await self.bot.get_chat(chat_id=chat_id)
            # Получаем дополнительные поля
            chat_member = await self.bot.get_chat_member(chat_id=chat_id, user_id=self.bot.id)
            
            # Формируем структуру с данными о чате
            chat_info = {
                "id": str(chat.id),
                "chat_id": chat.id,
                "type": chat.type.value if hasattr(chat.type, 'value') else str(chat.type),
                "title": chat.title,
                "username": chat.username,
                "description": chat.description,
                "member_count": None,  # В aiogram 3.x нет прямого доступа
                "is_forum": getattr(chat, 'is_forum', False),
                "avatar_url": None,  # API не дает прямого доступа к аватарке
                "bot_status": chat_member.status.value if hasattr(chat_member.status, 'value') else str(chat_member.status),
                "can_send_messages": getattr(chat_member, 'can_send_messages', False),
                "can_edit_messages": getattr(chat_member, 'can_edit_messages', False),
                "can_delete_messages": getattr(chat_member, 'can_delete_messages', False),
                "can_pin_messages": getattr(chat_member, 'can_pin_messages', False),
                "can_manage_topics": getattr(chat_member, "can_manage_topics", False)
            }
            
            # Если это форум, получаем темы
            if chat_info["is_forum"]:
                logger.debug(f"Чат {chat_id} является форумом, получаем темы")
                chat_info["forum_topics"] = await self.get_forum_topics(chat_id)
            
            logger.info(f"✅ Информация о чате {chat_id} получена: {chat_info['title']}")
            return chat_info
        except TelegramAPIError as e:
            logger.error(f"❌ Ошибка при получении информации о чате {chat_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при получении информации о чате {chat_id}: {e}")
            return None
    
    async def get_forum_topics(self, chat_id: Union[int, str]) -> List[Dict]:
        """Получает список тем форума"""
        logger.debug(f"Получение тем форума для чата {chat_id}")
        
        try:
            # В aiogram 3.x метод может отличаться
            # Пока возвращаем пустой список, так как API может измениться
            logger.warning("Получение тем форума временно недоступно в aiogram 3.x")
            return []
        except TelegramAPIError as e:
            logger.error(f"❌ Ошибка при получении тем форума для чата {chat_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при получении тем форума для чата {chat_id}: {e}")
            return []
    
    async def send_message_to_chat(self, chat_id, message_text, media_files=None, buttons=None, disable_web_page_preview=False, disable_notification=False, protect_content=False, thread_id=None, parse_mode="HTML"):
        """Отправляет сообщение в чат"""
        try:
            # Подготовка кнопок, если они есть
            reply_markup = None
            if buttons and isinstance(buttons, list) and len(buttons) > 0:
                logger.debug(f"Подготовка кнопок: {buttons}")
                inline_keyboard = []
                for button in buttons:
                    # Проверяем наличие необходимых полей
                    if isinstance(button, dict) and 'text' in button and 'url' in button:
                        inline_keyboard.append([{"text": button["text"], "url": button["url"]}])
                
                if inline_keyboard:
                    reply_markup = {"inline_keyboard": inline_keyboard}
                    logger.debug(f"Инлайн клавиатура создана: {reply_markup}")

            # Отправляем сообщение в зависимости от наличия медиафайлов
            if media_files and len(media_files) > 0:
                # Логика отправки медиафайлов (если необходимо)
                pass
            else:
                # Отправка текстового сообщения с кнопками
                message = await self.bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode=parse_mode,
                    disable_web_page_preview=disable_web_page_preview,
                    disable_notification=disable_notification,
                    protect_content=protect_content,
                    message_thread_id=thread_id,
                    reply_markup=reply_markup  # Передаем подготовленные кнопки
                )

            logger.info(f"✅ Сообщение отправлено в чат {chat_id}")
        except TelegramAPIError as e:
            logger.error(f"❌ Ошибка при отправке сообщения в чат {chat_id}: {e}")
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при отправке сообщения в чат {chat_id}: {e}")
