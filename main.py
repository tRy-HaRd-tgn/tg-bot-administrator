import asyncio
import os
from datetime import datetime

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

from config import Config
from bot.telegram_bot import TelegramBot
from bot.campaign_scheduler import CampaignScheduler
from web.app import create_app
from utils.ngrok_manager import NgrokManager  # Импортируем NgrokManager

# Создание директорий если не существуют
os.makedirs("data", exist_ok=True)
os.makedirs("logs", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

logger.info("Создание директорий завершено")

# Инициализация конфигурации
config = Config()
logger.info("Конфигурация загружена")

async def main():
    logger.info("🚀 Запуск системы автопостинга")
    
    try:
        # Инициализация Telegram бота
        logger.debug("Инициализация Telegram бота")
        bot = TelegramBot(config)
        await bot.setup()
        logger.info("✅ Telegram бот инициализирован")
        
        # Инициализация планировщика
        logger.debug("Инициализация планировщика кампаний")
        scheduler = CampaignScheduler(bot, config)
        await scheduler.start()
        logger.info("✅ Планировщик кампаний запущен")
        
        # Запуск веб-сервера
        logger.debug("Запуск веб-сервера")
        app = create_app(bot, scheduler, config)
        logger.info("✅ Веб-сервер запущен")
        
        # Запускаем Ngrok если включен
        ngrok_url = None
        ngrok_manager = None
        if config.NGROK_ENABLED:
            logger.debug("Инициализация Ngrok менеджера")
            ngrok_manager = NgrokManager(config)
            if ngrok_manager.start():
                # Ждем немного, чтобы Ngrok запустился и получил URL
                await asyncio.sleep(2)
                ngrok_url = ngrok_manager.get_public_url()
                logger.info(f"✅ Ngrok запущен: {ngrok_url}")
        
        # Отправка уведомления админу о запуске (с URL Ngrok если доступен)
        logger.debug("Отправка уведомления админу о запуске")
        await bot.notify_admin_startup(config.WEB_HOST, config.WEB_PORT, ngrok_url)
        logger.info("✅ Уведомление админу отправлено")
        
        # Вечный цикл для поддержания работы бота
        logger.info("🎯 Система полностью готова к работе")
        while True:
            await asyncio.sleep(60)
            logger.debug("Heartbeat - система работает")
            
            # Проверяем, не обновился ли URL Ngrok
            if ngrok_manager and ngrok_manager.is_running:
                current_url = ngrok_manager.get_public_url()
                if current_url != ngrok_url:
                    logger.info(f"Обнаружен новый Ngrok URL: {current_url}")
                    ngrok_url = current_url                # Отправляем обновленную ссылку админам
                    for admin_id in config.ADMIN_IDS:
                        try:                            # Формируем время следующего обновления в UTC
                            from utils.time_helper import get_future_utc_time_str
                            restart_time_str = get_future_utc_time_str(hours=config.NGROK_RESTART_INTERVAL)
                            
                            await bot.bot.send_message(
                                admin_id,
                                f"🔄 <b>Ngrok ссылка обновлена!</b>\n\n"
                                f"🔗 Новая ссылка: {ngrok_url}\n"
                                f"⏱️ Ссылка обновится в <b>{restart_time_str}</b>"
                            )
                        except Exception as e:
                            logger.error(f"Ошибка при отправке обновленной ссылки админу {admin_id}: {e}")
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в main: {e}")
        raise
    except (KeyboardInterrupt, SystemExit):
        # Остановка всех задач при выключении
        logger.info("🛑 Получен сигнал остановки системы...")
        
        if ngrok_manager:
            logger.debug("Остановка Ngrok")
            ngrok_manager.stop()
            
        await scheduler.stop()
        await bot.stop()
        logger.info("✅ Система остановлена")

if __name__ == "__main__":
    # Создание цикла событий и запуск основной функции
    try:
        logger.info("🌟 Запуск приложения TG AutoPosting")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Система остановлена пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
    finally:
        logger.info("👋 Завершение работы приложения")
