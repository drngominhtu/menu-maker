@echo off
setlocal
cd /d "%~dp0"

echo ==================================================
echo   BUILD MENU MAKER - TAO FILE .EXE CHO WINDOWS
echo ==================================================
echo.
echo   Luu y: phai chay script nay TREN MAY WINDOWS.
echo   (PyInstaller khong the tao .exe Windows tu Linux/macOS.)
echo.

REM --- 1. Kiem tra Python ---
where python >nul 2>nul
if errorlevel 1 (
    echo [LOI] Khong tim thay Python.
    echo       Hay cai Python 3.10 tro len tu https://www.python.org/downloads/
    echo       va TICH CHON "Add python.exe to PATH" khi cai dat.
    echo.
    pause
    exit /b 1
)

REM --- 2. Tao moi truong ao ---
echo [1/3] Tao moi truong ao .venv ...
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 (
        echo [LOI] Tao moi truong ao that bai.
        pause
        exit /b 1
    )
)

set "PY=.venv\Scripts\python.exe"

REM --- 3. Cai thu vien ---
echo [2/3] Cai dat thu vien (Pillow + PyInstaller) ...
"%PY%" -m pip install --upgrade pip
"%PY%" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo [LOI] Cai dat thu vien that bai.
    pause
    exit /b 1
)

REM --- 4. Build file exe ---
echo [3/3] Dang build file .exe ...
REM build_exe_win.py goi PyInstaller + vá loi dis cua Python 3.10.0
"%PY%" build_exe_win.py
if errorlevel 1 (
    echo [LOI] Build that bai.
    echo       Meo: thu sua dong lenh PyInstaller phia tren thanh --console
    echo            de xem chi tiet loi.
    pause
    exit /b 1
)

echo.
echo ==================================================
echo   HOAN TAT!
echo   File exe:  dist\MenuMaker.exe
echo ==================================================
echo.
echo   - Copy file dist\MenuMaker.exe di dau cung chay duoc.
echo   - Lan dau chay, chuong trinh tu tao thu muc "data"
echo     ngay canh file exe de luu mon an va anh.
echo   - Nen dat exe trong thu muc thuong (Desktop, Documents),
echo     tranh Program Files de khong bi chan quyen ghi.
echo.
pause
