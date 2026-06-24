# Elysium 1.5

ELYSIUM is a Windows launcher GUI that updates and runs custom programs developed by Protech Automotive Solutions.

**Version 1.5** adds manifest-driven apps, dual-path install support, rotating logs, visible diagnostics, and the `elysium/` service package for Elysium 2.

## System requirements

- Windows 10 or Windows 11 (64-bit)
- Python 3.10 or newer (3.11 recommended) — **not required** if using the rebuilt `ELYSIUM.exe` (embedded Python)
- Git for Windows (for downloading and updating programs)
- Internet access (GitHub, PyPI)
- Node.js (only required to run the **Flow** program)

## How to launch (recommended)

1. Install [Python](https://www.python.org/downloads/) and check **Add python.exe to PATH** during setup.
2. Install [Git for Windows](https://git-scm.com/download/win).
3. Double-click **`LaunchElysium.bat`** in this repository folder.

The launcher will:

- Find a working Python installation
- Clone or update ELYSIUM into your active install directory (legacy `%USERPROFILE%\Documents\Elysium` or new `%LOCALAPPDATA%\Protech\Elysium`)
- Install required Python packages if missing
- Start the ELYSIUM GUI

### Alternative launch methods

**PowerShell:**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\launcher\LaunchElysium.ps1"
```

**Manual (for debugging):**

```powershell
cd $env:USERPROFILE\Documents\Elysium
python -u ELYSIUM.py
```

If `python` is not found, try:

```powershell
py -3.11 -u ELYSIUM.py
```

## Python dependencies

Install manually if needed:

```powershell
pip install -r requirements.txt
```

Packages: `PyQt5`, `requests`, `openpyxl`, `setuptools`, `platformdirs`, `pydantic`, `pyyaml`

## Building / replacing ELYSIUM.exe

The legacy Desktop `ELYSIUM.exe` (April 2024) is a frozen PyInstaller build that uses outdated startup code (`where git`, old error handling). **Replace it** with a new build from this repo:

```powershell
.\build.ps1
```

This creates `dist\ELYSIUM.exe`, which:

1. Shows "Starting ELYSIUM..."
2. Closes stale ELYSIUM / Flow processes
3. Git-pulls the latest code into your resolved Elysium base directory
4. Installs Python packages into the embedded runtime
5. Runs `ELYSIUM.py` from the resolved install path (always the latest git version)

### Diagnostics (1.5+)

The main window includes **Logs** and **Export Diagnostics** buttons. Export creates a zip with logs, settings, manifest, and system info under `logs/`.

### Per-app isolated environments (optional)

Enable in `settings.json`:

```json
{
  "use_isolated_envs": true,
  "isolated_env_apps": ["dfr"]
}
```

When enabled, DFR launches from an isolated venv at `%LOCALAPPDATA%\Protech\Elysium\envs\dfr\`.

Distribute `dist\ELYSIUM.exe` to users in place of the old Desktop executable.

### Alternative: LaunchElysium.bat

For development or when a system Python install is preferred, use **`LaunchElysium.bat`** instead of the EXE.

## Building the EXE launcher (legacy note)

`build.ps1` now outputs **`ELYSIUM.exe`** directly (not `ElysiumLauncher.exe`).

## Troubleshooting

### Git executable not found / `where git` failed

Git is installed on many PCs but not on PATH. ELYSIUM now searches common install locations (`C:\Program Files\Git\cmd`) and the Windows registry automatically.

If you still see this error:

1. Install Git from https://git-scm.com/download/win (choose **Add Git to PATH**)
2. Use **`LaunchElysium.bat`** instead of an older external EXE — the new launcher can install Git silently or launch an existing copy of ELYSIUM without Git
3. Restart your PC after installing Git so PATH updates apply

### WinError 32 — log file locked by another process

This happens when two ELYSIUM windows are open, a previous instance did not close cleanly, or a **Flow** dev server is still running in the background.

1. Close all ELYSIUM windows (check Task Manager for leftover `python.exe` / `node.exe` processes)
2. Run **`LaunchElysium.bat`** again — it now stops stale Flow servers and releases `Flow\launcher\logs\server.log` automatically
3. ELYSIUM will continue with console logging if its own log file is still locked

### Flow fails with server.log / Initialization Error

Flow's dev server writes to `%USERPROFILE%\Documents\Elysium\Flow\launcher\logs\server.log`. If a previous Flow session is still running, the new launch fails with WinError 32.

ELYSIUM now stops stale Flow processes before launching Flow and patches the Flow launcher after each update. Pull the latest ELYSIUM and relaunch via your executable or `LaunchElysium.bat`.

### Console flashes and closes immediately

This usually means an uncaught startup error.

1. Run **`LaunchElysium.bat`** from Command Prompt (not double-click) so the window stays open.
2. Or run manually:
   ```powershell
   cd $env:USERPROFILE\Documents\Elysium
   python -u ELYSIUM.py
   ```
3. Check log files:
   - `%USERPROFILE%\Documents\Elysium\logs\launcher_error.log`
   - `%USERPROFILE%\Documents\Elysium\logs\elysium_crash.log`
   - `%USERPROFILE%\Documents\Elysium\logs\dependency_log_*.log`

Inside ELYSIUM, press **Shift+F9** to reveal the **View Dependency Logs** button.

### Python not found

- Reinstall Python from https://www.python.org/downloads/
- Enable **Add python.exe to PATH**
- Avoid the Microsoft Store Python stub; install from python.org

### Git errors on startup

Install Git from https://git-scm.com/download/win and restart the launcher.

### Corporate networks / pip failures

If package install fails behind a proxy or SSL inspection, run pip manually with trusted hosts:

```powershell
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Flow won't launch

Install Node.js from https://nodejs.org and restart ELYSIUM.

## Data locations

| Path | Purpose |
|------|---------|
| `%USERPROFILE%\Documents\Elysium\` | Cloned programs and ELYSIUM install |
| `%USERPROFILE%\Documents\Elysium\logs\` | Crash, launcher, and dependency logs |

## Managed programs

DFR, SI MultiTool, Hyper, Analyzer+, SI Op Manager, Flow, SmartSplit, and Combiner are cloned from GitHub into `Documents\Elysium` and updated automatically on startup.
