@echo off
echo ==========================================
echo      BUILDING PYOBD DASHBOARD EXE
echo ==========================================

REM 1. Activate the Virtual Environment
if exist ".venv\Scripts\activate.bat" (
    echo Activating Virtual Environment...
    call .venv\Scripts\activate.bat
) else (
    echo WARNING: .venv not found. Trying global Python...
)

REM 2. Ensure PyInstaller is actually installed
echo Checking for PyInstaller...
pip install pyinstaller

REM 3. Clean previous builds (Quietly)
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

REM 4. Get CustomTkinter Location
echo Locating CustomTkinter...
for /f "delims=" %%i in ('python -c "import customtkinter; print(customtkinter.__path__[0])"') do set CTK_PATH=%%i

REM 5. Run PyInstaller
echo Starting Build Process...
echo ------------------------------------------

REM Check if icon exists, otherwise build without it
if exist "app_icon.ico" (
    pyinstaller --noconsole --onefile ^
        --name="PyOBD_Pro" ^
        --icon="app_icon.ico" ^
        --add-data "%CTK_PATH%;customtkinter/" ^
        --hidden-import "serial" ^
        --hidden-import "PIL._tkinter_finder" ^
        src/main.py
) else (
    echo WARNING: app_icon.ico not found. Building with default icon.
    pyinstaller --noconsole --onefile ^
        --name="PyOBD_Pro" ^
        --add-data "%CTK_PATH%;customtkinter/" ^
        --hidden-import "serial" ^
        --hidden-import "PIL._tkinter_finder" ^
        src/main.py
)

echo.
echo ==========================================
echo      BUILD FINISHED!
echo ==========================================
echo If successful, your app is in the 'dist' folder.
pause