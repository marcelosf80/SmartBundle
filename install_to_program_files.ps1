# install_to_program_files.ps1
# Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"

$AppName = "SmartBundle"
$InstallDir = "C:\Program Files\$AppName"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   INSTALADOR DE SMARTBUNDLE PRO (WINDOWS 10 / 11)       " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Crear carpeta en C:\Program Files\SmartBundle
Write-Host "`n[1/5] Creando directorio de instalacion: $InstallDir..." -ForegroundColor Green
if (!(Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# 2. Copiar ejecutables y archivos del programa
Write-Host "[2/5] Copiando binarios y recursos..." -ForegroundColor Green
$DistDir = Join-Path $ScriptDir "dist\SmartBundle"

if (Test-Path $DistDir) {
    Copy-Item -Path "$DistDir\*" -Destination $InstallDir -Recurse -Force
} else {
    # Fallback copiar archivos fuente y scripts
    Copy-Item -Path "$ScriptDir\*" -Destination $InstallDir -Recurse -Force
}

# Asegurar que el icono este presente
$IconPath = Join-Path $InstallDir "app_icon.ico"
if (!(Test-Path $IconPath) -and (Test-Path "$ScriptDir\app_icon.ico")) {
    Copy-Item -Path "$ScriptDir\app_icon.ico" -Destination $IconPath -Force
}

# 3. Registrar accesos directos
Write-Host "[3/5] Creando accesos directos (Escritorio y Menu Inicio)..." -ForegroundColor Green
$WshShell = New-Object -ComObject WScript.Shell
$ExePath = Join-Path $InstallDir "SmartBundle.exe"

if (!(Test-Path $ExePath)) {
    $ExePath = Join-Path $InstallDir "sb_gui.py"
}

# Acceso directo Escritorio
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutDesktop = $WshShell.CreateShortcut("$DesktopPath\SmartBundle.lnk")
$ShortcutDesktop.TargetPath = $ExePath
$ShortcutDesktop.IconLocation = "$IconPath,0"
$ShortcutDesktop.Description = "SmartBundle Pro - Archivador & Compresor"
$ShortcutDesktop.Save()

# Acceso directo Menu Inicio
$StartMenuDir = "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\SmartBundle"
if (!(Test-Path $StartMenuDir)) {
    New-Item -ItemType Directory -Path $StartMenuDir -Force | Out-Null
}
$ShortcutStart = $WshShell.CreateShortcut("$StartMenuDir\SmartBundle.lnk")
$ShortcutStart.TargetPath = $ExePath
$ShortcutStart.IconLocation = "$IconPath,0"
$ShortcutStart.Description = "SmartBundle Pro"
$ShortcutStart.Save()

# 4. Registrar Menu Contextual estilo WinRAR
Write-Host "[4/5] Registrando menu contextual estilo WinRAR en el Explorador..." -ForegroundColor Green
$ContextScript = Join-Path $InstallDir "sb_context_menu.py"
if (Test-Path $ContextScript) {
    python $ContextScript
} else {
    python "$ScriptDir\sb_context_menu.py"
}

# 5. Generar Desinstalador
Write-Host "[5/5] Creando script de desinstalacion..." -ForegroundColor Green
$UninstallScript = @"
@echo off
title Desinstalador de SmartBundle
echo Solicitando permisos de administrador...
net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo Eliminando menu contextual...
python "$InstallDir\sb_context_menu.py" uninstall

echo Eliminando accesos directos...
del "%PUBLIC%\Desktop\SmartBundle.lnk" >nul 2>&1
del "$DesktopPath\SmartBundle.lnk" >nul 2>&1
rmdir /s /q "$StartMenuDir" >nul 2>&1

echo Eliminando archivos de C:\Program Files\SmartBundle...
cd /d "C:\Program Files"
rmdir /s /q "$InstallDir"

echo [OK] SmartBundle desinstalado correctamente.
pause
"@

Set-Content -Path (Join-Path $InstallDir "Desinstalar.bat") -Value $UninstallScript -Encoding ASCII

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " [EXITO] SMARTBUNDLE PRO INSTALADO EN C:\Program Files" -ForegroundColor Yellow
Write-Host " El menu contextual estilo WinRAR ya esta activo." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
