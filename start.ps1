# Watchdog Launcher Startup Script
# This script checks for a virtual environment, creates one if needed, and launches the application

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Define venv path
$VenvPath = Join-Path $ScriptDir "venv"
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
$VenvActivate = Join-Path $VenvPath "Scripts\Activate.ps1"
$RequirementsFile = Join-Path $ScriptDir "requirements.txt"
$LauncherScript = Join-Path $ScriptDir "watchdogd-launcher.py"

# Check if venv exists
if (-not (Test-Path $VenvPath)) {
    Write-Host "Virtual environment not found. Creating new venv..." -ForegroundColor Yellow
    python -m venv venv
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create virtual environment. Please ensure Python is installed and in your PATH." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Host "Virtual environment created successfully." -ForegroundColor Green
    
    # Install dependencies
    if (Test-Path $RequirementsFile) {
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        & $VenvPython -m pip install --upgrade pip
        & $VenvPython -m pip install -r $RequirementsFile
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to install dependencies." -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
        
        Write-Host "Dependencies installed successfully." -ForegroundColor Green
    }
} else {
    Write-Host "Virtual environment found." -ForegroundColor Green
    
    # Check if requirements.txt has been updated (optional check)
    if (Test-Path $RequirementsFile) {
        $RequirementsModified = (Get-Item $RequirementsFile).LastWriteTime
        $VenvModified = (Get-Item $VenvPath).LastWriteTime
        
        if ($RequirementsModified -gt $VenvModified) {
            Write-Host "Requirements file has been updated. Reinstalling dependencies..." -ForegroundColor Yellow
            & $VenvPython -m pip install -r $RequirementsFile
        }
    }
}

# Launch the application
Write-Host "Starting Watchdog Launcher..." -ForegroundColor Cyan
& $VenvPython $LauncherScript

# If the application exits with an error, pause to show the error message
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nApplication exited with error code: $LASTEXITCODE" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}

