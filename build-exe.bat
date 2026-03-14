@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt

if exist "dist" (
    echo Cleaning dist folder...
    for /d %%D in ("dist\*") do (
        if /I not "%%~nxD"=="tesseract" rd /s /q "%%D"
    )
    for %%F in ("dist\*") do (
        if /I not "%%~nxF"=="tesseract.zip" del /f /q "%%F"
    )
)

pyinstaller --noconfirm --clean --onefile --console --name "gtaol-ceo-helper" main.py
copy /Y "config.example.yaml" "dist\config.yaml" >nul
pyinstaller --noconfirm --clean --onefile --console --name "find_coords" tools\find_coords.py

mkdir "dist\gtaol-ceo-helper"
copy /Y "dist\gtaol-ceo-helper.exe" "dist\gtaol-ceo-helper\" >nul
copy /Y "dist\config.yaml" "dist\gtaol-ceo-helper\" >nul
powershell -NoProfile -Command "Compress-Archive -Path 'dist\gtaol-ceo-helper' -DestinationPath 'dist\gtaol-ceo-helper.zip' -Force"
rmdir /S /Q "dist\gtaol-ceo-helper"

echo.
echo Build finished
