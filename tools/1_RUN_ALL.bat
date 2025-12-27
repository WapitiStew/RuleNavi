@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0\.."
set "ROOT=%cd%"
set "SCRIPTS=%ROOT%\scripts"
set "SRC=%ROOT%\src"
set "PYTHONPATH=%SRC%"

call :banner "__RUN_ALL (STEP1 + STEP2)"
call :envinfo

call :section "STEP1"
call :run "step1_p00_check_excel.py"
call :run "step1_p01_import_excel_to_sqlite.py"
call :run "step1_p02_check_db.py"

call :section "STEP2"
call :run "step2_p00_make_directory_rules.py"
call :run "step2_p01_dump_category_tree.py"
call :run "step2_p02_export_tree_json.py"
call :run "step2_p03_export_rules_index.py"
call :run "step2_p04_export_markdown_rules.py"
call :run "step2_p05_make_site_stub.py"

call :footer "DONE"
pause
exit /b 0


:banner
set "TITLE=%~1"
echo ============================================================
echo [%date% %time%] %TITLE%
echo ============================================================
exit /b 0


:envinfo
echo [ENV] ROOT      = "%ROOT%"
echo [ENV] SCRIPTS   = "%SCRIPTS%"
echo [ENV] SRC       = "%SRC%"
echo [ENV] PYTHONPATH= "%PYTHONPATH%"
echo.
exit /b 0


:section
set "NAME=%~1"
echo ------------------------------------------------------------
echo [%date% %time%] %NAME%
echo ------------------------------------------------------------
exit /b 0


:run
set "FILE=%~1"
set "FULL=%SCRIPTS%\%FILE%"

if not exist "%FULL%" (
  echo [ERR] NOT FOUND : "%FULL%"
  exit /b 1
)

echo [RUN]  %FILE%
echo [TIME] start = %date% %time%
py "%FULL%"
set "EC=%errorlevel%"
echo [TIME] end   = %date% %time%

if not "!EC!"=="0" (
  echo [ERR] FAILED : %FILE%  (exitcode=!EC!)
  exit /b !EC!
)

echo [OK ]  %FILE%
echo.
exit /b 0


:footer
set "MSG=%~1"
echo ============================================================
echo [%date% %time%] %MSG%
echo ============================================================
exit /b 0
