@echo off
call "%~dp0sub_run_script.bat" step2_p02_export_tree_json.py %*
exit /b %errorlevel%
