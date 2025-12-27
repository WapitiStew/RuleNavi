@echo off
call "%~dp0sub_run_script.bat" step1_p01_import_excel_to_sqlite.py %*
exit /b %errorlevel%