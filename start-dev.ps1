param(
  [string]$ApiUrl = "http://localhost:8000",
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 5173
)

Write-Host "Starting Agent Interface (backend + frontend)..." -ForegroundColor Cyan

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# ---------- Backend ----------
Write-Host "`n[1/2] Backend setup..." -ForegroundColor Yellow
Push-Location "$root\backend"

if (-not (Test-Path ".venv")) {
  Write-Host "Creating Python virtual environment (.venv)..." -ForegroundColor DarkYellow
  python -m venv .venv
}

if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
  Write-Error "Virtual environment activation script not found. Ensure Python is installed and re-run."
  Pop-Location
  exit 1
}

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force | Out-Null
. ".\.venv\Scripts\Activate.ps1"

Write-Host "Installing backend dependencies..." -ForegroundColor DarkYellow
python -m pip install -U pip | Out-Null
python -m pip install -r requirements.txt

Write-Host "Starting backend on port $BackendPort ..." -ForegroundColor Green
$backendJob = Start-Job -ScriptBlock {
  param($port)
  uvicorn app.main:app --reload --host 0.0.0.0 --port $port
} -ArgumentList $BackendPort

Pop-Location

# ---------- Frontend ----------
Write-Host "`n[2/2] Frontend setup..." -ForegroundColor Yellow
Push-Location "$root\frontend"

if (-not (Test-Path "package.json")) {
  Write-Error "frontend/package.json not found. Are you in the correct repository?"
  Pop-Location
  exit 1
}

Write-Host "Installing frontend dependencies..." -ForegroundColor DarkYellow
npm install

Write-Host "Starting frontend on port $FrontendPort (VITE_API_BASE_URL=$ApiUrl)..." -ForegroundColor Green
$env:VITE_API_BASE_URL = $ApiUrl
$frontendJob = Start-Job -ScriptBlock {
  param($apiUrl)
  $env:VITE_API_BASE_URL = $apiUrl
  npm run dev
} -ArgumentList $ApiUrl

Pop-Location

Write-Host "`nDone. Services starting..." -ForegroundColor Cyan
Write-Host "Backend:  http://127.0.0.1:$BackendPort/health"
Write-Host "Docs:     http://127.0.0.1:$BackendPort/docs"
Write-Host "Frontend: http://localhost:$FrontendPort/"

Write-Host "`nUse 'Get-Job' to view jobs and 'Receive-Job -Id <id>' to view logs."
Write-Host "Stop jobs with: 'Stop-Job *' or close this terminal." -ForegroundColor DarkGray


