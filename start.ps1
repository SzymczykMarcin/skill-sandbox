[CmdletBinding()]
param(
    [switch]$NoReload,
    [int]$Port = 8000,
    [Alias("Host")][string]$BindHost = "127.0.0.1",
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
        throw "Python interpreter not found: $Preferred"
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

    throw "Python 3 was not found. Install Python 3.11+ and run this script again."
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
        throw "Python command failed: $Python $($Args -join ' ')"
    }
}

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

$pythonCmd = Find-Python -Preferred $PythonExe
Write-Host "[1/4] Python: $pythonCmd"

$venvPath = Join-Path $RepoRoot ".venv"
if (-not $SkipVenv) {
    if (-not (Test-Path $venvPath)) {
        Write-Host "[2/4] Creating virtual environment (.venv)..."
        Invoke-Python -Python $pythonCmd -Args @("-m", "venv", ".venv")
    }

    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        throw "Virtual environment interpreter is missing: $venvPython"
    }
    $pythonCmd = $venvPython
}

Write-Host "[3/4] Installing / updating Python dependencies..."
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

Write-Host "[4/4] Starting application..."
Write-Host "Application will be available at: http://${BindHost}:$Port/kurs/sql"
$uvicornArgs = @(
    "-m", "uvicorn",
    "backend.main:app",
    "--host", $BindHost,
    "--port", "$Port"
) + $reloadArgs
Invoke-Python -Python $pythonCmd -Args $uvicornArgs
