@echo off
echo Building ProductivityTracker.exe...

REM Kill any running instances
echo Checking for running instances...
tasklist | findstr /I ProductivityTracker.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo Killing running ProductivityTracker instances...
    taskkill /F /IM ProductivityTracker.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
)

REM Create dist directory if it doesn't exist
if not exist "dist" mkdir dist

REM Store the old exe timestamp for comparison
set OLD_TIME=0
if exist "dist\ProductivityTracker.exe" (
    for %%f in ("dist\ProductivityTracker.exe") do set OLD_TIME=%%~tf
)

REM Install PyInstaller if not already installed
pip install pyinstaller >nul 2>&1

REM Build the executable with all required files
pyinstaller --onefile ^
    --windowed ^
    --name ProductivityTracker ^
    --icon=icon.ico ^
    --add-data "icon.ico;." ^
    --add-data "viewer.html;." ^
    --distpath dist ^
    --clean ^
    productivity_tracker.py

echo.

REM Check if build was successful by comparing timestamps
set NEW_TIME=0
if exist "dist\ProductivityTracker.exe" (
    for %%f in ("dist\ProductivityTracker.exe") do set NEW_TIME=%%~tf
)

if "%OLD_TIME%" neq "%NEW_TIME%" (
    echo SUCCESS: ProductivityTracker.exe built successfully!
    echo Location: %cd%\dist\ProductivityTracker.exe
    echo.
    echo To test: cd dist && ProductivityTracker.exe
) else (
    echo ERROR: Build failed. The exe was not updated.
    echo Check output above for errors.
)

REM Clean up build artifacts
if exist "build" rmdir /s /q build
if exist "ProductivityTracker.spec" del ProductivityTracker.spec

pause 