@echo off
echo Building ProductivityTracker.exe...

REM Create dist directory if it doesn't exist
if not exist "dist" mkdir dist

REM Install PyInstaller if not already installed
pip install pyinstaller

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
if exist "dist\ProductivityTracker.exe" (
    echo SUCCESS: ProductivityTracker.exe built successfully!
    echo Location: %cd%\dist\ProductivityTracker.exe
    echo.
    echo To test: cd dist && ProductivityTracker.exe
) else (
    echo ERROR: Build failed. Check output above for errors.
)

REM Clean up build artifacts
if exist "build" rmdir /s /q build
if exist "ProductivityTracker.spec" del ProductivityTracker.spec

pause 