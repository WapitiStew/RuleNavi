@echo off
setlocal EnableExtensions DisableDelayedExpansion

rem ===========================================================
rem RuleNavi Development Bootstrap
rem  - Create Python venv
rem  - Upgrade pip tools and install deps if project files exist
rem  - Install required pip packages (pandas/openpyxl/markdown)
rem  - Save logs under build\logs
rem  - On failure print log tail to console (best effort)
rem ===========================================================

set "SCRIPT_VERSION=20251227_v19_remove_sqlite_add_pip_pkgs"

rem ------------------------------------------------------------
rem Packages installed by this script (EDIT HERE)
rem  - Add packages separated by spaces, easy to extend later.
rem  - Example: set "PIP_PKGS=pandas openpyxl markdown requests rich"
rem ------------------------------------------------------------
set "PIP_PKGS=pandas openpyxl markdown"

call :detect_root || goto :end_fail
call :init_log    || goto :end_fail

call :log ===========================================================
call :log RuleNavi Development Bootstrap
call :log SCRIPT_VERSION: %SCRIPT_VERSION%
call :log Timestamp: %TS_STAMP%
call :log ===========================================================
call :log ROOT=%ROOT%
call :log LOG=%LOG%
call :log

set "EXIT_CODE=0"
set "HAS_PS=0"
set "HAS_WINGET=0"

set "VENV_DIR=%ROOT%\.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

rem ------------------------------------------------------------
rem Run from ROOT
rem ------------------------------------------------------------
pushd "%ROOT%" >nul 2>&1
if errorlevel 1 (
  call :log [FAIL] Cannot change directory to ROOT: %ROOT%
  set "EXIT_CODE=1"
  goto :end
)

call :log ------------------------------------------------------------
call :run "Check PowerShell" "where powershell"
if errorlevel 1 (
  set "HAS_PS=0"
  call :log [WARN] PowerShell not found. (log tail may be limited)
) else (
  set "HAS_PS=1"
)

call :log ------------------------------------------------------------
call :run "Check winget optional" "where winget"
if errorlevel 1 (
  set "HAS_WINGET=0"
  call :log [WARN] winget not found. auto-install limited.
) else (
  set "HAS_WINGET=1"
)

call :log ------------------------------------------------------------
call :run "Check git optional" "where git"
if errorlevel 1 (
  call :log [WARN] git not found. optional.
)

call :log ------------------------------------------------------------
call :run "Check py launcher" "where py"
if errorlevel 1 (
  call :log [FAIL] py not found. Install Python.
  if "%HAS_WINGET%"=="1" (
    call :log [HINT] winget install -e --id Python.Python.3.13
  )
  set "EXIT_CODE=1"
  goto :end
)

call :log ------------------------------------------------------------
call :run "Check Python runnable" "py -3 -V"
if errorlevel 1 (
  call :log [WARN] py -3 failed. Python 3.x may be missing.
  if "%HAS_WINGET%"=="1" (
    call :log [INFO] Trying to install Python 3.13 by winget...
    call :run "Install Python 3.13 by winget" "winget install -e --id Python.Python.3.13"
    call :run "Re-check Python runnable" "py -3 -V"
    if errorlevel 1 (
      call :log [FAIL] Python install/check failed.
      set "EXIT_CODE=1"
      goto :end
    )
  ) else (
    call :log [FAIL] winget is not available. Install Python manually.
    set "EXIT_CODE=1"
    goto :end
  )
)

call :log ------------------------------------------------------------
call :log [STEP] Create venv .venv
if exist "%VENV_PY%" (
  call :log [OK] venv already exists: %VENV_DIR%
) else (
  call :run "Create venv" "py -3 -m venv ""%VENV_DIR%"""
  if errorlevel 1 (
    call :log [FAIL] venv creation failed.
    set "EXIT_CODE=1"
    goto :end
  )
)

