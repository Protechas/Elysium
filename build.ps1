# Build ElysiumLauncher.exe (bootstrap that finds Python and starts ELYSIUM)
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

Write-Host "Installing PyInstaller..."
python -m pip install --upgrade pyinstaller

Write-Host "Building ElysiumLauncher.exe..."
python -m PyInstaller --noconfirm launcher\ElysiumLauncher.spec

$OutputExe = Join-Path $RepoRoot "dist\ElysiumLauncher.exe"
if (Test-Path $OutputExe) {
    Write-Host ""
    Write-Host "Build complete: $OutputExe" -ForegroundColor Green
    Write-Host "Distribute dist\ElysiumLauncher.exe to users who prefer an EXE launcher."
} else {
    Write-Error "Build failed - dist\ElysiumLauncher.exe was not created."
}
