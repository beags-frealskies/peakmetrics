@echo off
title PeakMetrics
cd /d "%~dp0"

set "PEAK_PYTHON=.venv\Scripts\python.exe"

if not exist "%PEAK_PYTHON%" (
    set "PEAK_PYTHON=python"
)

"%PEAK_PYTHON%" launch_peakmetrics.py

if errorlevel 1 (
    echo.
    echo PeakMetrics did not finish successfully.
    echo Review the message above.
    echo.
    pause
)