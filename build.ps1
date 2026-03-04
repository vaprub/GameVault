# build.ps1 – скрипт сборки с PyInstaller
# Запускать из корневой папки проекта

# Убедитесь, что PyInstaller установлен: pip install pyinstaller

$name = "GameVault"
$icon = "icon.ico"  # если есть файл иконки, иначе уберите --icon

$pyinstallerArgs = @(
    "--onefile",
    "--windowed",
    "--name", $name,
    "--add-data", "core;core",
    "--add-data", "gui;gui"
)

if (Test-Path $icon) {
    $pyinstallerArgs += "--icon", $icon
}

pyinstaller $pyinstallerArgs main.py

Write-Host "Сборка завершена. Исполняемый файл находится в папке dist/$name.exe"
