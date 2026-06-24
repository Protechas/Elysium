"""
ELYSIUM Windows bootstrap EXE entry point.

Mirrors the legacy Desktop ELYSIUM.exe behavior:
  1. Close stale ELYSIUM / Flow processes
  2. Git sync to %USERPROFILE%\\Documents\\Elysium
  3. Install Python deps if needed
  4. Run the git-pulled ELYSIUM.py (not frozen old code)

When built with PyInstaller (frozen), uses the embedded Python runtime via
sys.executable so users do not need a separate Python install.
"""
import ctypes
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

ELYSIUM_REPO = "https://github.com/Protechas/Elysium.git"
REQUIRED_PACKAGES = [
    "PyQt5",
    "PySide6==6.6.1",
    "shiboken6==6.6.1",
    "requests",
    "openpyxl",
    "setuptools",
    "platformdirs",
    "pydantic",
    "pyyaml",
]
SPLASH_ICON_URL = (
    "https://raw.githubusercontent.com/Protechas/Elysium/main/ELYSIUM_icon.ico"
)
GIT_INSTALLER_URL = (
    "https://github.com/git-for-windows/git/releases/download/"
    "v2.42.0.windows.2/Git-2.42.0.2-64-bit.exe"
)
STORE_STUB = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Microsoft",
    "WindowsApps",
    "python.exe",
)


def _dir_has_elysium_data(path):
    if not os.path.isdir(path):
        return False
    markers = ("ELYSIUM.py", "settings.json", ".git", "DFR", "Flow", "logs", "apps")
    try:
        entries = set(os.listdir(path))
    except OSError:
        return False
    return any(marker in entries for marker in markers)


def _get_new_default_base_dir():
    local_app = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(local_app, "Protech", "Elysium")


def _get_legacy_base_dir():
    try:
        from platformdirs import user_documents_dir

        docs = user_documents_dir()
        if docs:
            return os.path.join(docs, "Elysium")
    except Exception:
        pass
    return os.path.join(os.path.expanduser("~"), "Documents", "Elysium")


def resolve_elysium_base_dir():
    """Match elysium.core.paths.resolve_base_dir() without requiring imports."""
    for base in (_get_repo_root(), _get_legacy_base_dir(), _get_new_default_base_dir()):
        if base and _try_import_paths(base):
            try:
                from elysium.core.paths import get_base_dir

                return get_base_dir()
            except ImportError:
                pass

    new_base = _get_new_default_base_dir()
    legacy_base = _get_legacy_base_dir()
    if _dir_has_elysium_data(new_base) and not _dir_has_elysium_data(legacy_base):
        return new_base
    if _dir_has_elysium_data(legacy_base):
        return legacy_base
    if _dir_has_elysium_data(new_base):
        return new_base
    if os.path.isfile(os.path.join(legacy_base, "ELYSIUM.py")):
        return legacy_base
    return new_base


def _get_repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _try_import_paths(base):
    if not os.path.isdir(os.path.join(base, "elysium")):
        return False
    if base not in sys.path:
        sys.path.insert(0, base)
    return True


def get_elysium_paths():
    base = resolve_elysium_base_dir()
    logs = os.path.join(base, "logs")
    os.makedirs(logs, exist_ok=True)
    return base, logs


def is_frozen():
    return getattr(sys, "frozen", False)


def resource_path(relative):
    if is_frozen():
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), relative)


def no_window_flags():
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)


def show_error(title, message):
    try:
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)
    except Exception:
        print(f"{title}: {message}")
    if not is_frozen():
        input("Press Enter to close...")


