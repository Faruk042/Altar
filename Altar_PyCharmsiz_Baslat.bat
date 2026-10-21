@echo off
cd /d "%~dp0"

REM 1. Eger derlenmis Altar.exe varsa dogrudan tek tikla calistir
if exist "dist\Altar\Altar.exe" (
    start "" "dist\Altar\Altar.exe"
    exit /b
)

REM 2. Eger bagil .venv varsa pythonw ile calistir
if exist "..\..\.venv\Scripts\pythonw.exe" (
    start "" "..\..\.venv\Scripts\pythonw.exe" "main_altar.py"
    exit /b
)

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "main_altar.py"
    exit /b
)

REM 3. Diger konumlarda powershell ile otomatik tespit et
powershell -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -Command "$py = (Get-Item '..\..\.venv\Scripts\pythonw.exe','E:\Yaz*\Python\.venv\Scripts\pythonw.exe','E:\Yazilim\Python\.venv\Scripts\pythonw.exe','.venv\Scripts\pythonw.exe' -ErrorAction SilentlyContinue).FullName; if ($py -is [array]) { $py = $py[0] }; if (-not $py) { $py = 'pythonw.exe' }; Start-Process -FilePath $py -ArgumentList 'main_altar.py' -WorkingDirectory '%~dp0'"
exit /b
