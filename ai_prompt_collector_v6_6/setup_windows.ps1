$ErrorActionPreference = "Stop"
Write-Host "AI Prompt Collector v6 - Windows prerequisite setup" -ForegroundColor Cyan
function Has-Cmd($n) { return [bool](Get-Command $n -ErrorAction SilentlyContinue) }
if (-not (Has-Cmd "winget")) {
  Write-Host "winget is not available. Install Git and Python 3.10+ manually, then rerun." -ForegroundColor Red
  exit 2
}
if (-not (Has-Cmd "git")) {
  Write-Host "Installing Git..." -ForegroundColor Yellow
  winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements
}
if (-not (Has-Cmd "python")) {
  Write-Host "Installing Python..." -ForegroundColor Yellow
  winget install --id Python.Python.3.13 -e --accept-package-agreements --accept-source-agreements
}
Write-Host "Setup attempted. If Git/Python was newly installed, close this window and run START_HERE.bat again so PATH refreshes." -ForegroundColor Green
