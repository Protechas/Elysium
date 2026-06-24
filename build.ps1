# Build ELYSIUM.exe — git-pull bootstrap that runs Documents\Elysium\ELYSIUM.py
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

Write-Host "Installing PyInstaller..."
python -m pip install --upgrade pyinstaller
python -m pip uninstall pathlib -y 2>$null

Write-Host "Building ELYSIUM.exe..."
python -m PyInstaller --noconfirm launcher\ElysiumLauncher.spec

$OutputExe = Join-Path $RepoRoot "dist\ELYSIUM.exe"
if (Test-Path $OutputExe) {
    Write-Host ""
    Write-Host "Build complete: $OutputExe" -ForegroundColor Green
    Write-Host ""
    Write-Host "Replace the legacy Desktop ELYSIUM.exe with this new build."
    Write-Host "The new EXE git-pulls the latest ELYSIUM.py and runs it using embedded Python."
} else {
    Write-Error "Build failed - dist\ELYSIUM.exe was not created."
}
