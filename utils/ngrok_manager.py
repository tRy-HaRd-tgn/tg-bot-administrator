import subprocess
import threading
import re
import time
import os
import json
import shutil
from datetime import datetime, timezone
from loguru import logger

# Добавляем импорт requests для HTTP запросов
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("Библиотека requests не установлена. Будет использован curl, если он доступен.")

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
        
        # Проверка наличия curl в системе
        self.curl_available = self._check_curl_available()
        logger.debug(f"curl доступен: {self.curl_available}")
        
        # Проверка доступных инструментов для HTTP запросов
        if not self.curl_available and not REQUESTS_AVAILABLE:
            logger.warning("Ни curl, ни requests не доступны. Это может вызвать проблемы при получении Ngrok URL.")
    
    def _check_curl_available(self):
        """Проверяет доступность curl в системе"""
        return shutil.which("curl") is not None
    
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
        """Возвращает текущий публичный URL Ngrok с проверкой актуальности"""
        if not self.is_running:
            return None
        
        # Проверяем, работает ли текущий URL
        if self.current_url:
            # Попытка проверки через API, чтобы убедиться что туннель все еще активен
            try:
                is_valid = False
                
                # Пытаемся проверить URL с использованием доступных методов
                if REQUESTS_AVAILABLE:
                    try:
                        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
                        if response.status_code == 200 and self.current_url in response.text:
                            is_valid = True
                    except Exception as e:
                        logger.debug(f"Не удалось проверить URL через requests: {e}")
                
                # Если requests не сработал, пробуем через curl если он доступен
                if not is_valid and self.curl_available:
                    try:
                        curl_output = subprocess.check_output(
                            ["curl", "-s", "--connect-timeout", "3", "http://localhost:4040/api/tunnels"],
                            text=True
                        )
                        if self.current_url in curl_output:
                            is_valid = True
                    except Exception as e:
                        logger.debug(f"Не удалось проверить URL через curl: {e}")
                
                # Проверка прямым чтением логов Ngrok (альтернативный метод)
                if not is_valid and self.ngrok_process:
                    # Прямая проверка логов, если туннель активен (см. ниже метод _check_tunnel_from_logs)
                    is_valid = self._check_tunnel_from_logs()
                
                if is_valid:
                    return self.current_url
                else:
                    logger.warning(f"Текущий URL {self.current_url} не найден, получаем новый")
                    if self._get_and_save_url():
                        return self.current_url
            except Exception as e:
                logger.warning(f"Ошибка при проверке Ngrok URL: {e}")
                if self._get_and_save_url():
                    return self.current_url
        else:
            # Пытаемся получить URL если он еще не установлен
            if self._get_and_save_url():
                return self.current_url
        
        return self.current_url
    
    def _check_tunnel_from_logs(self):
        """Проверяет активность туннеля по логам процесса Ngrok"""
        if not self.ngrok_process:
            return False
        
        try:
            # Проверяем последний вывод Ngrok для определения статуса туннеля
            output, _ = self.ngrok_process.communicate(timeout=0.1)
            if "started tunnel" in output.lower() and "err" not in output.lower():
                return True
        except subprocess.TimeoutExpired:
            # Процесс ещё работает, это нормально
            return True
        except Exception as e:
            logger.debug(f"Ошибка при проверке логов Ngrok: {e}")
        
        return False
    
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
            time.sleep(5)  # Увеличиваем время ожидания для надежности
            
            # Делаем несколько попыток получить URL (с повторами в самом методе)
            if self._get_and_save_url():
                logger.info(f"Ngrok успешно перезапущен с URL: {self.current_url}")
            else:
                logger.error("Не удалось получить URL после перезапуска Ngrok даже с дополнительными попытками")
                # Пытаемся получить URL напрямую из логов Ngrok
                self._extract_url_from_process()
            
            # Планируем следующий перезапуск
            interval_seconds = self.config.NGROK_RESTART_INTERVAL * 60 * 60
            logger.info(f"Следующий перезапуск Ngrok через {self.config.NGROK_RESTART_INTERVAL} часов")
            self.restart_timer = threading.Timer(interval_seconds, self._restart_ngrok)
            self.restart_timer.daemon = True
            self.restart_timer.start()
            
            # Обновляем время следующего перезапуска с использованием UTC
            self.next_restart_time = datetime.now(timezone.utc).timestamp() + interval_seconds
            logger.debug(f"Установлено время следующего перезапуска: {self.next_restart_time}")
            logger.debug(f"Дата перезапуска в UTC: {datetime.fromtimestamp(self.next_restart_time, tz=timezone.utc)}")
            
        except Exception as e:
            logger.error(f"Не удалось запустить Ngrok: {e}")
            self.is_running = False
    
    def _extract_url_from_process(self):
        """Попытка извлечь URL непосредственно из вывода процесса Ngrok"""
        if not self.ngrok_process:
            logger.warning("Процесс Ngrok не запущен, невозможно извлечь URL из логов")
            return False
        
        try:
            # Читаем вывод процесса неблокирующим способом
            for _ in range(10):  # Несколько попыток с паузами
                line = self.ngrok_process.stdout.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                
                # Ищем URL в выводе
                url_match = re.search(r'(https://[^\s]+\.ngrok\.io)', line)
                if url_match:
                    self.current_url = url_match.group(1)
                    logger.info(f"Удалось извлечь Ngrok URL из логов процесса: {self.current_url}")
                    return True
            
            logger.warning("Не удалось найти URL в выводе процесса Ngrok")
            return False
        except Exception as e:
            logger.error(f"Ошибка при чтении вывода процесса Ngrok: {e}")
            return False
    
    def _get_and_save_url(self):
        """Получает URL из Ngrok API и сохраняет его с дополнительными попытками"""
        max_attempts = 4  # 1 основная + 3 дополнительных попытки
        attempt = 0
        retry_delay = 3  # секунды задержки между попытками
        
        while attempt < max_attempts:
            attempt += 1
            logger.debug(f"Попытка {attempt}/{max_attempts} получения Ngrok URL")
            
            # Сначала пробуем через requests если доступно
            if REQUESTS_AVAILABLE:
                try:
                    logger.debug(f"Попытка {attempt}/{max_attempts} получить URL через requests")
                    response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data and 'tunnels' in data and len(data['tunnels']) > 0:
                            for tunnel in data['tunnels']:
                                if 'public_url' in tunnel:
                                    self.current_url = tunnel['public_url']
                                    logger.info(f"Получен новый Ngrok URL через requests (попытка {attempt}): {self.current_url}")
                                    return True
                            
                            logger.warning(f"URL не найден в ответе API через requests (попытка {attempt})")
                        else:
                            logger.warning(f"Нет туннелей в ответе API через requests (попытка {attempt})")
                    else:
                        logger.warning(f"Ошибка API (HTTP {response.status_code}) через requests (попытка {attempt})")
                except Exception as e:
                    logger.error(f"Ошибка при получении URL через requests (попытка {attempt}): {e}")
            
            # Если requests не сработал, пробуем через curl если доступен
            if self.curl_available:
                try:
                    logger.debug(f"Попытка {attempt}/{max_attempts} получить URL через curl")
                    curl_output = subprocess.check_output(
                        ["curl", "-s", "--connect-timeout", "3", "http://localhost:4040/api/tunnels"],
                        text=True
                    )
                    url_match = re.search(r'"public_url":"(https://[^"]+)"', curl_output)
                    
                    if url_match:
                        self.current_url = url_match.group(1)
                        logger.info(f"Получен новый Ngrok URL через curl (попытка {attempt}): {self.current_url}")
                        return True
                    else:
                        logger.warning(f"URL не найден в ответе API через curl (попытка {attempt})")
                except Exception as e:
                    logger.error(f"Ошибка при получении URL через curl (попытка {attempt}): {e}")
            
            # Если локальный API не сработал и есть API ключ, пробуем через Ngrok API
            if self.config.NGROK_API_KEY:
                try:
                    logger.debug(f"Попытка {attempt}/{max_attempts} получения Ngrok URL через облачный API")
                    
                    # Пробуем через requests если доступно
                    if REQUESTS_AVAILABLE:
                        try:
                            headers = {"Authorization": f"Bearer {self.config.NGROK_API_KEY}"}
                            response = requests.get("https://api.ngrok.com/tunnels", headers=headers, timeout=10)
                            
                            if response.status_code == 200:
                                data = response.json()
                                if data and 'tunnels' in data and len(data['tunnels']) > 0:
                                    for tunnel in data['tunnels']:
                                        if 'public_url' in tunnel:
                                            self.current_url = tunnel['public_url']
                                            logger.info(f"Получен новый Ngrok URL через облачный API (попытка {attempt}): {self.current_url}")
                                            return True
                                
                                logger.warning(f"URL не найден в ответе облачного API через requests (попытка {attempt})")
                            else:
                                logger.warning(f"Ошибка облачного API (HTTP {response.status_code}) через requests (попытка {attempt})")
                        except Exception as e:
                            logger.error(f"Ошибка при получении URL через облачный API с requests (попытка {attempt}): {e}")
                    
                    # Пробуем через curl если доступен
                    if self.curl_available:
                        try:
                            api_output = subprocess.check_output(
                                ["curl", "-s", "--connect-timeout", "5", "-H", f"Authorization: Bearer {self.config.NGROK_API_KEY}", 
                                "https://api.ngrok.com/tunnels"],
                                text=True
                            )
                            
                            url_match = re.search(r'"public_url":"(https://[^"]+)"', api_output)
                            if url_match:
                                self.current_url = url_match.group(1)
                                logger.info(f"Получен новый Ngrok URL через облачный API с curl (попытка {attempt}): {self.current_url}")
                                return True
                            else:
                                logger.warning(f"URL не найден в ответе облачного API через curl (попытка {attempt})")
                        except Exception as e:
                            logger.error(f"Ошибка при получении URL через облачный API с curl (попытка {attempt}): {e}")
                    
                except Exception as api_error:
                    logger.error(f"Общая ошибка при получении Ngrok URL через облачное API (попытка {attempt}): {api_error}")
            
            # Если попытка не последняя, ждем и пробуем снова
            if attempt < max_attempts:
                logger.info(f"Ожидание {retry_delay} сек перед следующей попыткой получения Ngrok URL...")
                time.sleep(retry_delay)
                # Увеличиваем время ожидания для каждой последующей попытки
                retry_delay *= 1.5
        
        logger.warning(f"Не удалось получить Ngrok URL после {max_attempts} попыток")
        self.current_url = None
        return False
    
    def get_next_restart_info(self):
        """Возвращает информацию о следующем запланированном рестарте в UTC"""
        if not self.next_restart_time:
            logger.warning("Время следующего перезапуска не установлено")
            return None
        
        # Получаем текущее время в UTC
        current_time = datetime.now(timezone.utc).timestamp()
        logger.debug(f"Текущее время UTC: {datetime.now(timezone.utc)}")
        logger.debug(f"Время перезапуска: {datetime.fromtimestamp(self.next_restart_time, tz=timezone.utc)}")
        
        # Расчет оставшегося времени
        seconds_left = max(0, int(self.next_restart_time - current_time))
        hours_left = seconds_left // 3600
        minutes_left = (seconds_left % 3600) // 60
        seconds_remaining = seconds_left % 60
        
        logger.debug(f"Осталось времени: {hours_left}ч {minutes_left}м {seconds_remaining}с")
        
        # Форматируем время перезапуска
        next_restart_utc = datetime.fromtimestamp(self.next_restart_time, tz=timezone.utc)
        formatted_time = next_restart_utc.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Форматируем оставшееся время в зависимости от количества
        if hours_left > 0:
            formatted_left = f"{hours_left} ч. {minutes_left} мин."
        else:
            formatted_left = f"{minutes_left} мин. {seconds_remaining} сек."
        
        return {
            "next_restart_utc": formatted_time,
            "next_restart_timestamp": self.next_restart_time,
            "hours_left": hours_left,
            "minutes_left": minutes_left,
            "seconds_remaining": seconds_remaining,
            "seconds_left": seconds_left,
            "formatted_left": formatted_left
        }
