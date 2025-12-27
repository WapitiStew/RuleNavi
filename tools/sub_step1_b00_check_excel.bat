@echo off
call "%~dp0sub_run_script.bat" step1_p00_check_excel.py %*
exit /b %errorlevel%
