$ErrorActionPreference = "Stop"

$distDir = "dist"
$packageName = "gtaol-dre-helper"
$packageDirName = "$packageName-pyinstaller"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
. (Join-Path $scriptDir "build-common.ps1")

Assert-VenvReady
Assert-TesseractReady

Invoke-Step { uv sync --group dev --frozen }

Write-Host "Building $packageName with PyInstaller..."
Invoke-Step {
    uv run pyinstaller `
        --noconfirm `
        --clean `
        --onefile `
        --console `
        --name $packageName `
        --add-data "gtaol_dre_helper\style.scss;gtaol_dre_helper" `
        main.py
}

Write-Host "Building RegionLocator..."
Compile-RegionLocator -OutputPath "dist\RegionLocator.exe"

Write-Host "Packaging application files..."

$packageDir = Join-Path $distDir $packageDirName
if (Test-Path $packageDir) {
    Remove-Item -Path $packageDir -Recurse -Force
}

New-Item -Path $packageDir -ItemType Directory -Force | Out-Null
Move-Item -Path "dist\$packageName.exe" -Destination $packageDir -Force
Move-Item -Path "dist\RegionLocator.exe" -Destination $packageDir -Force
Copy-Item -Path "config.example.yaml" -Destination (Join-Path $packageDir "config.example.yaml") -Force
Copy-Item -Path "tesseract" -Destination (Join-Path $packageDir "tesseract") -Recurse -Force

$archiveFileName = "$packageDirName.7z"
Invoke-Create7ZipArchive -DistDir $distDir -ArchiveFileName $archiveFileName -SourcePath $packageDirName


Write-Host ""
Write-Host "PyInstaller build finished"
