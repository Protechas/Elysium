# Stops stale Flow dev server processes and releases server.log locks.
param(
    [string]$FlowDir = (Join-Path $env:USERPROFILE "Documents\Elysium\Flow")
)

$ErrorActionPreference = "SilentlyContinue"

$LauncherDir = Join-Path $FlowDir "launcher"
$LogDir = Join-Path $LauncherDir "logs"
$ServerLog = Join-Path $LogDir "server.log"
$PidFile = Join-Path $LogDir "server.pid"
$Port = 3000

if (-not (Test-Path $LauncherDir)) {
    exit 0
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if (Test-Path $PidFile) {
    $savedPid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($savedPid) {
        Stop-Process -Id $savedPid -Force -ErrorAction SilentlyContinue
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

for ($i = 0; $i -lt 6; $i++) {
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if (-not $conn) { break }
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
}

$flowPattern = [regex]::Escape($FlowDir)
Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -and (
            ($_.CommandLine -match $flowPattern -and $_.Name -in @('node.exe', 'cmd.exe')) -or
            $_.CommandLine -like '*launch-flow.ps1*' -or
            $_.CommandLine -like '*launch-flow.vbs*'
        )
    } |
    ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }

Start-Sleep -Milliseconds 500

if (Test-Path $ServerLog) {
    Remove-Item $ServerLog -Force -ErrorAction SilentlyContinue
}

exit 0
