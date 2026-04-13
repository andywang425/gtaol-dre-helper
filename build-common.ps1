$ErrorActionPreference = "Stop"

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

function Assert-VenvReady {
    if (-not (Test-Path ".venv\Scripts\python.exe")) {
        Write-Host "Virtual environment not found at .venv\Scripts\python.exe" -ForegroundColor Red
        Write-Host "Please create and sync the virtual environment before building." -ForegroundColor Yellow
        exit 1
    }
}

function Assert-TesseractReady {
    $tesseractDir = "tesseract"
    $tesseractExe = Join-Path $tesseractDir "tesseract.exe"

    if (-not (Test-Path $tesseractDir -PathType Container)) {
        Write-Host "Bundled Tesseract directory not found at $tesseractDir" -ForegroundColor Red
        Write-Host "Please prepare the trimmed tesseract folder before building." -ForegroundColor Yellow
        exit 1
    }

    if (-not (Test-Path $tesseractExe -PathType Leaf)) {
        Write-Host "Bundled Tesseract executable not found at $tesseractExe" -ForegroundColor Red
        Write-Host "Please ensure tesseract.exe exists in the packaged tesseract folder." -ForegroundColor Yellow
        exit 1
    }
}

function Import-VsBuildToolsEnvironment {
    if ($script:VsDevEnvironmentLoaded) {
        return
    }

    $programFilesX86 = ${env:ProgramFiles(x86)}
    if ([string]::IsNullOrWhiteSpace($programFilesX86)) {
        Write-Host "ProgramFiles(x86) environment variable is not available." -ForegroundColor Red
        exit 1
    }

    $vswhere = Join-Path $programFilesX86 "Microsoft Visual Studio\Installer\vswhere.exe"
    if (-not (Test-Path $vswhere)) {
        Write-Host "Visual Studio Build Tools 2022 not found. Please install Build Tools with C++ support." -ForegroundColor Red
        exit 1
    }

    $installationPath = & $vswhere `
        -latest `
        -products * `
        -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
        -property installationPath

    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($installationPath)) {
        Write-Host "No compatible Visual Studio Build Tools installation with MSVC was found." -ForegroundColor Red
        exit 1
    }

    $vsDevCmd = Join-Path $installationPath "Common7\Tools\VsDevCmd.bat"
    if (-not (Test-Path $vsDevCmd)) {
        Write-Host "VsDevCmd.bat was not found under $installationPath" -ForegroundColor Red
        exit 1
    }

    $environmentLines = & cmd /s /c "`"$vsDevCmd`" -no_logo -arch=amd64 -host_arch=amd64 >nul && set"
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    foreach ($line in $environmentLines) {
        if ($line -match "^(.*?)=(.*)$") {
            [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }

    $script:VsDevEnvironmentLoaded = $true
}

function Get-ClExe {
    Import-VsBuildToolsEnvironment

    $clExe = Get-Command "cl.exe" -ErrorAction SilentlyContinue
    if ($null -eq $clExe) {
        Write-Host "MSVC compiler cl.exe is unavailable even after loading Build Tools environment." -ForegroundColor Red
        exit 1
    }

    return $clExe
}

function Compile-RegionLocator {
    param(
        [Parameter(Mandatory = $true)]
        [string]$OutputPath
    )

    $clExe = Get-ClExe
    $objectPath = [System.IO.Path]::ChangeExtension($OutputPath, ".obj")
    Invoke-Step {
        & $clExe.Source `
            /nologo `
            /O2 `
            /W4 `
            /utf-8 `
            /Fo$objectPath `
            "RegionLocator.c" `
            /link `
            /OUT:$OutputPath `
            User32.lib
    }

    if (Test-Path $objectPath) {
        Remove-Item -Path $objectPath -Force
    }
}

function Invoke-Create7ZipArchive {
    param(
        [Parameter(Mandatory = $true)]
        [string]$DistDir,

        [Parameter(Mandatory = $true)]
        [string]$ArchiveFileName,

        [Parameter(Mandatory = $true)]
        [string]$SourcePath
    )

    $sevenZipExe = Get-Command "7z" -ErrorAction SilentlyContinue
    if ($null -eq $sevenZipExe) {
        Write-Host "7-Zip not found in PATH, skipped archive creation." -ForegroundColor Yellow
        return
    }

    $archivePath = Join-Path $DistDir $ArchiveFileName
    if (Test-Path $archivePath) {
        Remove-Item -Path $archivePath -Force
    }

    Write-Host "Creating 7z archive..."
    Invoke-Step {
        Push-Location $DistDir
        try {
            & $sevenZipExe.Source a -t7z -m0=lzma2 -mx=9 -md=256m -mfb=273 -ms=on $ArchiveFileName $SourcePath
        }
        finally {
            Pop-Location
        }
    }
}
