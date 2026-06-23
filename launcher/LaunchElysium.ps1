#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$ElysiumRepo = "https://github.com/Protechas/Elysium.git"
$ElysiumDir = Join-Path $env:USERPROFILE "Documents\Elysium"
$LogDir = Join-Path $ElysiumDir "logs"
$LauncherLog = Join-Path $LogDir "launcher_error.log"
$RequiredPackages = @("PyQt5", "requests", "openpyxl", "setuptools")

function Write-LauncherLog {
    param([string]$Message)
    try {
        if (-not (Test-Path $LogDir)) {
            New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
        }
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Add-Content -Path $LauncherLog -Value "$timestamp - $Message"
    } catch {
        # Best effort logging
    }
}

function Show-LauncherError {
    param([string]$Title, [string]$Message)
    Write-LauncherLog "$Title : $Message"
    Write-Host ""
    Write-Host $Title -ForegroundColor Red
    Write-Host $Message
    Write-Host ""
    try {
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show($Message, $Title, [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error) | Out-Null
    } catch {
        # Console output is sufficient if WinForms is unavailable
    }
    Read-Host "Press Enter to close"
    exit 1
}

function Test-RealPython {
    param([string]$PythonExe)
    if (-not (Test-Path $PythonExe)) {
        return $false
    }
    $storeStub = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\python.exe"
    if ($PythonExe -eq $storeStub) {
        try {
            $version = & $PythonExe --version 2>&1
            if ($version -match "was not found" -or $LASTEXITCODE -ne 0) {
                return $false
            }
        } catch {
            return $false
        }
    }
    try {
        $result = & $PythonExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>&1
        return $LASTEXITCODE -eq 0 -and $result -match "^\d+\.\d+"
    } catch {
        return $false
    }
}

function Find-Python {
    $candidates = @()

    foreach ($cmd in @("py -3.11", "py -3", "python")) {
        try {
            $resolved = Get-Command ($cmd.Split(" ")[0]) -ErrorAction SilentlyContinue
            if ($resolved) {
                if ($cmd -eq "python") {
                    $candidates += "python"
                } else {
                    $candidates += $cmd
                }
            }
        } catch {}
    }

    $commonPaths = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python310\python.exe"),
        "C:\Python311\python.exe",
        "C:\Python312\python.exe",
        "C:\Program Files\Python311\python.exe",
        "C:\Program Files\Python312\python.exe"
    )
    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            $candidates += $path
        }
    }

    foreach ($candidate in $candidates) {
        if ($candidate -match " ") {
            $parts = $candidate.Split(" ", 2)
            $exe = $parts[0]
            $args = $parts[1]
            try {
                $null = & $exe $args -c "import sys; print(sys.executable)" 2>&1
                if ($LASTEXITCODE -eq 0) {
                    return @{ Command = $exe; Args = @($args) }
                }
            } catch {}
        } else {
            if (Test-RealPython $candidate) {
                return @{ Command = $candidate; Args = @() }
            }
        }
    }

    return $null
}

function Invoke-Python {
    param(
        [hashtable]$Python,
        [string[]]$ScriptArgs
    )
    $allArgs = @()
    if ($Python.Args.Count -gt 0) {
        $allArgs += $Python.Args
    }
    $allArgs += $ScriptArgs
    & $Python.Command @allArgs
    return $LASTEXITCODE
}

function Find-Git {
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if ($gitCmd) {
        return $gitCmd.Source
    }

    $candidates = @(
        "C:\Program Files\Git\cmd\git.exe",
        "C:\Program Files\Git\bin\git.exe",
        "C:\Program Files (x86)\Git\cmd\git.exe",
        "C:\Program Files (x86)\Git\bin\git.exe"
    )

    try {
        $regPath = "HKLM:\SOFTWARE\GitForWindows"
        if (Test-Path $regPath) {
            $installPath = (Get-ItemProperty $regPath).InstallPath
            if ($installPath) {
                $candidates = @(
                    (Join-Path $installPath "cmd\git.exe"),
                    (Join-Path $installPath "bin\git.exe")
                ) + $candidates
            }
        }
    } catch {}

    foreach ($path in $candidates) {
        if (Test-Path $path) {
            $gitDir = Split-Path $path -Parent
            if ($env:PATH -notlike "*$gitDir*") {
                $env:PATH = "$gitDir;$env:PATH"
            }
            return $path
        }
    }

    return $null
}

function Install-Git {
    Write-Host "Git not found. Downloading Git for Windows..."
    $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.42.0.windows.2/Git-2.42.0.2-64-bit.exe"
    $installer = Join-Path $env:TEMP "elysium_git_installer.exe"
    try {
        Invoke-WebRequest -Uri $gitUrl -OutFile $installer -UseBasicParsing
        $installArgs = @(
            "/VERYSILENT",
            "/NORESTART",
            "/NOCANCEL",
            "/SP-",
            "/CLOSEAPPLICATIONS",
            "/RESTARTAPPLICATIONS",
            '/COMPONENTS="icons,ext\reg\shellhere,assoc,assoc_sh"'
        )
        $process = Start-Process -FilePath $installer -ArgumentList $installArgs -Wait -PassThru
        if ($process.ExitCode -ne 0) {
            return $null
        }
        Start-Sleep -Seconds 3
        return Find-Git
    } catch {
        Write-LauncherLog "Git install failed: $($_.Exception.Message)"
        return $null
    } finally {
        if (Test-Path $installer) {
            Remove-Item $installer -Force -ErrorAction SilentlyContinue
        }
    }
}

function Ensure-Git {
    $gitExe = Find-Git
    if ($gitExe) {
        return $gitExe
    }

    Write-Host "Git is not on PATH. Attempting silent install..."
    $gitExe = Install-Git
    if ($gitExe) {
        Write-Host "Git installed successfully."
        return $gitExe
    }

    return $null
}

