#Requires -Version 5.1
<#
.SYNOPSIS
  Starts HorizonAI (FastAPI backend + TanStack Start frontend).
.PARAMETER Hostname
  Host/interface to bind (default 127.0.0.1).
.PARAMETER Port
  Frontend port (default 5173).
.PARAMETER ApiPort
  Backend API port (default 8000).
.PARAMETER SkipSeed
  Skip database seeding on startup.
.NOTES
  Written to mirror start.sh. PowerShell is not available in the Linux Cloud Agent
  environment — please verify manually on Windows before relying on it.
#>
param(
  [string]$Hostname = "127.0.0.1",
  [int]$Port = 5173,
  [int]$ApiPort = 8000,
  [switch]$SkipSeed
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$ApiPidFile = Join-Path $ScriptDir ".horizon-ai-api.pid"
$WebPidFile = Join-Path $ScriptDir ".horizon-ai-web.pid"
$ApiLogFile = Join-Path $ScriptDir ".horizon-ai-api.log"
$WebLogFile = Join-Path $ScriptDir ".horizon-ai-web.log"

function Test-Running([string]$PidFile) {
  if (-not (Test-Path $PidFile)) { return $false }
  $pid = Get-Content $PidFile -ErrorAction SilentlyContinue
  return ($pid -and (Get-Process -Id $pid -ErrorAction SilentlyContinue))
}

if ((Test-Running $ApiPidFile) -or (Test-Running $WebPidFile)) {
  Write-Host "HorizonAI is already running."
  if (Test-Path $ApiPidFile) { Write-Host "  API PID: $(Get-Content $ApiPidFile)" }
  if (Test-Path $WebPidFile) { Write-Host "  Web PID: $(Get-Content $WebPidFile)" }
  Write-Host "Run .\stop.ps1 first if you want to restart."
  exit 0
}

Remove-Item $ApiPidFile, $WebPidFile -ErrorAction SilentlyContinue

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  Write-Error "Node.js is required but was not found on PATH. Install Node.js 18+."
  exit 1
}

if (-not (Get-Command python -ErrorAction SilentlyContinue) -and -not (Get-Command python3 -ErrorAction SilentlyContinue)) {
  Write-Error "Python 3 is required but was not found on PATH."
  exit 1
}

$Python = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "python3" }

$PkgRunner = "npm"
if ((Get-Command bun -ErrorAction SilentlyContinue) -and (Test-Path (Join-Path $ScriptDir "bun.lock"))) {
  $PkgRunner = "bun"
}

if (-not (Test-Path (Join-Path $ScriptDir "node_modules"))) {
  Write-Host "Installing frontend dependencies with $PkgRunner..."
  if ($PkgRunner -eq "bun") { & bun install } else { & npm install }
}

$VenvUvicorn = Join-Path $ScriptDir "backend\.venv\Scripts\uvicorn.exe"
if (-not (Test-Path $VenvUvicorn)) {
  Write-Host "Creating Python virtual environment..."
  & $Python -m venv (Join-Path $ScriptDir "backend\.venv")
  & (Join-Path $ScriptDir "backend\.venv\Scripts\pip.exe") install -r (Join-Path $ScriptDir "backend\requirements.txt")
}

if (-not (Test-Path (Join-Path $ScriptDir "backend\.env"))) {
  Copy-Item (Join-Path $ScriptDir "backend\.env.example") (Join-Path $ScriptDir "backend\.env")
}

if (-not (Test-Path (Join-Path $ScriptDir ".env"))) {
  Copy-Item (Join-Path $ScriptDir ".env.example") (Join-Path $ScriptDir ".env")
}

Write-Host "Ensuring PostgreSQL is configured..."
if (Get-Command bash -ErrorAction SilentlyContinue) {
  & bash (Join-Path $ScriptDir "scripts\setup-postgres.sh")
} else {
  Write-Warning "bash not found — skipping scripts/setup-postgres.sh. Ensure PostgreSQL is configured manually."
}

