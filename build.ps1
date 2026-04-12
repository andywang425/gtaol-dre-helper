$ErrorActionPreference = "Stop"

$distDir = "dist"
$packageName = "gtaol-dre-helper"
$sevenZipExe = Get-Command "7z" -ErrorAction SilentlyContinue

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Virtual environment not found at .venv\Scripts\python.exe" -ForegroundColor Red
    Write-Host "Please create and sync the virtual environment before building." -ForegroundColor Yellow
    exit 1
}

Invoke-Step { uv sync --group dev --frozen }

Write-Host "Building $packageName..."
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
Invoke-Step { gcc -Wall -Wextra -O2 "RegionLocator.c" -o "dist\RegionLocator.exe" }

Write-Host "Packaging application files..."

$packageDir = Join-Path $distDir $packageName
if (Test-Path $packageDir) {
    Remove-Item -Path $packageDir -Recurse -Force
}
New-Item -Path $packageDir -ItemType Directory -Force | Out-Null
Move-Item -Path "dist\$packageName.exe" -Destination $packageDir -Force
Move-Item -Path "dist\RegionLocator.exe" -Destination $packageDir -Force
Copy-Item -Path "config.example.yaml" -Destination (Join-Path $packageDir "config.yaml") -Force
Copy-Item -Path "tesseract" -Destination (Join-Path $packageDir "tesseract") -Recurse -Force

if ($null -eq $sevenZipExe) {
    Write-Host "7-Zip not found in PATH" -ForegroundColor Red
    exit 1
}

$archiveFileName = "$packageName.7z"
$archivePath = Join-Path $distDir $archiveFileName
if (Test-Path $archivePath) {
    Remove-Item -Path $archivePath -Force
}

Write-Host "Creating 7z archive..."
Invoke-Step {
    Push-Location $distDir
    try {
        & $sevenZipExe.Source a -t7z -m0=lzma2 -mx=9 -md=256m -mfb=273 -ms=on $archiveFileName $packageName
    }
    finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "Build finished"
