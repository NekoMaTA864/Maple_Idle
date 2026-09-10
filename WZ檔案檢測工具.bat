@echo off
title 新楓之谷 WZ 檔案檢測工具
set PYTHONNOUSERSITE=1
set "BASE_DIR=%~dp0"
set "PY_CMD=%BASE_DIR%runtime\python\python.exe"

if not exist "%PY_CMD%" (
    echo [錯誤] 找不到內建 Python: %PY_CMD%
    pause
    exit /b 1
)

echo ========================================================
echo   新楓之谷 WZ 檔案檢測與結構拆解工具
echo   可以直接把 .wz 檔案或包含 wz 的資料夾拖曳到本視窗
echo ========================================================
echo.

"%PY_CMD%" "%BASE_DIR%tools\wz_inspector.py" %*

if "%~1"=="" (
    rem 互動模式已由腳本內部等待 Enter
) else (
    echo.
    echo 檢測完成，詳細報表已輸出至 wz_inspect_report.txt
    pause
)
