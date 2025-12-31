
Write-Host "Installing Plain Language to User Directory" -ForegroundColor Cyan
Write-Host "=================================================="

$projectRoot = $PSScriptRoot
if (-not $projectRoot) {
    $projectRoot = Get-Location
}

Write-Host "Project directory: $projectRoot" -ForegroundColor Yellow

Write-Host ""
Write-Host "Installing Plain Language..." -ForegroundColor Cyan
python -m pip install --user -e "$projectRoot"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Installation successful!" -ForegroundColor Green
    
    $pythonVersion = python -c "import sys; print('{}{}'.format(sys.version_info.major, sys.version_info.minor))"
    $scriptsPath = Join-Path $env:APPDATA "Python\Python$pythonVersion\Scripts"
    
    Write-Host ""
    Write-Host "Scripts installed to: $scriptsPath" -ForegroundColor Yellow
    
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$scriptsPath*") {
        Write-Host ""
        Write-Host "Adding to user PATH..." -ForegroundColor Cyan
        if ($userPath) {
            $newPath = $userPath + ";" + $scriptsPath
        } else {
            $newPath = $scriptsPath
        }
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        Write-Host "Added to user PATH" -ForegroundColor Green
        Write-Host ""
        Write-Host "Please restart PowerShell/VS Code for changes to take effect!" -ForegroundColor Yellow
    } else {
        Write-Host ""
        Write-Host "Already in user PATH" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "Testing installation..." -ForegroundColor Cyan
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = $machinePath + ";" + $userPath
    
    $plainTest = Get-Command plain -ErrorAction SilentlyContinue
    if ($plainTest) {
        plain --version
        Write-Host ""
        Write-Host "Plain Language is now installed and working!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Installation complete, but 'plain' command not found in current session." -ForegroundColor Yellow
        Write-Host "Please restart PowerShell/VS Code to use the 'plain' command." -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "Installation failed!" -ForegroundColor Red
    exit 1
}
