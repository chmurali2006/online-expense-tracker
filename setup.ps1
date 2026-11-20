$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

function Find-HostPython {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { return @{ Command = $py.Source; Prefix = @("-3") } }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) { return @{ Command = $python.Source; Prefix = @() } }

    throw "Python 3.11 or newer is required but was not found. Install it from https://www.python.org/downloads/ and make sure 'python' or 'py' is on PATH."
}

function Invoke-Checked {
    param([string]$Exe, [string[]]$Arguments)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed: $Exe $($Arguments -join ' ')" }
}

if (-not (Test-Path $venvPython)) {
    $hostPython = Find-HostPython
    $venvArgs = @($hostPython.Prefix) + @("-m", "venv", ".venv")
    Write-Host "Creating virtual environment with $($hostPython.Command)..."
    Invoke-Checked -Exe $hostPython.Command -Arguments $venvArgs
}

Write-Host "Installing requirements..."
Invoke-Checked -Exe $venvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip")
Invoke-Checked -Exe $venvPython -Arguments @("-m", "pip", "install", "-r", "requirements.txt")

Write-Host "Preparing the database..."
Invoke-Checked -Exe $venvPython -Arguments @("-m", "flask", "--app", "app", "init-db")
Invoke-Checked -Exe $venvPython -Arguments @("-m", "flask", "--app", "app", "seed")

Write-Host "Setup complete. Run .\run.ps1 to start the app."
