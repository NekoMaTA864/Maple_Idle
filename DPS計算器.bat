@echo off
setlocal
title 新楓之谷 - DPS 演算計算器
cd /d "%~dp0"
set PYTHONNOUSERSITE=1

if not exist "%~dp0runtime\python\python.exe" (
    echo.
    echo =====================================================================
    echo [錯誤] 找不到內建執行環境，缺少 runtime\python\python.exe
    echo 請確認已將本資料夾完整解壓縮。
    echo =====================================================================
    echo.
    pause
    exit /b 1
)

"%~dp0runtime\python\python.exe" "%~dp0src\dps_calculator.py" -i

if errorlevel 1 (
    echo.
    echo =====================================================================
    echo [提示] DPS 計算器已關閉。
    echo =====================================================================
    echo.
    pause
)
