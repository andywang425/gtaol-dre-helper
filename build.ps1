param(
    [ValidateSet("pyinstaller", "nuitka")]
    [string]$Backend = "nuitka"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptMap = @{
    pyinstaller = "build-pyinstaller.ps1"
    nuitka      = "build-nuitka.ps1"
}

$targetScript = Join-Path $scriptDir $scriptMap[$Backend]
if (-not (Test-Path $targetScript)) {
    Write-Host "Build backend script not found: $targetScript" -ForegroundColor Red
    exit 1
}

Write-Host "Selected backend: $Backend"
& $targetScript

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
