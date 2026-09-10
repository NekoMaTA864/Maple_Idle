@echo off
chcp 65001 >nul
setlocal
title 新楓之谷：放置冒險記 - MapleStory Idle
cd /d "%~dp0"
set PYTHONNOUSERSITE=1

set "PY_EXE=%~dp0runtime\python\python.exe"

if not exist "%PY_EXE%" (
    where python >nul 2>&1
    if errorlevel 1 (
        echo.
        echo =====================================================================
        echo [錯誤] 找不到 Python 執行環境！
        echo 1. 請確認解壓縮時包含 runtime 資料夾 (Portable Python)
        echo 2. 或於系統中安裝 Python 3.12+ (並加入 PATH 環境變數)
        echo =====================================================================
        echo.
        pause
        exit /b 1
    ) else (
        set "PY_EXE=python"
    )
)

"%PY_EXE%" "%~dp0src\pyside_main.py"

if errorlevel 1 (
    echo.
    echo =====================================================================
    echo [異常] 遊戲發生未捕捉異常，請將上方錯誤訊息或 logs 檔案反饋回報。
    echo =====================================================================
    echo.
    pause
)

