@echo off
echo ========================================
echo    Clean Build - GameVault (DEV MODE)
echo ========================================
echo.

echo Starting clean build with -Clean parameter...
echo (user data files will NOT be deleted)
echo.

powershell -NoExit -ExecutionPolicy Bypass -Command "& .\build.ps1 -Clean"

pause