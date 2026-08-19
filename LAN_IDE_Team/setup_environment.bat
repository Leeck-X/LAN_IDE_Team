@echo off
setlocal enabledelayedexpansion
title LAN C++26 IDE - Environment Setup
cd /d "%~dp0"

echo ============================================================
echo   LAN C++26 IDE - Environment Setup
echo ============================================================
echo.

set "FAILED=0"

:: ---------- 1. Check Python ----------
echo [1/6] Checking Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo   [X] Python not found. Please install Python 3.9+ :
    echo       https://www.python.org/downloads/
    echo       (Remember to check "Add Python to PATH")
    set "FAILED=1"
) else (
    for /f "delims=" %%v in ('python --version 2^>^&1') do echo   [OK] %%v
)
echo.

:: ---------- 2. Install Python dependencies ----------
echo [2/6] Installing Python dependencies...
python -m pip install --quiet --upgrade pip >nul 2>&1
python -m pip install --quiet flask flask-socketio psutil >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] flask / flask-socketio / psutil installed.
) else (
    echo   [X] pip install failed. Run manually:
    echo       pip install flask flask-socketio psutil
    set "FAILED=1"
)
echo.

:: ---------- 3. Create directories ----------
echo [3/6] Creating directories...
mkdir workspace 2>nul
mkdir tools\clangd 2>nul
mkdir static\monaco 2>nul
mkdir static\monaco\vs 2>nul
echo   [OK] workspace / tools\clangd / static\monaco ready.
echo.

:: ---------- 4. Download socket.io ----------
echo [4/6] Downloading socket.io client...
if exist static\socket.io.min.js (
    echo   [OK] socket.io.min.js already present, skip.
) else (
    echo   - Downloading from jsDelivr...
    curl -L --fail --retry 2 -o static\socket.io.min.js "https://cdn.jsdelivr.net/npm/socket.io-client@4.7.5/dist/socket.io.min.js" 2>nul
    if exist static\socket.io.min.js (
        echo     [OK] socket.io.min.js downloaded.
    ) else (
        echo     [X] Failed to download socket.io.min.js.
        set "FAILED=1"
    )
)
echo.

:: ---------- 5. Download Monaco Editor ----------
echo [5/6] Downloading Monaco Editor...
if exist static\monaco\vs\loader.js (
    echo   [OK] Monaco already present, skip.
) else (
    set "MONACO_ZIP=static\monaco\vs.zip"
    echo   - Downloading Monaco 0.52.2 from jsDelivr...
    curl -L --fail --retry 2 -o "%MONACO_ZIP%" "https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs.zip" 2>nul
    if exist "%MONACO_ZIP%" (
        echo   - Extracting...
        powershell -NoProfile -Command "Expand-Archive -Path '%MONACO_ZIP%' -DestinationPath 'static\monaco\vs' -Force" >nul 2>&1
        if exist static\monaco\vs\loader.js (
            echo     [OK] Monaco extracted.
            del /Q "%MONACO_ZIP%" >nul 2>&1
        ) else (
            echo     [X] Extraction failed. Manually extract min/vs to static\monaco\vs.
            set "FAILED=1"
        )
    ) else (
        echo     [X] Failed to download Monaco package.
        set "FAILED=1"
    )
)
echo.

:: ---------- 6. Download clangd ----------
echo [6/6] Downloading clangd...
if exist tools\clangd\clangd_22.1.6\bin\clangd.exe (
    echo   [OK] clangd already present, skip.
) else (
    set "CLANGD_ZIP=tools\clangd\clangd-windows-22.1.6.zip"
    echo   - Downloading clangd 22.1.6 (~50MB) from GitHub...
    echo     If this fails, use a proxy/VPN or download manually:
    echo     https://github.com/clangd/clangd/releases/download/22.1.6/clangd-windows-22.1.6.zip
    curl -L --fail --retry 2 -o "%CLANGD_ZIP%" "https://github.com/clangd/clangd/releases/download/22.1.6/clangd-windows-22.1.6.zip" 2>nul
    if exist "%CLANGD_ZIP%" (
        echo   - Extracting...
        powershell -NoProfile -Command "Expand-Archive -Path '%CLANGD_ZIP%' -DestinationPath 'tools\clangd' -Force" >nul 2>&1
        if exist tools\clangd\clangd_22.1.6\bin\clangd.exe (
            echo     [OK] clangd extracted.
            del /Q "%CLANGD_ZIP%" >nul 2>&1
        ) else (
            echo     [X] Extraction failed. Manually extract to tools\clangd\.
            set "FAILED=1"
        )
    ) else (
        echo     [X] Failed to download clangd. Manual download required.
        set "FAILED=1"
    )
)
echo.

:: ---------- Compiler check ----------
echo ------------------------------------------------------------
echo   Compiler check (compile & run C/C++ requires one of these):
where g++ >nul 2>&1 && echo     [OK] g++ found
where g++ >nul 2>&1 || echo     [..] g++ NOT found (install MinGW-w64 or w64devkit)
where clang++ >nul 2>&1 && echo     [OK] clang++ found
where clang++ >nul 2>&1 || echo     [..] clang++ NOT found (install LLVM)
echo ------------------------------------------------------------
echo.

if "%FAILED%"=="1" (
    echo   Setup finished with errors. Fix the [X] items above and re-run.
) else (
    echo   All set! Start the IDE with:
    echo       python server.py
    echo   Then open http://localhost:5000
)
echo.
pause
exit /b 0
