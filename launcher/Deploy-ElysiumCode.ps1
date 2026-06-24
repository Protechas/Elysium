#Requires -Version 5.1
<#
.SYNOPSIS
  Copy the current dev repo into the user's Documents\Elysium install.

.DESCRIPTION
  Use this to test local QML changes with the bootstrap EXE or LaunchElysium.bat
  without pushing to GitHub. Preserves settings.json and user app folders.

  Example:
    .\launcher\Deploy-ElysiumCode.ps1
    $env:ELYSIUM_SKIP_GIT = "1"
    .\dist\ELYSIUM.exe
#>
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path (Split-Path $MyInvocation.MyCommand.Path -Parent) -Parent

function Test-ElysiumDataPresent {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return $false
    }
    $markers = @("ELYSIUM.py", "settings.json", ".git", "DFR", "Flow", "logs", "apps")
    foreach ($marker in $markers) {
        if (Test-Path (Join-Path $Path $marker)) {
            return $true
        }
    }
    return $false
}

function Get-LegacyElysiumBaseDir {
    $docs = [Environment]::GetFolderPath("MyDocuments")
    if (-not $docs) {
        $docs = Join-Path $env:USERPROFILE "Documents"
    }
    return Join-Path $docs "Elysium"
}

function Resolve-ElysiumBaseDir {
    $newBase = Join-Path $env:LOCALAPPDATA "Protech\Elysium"
    $legacyBase = Get-LegacyElysiumBaseDir

    if ((Test-ElysiumDataPresent $newBase) -and -not (Test-ElysiumDataPresent $legacyBase)) {
        return $newBase
    }
    if (Test-ElysiumDataPresent $legacyBase) {
        return $legacyBase
    }
    if (Test-ElysiumDataPresent $newBase) {
        return $newBase
    }
    if (Test-Path (Join-Path $legacyBase "ELYSIUM.py")) {
        return $legacyBase
    }
    return $newBase
}

$TargetDir = Resolve-ElysiumBaseDir
$ExcludeDirs = @(
    ".git",
    ".vs",
    ".venv",
    "venv",
    "__pycache__",
    "build",
    "dist",
    ".pytest_cache",
    "node_modules"
)

Write-Host "Deploying Elysium code"
Write-Host "  From: $RepoRoot"
Write-Host "  To:   $TargetDir"
Write-Host ""

if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

$settingsPath = Join-Path $TargetDir "settings.json"
$settingsBackup = $null
if (Test-Path $settingsPath) {
    $settingsBackup = Get-Content -Path $settingsPath -Raw -ErrorAction SilentlyContinue
}

$robocopyArgs = @(
    $RepoRoot,
    $TargetDir,
    "/E",
    "/NFL",
    "/NDL",
    "/NJH",
    "/NJS",
    "/NC",
    "/NS",
    "/NP"
)
foreach ($dir in $ExcludeDirs) {
    $robocopyArgs += "/XD"
    $robocopyArgs += (Join-Path $RepoRoot $dir)
}

& robocopy @robocopyArgs | Out-Null
$robocopyExit = $LASTEXITCODE
if ($robocopyExit -ge 8) {
    throw "robocopy failed with exit code $robocopyExit"
}

if ($settingsBackup) {
    try {
        Set-Content -Path $settingsPath -Value $settingsBackup -Encoding UTF8
        Write-Host "Restored existing settings.json"
    } catch {
        Write-Host "Warning: Could not restore settings.json"
    }
}

Write-Host ""
Write-Host "Deploy complete." -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Set `$env:ELYSIUM_SKIP_GIT = '1' to avoid git overwriting local code"
Write-Host "  2. Run dist\ELYSIUM.exe or LaunchElysium.bat"
Write-Host ""
