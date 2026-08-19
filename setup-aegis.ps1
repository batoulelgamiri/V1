[CmdletBinding()]
param(
    [string]$EnvironmentName = "aegis-pe",
    [switch]$SkipModel,
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Find-Executable {
    param(
        [string[]]$Commands,
        [string[]]$Candidates = @()
    )

    foreach ($command in $Commands) {
        $resolved = Get-Command $command -ErrorAction SilentlyContinue
        if ($resolved) {
            return $resolved.Source
        }
    }
    foreach ($candidate in $Candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    return $null
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory)] [string]$Executable,
        [Parameter(Mandatory)] [string[]]$Arguments,
        [Parameter(Mandatory)] [string]$FailureMessage
    )

    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FailureMessage (exit code $LASTEXITCODE)."
    }
}

function New-RandomHexSecret {
    param([int]$ByteCount = 32)

    $bytes = New-Object byte[] $ByteCount
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generator.GetBytes($bytes)
    }
    finally {
        $generator.Dispose()
    }
    return (($bytes | ForEach-Object { $_.ToString("x2") }) -join "")
}

$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path

$EnvironmentFile = Join-Path $ProjectRoot "environment.yml"
$BackendDirectory = Join-Path $ProjectRoot "backend"
$FrontendDirectory = Join-Path $ProjectRoot "frontend"
$EnvExample = Join-Path $ProjectRoot ".env.example"
$EnvFile = Join-Path $ProjectRoot ".env"
$ModelSetup = Join-Path $BackendDirectory "scripts\setup_model.py"
$EnvironmentVerifier = Join-Path $BackendDirectory "scripts\verify_model_environment.py"

foreach ($requiredPath in @($EnvironmentFile, $BackendDirectory, $FrontendDirectory, $EnvExample, $ModelSetup, $EnvironmentVerifier)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "The repository is incomplete. Missing: $requiredPath"
    }
}

Write-Host "Aegis setup" -ForegroundColor Green
Write-Host "Project root: $ProjectRoot"
Write-Host "The folder may have any name; paths are resolved from this script."

$Conda = Find-Executable -Commands @("conda.exe", "conda") -Candidates @(
    (Join-Path $env:USERPROFILE "miniconda3\Scripts\conda.exe"),
    (Join-Path $env:USERPROFILE "anaconda3\Scripts\conda.exe"),
    (Join-Path $env:LOCALAPPDATA "miniconda3\Scripts\conda.exe"),
    "C:\ProgramData\miniconda3\Scripts\conda.exe",
    "C:\ProgramData\anaconda3\Scripts\conda.exe"
)
$Git = Find-Executable -Commands @("git.exe", "git") -Candidates @(
    "C:\Program Files\Git\cmd\git.exe",
    "C:\Program Files (x86)\Git\cmd\git.exe"
)
$Node = Find-Executable -Commands @("node.exe", "node") -Candidates @(
    "C:\Program Files\nodejs\node.exe"
)
$Npm = Find-Executable -Commands @("npm.cmd", "npm") -Candidates @(
    "C:\Program Files\nodejs\npm.cmd"
)

$missing = @()
if (-not $Conda) { $missing += "Miniconda or Anaconda" }
if (-not $Git) { $missing += "Git for Windows" }
if (-not $Node -or -not $Npm) { $missing += "Node.js LTS (with npm)" }
if ($missing.Count -gt 0) {
    throw "Install the following prerequisites, reopen this script, and try again: $($missing -join ', ')."
}

# The exact EMBER package is installed from Git, so make Git visible to Conda's pip subprocess.
$env:PATH = "$(Split-Path -Parent $Git);$(Split-Path -Parent $Node);$env:PATH"

Write-Step "Checking prerequisites"
Invoke-Checked -Executable $Git -Arguments @("--version") -FailureMessage "Git is not working"
Invoke-Checked -Executable $Conda -Arguments @("--version") -FailureMessage "Conda is not working"
Invoke-Checked -Executable $Node -Arguments @("--version") -FailureMessage "Node.js is not working"
Invoke-Checked -Executable $Npm -Arguments @("--version") -FailureMessage "npm is not working"

