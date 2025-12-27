@echo off
call "%~dp0sub_run_script.bat" step1_p02_check_db.py %*
exit /b %errorlevel%