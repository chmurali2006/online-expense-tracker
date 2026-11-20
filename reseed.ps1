$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual environment not found; running setup first..."
    & (Join-Path $PSScriptRoot "setup.ps1")
}

& $venvPython -m flask --app app reseed-demo
exit $LASTEXITCODE