function Sync-ElysiumRepo {
    param([hashtable]$Python)

    if (-not (Test-Path $ElysiumDir)) {
        New-Item -ItemType Directory -Path $ElysiumDir -Force | Out-Null
    }

    $elysiumScript = Join-Path $ElysiumDir "ELYSIUM.py"
    $gitExe = Ensure-Git
    if (-not $gitExe) {
        if (Test-Path $elysiumScript) {
            Write-Host "Warning: Git not found. Using existing ELYSIUM installation without updating."
            return
        }
        Show-LauncherError "ELYSIUM - Git Required" @"
Git is required to download ELYSIUM but was not found and could not be installed automatically.

Install Git for Windows from:
https://git-scm.com/download/win

Then run LaunchElysium.bat again.
"@
    }

    $gitDir = Join-Path $ElysiumDir ".git"
    if (Test-Path $gitDir) {
        Write-Host "Updating ELYSIUM from GitHub..."
        Push-Location $ElysiumDir
        try {
            & $gitExe pull --ff-only 2>&1 | ForEach-Object { Write-Host $_ }
            if ($LASTEXITCODE -ne 0) {
                if (Test-Path $elysiumScript) {
                    Write-Host "Warning: git pull failed; continuing with existing ELYSIUM.py."
                    return
                }
                throw "git pull failed with exit code $LASTEXITCODE"
            }
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "Cloning ELYSIUM from GitHub..."
        $parent = Split-Path $ElysiumDir -Parent
        $folder = Split-Path $ElysiumDir -Leaf
        Push-Location $parent
        try {
            & $gitExe clone $ElysiumRepo $folder 2>&1 | ForEach-Object { Write-Host $_ }
            if ($LASTEXITCODE -ne 0) {
                throw "git clone failed with exit code $LASTEXITCODE"
            }
        } finally {
            Pop-Location
        }
    }
}

function Install-ElysiumDependencies {
    param([hashtable]$Python)

    Write-Host "Checking Python dependencies..."
    $checkScript = "import importlib; pkgs=['PyQt5.QtCore','requests','openpyxl','pkg_resources']; [importlib.import_module(p if '.' in p else p) for p in pkgs]"
    $checkCode = Invoke-Python $Python @("-c", $checkScript)
    if ($checkCode -eq 0) {
        Write-Host "All dependencies are installed."
        return
    }

    Write-Host "Installing dependencies: $($RequiredPackages -join ', ')"
    $pipArgs = @("-m", "pip", "install", "--upgrade") + $RequiredPackages
    $pipCode = Invoke-Python $Python $pipArgs
    if ($pipCode -ne 0) {
        $manual = "pip install $($RequiredPackages -join ' ')"
        Show-LauncherError "ELYSIUM - Dependency Install Failed" @"
Could not install required Python packages.

Open a terminal and run:
$manual

Log file:
$LauncherLog
"@
    }
}

function Stop-StaleFlowServer {
    $flowDir = Join-Path $ElysiumDir "Flow"
    $stopScript = Join-Path $ElysiumDir "launcher\stop-flow.ps1"
    if (Test-Path $stopScript) {
        Write-Host "Stopping any stale Flow server processes..."
        powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $stopScript -FlowDir $flowDir | Out-Null
    }
}

function Stop-OtherElysiumInstances {
    $processes = Get-CimInstance Win32_Process | Where-Object {
        ($_.CommandLine -and (
            $_.CommandLine -like '*ELYSIUM.py*' -or
            $_.CommandLine -like '*elysium_launcher.py*' -or
            $_.CommandLine -like '*ElysiumLauncher.exe*'
        )) -or $_.Name -eq 'ElysiumLauncher.exe'
    }

    foreach ($proc in $processes) {
        Write-Host "Closing existing ELYSIUM process (PID $($proc.ProcessId))..."
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
    }

    if ($processes) {
        Start-Sleep -Milliseconds 500
    }
}

try {
    Write-Host "ELYSIUM Launcher"
    Write-Host "================"
    Write-Host ""

    Stop-OtherElysiumInstances

    $python = Find-Python
    if (-not $python) {
        Show-LauncherError "ELYSIUM - Python Not Found" @"
Python 3.10+ was not found on this computer.

Install Python from:
https://www.python.org/downloads/

During installation, check ""Add python.exe to PATH"".

If you already installed Python, close this window and run LaunchElysium.bat from Command Prompt to see detailed errors.

Log file:
$LauncherLog
"@
    }

    Write-Host "Using Python: $($python.Command) $($python.Args -join ' ')"
    Sync-ElysiumRepo -Python $python
    Stop-StaleFlowServer
    Install-ElysiumDependencies -Python $python

    $elysiumScript = Join-Path $ElysiumDir "ELYSIUM.py"
    if (-not (Test-Path $elysiumScript)) {
        Show-LauncherError "ELYSIUM - Missing Script" @"
ELYSIUM.py was not found at:
$elysiumScript

The Git sync may have failed. Check your internet connection and try again.

Log file:
$LauncherLog
"@
    }

    Write-Host "Starting ELYSIUM..."
    $launchCode = Invoke-Python $python @("-u", $elysiumScript)
    if ($launchCode -ne 0) {
        $crashLog = Join-Path $LogDir "elysium_crash.log"
        Show-LauncherError "ELYSIUM - Startup Failed" @"
ELYSIUM exited with code $launchCode.

Check these log files for details:
$crashLog
$LauncherLog

You can also run this from Command Prompt:
python -u ""$elysiumScript""
"@
    }

    exit 0
} catch {
    Show-LauncherError "ELYSIUM - Launcher Error" @"
$($_.Exception.Message)

Log file:
$LauncherLog
"@
}