$nodeVersionText = (& $Node --version).Trim().TrimStart("v")
$nodeMajor = 0
if (-not [int]::TryParse(($nodeVersionText -split "\.")[0], [ref]$nodeMajor) -or $nodeMajor -lt 20) {
    throw "Node.js 20 or newer is required. Detected: $nodeVersionText"
}

Push-Location $ProjectRoot
try {
    Write-Step "Creating or updating Conda environment '$EnvironmentName'"
    $environmentJson = & $Conda env list --json
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to read the Conda environment list."
    }
    $environmentData = $environmentJson | ConvertFrom-Json
    $environmentExists = @($environmentData.envs) | Where-Object {
        (Split-Path -Leaf $_) -eq $EnvironmentName
    }

    if ($environmentExists) {
        Invoke-Checked -Executable $Conda `
            -Arguments @("env", "update", "--name", $EnvironmentName, "--file", $EnvironmentFile, "--prune") `
            -FailureMessage "Conda environment update failed"
    }
    else {
        Invoke-Checked -Executable $Conda `
            -Arguments @("env", "create", "--file", $EnvironmentFile) `
            -FailureMessage "Conda environment creation failed"
    }

    Write-Step "Verifying the exact EMBER/XGBoost environment"
    Invoke-Checked -Executable $Conda `
        -Arguments @("run", "--no-capture-output", "--name", $EnvironmentName, "python", $EnvironmentVerifier) `
        -FailureMessage "Exact dependency verification failed"

    Write-Step "Creating application configuration"
    if (-not (Test-Path -LiteralPath $EnvFile)) {
        Copy-Item -LiteralPath $EnvExample -Destination $EnvFile
        Write-Host "Created $EnvFile"
    }
    else {
        Write-Host "Keeping existing configuration: $EnvFile"
    }

    $envText = [System.IO.File]::ReadAllText($EnvFile)
    if ($envText -match "(?m)^WAZUH_INGEST_API_KEY=change-me\s*$") {
        $secret = New-RandomHexSecret
        $envText = [System.Text.RegularExpressions.Regex]::Replace(
            $envText,
            "(?m)^WAZUH_INGEST_API_KEY=change-me\s*$",
            "WAZUH_INGEST_API_KEY=$secret"
        )
        [System.IO.File]::WriteAllText(
            $EnvFile,
            $envText,
            (New-Object System.Text.UTF8Encoding($false))
        )
        Write-Host "Generated a random Wazuh intake API key in .env (value not displayed)."
    }

    if (-not $SkipModel) {
        Write-Step "Installing and verifying the XGBoost model"
        Invoke-Checked -Executable $Conda `
            -Arguments @("run", "--no-capture-output", "--name", $EnvironmentName, "python", $ModelSetup) `
            -FailureMessage "Model installation failed"
    }
    else {
        Write-Host "Model setup skipped by request."
    }

    Write-Step "Installing frontend dependencies"
    Push-Location $FrontendDirectory
    try {
        Invoke-Checked -Executable $Npm -Arguments @("ci") -FailureMessage "Frontend dependency installation failed"
        if (-not $SkipFrontendBuild) {
            Invoke-Checked -Executable $Npm -Arguments @("run", "build") -FailureMessage "Frontend build failed"
        }
    }
    finally {
        Pop-Location
    }

    if (-not $SkipModel) {
        Write-Step "Loading the application and model"
        $applicationCheck = @'
from app.api.dependencies import get_detection_engine
from app.main import app

engine = get_detection_engine()
if not engine.available:
    raise SystemExit("The model engine is unavailable")
print(f"Application verified: {app.title}; model={engine.model_version}")
'@
        Push-Location $BackendDirectory
        try {
            Invoke-Checked -Executable $Conda `
                -Arguments @("run", "--no-capture-output", "--name", $EnvironmentName, "python", "-c", $applicationCheck) `
                -FailureMessage "Application verification failed"
        }
        finally {
            Pop-Location
        }
    }
}
finally {
    Pop-Location
}

Write-Host "`nAegis setup completed successfully." -ForegroundColor Green
Write-Host "Start it by double-clicking start-aegis.cmd, or run .\start-aegis.ps1"
Write-Host "Ollama is optional; install it and run 'ollama pull llama3' for AI/PDF reports."
