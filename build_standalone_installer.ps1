Write-Host "Building Standalone Plain Language Installer" -ForegroundColor Cyan
Write-Host ("=" * 60)

$errors = @()

try {
    $pythonVersion = python --version 2>&1
    Write-Host ("[OK] Found Python: {0}" -f $pythonVersion) -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found!" -ForegroundColor Red
    $errors += "Python 3.9+ is required"
}

$innoSetupPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $innoSetupPath)) {
    $innoSetupPath = "C:\Program Files\Inno Setup 6\ISCC.exe"
}

if (-not (Test-Path $innoSetupPath)) {
    Write-Host "[ERROR] Inno Setup not found!" -ForegroundColor Red
    Write-Host "  Download from: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    $errors += "Inno Setup 6 is required"
} else {
    Write-Host "[OK] Found Inno Setup" -ForegroundColor Green
}

if ($errors.Count -gt 0) {
    Write-Host "`nErrors found. Please fix them before continuing." -ForegroundColor Red
    exit 1
}

Write-Host "`nCleaning previous builds..." -ForegroundColor Cyan
if (Test-Path "dist") {
    Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path "build") {
    Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "`nInstalling dependencies..." -ForegroundColor Cyan
pip install --upgrade -r requirements.txt
pip install --upgrade setuptools wheel

Write-Host "`nInstalling Plain Language..." -ForegroundColor Cyan
python setup.py install --force

Write-Host "`nBuilding package..." -ForegroundColor Cyan
python setup.py bdist_wheel

if (-not (Test-Path "dist")) {
    New-Item -ItemType Directory -Path "dist" | Out-Null
}

Write-Host "`nCompiling installer (this may take a minute)..." -ForegroundColor Cyan
& $innoSetupPath "installer.iss"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n" + ("=" * 60) -ForegroundColor Green
    Write-Host "[SUCCESS] Installer created successfully!" -ForegroundColor Green
    Write-Host ("=" * 60) -ForegroundColor Green
    Write-Host "`nLocation: dist\PlainLanguage-Setup.exe" -ForegroundColor Cyan
    
    Write-Host "`nCopying installer to docs folder..." -ForegroundColor Cyan
    if (Test-Path "dist\PlainLanguage-Setup.exe") {
        Copy-Item -Path "dist\PlainLanguage-Setup.exe" -Destination "docs\PlainLanguage-Setup.exe" -Force
        Write-Host "[OK] Installer copied to docs\PlainLanguage-Setup.exe" -ForegroundColor Green
    }
    
    Write-Host "`nYou can now share this file with your friends!" -ForegroundColor Yellow
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "  1. Test the installer on your system" -ForegroundColor White
    Write-Host "  2. The installer is available in docs\ for documentation download" -ForegroundColor White
    Write-Host "  3. Upload to Google Drive/Dropbox/GitHub" -ForegroundColor White
    Write-Host "  4. Share the download link" -ForegroundColor White
    Write-Host "`nSee docs\DISTRIBUTE.md for detailed instructions." -ForegroundColor Cyan
} else {
    Write-Host "`n[ERROR] Installer build failed!" -ForegroundColor Red
    Write-Host "Check the error messages above." -ForegroundColor Yellow
    exit 1
}
