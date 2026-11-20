param([switch]$Debug)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual environment not found; running setup first..."
    & (Join-Path $PSScriptRoot "setup.ps1")
}

if ($Debug) { $env:FLASK_DEBUG = "1" }

& $venvPython -m flask --app app init-db
if ($LASTEXITCODE -ne 0) { throw "Database setup failed." }

& $venvPython -m flask --app app run
exit $LASTEXITCODE
