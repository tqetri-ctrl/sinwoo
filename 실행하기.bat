@echo off
chcp 65001 >nul
cd /d "%~dp0"

if exist "%~dp0dist\공인중개사_블로그_생성기\공인중개사_블로그_생성기.exe" (
    start "" "%~dp0dist\공인중개사_블로그_생성기\공인중개사_블로그_생성기.exe"
    exit /b
)

if exist "%~dp0공인중개사_블로그_생성기.exe" (
    start "" "%~dp0공인중개사_블로그_생성기.exe"
    exit /b
)

python app.py

