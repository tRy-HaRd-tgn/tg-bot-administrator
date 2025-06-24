import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
import uuid
from typing import Dict, List, Optional, Any, Set, Union

from loguru import logger
from aiogram.types import InputMediaPhoto, InputMediaVideo, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.exceptions import TelegramAPIError

class CampaignScheduler:
    def __init__(self, telegram_bot, config):
        logger.debug("Инициализация CampaignScheduler")
        self.bot = telegram_bot
        self.config = config
        self.campaigns = {}
        self.running = False
        self.tasks = set()
        self.next_run_times = {}
        logger.info("CampaignScheduler инициализирован")
    
    async def start(self):
        """Запускает планировщик кампаний"""
        logger.debug("Запуск планировщика кампаний")
        self.running = True
        
        # Загружаем существующие кампании из JSON файла
        await self.load_campaigns()
        
        # Запускаем задачу проверки расписания
        task = asyncio.create_task(self._schedule_checker())
        self.tasks.add(task)
        
        logger.info("✅ Планировщик кампаний запущен")
    
    async def stop(self):
        """Останавливает планировщик кампаний"""
        logger.debug("Остановка планировщика кампаний")
        self.running = False
        
        # Отменяем все запущенные задачи
        for task in self.tasks:
            task.cancel()
        
        logger.info("✅ Планировщик кампаний остановлен")
    
    async def load_campaigns(self):
        """Загружает кампании из JSON файла"""
        logger.debug(f"Загрузка кампаний из файла: {self.config.CAMPAIGNS_FILE}")
        
        try:
            # Проверяем существование директории data
            data_dir = os.path.dirname(self.config.CAMPAIGNS_FILE)
            if not os.path.exists(data_dir):
                logger.warning(f"Директория {data_dir} не существует, создаем...")
                os.makedirs(data_dir, exist_ok=True)

            # Проверяем существование файла
            if os.path.exists(self.config.CAMPAIGNS_FILE):
                try:
                    with open(self.config.CAMPAIGNS_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if not isinstance(data, dict):
                            raise ValueError("Некорректный формат JSON - ожидается объект")
                        
                        campaigns = data.get('campaigns', [])
                        if not isinstance(campaigns, list):
                            raise ValueError("Некорректный формат campaigns - ожидается массив")
                        
                        # Очищаем текущие кампании
                        self.campaigns.clear()
                        
                        # Загружаем кампании в память
                        for campaign in campaigns:
                            if not isinstance(campaign, dict) or 'id' not in campaign:
                                logger.warning(f"Пропущена некорректная кампания: {campaign}")
                                continue
                                
                            self.campaigns[campaign['id']] = campaign
                            logger.debug(f"Загружена кампания: {campaign['id']} - {campaign.get('name', 'Без названия')}")
                        
                        logger.info(f"✅ Успешно загружено {len(self.campaigns)} кампаний из JSON")
                
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Ошибка декодирования JSON: {e}")
                    # Создаем резервную копию поврежденного файла
                    backup_path = f"{self.config.CAMPAIGNS_FILE}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    os.rename(self.config.CAMPAIGNS_FILE, backup_path)
                    logger.info(f"📑 Создана резервная копия поврежденного файла: {backup_path}")
                    # Создаем новый пустой файл
                    self._create_empty_campaigns_file()
                
                except ValueError as e:
                    logger.error(f"❌ Ошибка валидации данных: {e}")
                    self._create_empty_campaigns_file()
                
            else:
                logger.info("📄 Файл кампаний не существует, создаем новый...")
                self._create_empty_campaigns_file()
            
        except PermissionError as e:
            logger.error(f"❌ Ошибка доступа к файлу: {e}")
            raise RuntimeError(f"Нет доступа к файлу кампаний: {self.config.CAMPAIGNS_FILE}")
            
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при загрузке кампаний: {e}")
            raise RuntimeError(f"Не удалось загрузить кампании: {e}")

    def _create_empty_campaigns_file(self):
        """Создает пустой файл кампаний"""
        try:
            with open(self.config.CAMPAIGNS_FILE, 'w', encoding='utf-8') as f:
                json.dump({"campaigns": []}, f, ensure_ascii=False, indent=2)
            logger.info("✅ Создан новый пустой файл кампаний")
            self.campaigns.clear()
        except Exception as e:
            logger.error(f"❌ Ошибка при создании пустого файла кампаний: {e}")
            raise RuntimeError(f"Не удалось создать файл кампаний: {e}")
    
    async def save_campaigns(self):
        """Сохраняет кампании в JSON файл"""
        logger.debug("Сохранение кампаний в JSON файл")
        
        try:
            campaigns_list = list(self.campaigns.values())
            with open(self.config.CAMPAIGNS_FILE, 'w', encoding='utf-8') as f:
                json.dump({"campaigns": campaigns_list}, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Сохранено {len(campaigns_list)} кампаний в JSON")
        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении кампаний: {e}")
    
    async def add_campaign(self, campaign_data: Dict) -> str:
        """Добавляет новую кампанию"""
        # Генерируем уникальный ID для кампании
        campaign_id = str(uuid.uuid4())
        logger.debug(f"Добавление новой кампании с ID: {campaign_id}")
        
        # Добавляем служебные поля
        campaign_data["id"] = campaign_id
        campaign_data["created_at"] = datetime.now().isoformat()
        campaign_data["updated_at"] = datetime.now().isoformat()
        # Убедимся, что у нас всегда есть UTC метка времени
        if "created_utc" not in campaign_data:
            campaign_data["created_utc"] = datetime.now(timezone.utc).isoformat()
        
        # Добавляем кампанию в память
        self.campaigns[campaign_id] = campaign_data
        
        # Сохраняем изменения в JSON
        await self.save_campaigns()
        
        logger.info(f"✅ Добавлена новая кампания: {campaign_id} - {campaign_data.get('name', 'Без названия')}")
        
        return campaign_id
    
    async def update_campaign(self, campaign_id: str, campaign_data: Dict) -> bool:
        """Обновляет существующую кампанию"""
        logger.debug(f"Обновление кампании: {campaign_id}")
        
        if campaign_id not in self.campaigns:
            logger.error(f"❌ Кампания не найдена: {campaign_id}")
            return False
        
        # Обновляем поля кампании
        campaign_data["id"] = campaign_id  # Сохраняем исходный ID
        campaign_data["updated_at"] = datetime.now().isoformat()
        
        # Обновляем кампанию в памяти
        self.campaigns[campaign_id] = campaign_data
        
        # Сохраняем изменения в JSON
        await self.save_campaigns()
        
        logger.info(f"✅ Обновлена кампания: {campaign_id}")
        
        return True
    
    async def delete_campaign(self, campaign_id: str) -> bool:
        """Удаляет кампанию"""
        logger.debug(f"Удаление кампании: {campaign_id}")
        
        if campaign_id not in self.campaigns:
            logger.error(f"❌ Кампания не найдена: {campaign_id}")
            return False
        
        # Удаляем кампанию из памяти
        campaign_name = self.campaigns[campaign_id].get('name', 'Без названия')
        del self.campaigns[campaign_id]
        
        # Сохраняем изменения в JSON
        await self.save_campaigns()
        
        logger.info(f"✅ Удалена кампания: {campaign_id} - {campaign_name}")
        
        return True
    
    async def toggle_campaign_status(self, campaign_id: str) -> Optional[str]:
        """Изменяет статус кампании (активна/приостановлена)"""
        logger.debug(f"Изменение статуса кампании: {campaign_id}")
        
        if campaign_id not in self.campaigns:
            logger.error(f"❌ Кампания не найдена: {campaign_id}")
            return None
        
        campaign = self.campaigns[campaign_id]
        
        # Переключаем статус
        current_status = campaign.get("status", "draft")
        new_status = "paused" if current_status == "active" else "active"
        
        # Обновляем статус
        campaign["status"] = new_status
        campaign["updated_at"] = datetime.now().isoformat()
        
        # Сохраняем изменения в JSON
        await self.save_campaigns()
        
        logger.info(f"✅ Изменен статус кампании {campaign_id}: {current_status} → {new_status}")
        
        return new_status
    
    async def _schedule_checker(self):
        """Периодически проверяет кампании для публикации"""
        logger.debug("Запуск проверки расписания кампаний")
        
        try:
            while self.running:
                # Используем UTC время для проверки
                now_utc = datetime.now(timezone.utc)
                logger.debug(f"Проверка кампаний в UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S')} (Локальное: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
                
                # Перебираем все активные кампании
                for campaign_id, campaign in self.campaigns.items():
                    # Пропускаем неактивные кампании
                    if campaign.get("status") != "active":
                        continue
                    
                    # Проверяем, подходит ли время для публикации
                    if await self._should_run_campaign(campaign, now_utc):
                        logger.info(f"🎯 Запуск кампании: {campaign_id}")
                        # Запускаем публикацию в отдельной задаче
                        task = asyncio.create_task(self._process_campaign(campaign))
                        self.tasks.add(task)
                        task.add_done_callback(self.tasks.discard)
                
                # Проверяем каждую минуту
                await asyncio.sleep(60)
                
        except asyncio.CancelledError:
            logger.info("⏹️ Задача проверки расписания отменена")
        except Exception as e:
            logger.error(f"❌ Ошибка в планировщике кампаний: {e}")
    
    async def _should_run_campaign(self, campaign: Dict, now_utc: datetime) -> bool:
        """Проверяет, должна ли кампания запуститься в текущее время (UTC)"""
        logger.debug(f"Проверка времени запуска кампании: {campaign.get('id')}")
        
        try:
            # Базовые проверки дат
            start_date_str = campaign.get("start_date")
            end_date_str = campaign.get("end_date")
            
            if not start_date_str or not end_date_str:
                return False
            
            try:
                start_date = datetime.fromisoformat(start_date_str).astimezone(timezone.utc).date()
                end_date = datetime.fromisoformat(end_date_str).astimezone(timezone.utc).date()
            except ValueError:
                start_date = datetime.fromisoformat(start_date_str).date()
                end_date = datetime.fromisoformat(end_date_str).date()
            
            current_date_utc = now_utc.date()
            
            if current_date_utc < start_date or current_date_utc > end_date:
                return False

            # Проверка настроек автоповтора
            repeat_enabled = campaign.get("repeat_enabled", False)
            if repeat_enabled:
                repeat_settings = campaign.get("repeat_settings", {})
                interval = repeat_settings.get("interval")
                post_time_str = campaign.get("post_time", "12:00")
                post_time_parts = post_time_str.split(":")
                post_time_hour = int(post_time_parts[0])
                post_time_minute = int(post_time_parts[1])
                last_run = self.next_run_times.get(campaign.get('id'))
                
                if interval == "minutely":
                    # Каждую минуту в диапазоне дат
                    logger.debug(f"Кампания {campaign.get('id')} — автоповтор: каждую минуту")
                    if last_run and (now_utc - last_run).total_seconds() < 60:
                        return False
                elif interval == "hourly":
                    # Каждый час в указанную минуту
                    logger.debug(f"Кампания {campaign.get('id')} — автоповтор: каждый час в {post_time_minute:02d} минуту")
                    if now_utc.minute != post_time_minute:
                        return False
                    if last_run and (now_utc - last_run).total_seconds() < 3600:
                        return False
                elif interval == "daily":
                    # Каждый день в указанное время
                    if now_utc.hour != post_time_hour or now_utc.minute != post_time_minute:
                        return False
                    if last_run and (now_utc - last_run).total_seconds() < 86400:
                        return False
                elif interval == "weekly":
                    # В указанный день недели и время
                    week_day = repeat_settings.get("weekDay")
                    if str(now_utc.isoweekday()) != str(week_day):
                        return False
                    if now_utc.hour != post_time_hour or now_utc.minute != post_time_minute:
                        return False
                    if last_run and (now_utc - last_run).total_seconds() < 604800:
                        return False
                elif interval == "monthly":
                    month_settings = repeat_settings.get("monthlySettings", {})
                    if month_settings.get("type") == "date":
                        # В указанный день месяца и время
                        if str(now_utc.day) != str(month_settings.get("date")):
                            return False
                        if now_utc.hour != post_time_hour or now_utc.minute != post_time_minute:
                            return False
                    else:
                        # В определённый день недели месяца
                        week_num = month_settings.get("week")
                        week_day = month_settings.get("weekDay")
                        current_week = (now_utc.day - 1) // 7 + 1
                        if (str(current_week) != str(week_num) or str(now_utc.isoweekday()) != str(week_day)):
                            return False
                        if now_utc.hour != post_time_hour or now_utc.minute != post_time_minute:
                            return False
                # Если не minutely/hourly/daily/weekly/monthly — старая логика времени
            else:
                # Если автоповтор не включён — старая логика: публикация только в указанное время
                post_time_str = campaign.get("post_time", "12:00")
                post_time_parts = post_time_str.split(":")
                post_time_hour = int(post_time_parts[0])
                post_time_minute = int(post_time_parts[1])
                if now_utc.hour != post_time_hour or now_utc.minute != post_time_minute:
                    return False

            # Проверка дополнительных условий публикации
            conditions = campaign.get("conditions", [])
            if conditions:
                should_publish = False
                
                for condition in conditions:
                    condition_type = condition.get("type")
                    
                    if condition_type == "time-range":
                        # Проверка временного диапазона
                        time_start = datetime.strptime(condition["timeStart"], "%H:%M").time()
                        time_end = datetime.strptime(condition["timeEnd"], "%H:%M").time()
                        current_time = now_utc.time()
                        
                        if time_start <= current_time <= time_end:
                            should_publish = True
                            break
                            
                    elif condition_type == "weekdays":
                        # Проверка дней недели
                        weekdays = condition.get("weekdays", [])
                        if str(now_utc.isoweekday()) in map(str, weekdays):
                            should_publish = True
                            break
                            
                    elif condition_type == "month-days":
                        # Проверка дней месяца
                        days = condition.get("days", [])
                        current_month = condition.get("month")
                        
                        if (str(now_utc.day) in map(str, days) and 
                            (not current_month or now_utc.month == int(current_month))):
                            should_publish = True
                            break
                            
                if not should_publish:
                    logger.debug(f"Кампания {campaign.get('id')} не соответствует дополнительным условиям")
                    return False

            # Обновляем время последнего запуска
            self.next_run_times[campaign.get('id')] = now_utc
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке времени запуска кампании: {e}")
            return False
    
    async def _process_campaign(self, campaign: Dict):
        """Обрабатывает запуск кампании"""
        campaign_id = campaign.get("id")
        campaign_name = campaign.get("name", "Без названия")
        
        logger.info(f"🚀 Начало обработки кампании {campaign_id} ({campaign_name}) в UTC {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            chats = campaign.get("chats", [])
            if not chats:
                logger.warning(f"⚠️ Кампания {campaign_id} не имеет чатов для публикации")
                return
            
            message_text = campaign.get("message_text", "")
            if not message_text:
                logger.warning(f"⚠️ Кампания {campaign_id} имеет пустой текст")
                return
            
            # Получаем настройки публикации с логированием
            disable_preview = bool(campaign.get("disable_preview", False))
            disable_notification = bool(campaign.get("disable_notification", False))
            protect_content = bool(campaign.get("protect_content", False))
            pin_message = bool(campaign.get("pin_message", False))
            
            # Детальное логирование параметров для отладки
            logger.info(f"📋 Настройки публикации для кампании {campaign_id}:")
            logger.info(f"   🔗 Отключить предпросмотр ссылок: {disable_preview}")
            logger.info(f"   🔕 Тихая отправка: {disable_notification}")
            logger.info(f"   🛡️ Защищённый контент: {protect_content}")
            logger.info(f"   📌 Закрепить сообщение: {pin_message}")
            
            buttons = campaign.get("buttons", [])
            media_files = campaign.get("media_files", [])
            has_media = len(media_files) > 0
            
            logger.debug(f"Кампания {campaign_id}: чатов={len(chats)}, кнопок={len(buttons)}, медиа={len(media_files)}")
            
            # Проверяем наличие кнопок
            buttons = None
            if campaign.get("buttons"):
                try:
                    if isinstance(campaign["buttons"], list):
                        buttons = campaign["buttons"]
                    else:
                        buttons = json.loads(campaign["buttons"])
                
                    # Проверка валидности кнопок
                    if not isinstance(buttons, list):
                        logger.warning(f"⚠️ Некорректный формат кнопок: {buttons}")
                        buttons = None
                except Exception as e:
                    logger.error(f"❌ Ошибка при обработке кнопок: {e}")
                    buttons = None
            
            # Логируем информацию о кнопках для отладки
            logger.debug(f"Кнопки для кампании {campaign_id}: {buttons}")

            # Отправка сообщений в чаты с учетом всех параметров
            for chat in chats:
                chat_id = chat.get("chat_id")
                thread_id = chat.get("thread_id")
                
                logger.info(f"📤 Публикация в чат: {chat_id}, thread_id: {thread_id}")
                
                if not chat.get("is_active", True):
                    logger.debug(f"Пропуск неактивного чата: {chat_id}")
                    continue
                
                try:
                    message_sent = None
                    
                    if has_media:
                        # Подготавливаем медиа файлы
                        media = []
                        for file_info in media_files:
                            file_path = os.path.join(self.config.UPLOADS_DIR, file_info.get("filename"))
                            if not os.path.exists(file_path):
                                logger.warning(f"⚠️ Файл не найден: {file_path}")
                                continue
                                
                            media.append({
                                "path": file_path,
                                "type": file_info.get("type", ""),
                                "caption": message_text if len(media) == 0 else None
                            })
                        
                        # Отправляем медиа группу с параметрами
                        logger.info(f"📸 Отправка медиа-группы в чат {chat_id} с параметрами: disable_notification={disable_notification}, protect_content={protect_content}")
                        
                        messages = await self.bot.send_media_group_with_buttons(
                            chat_id=chat_id,
                            thread_id=thread_id,
                            media=media,
                            buttons=buttons,
                            disable_notification=disable_notification,
                            protect_content=protect_content
                        )
                        
                        message_sent = messages[-1] if messages else None
                        
                    else:
                        # Отправляем текстовое сообщение с кнопками и всеми параметрами
                        logger.info(f"💬 Отправка текстового сообщения в чат {chat_id} с параметрами:")
                        logger.info(f"    disable_preview={disable_preview}, disable_notification={disable_notification}")
                        logger.info(f"    protect_content={protect_content}")
                        
                        message_sent = await self.bot.send_message(
                            chat_id=chat_id,
                            thread_id=thread_id,
                            text=message_text,
                            buttons=buttons,
                            disable_preview=disable_preview,
                            disable_notification=disable_notification,
                            protect_content=protect_content
                        )
                    
                    # Закрепляем сообщение, если нужно
                    if message_sent and pin_message:
                        try:
                            logger.info(f"📌 Попытка закрепить сообщение {message_sent.message_id} в чате {chat_id}")
                            
                            await self.bot.bot.pin_chat_message(
                                chat_id=chat_id,
                                message_id=message_sent.message_id,
                                disable_notification=disable_notification
                            )
                            logger.info(f"✅ Сообщение {message_sent.message_id} успешно закреплено в чате {chat_id}")
                            
                        except TelegramAPIError as e:
                            logger.error(f"❌ Ошибка Telegram API при закреплении сообщения: {e}")
                            logger.error(f"   Код ошибки: {e.error_code if hasattr(e, 'error_code') else 'неизвестен'}")
                            logger.error(f"   Описание: {e.message if hasattr(e, 'message') else str(e)}")
                        except Exception as e:
                            logger.error(f"❌ Неожиданная ошибка при закреплении сообщения: {e}")
                
                except TelegramAPIError as e:
                    logger.error(f"❌ Ошибка Telegram API при публикации в чат {chat_id}: {e}")
                    logger.error(f"   Код ошибки: {e.error_code if hasattr(e, 'error_code') else 'неизвестен'}")
                    logger.error(f"   Описание: {e.message if hasattr(e, 'message') else str(e)}")
                    continue
                except Exception as e:
                    logger.error(f"❌ Неожиданная ошибка при публикации в чат {chat_id}: {e}")
                    continue

                # Обновляем статистику чата
                chat["last_posted"] = datetime.now().isoformat()
                chat["post_count"] = chat.get("post_count", 0) + 1
            
            # Обновляем статистику кампании
            campaign["last_run"] = datetime.now(timezone.utc).isoformat()
            campaign["run_count"] = campaign.get("run_count", 0) + 1
            
            await self.save_campaigns()
            
            logger.info(f"🎉 Кампания {campaign_id} ({campaign_name}) успешно выполнена в UTC {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке кампании {campaign_id}: {e}")
    
    async def _prepare_media_group(self, media_files, caption=None):
        """Подготавливает группу медиа файлов для отправки"""
        logger.debug(f"Подготовка медиа-группы из {len(media_files)} файлов")
        
        media_group = []
        
        for i, media_file in enumerate(media_files):
            file_path = os.path.join(self.config.UPLOADS_DIR, media_file.get("filename"))
            is_first = (i == 0)
            
            # Проверяем существование файла
            if not os.path.exists(file_path):
                logger.warning(f"⚠️ Файл не найден: {file_path}")
                continue
            
            # Определяем тип медиа
            media_type = media_file.get("type", "")
            
            try:
                if media_type.startswith("image/"):
                    # Для первого изображения добавляем описание
                    media = InputMediaPhoto(
                        media=InputFile(file_path),
                        caption=caption if is_first else None
                    )
                elif media_type.startswith("video/"):
                    media = InputMediaVideo(
                        media=InputFile(file_path),
                        caption=caption if is_first else None
                    )
                else:
                    logger.warning(f"⚠️ Неподдерживаемый тип файла: {media_type}")
                    continue
                
                media_group.append(media)
                logger.debug(f"Добавлен файл в медиа-группу: {file_path}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка при подготовке медиа файла {file_path}: {e}")
                continue
        
        logger.info(f"✅ Медиа-группа подготовлена: {len(media_group)} файлов")
        return media_group
    
    def add_campaign(self, campaign_data: Dict) -> str:
        """Добавляет новую кампанию (синхронная версия)"""
        # Генерируем уникальный ID для кампании
        campaign_id = str(uuid.uuid4())
        logger.debug(f"Добавление новой кампании с ID: {campaign_id}")
        
        # Добавляем служебные поля с явным указанием UTC
        campaign_data["id"] = campaign_id
        campaign_data["created_at"] = datetime.now().isoformat()
        campaign_data["updated_at"] = datetime.now().isoformat()
        # Убедимся, что у нас всегда есть UTC метка времени
        if "created_utc" not in campaign_data:
            campaign_data["created_utc"] = datetime.now(timezone.utc).isoformat()
        
        # Добавляем кампанию в память
        self.campaigns[campaign_id] = campaign_data
        
        # Сохраняем изменения в JSON (синхронно)
        self._save_campaigns_sync()
        
        logger.info(f"✅ Добавлена новая кампания: {campaign_id} - {campaign_data.get('name', 'Без названия')}")
        
        return campaign_id
    
    def update_campaign(self, campaign_id: str, campaign_data: Dict) -> bool:
        """Обновляет существующую кампанию (синхронная версия)"""
        logger.debug(f"Обновление кампании: {campaign_id}")
        
        if campaign_id not in self.campaigns:
            logger.error(f"❌ Кампания не найдена: {campaign_id}")
            return False
        
        # Обновляем поля кампании
        campaign_data["id"] = campaign_id  # Сохраняем исходный ID
        campaign_data["updated_at"] = datetime.now().isoformat()
        
        # Обновляем кампанию в памяти
        self.campaigns[campaign_id] = campaign_data
        
        # Сохраняем изменения в JSON
        self._save_campaigns_sync()
        
        logger.info(f"✅ Обновлена кампания: {campaign_id}")
        
        return True
    
    def delete_campaign(self, campaign_id: str) -> bool:
        """Удаляет кампанию (синхронная версия)"""
        logger.debug(f"Удаление кампании: {campaign_id}")
        
        if campaign_id not in self.campaigns:
            logger.error(f"❌ Кампания не найдена: {campaign_id}")
            return False
        
        # Удаляем кампанию из памяти
        campaign_name = self.campaigns[campaign_id].get('name', 'Без названия')
        del self.campaigns[campaign_id]
        
        # Сохраняем изменения в JSON
        self._save_campaigns_sync()
        
        logger.info(f"✅ Удалена кампания: {campaign_id} - {campaign_name}")
        
        return True
    
    def toggle_campaign_status(self, campaign_id: str) -> Optional[str]:
        """Изменяет статус кампании (синхронная версия)"""
        logger.debug(f"Изменение статуса кампании: {campaign_id}")
        
        if campaign_id not in self.campaigns:
            logger.error(f"❌ Кампания не найдена: {campaign_id}")
            return None
        
        campaign = self.campaigns[campaign_id]
        
        # Переключаем статус
        current_status = campaign.get("status", "draft")
        new_status = "paused" if current_status == "active" else "active"
        
        # Обновляем статус
        campaign["status"] = new_status
        campaign["updated_at"] = datetime.now().isoformat()
        
        # Сохраняем изменения в JSON
        self._save_campaigns_sync()
        
        logger.info(f"✅ Изменен статус кампании {campaign_id}: {current_status} → {new_status}")
        
        return new_status
    
    def _save_campaigns_sync(self):
        """Синхронное сохранение кампаний в JSON файл"""
        try:
            campaigns_list = list(self.campaigns.values())
            with open(self.config.CAMPAIGNS_FILE, 'w', encoding='utf-8') as f:
                json.dump({"campaigns": campaigns_list}, f, ensure_ascii=False, indent=2)
            logger.debug(f"Синхронно сохранено {len(campaigns_list)} кампаний")
        except Exception as e:
            logger.error(f"❌ Ошибка при синхронном сохранении кампаний: {e}")
