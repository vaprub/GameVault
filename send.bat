@echo off
echo ========================================
echo    GameVault - Send to GitHub
echo ========================================
echo.

:: Настройка пользователя
git config user.email "vaprub@mail.ru"
git config user.name "vaprub"

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

:: Запрашиваем комментарий (с проверкой)
:get_msg
set /p msg="Enter commit message: "
if "%msg%"=="" (
    echo Message cannot be empty!
    goto get_msg
)

:: Создаем коммит
git commit -m "%msg%"
if %errorlevel% neq 0 (
    echo Error creating commit
    pause
    exit /b 1
)
echo OK
echo.

:: Отправляем
echo Pushing to GitHub...
git push origin main
if %errorlevel% neq 0 (
    echo Error pushing to GitHub
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