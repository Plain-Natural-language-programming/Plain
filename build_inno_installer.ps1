
Write-Host "Plain Language Installer Builder" -ForegroundColor Cyan
Write-Host "=" * 50

$innoSetupPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $innoSetupPath)) {
    $innoSetupPath = "C:\Program Files\Inno Setup 6\ISCC.exe"
}

if (-not (Test-Path $innoSetupPath)) {
    Write-Host "ERROR: Inno Setup not found!" -ForegroundColor Red
    Write-Host "Please install Inno Setup from: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    Write-Host "Or download portable version and update the path in this script." -ForegroundColor Yellow
    exit 1
}

Write-Host "Found Inno Setup at: $innoSetupPath" -ForegroundColor Green

try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found in PATH!" -ForegroundColor Red
    exit 1
}

Write-Host "`nInstalling Python dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt
pip install pyinstaller

Write-Host "`nInstalling Plain Language..." -ForegroundColor Cyan
python setup.py install

Write-Host "`nBuilding Plain Language package..." -ForegroundColor Cyan
python setup.py bdist_wheel

if (-not (Test-Path "dist")) {
    New-Item -ItemType Directory -Path "dist" | Out-Null
}

Write-Host "`nCompiling installer..." -ForegroundColor Cyan
& $innoSetupPath "installer.iss"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nInstaller created successfully!" -ForegroundColor Green
    Write-Host "Location: dist\\PlainLanguage-Setup.exe" -ForegroundColor Green
} else {
    Write-Host "`nInstaller build failed!" -ForegroundColor Red
    exit 1
}
