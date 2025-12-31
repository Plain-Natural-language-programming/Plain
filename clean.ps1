Write-Host "Cleaning temporary files..." -ForegroundColor Cyan

Get-ChildItem -Path "." -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Write-Host "[OK] Removed __pycache__ directories" -ForegroundColor Green

Get-ChildItem -Path "." -Filter "*.pyc" -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force
Write-Host "[OK] Removed .pyc files" -ForegroundColor Green

if (Test-Path "plain_lang.egg-info") {
    Remove-Item -Path "plain_lang.egg-info" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Removed egg-info" -ForegroundColor Green
}

if (Test-Path "build") {
    Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Removed build directory" -ForegroundColor Green
}

Get-ChildItem -Path "." -Filter "*.log" -ErrorAction SilentlyContinue | Remove-Item -Force
Write-Host "[OK] Removed log files" -ForegroundColor Green

Get-ChildItem -Path "." -Filter "*.vsix" -ErrorAction SilentlyContinue | Remove-Item -Force
Write-Host "[OK] Removed VSIX files" -ForegroundColor Green

Write-Host "`nCleanup complete!" -ForegroundColor Green
