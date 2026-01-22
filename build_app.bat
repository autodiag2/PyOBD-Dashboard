@echo off
echo ==========================================
echo      BUILDING PYOBD SUITE (2 APPS)
echo ==========================================

REM 1. Activate venv
if exist ".venv\Scripts\activate.bat" (
    echo Activating Virtual Environment...
    call .venv\Scripts\activate.bat
) else (
    echo WARNING: .venv not found.
)

REM 2. Clean old builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

REM 3. Get CTK Path
for /f "delims=" %%i in ('python -c "import customtkinter; print(customtkinter.__path__[0])"') do set CTK_PATH=%%i

echo.
echo ------------------------------------------
echo 1. BUILDING DASHBOARD (Standard User)
echo ------------------------------------------

if exist "app_icon.ico" (
    pyinstaller --noconsole --onefile ^
        --name="PyOBD_Pro" ^
        --icon="app_icon.ico" ^
        --add-data "%CTK_PATH%;customtkinter/" ^
        --hidden-import "serial" ^
        src/main.py
) else (
    pyinstaller --noconsole --onefile ^
        --name="PyOBD_Pro" ^
        --add-data "%CTK_PATH%;customtkinter/" ^
        --hidden-import "serial" ^
        src/main.py
)

echo.
echo ------------------------------------------
echo 2. BUILDING CAN HACKER (Dev Tool)
echo ------------------------------------------

if exist "app_icon.ico" (
    pyinstaller --noconsole --onefile ^
        --name="PyCAN_Hacker" ^
        --icon="app_icon.ico" ^
        --add-data "%CTK_PATH%;customtkinter/" ^
        --hidden-import "serial" ^
        src/sniffer_main.py
) else (
    pyinstaller --noconsole --onefile ^
        --name="PyCAN_Hacker" ^
        --add-data "%CTK_PATH%;customtkinter/" ^
        --hidden-import "serial" ^
        src/sniffer_main.py
)

echo.
echo ==========================================
echo      ALL BUILDS COMPLETE!
echo ==========================================
echo Check 'dist' folder for PyOBD_Pro.exe and PyCAN_Hacker.exe
pause