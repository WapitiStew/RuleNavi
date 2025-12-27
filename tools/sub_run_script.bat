@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0\.."
set "ROOT=%cd%"
set "SCRIPTS=%ROOT%\scripts"
set "SRC=%ROOT%\src"

rem Let scripts import modules under src
set "PYTHONPATH=%SRC%;%PYTHONPATH%"

if "%~1"=="" (
  echo [ERR] script name is required.
  echo Usage:
  echo   %~nx0 step2_p05_make_site_stub.py
  echo   %~nx0 step2_p01_dump_category_tree.py --out out.txt --log-level DEBUG
  echo.
  pause
  exit /b 1
)

set "SCRIPT=%~1"
shift

set "FULL=%SCRIPTS%\%SCRIPT%"
if not exist "%FULL%" (
  echo [ERR] not found: "%FULL%"
  echo.
  pause
  exit /b 1
)

for %%F in ("%FULL%") do set "FULL_F=%%~fF"

rem ------------------------------------------------------------
rem Build ARGS from remaining %1.. (do NOT use %* because SHIFT does not affect it)
rem Also drop duplicated script tokens if they appear in args.
rem ------------------------------------------------------------
set "ARGS="

:BUILD_ARGS
if "%~1"=="" goto AFTER_BUILD

set "ARG=%~1"
set "ARG_NX=%~nx1"
for %%A in ("%~1") do set "ARG_F=%%~fA"

rem Drop duplicates (script name / basename / full path)
if /i "!ARG!"=="%SCRIPT%"  (shift & goto BUILD_ARGS)
if /i "!ARG_NX!"=="%SCRIPT%" (shift & goto BUILD_ARGS)
if /i "!ARG_F!"=="!FULL_F!"  (shift & goto BUILD_ARGS)

rem Keep the arg
set "ARGS=!ARGS! "%~1""
shift
goto BUILD_ARGS

:AFTER_BUILD

echo ----------------------------------------
echo [RUN] %SCRIPT%!ARGS!
echo ----------------------------------------

py "%FULL%"!ARGS!
set "EC=%errorlevel%"

echo [EXIT] %EC%
pause
exit /b %EC%
