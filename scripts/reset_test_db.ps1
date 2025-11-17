Write-Host "========================================"
Write-Host "Resetting Test Database"
Write-Host "========================================"
Write-Host ""

# Check for running Python processes
Write-Host "Checking for running Python processes..."
$pythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    Write-Host "[WARNING] Found $($pythonProcesses.Count) Python process(es). Stopping all..."
    $pythonProcesses | ForEach-Object {
        Write-Host "  Stopping process: $($_.ProcessName) (PID: $($_.Id))"
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "  Waiting 3 seconds for processes to fully stop..."
    Start-Sleep -Seconds 3

    # Verify all stopped
    $remainingProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue
    if ($remainingProcesses) {
        Write-Host "[WARNING] Some Python processes still running. Forcing termination..."
        $remainingProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
    Write-Host "[OK] Python processes stopped"
} else {
    Write-Host "[OK] No Python processes found"
}

Write-Host ""

# Clean data\chromadb directory
Write-Host "Cleaning data\chromadb directory..."
if (Test-Path "data\chromadb") {
    Write-Host "  Removing all contents from data\chromadb..."
    try {
        Get-ChildItem -Path "data\chromadb" -Recurse | Remove-Item -Force -Recurse -ErrorAction Stop
        Write-Host "[OK] data\chromadb cleaned"
    } catch {
        Write-Host "[ERROR] Failed to clean data\chromadb - files may be locked"
        Write-Host "  Please stop the server manually and try again"
        Write-Host "  Error: $_"
    }
} else {
    New-Item -ItemType Directory -Path "data\chromadb" -Force | Out-Null
    Write-Host "[OK] data\chromadb created"
}

Write-Host ""

# Clean data\users directory
Write-Host "Cleaning data\users directory..."
if (Test-Path "data\users") {
    Write-Host "  Removing all contents from data\users..."
    try {
        Get-ChildItem -Path "data\users" -Recurse | Remove-Item -Force -Recurse -ErrorAction Stop
        Write-Host "[OK] data\users cleaned"
    } catch {
        Write-Host "[ERROR] Failed to clean data\users - files may be locked"
        Write-Host "  Error: $_"
    }
} else {
    New-Item -ItemType Directory -Path "data\users" -Force | Out-Null
    Write-Host "[OK] data\users created"
}

Write-Host ""
Write-Host "========================================"
Write-Host "Test database reset completed!"
Write-Host "========================================"