def write_log(message):
    try:
        _, log_dir = get_elysium_paths()
        os.makedirs(log_dir, exist_ok=True)
        launcher_log = os.path.join(log_dir, "launcher_error.log")
        with open(launcher_log, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception:
        pass


def show_starting_notice():
    try:
        ctypes.windll.user32.MessageBoxW(
            0,
            "Starting ELYSIUM...\n\nDownloading updates and preparing the launcher.",
            "ELYSIUM",
            0x40,
        )
    except Exception:
        pass


def get_python_command():
    if is_frozen():
        return [sys.executable]
    return find_python()


def close_other_elysium_instances():
    current_pid = os.getpid()
    ps_script = (
        f"$current = {current_pid}; "
        "Get-CimInstance Win32_Process | Where-Object { "
        "$_.ProcessId -ne $current -and ("
        "($_.CommandLine -and ("
        "$_.CommandLine -like '*ELYSIUM.py*' -or "
        "$_.CommandLine -like '*elysium_launcher.py*' -or "
        "$_.CommandLine -like '*ElysiumLauncher.exe*'"
        ")) -or $_.Name -in @('ElysiumLauncher.exe', 'ELYSIUM.exe')"
        ") } | ForEach-Object { "
        "Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue "
        "}"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            check=False,
            timeout=30,
            creationflags=no_window_flags(),
        )
        time.sleep(0.5)
    except Exception:
        pass


def stop_flow_server():
    elysium_dir, _ = get_elysium_paths()
    flow_dir = os.path.join(elysium_dir, "Flow")
    stop_script = os.path.join(elysium_dir, "launcher", "stop-flow.ps1")
    if not os.path.isfile(stop_script):
        stop_script = resource_path(os.path.join("launcher", "stop-flow.ps1"))
    if not os.path.isfile(stop_script):
        return

    try:
        subprocess.run(
            [
                "powershell", "-NoProfile", "-NonInteractive",
                "-ExecutionPolicy", "Bypass", "-File", stop_script,
                "-FlowDir", flow_dir,
            ],
            check=False,
            timeout=60,
            creationflags=no_window_flags(),
        )
        time.sleep(0.5)
    except Exception:
        pass


def is_real_python(python_exe):
    if not os.path.isfile(python_exe):
        return False
    try:
        result = subprocess.run(
            [python_exe, "-c", "import sys; print(sys.version_info[:2])"],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=no_window_flags(),
        )
        return result.returncode == 0 and "." in result.stdout
    except Exception:
        return False


def find_python():
    candidates = []

    for cmd in (["py", "-3.11"], ["py", "-3"], ["python"]):
        if shutil.which(cmd[0]):
            candidates.append(cmd)

    for version in ("311", "312", "310"):
        path = os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Programs",
            "Python",
            f"Python{version}",
            "python.exe",
        )
        if os.path.isfile(path):
            candidates.append([path])

    for path in (
        r"C:\Python311\python.exe",
        r"C:\Python312\python.exe",
        r"C:\Program Files\Python311\python.exe",
        r"C:\Program Files\Python312\python.exe",
    ):
        if os.path.isfile(path):
            candidates.append([path])

    for cmd in candidates:
        exe = cmd[0]
        if exe == STORE_STUB and not is_real_python(exe):
            continue
        if len(cmd) == 1:
            if is_real_python(exe):
                return cmd
        else:
            try:
                result = subprocess.run(
                    cmd + ["-c", "import sys; print(sys.executable)"],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    creationflags=no_window_flags(),
                )
                if result.returncode == 0:
                    return cmd
            except Exception:
                continue
    return None


def run_python(python_cmd, args):
    return subprocess.run(
        python_cmd + args,
        check=False,
        creationflags=no_window_flags(),
    )


def resolve_git_executable():
    git_exe = shutil.which("git")
    if git_exe:
        return git_exe

    candidates = [
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe",
    ]
    for path in candidates:
        if os.path.isfile(path):
            git_dir = os.path.dirname(path)
            path_env = os.environ.get("PATH", "")
            if git_dir.lower() not in path_env.lower():
                os.environ["PATH"] = git_dir + os.pathsep + path_env
            return path
    return None


def install_git():
    temp_dir = tempfile.mkdtemp()
    installer_path = os.path.join(temp_dir, "git_installer.exe")
    try:
        urllib.request.urlretrieve(GIT_INSTALLER_URL, installer_path)
        result = subprocess.run(
            [
                installer_path,
                "/VERYSILENT",
                "/NORESTART",
                "/NOCANCEL",
                "/SP-",
                "/CLOSEAPPLICATIONS",
                "/RESTARTAPPLICATIONS",
                '/COMPONENTS="icons,ext\\reg\\shellhere,assoc,assoc_sh"',
            ],
            check=False,
            creationflags=no_window_flags(),
        )
        if result.returncode != 0:
            return None
        time.sleep(3)
        return resolve_git_executable()
    except Exception:
        return None
    finally:
        try:
            if os.path.isfile(installer_path):
                os.remove(installer_path)
            os.rmdir(temp_dir)
        except OSError:
            pass


def ensure_git():
    git_exe = resolve_git_executable()
    if git_exe:
        return git_exe
    return install_git()


def _git_run(git_exe, args, *, cwd=None):
    return subprocess.run(
        [git_exe] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        creationflags=no_window_flags(),
    )


def _resolve_default_branch(git_exe, elysium_dir):
    for branch in ("main", "master"):
        probe = _git_run(
            git_exe,
            ["ls-remote", "--heads", ELYSIUM_REPO, branch],
        )
        if probe.returncode == 0 and probe.stdout.strip():
            return branch
    return "main"


