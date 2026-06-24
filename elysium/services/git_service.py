"""Git executable resolution (extracted from legacy ELYSIUM.py)."""

from __future__ import annotations

import os
import shutil
import winreg


def resolve_git_executable() -> str | None:
    git_in_path = shutil.which("git")
    if git_in_path:
        return git_in_path

    candidate_paths = [
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe",
    ]

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\GitForWindows") as key:
            install_path = winreg.QueryValueEx(key, "InstallPath")[0]
            candidate_paths.insert(0, os.path.join(install_path, "cmd", "git.exe"))
            candidate_paths.insert(1, os.path.join(install_path, "bin", "git.exe"))
    except (OSError, FileNotFoundError):
        pass

    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        ) as key:
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    with winreg.OpenKey(key, subkey_name) as subkey:
                        try:
                            display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        except (OSError, FileNotFoundError):
                            continue
                        if "Git" not in display_name:
                            continue
                        try:
                            install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                        except (OSError, FileNotFoundError):
                            continue
                        if install_location:
                            candidate_paths.insert(0, os.path.join(install_location, "cmd", "git.exe"))
                            candidate_paths.insert(1, os.path.join(install_location, "bin", "git.exe"))
                except (OSError, FileNotFoundError):
                    continue
    except (OSError, FileNotFoundError):
        pass

    for git_exe in candidate_paths:
        if os.path.isfile(git_exe):
            git_dir = os.path.dirname(git_exe)
            current_path = os.environ.get("PATH", "")
            if git_dir.lower() not in current_path.lower():
                os.environ["PATH"] = git_dir + os.pathsep + current_path
            return git_exe

    return None


def is_git_installed() -> bool:
    return resolve_git_executable() is not None


def git_command(*args: str) -> list[str]:
    git_exe = resolve_git_executable()
    if not git_exe:
        raise FileNotFoundError(
            "Git executable not found. Install Git for Windows from https://git-scm.com/download/win"
        )
    return [git_exe, *args]
