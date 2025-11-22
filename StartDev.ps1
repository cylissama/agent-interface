# StartDev.ps1 - Unified development startup script for Windows
# Usage: .\StartDev.ps1

Write-Host "`nStarting Agent Interface..." -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor DarkGray

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# Check prerequisites
Write-Host "`n[1/4] Checking prerequisites..." -ForegroundColor Yellow
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found. Please install Python 3.11+ and try again."
    exit 1
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js/npm not found. Please install Node.js and try again."
    exit 1
}
Write-Host "[OK] Prerequisites OK" -ForegroundColor Green

# Backend setup - using root-level venv
Write-Host "`n[2/4] Setting up backend..." -ForegroundColor Yellow

# Check if venv exists and is valid
$venvActivate = "$root\.venv\Scripts\Activate.ps1"
$venvPython = "$root\.venv\Scripts\python.exe"

# Create or recreate venv if it doesn't exist or is incomplete
if (-not (Test-Path $venvActivate) -or -not (Test-Path $venvPython)) {
    if (Test-Path "$root\.venv") {
        Write-Host "Existing .venv appears incomplete. Recreating..." -ForegroundColor Yellow
        Remove-Item "$root\.venv" -Recurse -Force -ErrorAction SilentlyContinue
    }
    Write-Host "Creating Python virtual environment at project root..." -ForegroundColor DarkYellow
    python -m venv "$root\.venv"
    if (-not (Test-Path "$root\.venv")) {
        Write-Error "Failed to create virtual environment. Please check Python installation."
        exit 1
    }
    # Wait a moment for venv to be fully created
    Start-Sleep -Seconds 1
}

# Verify activation script exists
if (-not (Test-Path $venvActivate)) {
    Write-Error "Virtual environment activation script not found at $venvActivate. The venv may be corrupted. Try deleting .venv and running again."
    exit 1
}

# Activate venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force | Out-Null
try {
    . $venvActivate
    Write-Host "Virtual environment activated" -ForegroundColor DarkGray
} catch {
    Write-Error "Failed to activate virtual environment: $_"
    exit 1
}

# Install dependencies from backend/requirements.txt
Write-Host "Installing backend dependencies..." -ForegroundColor DarkYellow
python -m pip install -q --upgrade pip
python -m pip install -q -r "$root\backend\requirements.txt"

# Start backend in background
Write-Host "Starting backend server on http://localhost:8000..." -ForegroundColor Green
$venvPython = "$root\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Python virtual environment not found at $venvPython"
    exit 1
}
$backendJob = Start-Job -ScriptBlock {
    param($pythonPath, $rootDir)
    # Set working directory and Python path
    Set-Location "$rootDir\backend"
    $env:PYTHONPATH = "$rootDir\backend"
    # Run uvicorn and capture all output (including errors)
    & $pythonPath -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 2>&1
} -ArgumentList $venvPython, $root

# Frontend setup
Write-Host "`n[3/4] Setting up frontend..." -ForegroundColor Yellow
Push-Location "$root\frontend"

# Install dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor DarkYellow
    npm install --silent
}

# Start frontend
Write-Host "Starting frontend server on http://localhost:5173..." -ForegroundColor Green
$env:VITE_API_BASE_URL = "http://localhost:8000"
$frontendJob = Start-Job -ScriptBlock {
    param($rootDir, $apiUrl)
    $env:VITE_API_BASE_URL = $apiUrl
    Set-Location "$rootDir\frontend"
    npm run dev
} -ArgumentList $root, "http://localhost:8000"

Pop-Location

# Wait a moment for servers to start
Write-Host "Waiting for services to start..." -ForegroundColor DarkYellow
Start-Sleep -Seconds 8

# Check job output early for errors
$backendOutput = Receive-Job $backendJob -ErrorAction SilentlyContinue
if ($backendOutput) {
    # Check for any error patterns
    $errorLines = $backendOutput | Where-Object { 
        $_ -match "error|Error|ERROR|failed|Failed|FAILED|Traceback|ImportError|ModuleNotFoundError|Exception|cannot|Cannot|not found|Not found" 
    }
    if ($errorLines) {
        Write-Host "`n[WARNING] Backend job shows errors:" -ForegroundColor Yellow
        $errorLines | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    } else {
        # Show startup messages if any
        $startupLines = $backendOutput | Where-Object { $_ -match "Started|Uvicorn|Application startup|INFO" }
        if ($startupLines) {
            Write-Host "Backend startup messages:" -ForegroundColor DarkGray
            $startupLines | Select-Object -Last 5 | ForEach-Object { Write-Host $_ -ForegroundColor DarkGray }
        }
    }
}

