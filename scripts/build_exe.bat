@echo off
echo ========================================
echo Building GroundParam.exe
echo ========================================
echo.

REM Move to project root
cd /d "%~dp0\.."
echo Working directory: %CD%
echo.

REM Activate virtual environment if exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo Warning: Virtual environment not found
)

echo.
echo Installing required packages...
python -m pip install --upgrade pip
pip install pyinstaller pillow

echo.
echo Converting PNG to ICO...
python scripts\convert_icon.py

echo.
echo Building single executable with PyInstaller...
pyinstaller --clean GroundParam.spec

echo.
if exist "dist\GroundParam.exe" (
    echo ========================================
    echo Build SUCCESSFUL!
    echo ========================================
    echo.
    echo Executable: dist\GroundParam.exe
    echo.
    echo NOTE: No .env file needed — credentials
    echo       are embedded in the executable.
) else (
    echo ========================================
    echo Build FAILED — check errors above
    echo ========================================
)
echo.
pause
