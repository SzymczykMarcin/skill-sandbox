[CmdletBinding()]
param(
    [switch]$NoReload,
    [int]$Port = 8000,
    [string]$Host = "127.0.0.1",
    [string]$PythonExe,
    [switch]$SkipVenv
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Find-Python {
    param([string]$Preferred)

    if ($Preferred) {
        if (Get-Command $Preferred -ErrorAction SilentlyContinue) {
            return $Preferred
        }
        throw "Nie znaleziono interpretera Python: $Preferred"
    }

    $candidates = @("py -3", "python", "python3")
    foreach ($candidate in $candidates) {
        try {
            if ($candidate -eq "py -3") {
                & py -3 --version | Out-Null
                return "py -3"
            }
            else {
                & $candidate --version | Out-Null
                return $candidate
            }
        }
        catch {
            continue
        }
    }

    throw "Python 3 nie został znaleziony. Zainstaluj Python 3.11+ i uruchom skrypt ponownie."
}

function Invoke-Python {
    param(
        [Parameter(Mandatory = $true)][string]$Python,
        [Parameter(Mandatory = $true)][string[]]$Args
    )

    if ($Python -eq "py -3") {
        & py -3 @Args
    }
    else {
        & $Python @Args
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Polecenie Python zakończyło się błędem: $Python $($Args -join ' ')"
    }
}

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

$pythonCmd = Find-Python -Preferred $PythonExe
Write-Host "[1/4] Python: $pythonCmd"

$venvPath = Join-Path $RepoRoot ".venv"
if (-not $SkipVenv) {
    if (-not (Test-Path $venvPath)) {
        Write-Host "[2/4] Tworzenie środowiska wirtualnego (.venv)..."
        Invoke-Python -Python $pythonCmd -Args @("-m", "venv", ".venv")
    }

    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        throw "Brak interpretera wirtualnego środowiska: $venvPython"
    }
    $pythonCmd = $venvPython
}

Write-Host "[3/4] Instalacja / aktualizacja zależności Python..."
Invoke-Python -Python $pythonCmd -Args @("-m", "pip", "install", "--upgrade", "pip")
Invoke-Python -Python $pythonCmd -Args @(
    "-m", "pip", "install",
    "fastapi>=0.110",
    "uvicorn[standard]>=0.29",
    "pydantic>=2",
    "redis>=5"
)

if (-not $env:SQLITE_RUNTIME_DIR) {
    $env:SQLITE_RUNTIME_DIR = Join-Path $RepoRoot ".runtime/sqlite"
}

$reloadArgs = @()
if (-not $NoReload) {
    $reloadArgs += "--reload"
}

Write-Host "[4/4] Uruchamianie aplikacji..."
Write-Host "Aplikacja będzie dostępna pod adresem: http://${Host}:$Port/kurs/sql"
$uvicornArgs = @(
    "-m", "uvicorn",
    "backend.main:app",
    "--host", $Host,
    "--port", "$Port"
) + $reloadArgs
Invoke-Python -Python $pythonCmd -Args $uvicornArgs
