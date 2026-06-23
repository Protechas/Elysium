"""
Minimal Windows bootstrap for ELYSIUM.
Finds Python, syncs the repo, installs deps, and launches ELYSIUM.py.
Used as the PyInstaller entry point for ElysiumLauncher.exe.
"""
import ctypes
import os
import shutil
import subprocess
import sys

ELYSIUM_REPO = "https://github.com/Protechas/Elysium.git"
ELYSIUM_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Elysium")
LOG_DIR = os.path.join(ELYSIUM_DIR, "logs")
LAUNCHER_LOG = os.path.join(LOG_DIR, "launcher_error.log")
REQUIRED_PACKAGES = ["PyQt5", "requests", "openpyxl", "setuptools"]
STORE_STUB = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Microsoft",
    "WindowsApps",
    "python.exe",
)


def show_error(title, message):
    try:
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)
    except Exception:
        print(f"{title}: {message}")
    input("Press Enter to close...")


def write_log(message):
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(LAUNCHER_LOG, "a", encoding="utf-8") as f:
            f.write(message + "\n")
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
                )
                if result.returncode == 0:
                    return cmd
            except Exception:
                continue
    return None


def run_python(python_cmd, args):
    return subprocess.run(python_cmd + args, check=False)


def sync_repo():
    os.makedirs(ELYSIUM_DIR, exist_ok=True)
    if not shutil.which("git"):
        raise RuntimeError(
            "Git is required but was not found.\n\n"
            "Install from: https://git-scm.com/download/win"
        )

    git_dir = os.path.join(ELYSIUM_DIR, ".git")
    if os.path.isdir(git_dir):
        result = subprocess.run(
            ["git", "-C", ELYSIUM_DIR, "pull", "--ff-only"],
            capture_output=True,
            text=True,
        )
    else:
        parent = os.path.dirname(ELYSIUM_DIR)
        folder = os.path.basename(ELYSIUM_DIR)
        result = subprocess.run(
            ["git", "clone", ELYSIUM_REPO, folder],
            cwd=parent,
            capture_output=True,
            text=True,
        )

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"Git sync failed:\n{detail}")


def install_dependencies(python_cmd):
    check = run_python(
        python_cmd,
        [
            "-c",
            "import importlib; "
            "[importlib.import_module(p) for p in "
            "('PyQt5.QtCore','requests','openpyxl','pkg_resources')]",
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
            f"Could not install Python packages.\n\nRun manually:\n{manual}"
        )


def main():
    try:
        python_cmd = find_python()
        if not python_cmd:
            raise RuntimeError(
                "Python 3.10+ was not found.\n\n"
                "Install from: https://www.python.org/downloads/\n"
                "Check \"Add python.exe to PATH\" during setup."
            )

        sync_repo()
        install_dependencies(python_cmd)

        elysium_script = os.path.join(ELYSIUM_DIR, "ELYSIUM.py")
        if not os.path.isfile(elysium_script):
            raise RuntimeError(f"ELYSIUM.py not found at:\n{elysium_script}")

        launch = run_python(python_cmd, ["-u", elysium_script])
        if launch.returncode != 0:
            crash_log = os.path.join(LOG_DIR, "elysium_crash.log")
            raise RuntimeError(
                f"ELYSIUM exited with code {launch.returncode}.\n\n"
                f"Check logs:\n{crash_log}\n{LAUNCHER_LOG}"
            )
        return 0
    except Exception as exc:
        message = str(exc)
        write_log(message)
        show_error("ELYSIUM Launcher Error", f"{message}\n\nLog:\n{LAUNCHER_LOG}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
