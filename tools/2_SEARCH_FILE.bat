@echo off
setlocal EnableExtensions

REM =========================================================
REM 1つ上のディレクトリ配下の「全ファイル名」を再帰的に列挙
REM この .bat を置いた場所 기준:
REM   %~dp0 = このbatのフォルダ（末尾\付き）
REM   %~dp0.. = 1つ上のフォルダ
REM =========================================================

set "TARGET_DIR=%~dp0.."

echo ---------------------------------------------------------
echo Target: "%TARGET_DIR%"
echo ---------------------------------------------------------
echo.

REM ---- (B) TARGET_DIR からの相対パスで列挙 ----
echo [RELATIVE PATH]
pushd "%TARGET_DIR%" >nul
for /r %%F in (*) do (
    set "P=%%F"
    setlocal EnableDelayedExpansion
    echo !P:%CD%\=!
    endlocal
)
popd >nul
echo.

pause