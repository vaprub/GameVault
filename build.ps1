# build.ps1 - GameVault Builder (Development Mode)

param(
    [switch]$Clean
)

# Цвета для вывода
$Host.UI.RawUI.ForegroundColor = "Gray"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    Building GameVault.exe (Dev Mode)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function Write-Success {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "  [INFO] $Message" -ForegroundColor Cyan
}

function Write-Warning {
    param([string]$Message)
    Write-Host "  [WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "  [ERROR] $Message" -ForegroundColor Red
}

function Clean-Build {
    Write-Host "Cleaning temporary build files..." -ForegroundColor Yellow
    
    $paths = @("dist", "build", "__pycache__")
    foreach ($path in $paths) {
        if (Test-Path $path) {
            Remove-Item -Recurse -Force $path -ErrorAction SilentlyContinue
            Write-Success "Removed: $path"
        }
    }
    
    if (Test-Path "GameVault.spec") {
        Remove-Item -Force "GameVault.spec" -ErrorAction SilentlyContinue
        Write-Success "Removed: GameVault.spec"
    }
    
    Get-ChildItem -Path . -Directory -Recurse -Include '__pycache__' | ForEach-Object {
        Remove-Item -Recurse -Force $_.FullName -ErrorAction SilentlyContinue
        Write-Success "Removed cache: $($_.FullName)"
    }
    
    Write-Host "[OK] Clean completed (user data preserved)" -ForegroundColor Green
}

# Принудительно закрываем старый процесс
$processName = "GameVault"
$process = Get-Process -Name $processName -ErrorAction SilentlyContinue
if ($process) {
    Write-Host "Closing running GameVault.exe..." -ForegroundColor Yellow
    Stop-Process -Name $processName -Force
    Start-Sleep -Seconds 2
    Write-Success "Closed old process"
    Write-Host ""
}

if ($Clean) {
    Clean-Build
}

Write-Host "Checking Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python not found!"
    Write-Info "Download from: https://www.python.org/downloads/"
    pause
    exit 1
}
Write-Success "$pythonVersion"
Write-Host ""

# Определяем версию Python
$pythonMajor = $pythonVersion -replace 'Python (\d+)\.(\d+).*', '$1'
$pythonMinor = $pythonVersion -replace 'Python (\d+)\.(\d+).*', '$2'

Write-Info "Python version: $pythonMajor.$pythonMinor"
Write-Host ""

# Выбираем совместимую версию PyInstaller
$pyinstallerVersion = "6.11.1"

Write-Host "Checking project files..." -ForegroundColor Yellow
$requiredFiles = @(
    "main.py",
    "core\__init__.py",
    "core\crypto.py",
    "core\database.py",
    "core\email_sender.py",
    "core\cloud_storage.py",
    "core\logger.py",
    "gui\__init__.py",
    "gui\login_dialog.py",
    "gui\main_window.py",
    "gui\add_account.py",
    "gui\settings.py",
    "gui\backups.py",
    "gui\cloud_backups.py",
    "gui\password_dialog.py"
)

$allFilesOk = $true
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Error "Missing: $file"
        $allFilesOk = $false
    }
}

if (-not $allFilesOk) {
    Write-Host ""
    Write-Error "Some project files are missing!"
    pause
    exit 1
}
Write-Success "All project files found"
Write-Host ""

Write-Host "Checking user data..." -ForegroundColor Yellow
$userFiles = @("vault.dat", "vault.salt", "vault.cfg")
$hasUserData = $false
foreach ($file in $userFiles) {
    if (Test-Path $file) {
        Write-Success "$file found"
        $hasUserData = $true
    } else {
        Write-Info "$file (will be created on first run)"
    }
}

if (-not $hasUserData) {
    Write-Info "User data files will be created on first program launch"
}
Write-Host ""

Write-Host "Installing dependencies..." -ForegroundColor Yellow

$packages = @(
    @{name="PyQt6"; version="6.5.0"},
    @{name="cryptography"; version="41.0.0"},
    @{name="pyinstaller"; version=$pyinstallerVersion}
)

