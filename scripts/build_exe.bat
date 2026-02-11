@echo off
echo ========================================
echo Building Geotech.exe
echo ========================================
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
pip install pyinstaller pillow reportlab

echo.
echo Converting PNG to ICO...
python convert_icon.py

echo.
echo Building executable with PyInstaller...
pyinstaller --clean Geotech.spec

echo.
echo ========================================
echo Build complete!
echo ========================================
echo.
echo Executable location: dist\Geotech.exe
echo.
pause
