$ErrorActionPreference = "Stop"

$distDir = "dist"
$buildDir = "build"
$packageName = "gtaol-dre-helper"
$packageDirName = $packageName
$packageDir = Join-Path $distDir $packageDirName
$tempBuildDir = Join-Path $buildDir $packageDirName
$archiveFileName = "$packageDirName.7z"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
. (Join-Path $scriptDir "build-common.ps1")

Assert-VenvReady
Assert-TesseractReady

Invoke-Step { uv sync --group dev --frozen }

if (Test-Path $packageDir) {
    Remove-Item -Path $packageDir -Recurse -Force
}

New-Item -Path $distDir -ItemType Directory -Force | Out-Null

Write-Host "Building $packageName with Nuitka (standalone)..."
Invoke-Step {
    uv run python -m nuitka `
        --standalone `
        --msvc=latest `
        --include-package=rich._unicode_data `
        --remove-output `
        --output-dir="$tempBuildDir" `
        --output-filename="$packageName.exe" `
        --include-data-files="gtaol_dre_helper\style.scss=gtaol_dre_helper\style.scss" `
        main.py
}

$standaloneDir = Get-ChildItem -Path $tempBuildDir -Directory -Filter "*.dist" | Select-Object -First 1
if ($null -eq $standaloneDir) {
    Write-Host "Nuitka standalone output directory was not found under $tempBuildDir" -ForegroundColor Red
    exit 1
}

Write-Host "Packaging application files..."
Move-Item -Path $standaloneDir.FullName -Destination $packageDir -Force
Copy-Item -Path "config.example.yaml" -Destination (Join-Path $packageDir "config.example.yaml") -Force
Copy-Item -Path "tesseract" -Destination (Join-Path $packageDir "tesseract") -Recurse -Force
$exampleConfigPath = Join-Path $packageDir "config.example.yaml"
Set-ItemProperty -Path $exampleConfigPath -Name IsReadOnly -Value $true

Write-Host "Building RegionLocator..."
Compile-RegionLocator -OutputPath (Join-Path $packageDir "RegionLocator.exe")
Copy-Item -Path (Join-Path $packageDir "RegionLocator.exe") -Destination . -Force

Invoke-Create7ZipArchive -DistDir $distDir -ArchiveFileName $archiveFileName -SourcePath $packageDirName

Write-Host ""
Write-Host "Nuitka build finished"
