@echo off
chcp 65001 >nul
setlocal
title 新楓之谷：DPS 高速演算診斷器
cd /d "%~dp0"
set PYTHONNOUSERSITE=1

set "PY_EXE=%~dp0runtime\python\python.exe"
if not exist "%PY_EXE%" (
    where python >nul 2>&1
    if errorlevel 1 (
        echo [錯誤] 找不到 Python 執行環境！
        pause
        exit /b 1
    ) else (
        set "PY_EXE=python"
    )
)

"%PY_EXE%" "%~dp0src\dps_calculator.py" -i

if errorlevel 1 (
    echo.
    echo DPS 計算器執行完畢或中斷。
    pause
)
