$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

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
    Invoke-Step { uv venv }
}

Invoke-Step { uv sync --group dev --frozen }

if (Test-Path "dist") {
    Write-Host "Cleaning dist folder..."

    Get-ChildItem -Path "dist" -Directory |
    Where-Object { $_.Name -ine "tesseract" } |
    Remove-Item -Recurse -Force

    Get-ChildItem -Path "dist" -File |
    Where-Object { $_.Name -ine "tesseract.zip" } |
    Remove-Item -Force
}

Invoke-Step { uv run pyinstaller --noconfirm --clean --onefile --console --name "gtaol-ceo-helper" main.py }
Copy-Item -Path "config.example.yaml" -Destination "dist\config.yaml" -Force
Invoke-Step { uv run pyinstaller --noconfirm --clean --onefile --console --name "find_coords" find_coords.py }

$packageDir = "dist\gtaol-ceo-helper"
New-Item -Path $packageDir -ItemType Directory -Force | Out-Null
Copy-Item -Path "dist\gtaol-ceo-helper.exe" -Destination $packageDir -Force
Copy-Item -Path "dist\config.yaml" -Destination $packageDir -Force
Compress-Archive -Path $packageDir -DestinationPath "dist\gtaol-ceo-helper.zip" -Force
Remove-Item -Path $packageDir -Recurse -Force

Write-Host ""
Write-Host "Build finished"
