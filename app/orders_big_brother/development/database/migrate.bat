@echo off
color A
cls

echo ScorpionIPX Django migrate utils v2.0
@cd /d "%~dp0"
cd..
cd..

set BASE_DIR=%cd%
echo Using base dir: %BASE_DIR%

set /P VIRTUALENV_SUFIX=<development\virtualenv.path
set VIRTUALENV=%BASE_DIR%\%VIRTUALENV_SUFIX%
echo Using virtual environment: %VIRTUALENV%

set DJANGO_MANAGER=%BASE_DIR%\manage.py
echo Using Django manager: %DJANGO_MANAGER%

echo Waiting for user input...
pause

%VIRTUALENV% %DJANGO_MANAGER% makemigrations
%VIRTUALENV% %DJANGO_MANAGER% migrate

pause