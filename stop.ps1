#Requires -Version 5.1
<#
.SYNOPSIS
  Stops HorizonAI processes started by start.ps1.
#>
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$ApiPidFile = Join-Path $ScriptDir ".horizon-ai-api.pid"
$WebPidFile = Join-Path $ScriptDir ".horizon-ai-web.pid"

function Stop-PidFile([string]$Label, [string]$PidFile) {
  if (-not (Test-Path $PidFile)) { return }

  $targetPid = Get-Content $PidFile -ErrorAction SilentlyContinue
  $proc = if ($targetPid) { Get-Process -Id $targetPid -ErrorAction SilentlyContinue } else { $null }

  if (-not $proc) {
    Write-Host "$Label process $targetPid is not running. Cleaning stale PID file."
    Remove-Item $PidFile -ErrorAction SilentlyContinue
    return
  }

  Write-Host "Stopping $Label (PID $targetPid)..."
  Stop-Process -Id $targetPid -ErrorAction SilentlyContinue

  for ($i = 0; $i -lt 10; $i++) {
    if (-not (Get-Process -Id $targetPid -ErrorAction SilentlyContinue)) {
      Remove-Item $PidFile -ErrorAction SilentlyContinue
      Write-Host "$Label stopped."
      return
    }
    Start-Sleep -Seconds 1
  }

  Write-Host "$Label did not exit in time, forcing..."
  Stop-Process -Id $targetPid -Force -ErrorAction SilentlyContinue
  Remove-Item $PidFile -ErrorAction SilentlyContinue
  Write-Host "$Label stopped."
}

if (-not (Test-Path $ApiPidFile) -and -not (Test-Path $WebPidFile)) {
  Write-Host "No PID files found — HorizonAI doesn't look like it's running via start.ps1."
  exit 0
}

Stop-PidFile "API" $ApiPidFile
Stop-PidFile "Web" $WebPidFile
Write-Host "Done."
