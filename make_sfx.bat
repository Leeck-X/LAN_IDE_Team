@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title LAN C++26 IDE - 自解压安装包生成器
cd /d "%~dp0"

echo ==========================================
echo   LAN C++26 IDE - 自解压安装包生成器
echo ==========================================
echo.

:: ---------- 定位 7-Zip ----------
set "SZ="
set "SFX="
if exist "%ProgramFiles%\7-Zip\7z.exe" set "SZ=%ProgramFiles%\7-Zip\7z.exe"
if exist "%ProgramFiles(x86)%\7-Zip\7z.exe" set "SZ=%ProgramFiles(x86)%\7-Zip\7z.exe"
if exist "D:\Apps\Compress\7z\7-Zip\7z.exe" set "SZ=D:\Apps\Compress\7z\7-Zip\7z.exe"
if exist "%ProgramFiles%\7-Zip\7z.sfx" set "SFX=%ProgramFiles%\7-Zip\7z.sfx"
if exist "%ProgramFiles(x86)%\7-Zip\7z.sfx" set "SFX=%ProgramFiles(x86)%\7-Zip\7z.sfx"
if exist "D:\Apps\Compress\7z\7-Zip\7z.sfx" set "SFX=D:\Apps\Compress\7z\7-Zip\7z.sfx"

if not defined SZ (
    echo [错误] 未找到 7-Zip，请先安装: https://www.7-zip.org/
    echo        安装后重新运行本脚本。
    pause
    exit /b 1
)
if not defined SFX (
    echo [错误] 未找到 7z.sfx 模块。
    pause
    exit /b 1
)

:: ---------- 检查打包产物 ----------
if not exist "dist\LAN_IDE\LAN_IDE.exe" (
    echo [错误] 未找到 dist\LAN_IDE\LAN_IDE.exe。
    echo        请先运行: python -m PyInstaller --noconfirm LAN_IDE.spec
    pause
    exit /b 1
)
if not exist "dist\LAN_IDE\tools\clangd\clangd_22.1.6\bin\clangd.exe" (
    echo [警告] dist\LAN_IDE\tools\clangd 缺失，clangd 补全将不可用。
)

echo [1/2] 压缩 dist\LAN_IDE ...
"%SZ%" a -t7z LAN_IDE.7z ".\dist\LAN_IDE\*" -m0=LZMA2 -mx=9 -y >nul

echo [2/2] 拼接自解压 exe ...
copy /b "%SFX%" + sfx_config.txt + LAN_IDE.7z LAN_IDE_Setup.exe >nul

del LAN_IDE.7z >nul 2>&1

echo.
echo ==========================================
echo   生成完成: LAN_IDE_Setup.exe
echo ==========================================
echo.
pause
exit /b 0
