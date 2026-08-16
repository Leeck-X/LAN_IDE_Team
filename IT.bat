@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title LAN C++26 IDE Setup

:: 记录初始目录
set "ROOT=%~dp0"
cd /d "%ROOT%"

echo ==========================================
echo   LAN C++26 IDE - One-click Setup
echo ==========================================
echo.

:: ---------- 1. 创建目录结构 ----------
echo [1/4] Creating project structure...
mkdir workspace 2>nul
mkdir templates 2>nul
mkdir static 2>nul
mkdir static\monaco 2>nul
mkdir static\monaco\vs 2>nul
echo   [OK] Directories created.
echo.

:: ---------- 2. 安装 Python 依赖 ----------
echo [2/4] Installing Python dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install flask flask-socketio >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Dependencies installed.
) else (
    echo   [WARN] pip install failed. Please run: pip install flask flask-socketio
)
echo.

:: ---------- 3. 下载静态资源 ----------
echo [3/4] Downloading static assets...
call :download_socketio
call :download_monaco
echo.

:: ---------- 4. 创建占位文件 ----------
echo [4/4] Creating placeholder files...
if not exist server.py type nul > server.py
if not exist templates\index.html type nul > templates\index.html
echo   [OK] Placeholder files created.
echo.

echo ==========================================
echo   Setup complete!
echo.
echo   Next steps:
echo     1. Open server.py and paste the backend code.
echo     2. Open templates\index.html and paste the frontend code.
echo     3. Run: python server.py
echo ==========================================
pause
exit /b 0

:: ===================== 子例程 =====================

:download_socketio
echo   - Downloading socket.io.min.js...
curl -L -o static\socket.io.min.js https://cdn.jsdelivr.net/npm/socket.io-client@4.7.5/dist/socket.io.min.js >nul 2>&1
if exist static\socket.io.min.js (
    echo     [OK] socket.io.min.js downloaded.
) else (
    echo     [FAIL] Failed to download socket.io.min.js.
)
goto :eof

:download_monaco
echo   - Downloading Monaco Editor 0.52.2...
:: 使用 jsDelivr 下载完整 min/vs 打包（zip 格式）
set "MONACO_ZIP=static\monaco\vs.zip"
curl -L -o "%MONACO_ZIP%" "https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs.zip" >nul 2>&1
if exist "%MONACO_ZIP%" (
    echo     [OK] Monaco package downloaded.
    echo     - Extracting Monaco Editor...
    powershell -Command "Expand-Archive -Path '%MONACO_ZIP%' -DestinationPath 'static\monaco\vs' -Force" >nul 2>&1
    if %errorlevel% equ 0 (
        echo     [OK] Monaco Editor extracted.
        del /Q "%MONACO_ZIP%" >nul 2>&1
    ) else (
        echo     [WARN] Extraction failed. Please manually download and extract min/vs to static\monaco\vs.
    )
) else (
    echo     [FAIL] Failed to download Monaco package. Check your internet connection.
)
goto :eof