# Verify services are running
$backendRunning = $false
$frontendRunning = $false

for ($i = 0; $i -lt 20; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $backendRunning = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

# Display status
Write-Host "`n[4/4] Services status:" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor DarkGray
if ($backendRunning) {
    Write-Host "[OK] Backend:  http://localhost:8000" -ForegroundColor Cyan
    Write-Host "[OK] API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
} else {
    Write-Host "[ERROR] Backend is not responding!" -ForegroundColor Red
    Write-Host "`nChecking backend job status..." -ForegroundColor Yellow
    $jobState = Get-Job -Id $backendJob.Id | Select-Object -ExpandProperty State
    Write-Host "Backend job state: $jobState" -ForegroundColor Yellow
    
    # Automatically show backend logs if it failed
    Write-Host "`nBackend job output:" -ForegroundColor Yellow
    Write-Host "----------------------------------------------------------------------" -ForegroundColor DarkGray
    $backendOutput = Receive-Job $backendJob -ErrorAction SilentlyContinue
    if ($backendOutput) {
        # Show all output, not just last 20 lines
        $backendOutput | ForEach-Object { Write-Host $_ }
    } else {
        Write-Host "(No output yet - checking job state...)" -ForegroundColor DarkGray
        # Check if job has any errors
        $jobInfo = Get-Job -Id $backendJob.Id
        if ($jobInfo.HasMoreData) {
            $allOutput = Receive-Job $backendJob
            if ($allOutput) {
                $allOutput | ForEach-Object { Write-Host $_ }
            }
        }
        if ($jobInfo.State -eq "Failed") {
            Write-Host "Job has failed. Error details:" -ForegroundColor Red
            $jobInfo | Format-List * | Write-Host
        }
    }
    Write-Host "----------------------------------------------------------------------" -ForegroundColor DarkGray
    
    Write-Host "`nTroubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check if port 8000 is already in use: netstat -ano | findstr :8000" -ForegroundColor DarkGray
    Write-Host "2. Verify .env file exists in project root with GROQ_API_KEY" -ForegroundColor DarkGray
    Write-Host "3. Check the output above for Python/import errors" -ForegroundColor DarkGray
    Write-Host "`nTo view full logs in a new terminal, run:" -ForegroundColor Yellow
    Write-Host "  Receive-Job -Id $($backendJob.Id)" -ForegroundColor Cyan
}
Write-Host "[OK] Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor DarkGray
Write-Host "`nPress Ctrl+C to stop all services" -ForegroundColor Yellow

# Wait for Ctrl+C and periodically check job status
try {
    $checkCount = 0
    while ($true) {
        Start-Sleep -Seconds 1
        $checkCount++
        # Every 10 seconds, check if backend is still running
        if ($checkCount -ge 10 -and -not $backendRunning) {
            $checkCount = 0
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 1 -ErrorAction Stop
                if ($response.StatusCode -eq 200) {
                    Write-Host "`n[SUCCESS] Backend is now running!" -ForegroundColor Green
                    $backendRunning = $true
                }
            } catch {
                # Backend still not running, continue waiting
            }
        }
    }
} finally {
    Write-Host "`nStopping services..." -ForegroundColor Yellow
    if ($backendJob) {
        Write-Host "Stopping backend..." -ForegroundColor DarkYellow
        Stop-Job $backendJob -ErrorAction SilentlyContinue
        # Show any remaining output before removing
        $backendOutput = Receive-Job $backendJob -ErrorAction SilentlyContinue
        if ($backendOutput) {
            Write-Host "Backend output:" -ForegroundColor DarkGray
            Write-Host $backendOutput
        }
        Remove-Job $backendJob -Force -ErrorAction SilentlyContinue
    }
    if ($frontendJob) {
        Write-Host "Stopping frontend..." -ForegroundColor DarkYellow
        Stop-Job $frontendJob -ErrorAction SilentlyContinue
        Remove-Job $frontendJob -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[OK] Services stopped" -ForegroundColor Green
}

