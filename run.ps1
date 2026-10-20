# Single command launcher for Backend + Frontend in PowerShell
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

$PythonExe = "python"
if (Test-Path "$ScriptDir\.venv\Scripts\python.exe") {
    $PythonExe = "$ScriptDir\.venv\Scripts\python.exe"
}

& $PythonExe "$ScriptDir\run.py" @args