if (-not $SkipSeed) {
  Write-Host "Seeding database and golden dataset..."
  & (Join-Path $ScriptDir "backend\.venv\Scripts\python.exe") (Join-Path $ScriptDir "backend\scripts\seed_data.py")
}

Write-Host "Starting FastAPI on http://${Hostname}:${ApiPort} ..."
$apiProc = Start-Process -FilePath $VenvUvicorn `
  -ArgumentList @("app.main:app", "--host", $Hostname, "--port", $ApiPort, "--app-dir", "backend") `
  -RedirectStandardOutput $ApiLogFile -RedirectStandardError "$ApiLogFile.err" `
  -PassThru -WindowStyle Hidden
$apiProc.Id | Out-File -FilePath $ApiPidFile -Encoding ascii

$apiReady = $false
for ($i = 0; $i -lt 30; $i++) {
  if ($apiProc.HasExited) {
    Write-Error "API failed to start. Last log lines:"
    if (Test-Path $ApiLogFile) { Get-Content $ApiLogFile -Tail 30 | Write-Host }
    Remove-Item $ApiPidFile -ErrorAction SilentlyContinue
    exit 1
  }
  try {
    $resp = Invoke-WebRequest -Uri "http://${Hostname}:${ApiPort}/health" -UseBasicParsing -TimeoutSec 2
    if ($resp.StatusCode -eq 200) { $apiReady = $true; break }
  } catch { }
  Start-Sleep -Seconds 1
}

if (-not $apiReady) {
  Write-Error "API did not become healthy in time. Last log lines:"
  if (Test-Path $ApiLogFile) { Get-Content $ApiLogFile -Tail 30 | Write-Host }
  Stop-Process -Id $apiProc.Id -ErrorAction SilentlyContinue
  Remove-Item $ApiPidFile -ErrorAction SilentlyContinue
  exit 1
}

Write-Host "Starting frontend on http://${Hostname}:${Port} ..."
if ($PkgRunner -eq "bun") {
  $webProc = Start-Process -FilePath "bun" -ArgumentList @("run", "dev", "--host", $Hostname, "--port", $Port) `
    -RedirectStandardOutput $WebLogFile -RedirectStandardError "$WebLogFile.err" -PassThru -WindowStyle Hidden
} else {
  $webProc = Start-Process -FilePath "npm" -ArgumentList @("run", "dev", "--", "--host", $Hostname, "--port", $Port) `
    -RedirectStandardOutput $WebLogFile -RedirectStandardError "$WebLogFile.err" -PassThru -WindowStyle Hidden
}
$webProc.Id | Out-File -FilePath $WebPidFile -Encoding ascii

$webReady = $false
for ($i = 0; $i -lt 30; $i++) {
  if ($webProc.HasExited) {
    Write-Error "Frontend failed to start. Last log lines:"
    if (Test-Path $WebLogFile) { Get-Content $WebLogFile -Tail 30 | Write-Host }
    Stop-Process -Id $apiProc.Id -ErrorAction SilentlyContinue
    Remove-Item $ApiPidFile, $WebPidFile -ErrorAction SilentlyContinue
    exit 1
  }
  if ((Test-Path $WebLogFile) -and (Select-String -Path $WebLogFile -Pattern "ready in|Local:" -Quiet -ErrorAction SilentlyContinue)) {
    $webReady = $true
    break
  }
  Start-Sleep -Seconds 1
}

Write-Host ""
Write-Host "HorizonAI is running."
Write-Host "  Cockpit:  http://${Hostname}:${Port}"
Write-Host "  API:      http://${Hostname}:${ApiPort}/health"
Write-Host "  API PID:  $($apiProc.Id) (log: $ApiLogFile)"
Write-Host "  Web PID:  $($webProc.Id) (log: $WebLogFile)"
Write-Host "Stop with: .\stop.ps1"
Write-Host "Guide:     docs/HOW_TO_USE.md"