call :log ------------------------------------------------------------
call :run "Upgrade pip setuptools wheel" """%VENV_PY%"" -m pip install -U pip setuptools wheel"
if errorlevel 1 (
  call :log [FAIL] pip upgrade failed.
  set "EXIT_CODE=1"
  goto :end
)

call :log ------------------------------------------------------------
call :log [STEP] Install Python deps best effort
if exist "%ROOT%\pyproject.toml" (
  call :log [INFO] pyproject.toml found. Try editable install with dev extras.
  call :run "pip install editable dev" """%VENV_PY%"" -m pip install -e "".[dev]"""
  if errorlevel 1 (
    call :log [WARN] editable dev failed. Fallback to editable.
    call :run "pip install editable" """%VENV_PY%"" -m pip install -e ""."""
    if errorlevel 1 (
      call :log [FAIL] pip editable install failed.
      set "EXIT_CODE=1"
      goto :end
    )
  )
) else if exist "%ROOT%\requirements-dev.txt" (
  call :log [INFO] requirements-dev.txt found.
  call :run "pip install requirements-dev" """%VENV_PY%"" -m pip install -r ""%ROOT%\requirements-dev.txt"""
  if errorlevel 1 (
    call :log [FAIL] pip install requirements-dev.txt failed.
    set "EXIT_CODE=1"
    goto :end
  )
) else if exist "%ROOT%\requirements.txt" (
  call :log [INFO] requirements.txt found.
  call :run "pip install requirements" """%VENV_PY%"" -m pip install -r ""%ROOT%\requirements.txt"""
  if errorlevel 1 (
    call :log [FAIL] pip install requirements.txt failed.
    set "EXIT_CODE=1"
    goto :end
  )
) else (
  call :log [INFO] No pyproject or requirements found. Skip deps install.
  call :log [HINT] Add pyproject.toml or requirements files to automate deps.
)

rem ------------------------------------------------------------
rem Always ensure required packages exist (easy to extend)
rem ------------------------------------------------------------
call :log ------------------------------------------------------------
call :log [STEP] Ensure pip packages installed: %PIP_PKGS%
call :run "pip install packages" """%VENV_PY%"" -m pip install -U %PIP_PKGS%"
if errorlevel 1 (
  call :log [FAIL] pip install packages failed: %PIP_PKGS%
  set "EXIT_CODE=1"
  goto :end
)

call :log ------------------------------------------------------------
call :log [STEP] Show versions
call :run "Python version" """%VENV_PY%"" -V"
call :run "pip version" """%VENV_PY%"" -m pip -V"
call :run "pip show packages" """%VENV_PY%"" -m pip show %PIP_PKGS%"

goto :end

rem ------------------------------------------------------------
rem Functions
rem ------------------------------------------------------------

:detect_root
setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%") do set "SCRIPT_DIR=%%~fI"
set "ROOT="
if exist "%SCRIPT_DIR%\.rulenavi_root" (
  set "ROOT=%SCRIPT_DIR%"
) else if exist "%SCRIPT_DIR%\..\.rulenavi_root" (
  for %%I in ("%SCRIPT_DIR%\..") do set "ROOT=%%~fI"
) else (
  set "ROOT=%SCRIPT_DIR%"
)
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
endlocal & set "ROOT=%ROOT%" & exit /b 0

:init_log
setlocal
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss" 2^>nul') do set "TS=%%I"
if not defined TS set "TS=%RANDOM%%RANDOM%"
set "LOG_DIR=%ROOT%\build\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1
set "LOG=%LOG_DIR%\9_DEVELOPMENT_%TS%.log"
set "TS_STAMP=%TS%"
endlocal & (
  set "LOG=%LOG%"
  set "TS_STAMP=%TS_STAMP%"
) & exit /b 0

:log
setlocal DisableDelayedExpansion
set "TS=%time: =0%"
set "MSG=%*"
echo [%TS%] %MSG%
>> "%LOG%" echo [%TS%] %MSG%
endlocal & exit /b 0

:run
setlocal DisableDelayedExpansion
set "DESC=%~1"
set "CMD=%~2"
call :log [STEP] %DESC%
call :log CMD: %CMD%
set "TMP=%TEMP%\rulenavi_%RANDOM%_%RANDOM%.tmp"
cmd /d /s /c "%CMD%" > "%TMP%" 2>&1
set "EC=%errorlevel%"
type "%TMP%"
>> "%LOG%" type "%TMP%"
del "%TMP%" >nul 2>&1
call :log EXITCODE: %EC%
endlocal & exit /b %EC%

:show_log_tail
setlocal
set "N=%~1"
if not defined N set "N=200"
echo.
echo ====== LOG TAIL last %N% lines ======
if "%HAS_PS%"=="1" (
  powershell -NoProfile -Command "Get-Content -Path '%LOG%' -Tail %N%" 2>nul
) else (
  echo [WARN] PowerShell not available. Showing full log instead.
  type "%LOG%" 2>nul
)
echo ====== END LOG TAIL ======
endlocal & exit /b 0

:end
popd >nul 2>&1

call :log ============================================================
call :log [DEV] LOG FILE: %LOG%
call :log [DEV] EXIT CODE: %EXIT_CODE%
call :log ============================================================
if "%EXIT_CODE%"=="0" (
  call :log [DEV] SUCCESS.
) else (
  call :log [DEV] FAILED. Open the log file to see details.
  call :log %LOG%
  call :show_log_tail 200
)

echo.
echo [DEV] LOG FILE: %LOG%
echo [DEV] EXIT CODE: %EXIT_CODE%
echo.

pause
endlocal & exit /b %EXIT_CODE%

:end_fail
echo Failed to initialize bootstrap.
pause
exit /b 1
