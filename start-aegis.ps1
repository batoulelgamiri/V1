[CmdletBinding()]
param(
    [string]$EnvironmentName = "aegis-pe"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$BackendDirectory = Join-Path $ProjectRoot "backend"
$FrontendDirectory = Join-Path $ProjectRoot "frontend"

function Find-Program {
    param([string[]]$Commands, [string[]]$Candidates)
    foreach ($command in $Commands) {
        $found = Get-Command $command -ErrorAction SilentlyContinue
        if ($found) { return $found.Source }
    }
    foreach ($candidate in $Candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    return $null
}

function ConvertTo-EncodedCommand {
    param([string]$Command)
    return [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($Command))
}

$Conda = Find-Program @("conda.exe", "conda") @(
    (Join-Path $env:USERPROFILE "miniconda3\Scripts\conda.exe"),
    (Join-Path $env:USERPROFILE "anaconda3\Scripts\conda.exe"),
    (Join-Path $env:LOCALAPPDATA "miniconda3\Scripts\conda.exe"),
    "C:\ProgramData\miniconda3\Scripts\conda.exe",
    "C:\ProgramData\anaconda3\Scripts\conda.exe"
)
$Npm = Find-Program @("npm.cmd", "npm") @("C:\Program Files\nodejs\npm.cmd")

if (-not $Conda -or -not $Npm) {
    throw "Conda or npm was not found. Run setup-aegis.cmd first."
}
if (-not (Test-Path -LiteralPath (Join-Path $FrontendDirectory "node_modules"))) {
    throw "Frontend dependencies are missing. Run setup-aegis.cmd first."
}

$backendCommand = @"
Set-Location -LiteralPath '$($BackendDirectory.Replace("'", "''"))'
& '$($Conda.Replace("'", "''"))' run --no-capture-output --name '$($EnvironmentName.Replace("'", "''"))' python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
"@
$frontendCommand = @"
Set-Location -LiteralPath '$($FrontendDirectory.Replace("'", "''"))'
& '$($Npm.Replace("'", "''"))' run dev
"@

Write-Host "Starting Aegis backend and dashboard..." -ForegroundColor Cyan
$backendProcess = Start-Process powershell.exe -PassThru -ArgumentList @(
    "-NoLogo", "-NoExit", "-EncodedCommand", (ConvertTo-EncodedCommand $backendCommand)
)
$frontendProcess = Start-Process powershell.exe -PassThru -ArgumentList @(
    "-NoLogo", "-NoExit", "-EncodedCommand", (ConvertTo-EncodedCommand $frontendCommand)
)

$backendReady = $false
$frontendReady = $false
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -TimeoutSec 2
        if ($health.status -eq "ok" -and $health.model_available) {
            $backendReady = $true
        }
    }
    catch { }

    try {
        $frontendResponse = Invoke-WebRequest `
            -Uri "http://127.0.0.1:5173" `
            -UseBasicParsing `
            -TimeoutSec 2
        if ($frontendResponse.StatusCode -eq 200) {
            $frontendReady = $true
        }
    }
    catch { }

    if ($backendReady -and $frontendReady) {
        break
    }
    Start-Sleep -Seconds 1
}

if (-not $backendReady) {
    throw "The backend did not become ready. Review the backend terminal (process $($backendProcess.Id))."
}
if (-not $frontendReady) {
    throw "The dashboard did not start on port 5173. Review the frontend terminal (process $($frontendProcess.Id))."
}

Start-Process "http://127.0.0.1:5173"
Write-Host "Aegis is ready at http://127.0.0.1:5173" -ForegroundColor Green