def _init_git_in_existing_dir(git_exe, elysium_dir):
    """
    Attach git to a non-empty Documents\\Elysium folder (apps, settings, etc.)
    and sync tracked files from GitHub without deleting untracked user data.
    """
    settings_path = os.path.join(elysium_dir, "settings.json")
    settings_backup = None
    if os.path.isfile(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as handle:
                settings_backup = handle.read()
        except OSError:
            settings_backup = None

    steps = [
        _git_run(git_exe, ["-C", elysium_dir, "init"]),
        _git_run(
            git_exe,
            ["-C", elysium_dir, "remote", "add", "origin", ELYSIUM_REPO],
        ),
    ]
    for step in steps:
        if step.returncode != 0:
            detail = (step.stderr or step.stdout or "").strip()
            raise RuntimeError(f"Failed to initialize git repository.\n\n{detail}")

    branch = _resolve_default_branch(git_exe, elysium_dir)
    fetch = _git_run(
        git_exe,
        ["-C", elysium_dir, "fetch", "--depth", "1", "origin", branch],
    )
    if fetch.returncode != 0:
        detail = (fetch.stderr or fetch.stdout or "").strip()
        raise RuntimeError(f"Failed to fetch Elysium updates.\n\n{detail}")

    reset = _git_run(
        git_exe,
        ["-C", elysium_dir, "reset", "--hard", f"origin/{branch}"],
    )
    if reset.returncode != 0:
        detail = (reset.stderr or reset.stdout or "").strip()
        raise RuntimeError(f"Failed to sync Elysium files from GitHub.\n\n{detail}")

    if settings_backup:
        try:
            with open(settings_path, "w", encoding="utf-8") as handle:
                handle.write(settings_backup)
        except OSError:
            pass


def sync_repo():
    try:
        repo_root = _get_repo_root()
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
        from elysium.bootstrap.repo_sync import resolve_install_dir, sync_repo as bootstrap_sync

        bootstrap_sync(resolve_install_dir())
        return
    except ImportError:
        pass

    if os.environ.get("ELYSIUM_SKIP_GIT") == "1":
        return

    elysium_dir, _ = get_elysium_paths()
    os.makedirs(elysium_dir, exist_ok=True)
    elysium_script = os.path.join(elysium_dir, "ELYSIUM.py")
    git_exe = ensure_git()
    if not git_exe:
        if os.path.isfile(elysium_script):
            return
        raise RuntimeError(
            "Git is required but was not found and could not be installed automatically.\n\n"
            "Install Git for Windows from:\nhttps://git-scm.com/download/win"
        )

    git_dir = os.path.join(elysium_dir, ".git")
    if os.path.isdir(git_dir):
        result = _git_run(
            git_exe,
            ["-C", elysium_dir, "pull", "--ff-only"],
        )
        if result.returncode != 0 and os.path.isfile(elysium_script):
            return
    else:
        parent = os.path.dirname(elysium_dir)
        folder = os.path.basename(elysium_dir)
        result = _git_run(
            git_exe,
            ["clone", "--depth", "1", ELYSIUM_REPO, folder],
            cwd=parent,
        )
        if result.returncode != 0 and _dir_has_elysium_data(elysium_dir):
            _init_git_in_existing_dir(git_exe, elysium_dir)
            return

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"Failed to update or clone repository.\n\n{detail}")


def install_dependencies(python_cmd):
    check = run_python(
        python_cmd,
        [
            "-c",
            "import importlib; "
            "[importlib.import_module(p) for p in "
            "('PyQt5.QtCore','PySide6.QtCore','requests','openpyxl','pkg_resources','platformdirs','pydantic','yaml')]",
        ],
    )
    if check.returncode == 0:
        return

    install = run_python(
        python_cmd,
        ["-m", "pip", "install", "--upgrade"] + REQUIRED_PACKAGES,
    )
    if install.returncode != 0:
        manual = "pip install " + " ".join(REQUIRED_PACKAGES)
        raise RuntimeError(
            f"Could not install required Python packages.\n\nRun manually:\n{manual}"
        )


def launch_elysium(python_cmd):
    elysium_dir, log_dir = get_elysium_paths()
    elysium_script = os.path.join(elysium_dir, "ELYSIUM.py")
    if not os.path.isfile(elysium_script):
        raise RuntimeError(
            "The ELYSIUM.py script could not be found.\n\n"
            f"Expected path:\n{elysium_script}"
        )

    if is_frozen():
        os.execv(sys.executable, [sys.executable, elysium_script])

    result = run_python(python_cmd, ["-u", elysium_script])
    if result.returncode != 0:
        crash_log = os.path.join(log_dir, "elysium_crash.log")
        launcher_log = os.path.join(log_dir, "launcher_error.log")
        raise RuntimeError(
            f"Failed to launch ELYSIUM.py (exit code {result.returncode}).\n\n"
            f"Check logs:\n{crash_log}\n{launcher_log}"
        )


def main():
    try:
        close_other_elysium_instances()
        show_starting_notice()

        python_cmd = get_python_command()
        if not python_cmd:
            raise RuntimeError(
                "Python 3.10+ was not found.\n\n"
                "Install from: https://www.python.org/downloads/\n"
                "Check \"Add python.exe to PATH\" during setup."
            )

        sync_repo()
        stop_flow_server()
        install_dependencies(python_cmd)
        launch_elysium(python_cmd)
        return 0
    except Exception as exc:
        message = str(exc)
        write_log(message)
        show_error("Initialization Error", f"Failed during initialization:\n\n{message}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
