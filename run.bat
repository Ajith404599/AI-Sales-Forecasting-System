@echo off
REM Single command launcher for Backend + Frontend
SETLOCAL

cd /d "%~dp0"

IF EXIST ".venv\Scripts\python.exe" (
    SET "PYTHON_EXE=.venv\Scripts\python.exe"
) ELSE (
    SET "PYTHON_EXE=python"
)

"%PYTHON_EXE%" run.py %*
