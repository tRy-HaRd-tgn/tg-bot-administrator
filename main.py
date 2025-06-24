import asyncio
import os
from datetime import datetime
from typing import Optional

# Настройка логирования с loguru
from loguru import logger
import sys

# Настройка loguru
logger.remove()  # Удаляем стандартный обработчик
logger.add(
    sys.stderr,
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True
)
logger.add(
    "logs/bot_{time:YYYY-MM-DD}.log",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    rotation="1 day",
    retention="30 days",
    compression="zip"
)

# Проверка наличия необходимых библиотек
try:
    import requests
    logger.info("Библиотека requests найдена")
except ImportError:
    logger.warning("Библиотека requests не установлена. Рекомендуется установить её командой: pip install requests")

from config import Config
from bot.telegram_bot import TelegramBot
from bot.campaign_scheduler import CampaignScheduler
from web.app import create_app
from utils.ngrok_manager import NgrokManager  # Импортируем NgrokManager
from utils.time_helper import get_future_utc_time_str  # Вынес импорт наверх

# Создание директорий если не существуют
os.makedirs("data", exist_ok=True)
os.makedirs("logs", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

logger.info("Создание директорий завершено")

# Инициализация конфигурации
config = Config()
logger.info("Конфигурация загружена")

def format_ngrok_message(ngrok_url: str, restart_time_str: str) -> str:
    return (
        f"🔄 <b>Ngrok ссылка обновлена!</b>\n\n"
        f"🔗 Новая ссылка: {ngrok_url}\n"
        f"⏱️ Ссылка обновится в <b>{restart_time_str}</b>"
    )

async def notify_admins(bot: TelegramBot, admin_ids: list, ngrok_url: Optional[str], config: Config):
    """Уведомить админов о запуске или смене ссылки."""
    restart_time_str = get_future_utc_time_str(hours=config.NGROK_RESTART_INTERVAL)
    for admin_id in admin_ids:
        try:
            await bot.bot.send_message(
                admin_id,
                format_ngrok_message(ngrok_url, restart_time_str)
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления админу {admin_id}: {e}")

async def graceful_shutdown(bot: TelegramBot, scheduler: CampaignScheduler, ngrok_manager: Optional[NgrokManager]):
    logger.info("🛑 Остановка системы...")
    if ngrok_manager and getattr(ngrok_manager, 'is_running', False):
        logger.debug("Остановка Ngrok")
        ngrok_manager.stop()
    await scheduler.stop()
    await bot.stop()
    logger.info("✅ Система остановлена")

async def main() -> None:
    logger.info("🚀 Запуск системы автопостинга")
    telegram_bot: Optional[TelegramBot] = None
    scheduler: Optional[CampaignScheduler] = None
    ngrok_manager: Optional[NgrokManager] = None
    ngrok_url: Optional[str] = None
    try:
        # Инициализация Telegram бота
        logger.debug("Инициализация Telegram бота")
        telegram_bot = TelegramBot(config)
        await telegram_bot.setup()
        logger.info("✅ Telegram бот инициализирован")
        
        # Инициализация планировщика
        logger.debug("Инициализация планировщика кампаний")
        scheduler = CampaignScheduler(telegram_bot, config)
        await scheduler.start()
        logger.info("✅ Планировщик кампаний запущен")
        
        # Запуск веб-сервера
        logger.debug("Запуск веб-сервера")
        app = create_app(telegram_bot, scheduler, config)
        logger.info("✅ Веб-сервер запущен")
        
        # Инициализация Ngrok менеджера
        logger.debug("Инициализация Ngrok менеджера")
        ngrok_manager = NgrokManager(config)
        
        # Сохраняем ссылку на NgrokManager в TelegramBot сразу
        telegram_bot.ngrok_manager = ngrok_manager
        
        if config.NGROK_ENABLED:
            if ngrok_manager.start():
                # Делаем несколько попыток получить URL с паузами
                for attempt in range(3):
                    ngrok_url = ngrok_manager.get_public_url()
                    if ngrok_url:
                        logger.info(f"✅ Ngrok запущен: {ngrok_url}")
                        # Теперь передаём ngrok_manager при уведомлении
                        logger.debug("Отправка уведомления админу о запуске")
                        await telegram_bot.notify_admin_startup(
                            host=config.WEB_HOST,
                            port=config.WEB_PORT,
                            ngrok_url=ngrok_url,
                            ngrok_manager=ngrok_manager  # Передаём NgrokManager в метод
                        )
                        logger.info("✅ Уведомление админу отправлено")
                        break
                    else:
                        logger.warning(f"Не удалось получить Ngrok URL (попытка {attempt+1}/3)")
                        await asyncio.sleep(5)
                
                if not ngrok_url:
                    logger.error("⛔ Не удалось получить Ngrok URL после нескольких попыток")
            else:
                logger.error("⛔ Не удалось запустить Ngrok")
        
        logger.info("🎯 Система полностью готова к работе")
        while True:
            await asyncio.sleep(60)
            logger.debug("Heartbeat - система работает")
            # Проверяем, не обновился ли URL Ngrok
            if ngrok_manager and getattr(ngrok_manager, 'is_running', False):
                current_url = ngrok_manager.get_public_url()
                if current_url and current_url != ngrok_url:
                    logger.info(f"Обнаружен новый Ngrok URL: {current_url}")
                    ngrok_url = current_url
                    await notify_admins(telegram_bot, config.ADMIN_IDS, ngrok_url, config)
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Получен сигнал остановки системы...")
        if telegram_bot and scheduler:
            await graceful_shutdown(telegram_bot, scheduler, ngrok_manager)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в main: {e}")
        if telegram_bot and scheduler:
            await graceful_shutdown(telegram_bot, scheduler, ngrok_manager)
        raise

if __name__ == "__main__":
    try:
        logger.info("🌟 Запуск приложения TG AutoPosting")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Система остановлена пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
    finally:
        logger.info("👋 Завершение работы приложения")
