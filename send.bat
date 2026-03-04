@echo off
echo ========================================
echo    GameVault - Push to GitHub
echo ========================================
echo.

:: Проверяем текущую ветку
git branch --show-current > branch.txt
set /p BRANCH=<branch.txt
del branch.txt

if "%BRANCH%"=="" (
    echo Error: Cannot determine current branch
    pause
    exit /b 1
)

echo Current branch: %BRANCH%
echo.

:: Добавляем файлы
echo Adding files...
git add .
if %errorlevel% neq 0 (
    echo Error adding files
    pause
    exit /b 1
)
echo OK
echo.

:: Коммит
set /p msg="Commit message: "
if "%msg%"=="" (
    echo Message cannot be empty!
    pause
    exit /b 1
)

git commit -m "%msg%"
if %errorlevel% neq 0 (
    echo Error creating commit
    pause
    exit /b 1
)
echo OK
echo.

:: Пуш (используем текущую ветку)
echo Pushing to GitHub...
git push origin %BRANCH%
if %errorlevel% neq 0 (
    echo Error pushing
    pause
    exit /b 1
)
echo OK

echo.
echo ========================================
echo    DONE!
echo ========================================
echo.
pause