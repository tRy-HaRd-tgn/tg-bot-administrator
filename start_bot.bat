@echo off
:: filepath: c:\Users\admin3\Downloads\автопостинг тгV2 — копия\start_bot.bat
chcp 65001 >nul
title TG AutoPosting Bot

echo ====================================
echo =       TG AutoPosting Bot         =
echo ====================================
echo.
echo [%date% %time%] Запуск системы автопостинга...
echo.

:: Устанавливаем переменную окружения для UTF-8
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8

:: Проверяем наличие Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не найден! Убедитесь, что Python установлен и добавлен в PATH.
    echo Вы можете скачать Python с сайта: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Проверяем наличие main.py
if not exist "main.py" (
    echo [ОШИБКА] Файл main.py не найден в текущей директории!
    echo Текущая директория: %cd%
    pause
    exit /b 1
)

echo [%date% %time%] Python найден, запускаем main.py...
echo.

:: Запускаем main.py с параметрами UTF-8
python -X utf8 main.py

:: Если скрипт завершился с ошибкой, не закрываем окно
if %errorlevel% neq 0 (
    echo.
    echo [%date% %time%] [ОШИБКА] Скрипт завершился с кодом: %errorlevel%
    echo.
    pause
)

exit /b %errorlevel%