foreach ($pkg in $packages) {
    Write-Host "  Installing $($pkg.name)..." -ForegroundColor Gray
    
    $installed = pip list --format=json | ConvertFrom-Json | Where-Object { $_.name -eq $pkg.name }
    
    if ($installed -and $installed.version -eq $pkg.version) {
        Write-Success "$($pkg.name) $($pkg.version) already installed"
    } else {
        pip install "$($pkg.name)==$($pkg.version)" --quiet
        if ($LASTEXITCODE -eq 0) {
            Write-Success "$($pkg.name) installed"
        } else {
            Write-Error "Failed to install $($pkg.name)"
            pause
            exit 1
        }
    }
}

Write-Host ""
Write-Success "Dependencies installed!"
Write-Host ""

Write-Host "Building GameVault.exe..." -ForegroundColor Yellow
Write-Info "EXE will be created in: $PWD\GameVault.exe"
Write-Info "User data files will remain untouched"
Write-Host ""

$pyinstallerArgs = @(
    "--onefile",
    "--name", "GameVault",
    "--windowed",
    "--distpath", ".",
    "--workpath", "build",
    "--specpath", ".",
    "--additional-hooks-dir", "hooks",
    "--hidden-import", "PyQt6.sip",
    "--hidden-import", "sip",
    "--add-data", "core;core",
    "--add-data", "gui;gui",
    "--hidden-import", "PyQt6",
    "--hidden-import", "PyQt6.QtCore",
    "--hidden-import", "PyQt6.QtWidgets",
    "--hidden-import", "PyQt6.QtGui",
    "--hidden-import", "cryptography",
    "--hidden-import", "cryptography.fernet",
    "--hidden-import", "cryptography.hazmat.primitives",
    "--hidden-import", "cryptography.hazmat.backends.openssl",
    "--hidden-import", "core",
    "--hidden-import", "core.crypto",
    "--hidden-import", "core.database",
    "--hidden-import", "core.email_sender",
    "--hidden-import", "core.cloud_storage",
    "--hidden-import", "core.logger",
    "--hidden-import", "gui",
    "--hidden-import", "gui.login_dialog",
    "--hidden-import", "gui.main_window",
    "--hidden-import", "gui.add_account",
    "--hidden-import", "gui.settings",
    "--hidden-import", "gui.backups",
    "--hidden-import", "gui.cloud_backups",
    "--hidden-import", "gui.password_dialog",
    "--hidden-import", "email.mime",
    "--hidden-import", "email.mime.text",
    "--hidden-import", "email.mime.multipart",
    "--hidden-import", "email.mime.base",
    "--hidden-import", "email.encoders",
    "--hidden-import", "smtplib",
    "--hidden-import", "imaplib",
    "--hidden-import", "threading",
    "--hidden-import", "time",
    "--hidden-import", "json",
    "--hidden-import", "base64",
    "--hidden-import", "random",
    "--hidden-import", "string",
    "--hidden-import", "datetime",
    "--hidden-import", "os",
    "--hidden-import", "sys",
    "main.py"
)

$buildOutput = pyinstaller @pyinstallerArgs 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Error "Build failed!"
    Write-Host ""
    Write-Warning "Possible solutions:"
    Write-Info "  1. Try updating pip: python -m pip install --upgrade pip"
    Write-Info "  2. Try installing the latest PyInstaller: pip install pyinstaller"
    Write-Info "  3. Check if all dependencies are installed correctly"
    Write-Host ""
    Write-Host $buildOutput -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    BUILD COMPLETED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path "GameVault.exe") {
    $exeFile = Get-ChildItem "GameVault.exe"
    $sizeMB = [math]::Round($exeFile.Length / 1MB, 2)
    
    Write-Success "EXE created: $($exeFile.FullName)"
    Write-Success "Size: $sizeMB MB"
    Write-Host ""
    
    Write-Host "User data files:" -ForegroundColor Yellow
    foreach ($file in @("vault.dat", "vault.salt", "vault.cfg")) {
        if (Test-Path $file) {
            $size = (Get-ChildItem $file).Length
            Write-Success "$file ($size bytes)"
        } else {
            Write-Info "$file (will be created on first run)"
        }
    }
    
    Write-Host ""
    Write-Info "Run: .\GameVault.exe"
    Write-Info "     (user data files are in the same folder)"
} else {
    Write-Error "GameVault.exe not found!"
}

Write-Host ""
pause