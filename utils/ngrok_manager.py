import subprocess
import threading
import re
import time
import os
from datetime import datetime
from loguru import logger

class NgrokManager:
    """Менеджер для управления Ngrok туннелями"""
    
    def __init__(self, config):
        """Инициализирует менеджер Ngrok с заданной конфигурацией"""
        self.config = config
        self.ngrok_process = None
        self.current_url = None
        self.restart_timer = None
        self.is_running = False
        # Добавляем переменные для отслеживания времени обновления
        self.next_restart_time = None
    
    def start(self):
        """Запускает Ngrok и начинает периодическое обновление"""
        if not self.config.NGROK_ENABLED:
            logger.info("Ngrok отключен в настройках")
            return False
        
        if not os.path.exists(self.config.NGROK_PATH):
            logger.error(f"Ngrok не найден: {self.config.NGROK_PATH}")
            return False
        
        logger.info("Запуск Ngrok менеджера")
        self.is_running = True
        self._restart_ngrok()
        return True
    
    def stop(self):
        """Останавливает Ngrok и отменяет все запланированные перезапуски"""
        logger.info("Остановка Ngrok менеджера")
        self.is_running = False
        
        # Отменяем запланированный перезапуск
        if self.restart_timer:
            self.restart_timer.cancel()
            self.restart_timer = None
        
        # Завершаем текущий процесс Ngrok
        if self.ngrok_process:
            try:
                logger.debug("Завершение процесса Ngrok")
                self.ngrok_process.terminate()
                self.ngrok_process.wait(timeout=10)
            except Exception as e:
                logger.error(f"Ошибка при завершении Ngrok: {e}")
                try:
                    self.ngrok_process.kill()
                except:
                    pass
            self.ngrok_process = None
        
        self.current_url = None
        logger.info("Ngrok менеджер остановлен")
    
    def get_public_url(self):
        """Возвращает текущий публичный URL Ngrok"""
        if not self.is_running or not self.current_url:
            return None
        return self.current_url
    
    def _restart_ngrok(self):
        """Перезапускает Ngrok и планирует следующий перезапуск"""
        if not self.is_running:
            return
        
        logger.info("Перезапуск Ngrok")
        
        # Останавливаем текущий процесс
        if self.ngrok_process:
            try:
                self.ngrok_process.terminate()
                self.ngrok_process.wait(timeout=10)
            except Exception as e:
                logger.error(f"Ошибка при завершении процесса Ngrok: {e}")
                try:
                    self.ngrok_process.kill()
                except:
                    pass
        
        # Запускаем новый процесс
        try:
            # Если есть authtoken, проверяем авторизацию Ngrok
            if self.config.NGROK_AUTHTOKEN:
                try:
                    logger.debug("Проверка авторизации Ngrok")
                    auth_process = subprocess.run(
                        [self.config.NGROK_PATH, "config", "check"],
                        capture_output=True,
                        text=True
                    )
                    
                    # Добавляем authtoken, если не авторизован
                    if "authtoken" not in auth_process.stdout.lower():
                        logger.debug("Ngrok не авторизован, выполняем авторизацию")
                        auth_result = subprocess.run(
                            [self.config.NGROK_PATH, "config", "add-authtoken", self.config.NGROK_AUTHTOKEN],
                            capture_output=True,
                            text=True
                        )
                        if auth_result.returncode == 0:
                            logger.info("Ngrok успешно авторизован")
                        else:
                            logger.error(f"Ошибка авторизации Ngrok: {auth_result.stderr}")
                except Exception as e:
                    logger.error(f"Ошибка при проверке авторизации Ngrok: {e}")
            
            # Используем порт из конфигурации
            cmd = [self.config.NGROK_PATH, "http", str(self.config.WEB_PORT)]
            
            logger.debug(f"Запуск Ngrok: {' '.join(cmd)}")
            self.ngrok_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Даем время на запуск
            time.sleep(3)  # Увеличиваем время ожидания для надежности
            
            # Получаем URL
            self._get_and_save_url()
            
            # Планируем следующий перезапуск
            interval_seconds = self.config.NGROK_RESTART_INTERVAL * 60 * 60
            logger.info(f"Следующий перезапуск Ngrok через {self.config.NGROK_RESTART_INTERVAL} часов")
            self.restart_timer = threading.Timer(interval_seconds, self._restart_ngrok)
            self.restart_timer.daemon = True
            self.restart_timer.start()
            
            # Обновляем время следующего перезапуска
            self.next_restart_time = datetime.now().timestamp() + interval_seconds
            
        except Exception as e:
            logger.error(f"Не удалось запустить Ngrok: {e}")
            self.is_running = False
    
    def _get_and_save_url(self):
        """Получает URL из Ngrok API и сохраняет его"""
        try:
            # Пробуем получить URL через локальный API
            curl_output = subprocess.check_output(
                ["curl", "-s", "http://localhost:4040/api/tunnels"],
                text=True
            )
            url_match = re.search(r'"public_url":"(https://[^"]+)"', curl_output)
            
            if url_match:
                self.current_url = url_match.group(1)
                logger.info(f"Получен новый Ngrok URL: {self.current_url}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка при получении Ngrok URL через локальный API: {e}")
            
            # Если локальный API не сработал и есть API ключ, пробуем через Ngrok API
            if self.config.NGROK_API_KEY:
                try:
                    # Используем правильный API ключ для API вызовов
                    api_output = subprocess.check_output(
                        ["curl", "-s", "-H", f"Authorization: Bearer {self.config.NGROK_API_KEY}", 
                         "https://api.ngrok.com/tunnels"],
                        text=True
                    )
                    
                    url_match = re.search(r'"public_url":"(https://[^"]+)"', api_output)
                    if url_match:
                        self.current_url = url_match.group(1)
                        logger.info(f"Получен новый Ngrok URL через API: {self.current_url}")
                        return True
                except Exception as api_error:
                    logger.error(f"Ошибка при получении Ngrok URL через API: {api_error}")
        
        logger.warning("Не удалось получить Ngrok URL")
        self.current_url = None
        return False
    
    def get_next_restart_info(self):
        """Возвращает информацию о следующем запланированном рестарте в UTC"""
        if not self.next_restart_time:
            return None
              # Конвертируем timestamp в datetime объект в UTC
        import datetime as dt
        next_restart_utc = dt.datetime.fromtimestamp(self.next_restart_time, tz=dt.timezone.utc)
        
        # Форматируем дату и время
        formatted_time = next_restart_utc.strftime('%Y-%m-%d %H:%M:%S UTC')
        seconds_left = int(self.next_restart_time - datetime.now().timestamp())
        hours_left = seconds_left // 3600
        minutes_left = (seconds_left % 3600) // 60
        
        return {
            "next_restart_utc": formatted_time,
            "next_restart_timestamp": self.next_restart_time,
            "hours_left": hours_left,
            "minutes_left": minutes_left,
            "seconds_left": seconds_left
        }
