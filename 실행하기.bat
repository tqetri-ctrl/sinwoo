@echo off
set FAST_EXE=%~dp0dist\공인중개사_블로그_생성기_고속실행\공인중개사_블로그_생성기_고속실행.exe
set SINGLE_EXE=%~dp0공인중개사_블로그_생성기.exe

if exist "%FAST_EXE%" (
    start "" "%FAST_EXE%"
) else if exist "%SINGLE_EXE%" (
    start "" "%SINGLE_EXE%"
) else (
    python "%~dp0app.py"
)

