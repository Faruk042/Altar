@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Altar EXE Paketleyici (PyInstaller)

set "PY="
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
if exist "..\.venv\Scripts\python.exe" set "PY=..\.venv\Scripts\python.exe"
if exist "..\..\.venv\Scripts\python.exe" set "PY=..\..\.venv\Scripts\python.exe"
if exist "E:\Yazilim\Python\.venv\Scripts\python.exe" set "PY=E:\Yazilim\Python\.venv\Scripts\python.exe"
if exist "E:\Yazılım\Python\.venv\Scripts\python.exe" set "PY=E:\Yazılım\Python\.venv\Scripts\python.exe"

if "%PY%"=="" set "PY=python"

echo ===================================================
echo   Altar Tam Kapsamli EXE Olusturucu (PyInstaller)
echo   Kullanilan Python: %PY%
echo ===================================================
echo.
echo [1/2] Gerekli kutuphaneler denetleniyor...
"%PY%" -m pip install -r requirements.txt
echo.
echo [2/2] PyInstaller ile Altar.exe derleniyor...
"%PY%" -m PyInstaller --noconfirm --clean Altar.spec
echo.
if exist "dist\Altar\Altar.exe" (
    echo ===================================================
    echo [BASARILI] dist\Altar\Altar.exe basariyla olusturuldu!
    echo ===================================================
) else (
    echo [HATA] EXE olusturma sirasinda bir sorun yasandi!
)
echo.
pause
