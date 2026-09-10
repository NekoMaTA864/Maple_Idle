@echo off
setlocal
title 新楓之谷：放置遠征隊 - MapleStory Idle
cd /d "%~dp0"
set PYTHONNOUSERSITE=1

if not exist "%~dp0runtime\python\python.exe" (
    echo.
    echo =====================================================================
    echo [錯誤] 找不到內建執行環境，路徑應為 runtime\python\python.exe
    echo 請確認整個資料夾包含 runtime 資料夾都有一併複製過來，
    echo 不要只複製部分檔案。
    echo =====================================================================
    echo.
    pause
    exit /b 1
)

"%~dp0runtime\python\python.exe" "%~dp0src\pyside_main.py"

if errorlevel 1 (
    echo.
    echo =====================================================================
    echo [錯誤] 遊戲發生異常並已結束，請將上方的錯誤訊息截圖回報。
    echo =====================================================================
    echo.
    pause
)
