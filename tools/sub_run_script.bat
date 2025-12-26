@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0\.."
set "ROOT=%cd%"
set "SRC=%ROOT%\src"
set "SCRIPTS=%ROOT%\scripts"

set "PYTHONPATH=%SRC%"

if "%~1"=="" (
  echo Usage:
  echo   sub_run_script.bat step2_p01_dump_category_tree.py
  echo   sub_run_script.bat step2_p01_dump_category_tree.py --out build\log\cat_tree.txt --log-level DEBUG
  pause
  exit /b 1
)

set "FILE=%~1"
shift

set "FULL=%SCRIPTS%\%FILE%"
if not exist "%FULL%" (
  echo [ERR] not found: "%FULL%"
  pause
  exit /b 1
)

rem ------------------------------------------------------------
rem shift 後の引数だけを組み立てる（%* を使わない）
rem ------------------------------------------------------------
set "ARGS="

:arg_loop
if "%~1"=="" goto arg_done
set "ARGS=!ARGS! "%~1""
shift
goto arg_loop

:arg_done
echo [RUN] %FILE%
py "%FULL%" !ARGS!
set "EC=%errorlevel%"
echo [EXIT] %EC%
pause
exit /b %EC%
