"""
Утилиты для работы с временем
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

def get_utc_time():
    """Возвращает текущее время в UTC"""
    return datetime.now(timezone.utc)

def get_utc_time_str(format_str: str = '%Y-%m-%d %H:%M:%S UTC') -> str:
    """Возвращает строку с текущим временем в UTC"""
    return get_utc_time().strftime(format_str)

def format_utc_time(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S UTC') -> str:
    """Форматирует datetime объект в UTC строку"""
    if dt.tzinfo is None:
        # Если время не содержит информации о часовом поясе, считаем что это UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime(format_str)

def get_future_utc_time(hours: int = 0, minutes: int = 0, seconds: int = 0) -> datetime:
    """Возвращает время в будущем в UTC"""
    return get_utc_time() + timedelta(hours=hours, minutes=minutes, seconds=seconds)

def get_future_utc_time_str(hours: int = 0, minutes: int = 0, seconds: int = 0, 
                          format_str: str = '%Y-%m-%d %H:%M:%S UTC') -> str:
    """Возвращает строку с временем в будущем в UTC"""
    future_time = get_future_utc_time(hours, minutes, seconds)
    return format_utc_time(future_time, format_str)

def get_time_left_info(future_timestamp: float) -> Dict[str, Any]:
    """Возвращает информацию об оставшемся времени до указанного timestamp"""
    now = datetime.now(timezone.utc).timestamp()
    seconds_left = max(0, int(future_timestamp - now))
    
    hours_left = seconds_left // 3600
    minutes_left = (seconds_left % 3600) // 60
    seconds_remaining = seconds_left % 60
    
    return {
        "hours": hours_left,
        "minutes": minutes_left,
        "seconds": seconds_remaining,
        "total_seconds": seconds_left,
        "formatted": f"{hours_left} ч. {minutes_left} мин." if hours_left > 0 else f"{minutes_left} мин. {seconds_remaining} сек."
    }