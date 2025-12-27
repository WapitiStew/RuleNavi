@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "RET=0"
set "FAIL=0"
set "ROOT="

rem ---- find ROOT by marker (.rulenavi_root) ----
for %%P in ("%~dp0\.." "%~dp0\..\.." "%~dp0\..\..\.." "%~dp0\..\..\..\.." "%~dp0\..\..\..\..\..") do (
  if exist "%%~fP\.rulenavi_root" set "ROOT=%%~fP"
)

echo =========================================================
echo [%date% %time%] INIT START
echo [ENV] tools="%~dp0"
echo [ENV] ROOT ="%ROOT%"
echo =========================================================

if not defined ROOT (
  echo [ERR] marker ".rulenavi_root" not found in parents.
  set "RET=2"
  goto :END
)

if not exist "%ROOT%\.rulenavi_root" (echo [ERR] missing marker & set "RET=2" & goto :END)
if not exist "%ROOT%\setting.csv"    (echo [ERR] missing setting.csv & set "RET=2" & goto :END)
if not exist "%ROOT%\src"            (echo [ERR] missing src & set "RET=2" & goto :END)
if not exist "%ROOT%\scripts"        (echo [ERR] missing scripts & set "RET=2" & goto :END)
if not exist "%ROOT%\tools"          (echo [ERR] missing tools & set "RET=2" & goto :END)

echo [OK] marker exists
echo [OK] setting.csv exists
echo [OK] src exists
echo [OK] scripts exists
echo [OK] tools exists

rem ---- subst (short path) ----
set "DRV=R:"
if exist "%DRV%\" set "DRV=S:"
if exist "%DRV%\" set "DRV=T:"
if exist "%DRV%\" set "DRV=U:"
if exist "%DRV%\" set "DRV=V:"
if exist "%DRV%\" set "DRV=W:"
if exist "%DRV%\" set "DRV=X:"
if exist "%DRV%\" set "DRV=Y:"
if exist "%DRV%\" set "DRV=Z:"
if exist "%DRV%\" set "DRV="

set "ROOTSUB=%ROOT%"
if defined DRV (
  echo ---------------------------------------------------------
  echo [UNMAP] subst %DRV% /d
  subst %DRV% /d
  echo [UNMAP] RC=!errorlevel!
  if not "!errorlevel!"=="0" (
    echo [WRN] subst /d failed. It is usually because some process is using %DRV%.
    echo [TIP ] Close Explorer/VSCode tabs opened under %DRV% and run: subst %DRV% /d
  )
)


echo ---------------------------------------------------------
echo [STEP] remove build dirs - whitelist only

rem =========================================================
rem DELETE #1: build
rem =========================================================
set "TARGET=!ROOTSUB!\build"
echo.
echo [DEL] target="!TARGET!"

if not exist "!TARGET!" (
  echo [SKIP] not found
) else (
  echo [INFO] try rename first - lock check
  set "REN=!ROOTSUB!\__del_build_!RANDOM!!RANDOM!"
  echo   move "!TARGET!" "!REN!"
  move "!TARGET!" "!REN!"
  echo [RC ] move=!errorlevel!

  if exist "!TARGET!" (
    echo [LOCK] rename failed. Someone is using this directory.
    set /a FAIL+=1
  ) else (
    set "TARGET=!REN!"
    echo [OK ] renamed -> "!TARGET!"

    attrib -R -S -H "!TARGET!\*" /S /D 2>nul
    rd /s /q "!TARGET!" 2>nul

    if exist "!TARGET!" (
      echo [WRN] rd failed. try robocopy wipe
      set "EMPTY=%TEMP%\rulenavi_empty_!RANDOM!!RANDOM!"
      md "!EMPTY!" 2>nul
      robocopy "!EMPTY!" "!TARGET!" /MIR /R:0 /W:0 /NFL /NDL /NJH /NJS /NP >nul
      rd /s /q "!EMPTY!" 2>nul
      attrib -R -S -H "!TARGET!\*" /S /D 2>nul
      rd /s /q "!TARGET!" 2>nul
    )

    if exist "!TARGET!" (
      echo [WRN] still exists. try PowerShell Remove-Item
      powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "try { Remove-Item -LiteralPath '%TARGET%' -Recurse -Force -ErrorAction Stop; 'PS:OK' } catch { 'PS:ERR ' + $_.Exception.Message; exit 1 }"
      rd /s /q "!TARGET!" 2>nul
    )

    if exist "!TARGET!" (
      echo [ERR] cannot remove "!TARGET!"
      dir /a "!TARGET!" 2>nul
      set /a FAIL+=1
    ) else (
      echo [OK ] removed build
    )
  )
)

rem =========================================================
rem DELETE #2: src\build
rem =========================================================
set "TARGET=!ROOTSUB!\src\build"
echo.
echo [DEL] target="!TARGET!"

if not exist "!TARGET!" (
  echo [SKIP] not found
) else (
  echo [INFO] try rename first - lock check
  set "REN=!ROOTSUB!\__del_src_build_!RANDOM!!RANDOM!"
  echo   move "!TARGET!" "!REN!"
  move "!TARGET!" "!REN!"
  echo [RC ] move=!errorlevel!

  if exist "!TARGET!" (
    echo [LOCK] rename failed. Someone is using this directory.
    set /a FAIL+=1
  ) else (
    set "TARGET=!REN!"
    echo [OK ] renamed -> "!TARGET!"

    attrib -R -S -H "!TARGET!\*" /S /D 2>nul
    rd /s /q "!TARGET!" 2>nul

    if exist "!TARGET!" (
      echo [WRN] rd failed. try robocopy wipe
      set "EMPTY=%TEMP%\rulenavi_empty_!RANDOM!!RANDOM!"
      md "!EMPTY!" 2>nul
      robocopy "!EMPTY!" "!TARGET!" /MIR /R:0 /W:0 /NFL /NDL /NJH /NJS /NP >nul
      rd /s /q "!EMPTY!" 2>nul
      attrib -R -S -H "!TARGET!\*" /S /D 2>nul
      rd /s /q "!TARGET!" 2>nul
    )

    if exist "!TARGET!" (
      echo [WRN] still exists. try PowerShell Remove-Item
      powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "try { Remove-Item -LiteralPath '%TARGET%' -Recurse -Force -ErrorAction Stop; 'PS:OK' } catch { 'PS:ERR ' + $_.Exception.Message; exit 1 }"
      rd /s /q "!TARGET!" 2>nul
    )

    if exist "!TARGET!" (
      echo [ERR] cannot remove "!TARGET!"
      dir /a "!TARGET!" 2>nul
      set /a FAIL+=1
    ) else (
      echo [OK ] removed src build
    )
  )
)

echo.
echo ---------------------------------------------------------
echo [CHECK] remaining build dirs
if exist "%ROOT%\build"     (echo   - EXISTS: "%ROOT%\build") else (echo   - OK    : "%ROOT%\build")
if exist "%ROOT%\src\build" (echo   - EXISTS: "%ROOT%\src\build") else (echo   - OK    : "%ROOT%\src\build")

if defined DRV (
  echo ---------------------------------------------------------
  echo [UNMAP] subst %DRV% /d
  subst %DRV% /d >nul 2>nul
)

echo =========================================================
if "!FAIL!"=="0" (
  echo [%date% %time%] INIT DONE OK
  set "RET=0"
) else (
  echo [%date% %time%] INIT DONE NG fail_count=!FAIL!
  set "RET=1"
)
echo =========================================================

:END
echo.
echo [EXIT] %RET%
pause
exit /b %RET%
