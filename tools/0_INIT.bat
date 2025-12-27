@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem =========================================================
rem 設定（ここだけ編集すればOK）
rem =========================================================

rem 1つ上のディレクトリを対象にする（このbatの場所 기준）
set "ROOT_REL=.."

rem 削除したい「ディレクトリ名」（完全一致）
set "DIR_NAMES=build __pycache__ .pytest_cache .mypy_cache dist out"

rem 削除したい「ファイルパターン」
set "FILE_PATTERNS=*.log *.tmp *.bak *.pyc *.pdb"

rem 1=削除せず表示のみ（ドライラン） / 0=実際に削除
set "DRY_RUN=0"

rem =========================================================
rem メイン
rem =========================================================

for %%I in ("%~dp0%ROOT_REL%") do set "ROOT=%%~fI"

echo =========================================================
echo [INFO] Target ROOT : "%ROOT%"
echo [INFO] DRY_RUN     : %DRY_RUN%
echo =========================================================

if not exist "%ROOT%\" (
  echo [ERR ] ROOT not found: "%ROOT%"
  goto :END
)

set /a CNT_DIR=0, CNT_FILE=0, CNT_DIR_FAIL=0, CNT_FILE_FAIL=0

echo.
echo -------------------------------
echo [STEP] Delete directories
echo -------------------------------
for %%N in (%DIR_NAMES%) do (
  echo.
  echo [DIR ] name="%%N"
  for /f "delims=" %%D in ('
    dir /ad /b /s "%ROOT%\*" 2^>nul ^| findstr /i /e /c:"\%%N" ^| sort /r
  ') do (
    call :DEL_DIR "%%D"
  )
)

echo.
echo -------------------------------
echo [STEP] Delete files
echo -------------------------------
for %%P in (%FILE_PATTERNS%) do (
  echo.
  echo [FILE] pattern="%%P"
  for /r "%ROOT%" %%F in (%%P) do (
    call :DEL_FILE "%%F"
  )
)

echo.
echo =========================================================
echo [DONE] Deleted directories : !CNT_DIR! (fail !CNT_DIR_FAIL!)
echo [DONE] Deleted files       : !CNT_FILE! (fail !CNT_FILE_FAIL!)
echo =========================================================

:END
echo.
pause
exit /b 0


rem =========================================================
rem Functions
rem =========================================================

:DEL_DIR
set "TARGET=%~1"
if not exist "%TARGET%\" exit /b 0

echo [DEL][DIR ] "%TARGET%"
if "%DRY_RUN%"=="1" (
  set /a CNT_DIR+=1
  exit /b 0
)

rmdir /s /q "%TARGET%" >nul 2>&1
if exist "%TARGET%\" (
  echo [NG ][DIR ] "%TARGET%"
  set /a CNT_DIR_FAIL+=1
) else (
  echo [OK ][DIR ] "%TARGET%"
  set /a CNT_DIR+=1
)
exit /b 0


:DEL_FILE
set "TARGET=%~1"
if not exist "%TARGET%" exit /b 0

echo [DEL][FILE] "%TARGET%"
if "%DRY_RUN%"=="1" (
  set /a CNT_FILE+=1
  exit /b 0
)

del /f /q "%TARGET%" >nul 2>&1
if exist "%TARGET%" (
  echo [NG ][FILE] "%TARGET%"
  set /a CNT_FILE_FAIL+=1
) else (
  echo [OK ][FILE] "%TARGET%"
  set /a CNT_FILE+=1
)
exit /b 0
