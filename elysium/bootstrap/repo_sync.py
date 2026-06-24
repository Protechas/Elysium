"""
Git sync and runtime resolution for ELYSIUM.py.

The legacy Desktop ELYSIUM.exe is a thin bootstrap: it downloads the app from
GitHub over the network (git clone/pull), caches it under Documents\\Elysium,
then runs Documents\\Elysium\\ELYSIUM.py. ELYSIUM.py repeats that sync on
startup so the modular elysium/ package stays current without redistributing
a new EXE.

When Git is unavailable, sync falls back to downloading the GitHub source
zip over HTTPS (stdlib urllib).

This module uses only the Python standard library so it can run before pip
dependencies are installed.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import winreg
import zipfile

ELYSIUM_REPO = "https://github.com/Protechas/Elysium.git"
GITHUB_OWNER = "Protechas"
GITHUB_REPO = "Elysium"
REPO_SYNC_RAW_URL = (
    "https://raw.githubusercontent.com/Protechas/Elysium/main/"
    "elysium/bootstrap/repo_sync.py"
)
GIT_INSTALLER_URL = (
    "https://github.com/git-for-windows/git/releases/download/"
    "v2.42.0.windows.2/Git-2.42.0.2-64-bit.exe"
)


def _subprocess_no_window_flags() -> int:
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        return subprocess.CREATE_NO_WINDOW
    return 0


def _norm(path: str) -> str:
    return os.path.normcase(os.path.abspath(path))


def _get_documents_dir() -> str:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
        ) as key:
            docs, _ = winreg.QueryValueEx(key, "Personal")
            docs = os.path.expandvars(docs)
            if docs and os.path.isdir(docs):
                return docs
    except OSError:
        pass
    return os.path.join(os.path.expanduser("~"), "Documents")


def _dir_has_elysium_data(path: str) -> bool:
    if not os.path.isdir(path):
        return False
    markers = ("ELYSIUM.py", "settings.json", ".git", "DFR", "Flow", "logs", "apps")
    try:
        entries = set(os.listdir(path))
    except OSError:
        return False
    return any(marker in entries for marker in markers)


def get_new_default_install_dir() -> str:
    local_app = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(local_app, "Protech", "Elysium")


def get_legacy_install_dir() -> str:
    return os.path.join(_get_documents_dir(), "Elysium")


def resolve_install_dir() -> str:
    """Resolve the user's Elysium install directory (matches paths.resolve_base_dir)."""
    new_base = get_new_default_install_dir()
    legacy_base = get_legacy_install_dir()

    if _dir_has_elysium_data(new_base) and not _dir_has_elysium_data(legacy_base):
        return new_base
    if _dir_has_elysium_data(legacy_base):
        return legacy_base
    if _dir_has_elysium_data(new_base):
        return new_base
    if os.path.isfile(os.path.join(legacy_base, "ELYSIUM.py")):
        return legacy_base
    return new_base


def is_complete_install(root: str) -> bool:
    return os.path.isdir(os.path.join(root, "elysium"))


def is_dev_checkout(entry_script: str) -> bool:
    """True when running from a full source checkout (not the user install dir)."""
    if os.environ.get("ELYSIUM_DEV") == "1":
        return True
    if os.environ.get("ELYSIUM_SKIP_GIT") == "1":
        return True

    root = os.path.dirname(os.path.abspath(entry_script))
    install_dir = resolve_install_dir()
    if _norm(root) == _norm(install_dir):
        return False

    if os.path.isdir(os.path.join(root, ".git")) and is_complete_install(root):
        return True
    return False


def _git_run(git_exe: str, args: list[str], *, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [git_exe] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        creationflags=_subprocess_no_window_flags(),
    )


def resolve_git_executable() -> str | None:
    git_exe = shutil.which("git")
    if git_exe:
        return git_exe

    candidates = (
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe",
    )
    for path in candidates:
        if os.path.isfile(path):
            git_dir = os.path.dirname(path)
            path_env = os.environ.get("PATH", "")
            if git_dir.lower() not in path_env.lower():
                os.environ["PATH"] = git_dir + os.pathsep + path_env
            return path
    return None


def _resolve_default_branch(git_exe: str) -> str:
    for branch in ("main", "master"):
        probe = _git_run(git_exe, ["ls-remote", "--heads", ELYSIUM_REPO, branch])
        if probe.returncode == 0 and probe.stdout.strip():
            return branch
    return "main"


def _backup_settings(install_dir: str) -> str | None:
    settings_path = os.path.join(install_dir, "settings.json")
    if not os.path.isfile(settings_path):
        return None
    try:
        with open(settings_path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return None


def _restore_settings(install_dir: str, settings_backup: str | None) -> None:
    if not settings_backup:
        return
    settings_path = os.path.join(install_dir, "settings.json")
    try:
        with open(settings_path, "w", encoding="utf-8") as handle:
            handle.write(settings_backup)
    except OSError:
        pass


def _init_git_in_existing_dir(git_exe: str, install_dir: str) -> None:
    settings_backup = _backup_settings(install_dir)

    for args in (
        ["-C", install_dir, "init"],
        ["-C", install_dir, "remote", "add", "origin", ELYSIUM_REPO],
    ):
        step = _git_run(git_exe, args)
        if step.returncode != 0:
            detail = (step.stderr or step.stdout or "").strip()
            raise RuntimeError(f"Failed to initialize git repository.\n\n{detail}")

    branch = _resolve_default_branch(git_exe)
    fetch = _git_run(
        git_exe,
        ["-C", install_dir, "fetch", "--depth", "1", "origin", branch],
    )
    if fetch.returncode != 0:
        detail = (fetch.stderr or fetch.stdout or "").strip()
        raise RuntimeError(f"Failed to fetch Elysium updates.\n\n{detail}")

    reset = _git_run(
        git_exe,
        ["-C", install_dir, "reset", "--hard", f"origin/{branch}"],
    )
    if reset.returncode != 0:
        detail = (reset.stderr or reset.stdout or "").strip()
        raise RuntimeError(f"Failed to sync Elysium files from GitHub.\n\n{detail}")

    _restore_settings(install_dir, settings_backup)


def github_zip_url(branch: str = "main") -> str:
    return f"https://codeload.github.com/{GITHUB_OWNER}/{GITHUB_REPO}/zip/refs/heads/{branch}"


def _download_url(url: str, dest_path: str, *, timeout: int = 120) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Elysium-Bootstrap"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        with open(dest_path, "wb") as handle:
            shutil.copyfileobj(response, handle)


def sync_repo_via_http(install_dir: str, branch: str = "main") -> None:
    """Download the GitHub source zip and merge it into the install directory."""
    settings_backup = _backup_settings(install_dir)
    os.makedirs(install_dir, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        zip_path = os.path.join(tmp, "elysium.zip")
        _download_url(github_zip_url(branch), zip_path)

        with zipfile.ZipFile(zip_path) as archive:
            root_prefix = ""
            for name in archive.namelist():
                if "/" in name:
                    root_prefix = name.split("/", 1)[0] + "/"
                    break

            for member in archive.namelist():
                if member.endswith("/"):
                    continue
                relative = member[len(root_prefix) :] if root_prefix and member.startswith(root_prefix) else member
                if not relative:
                    continue
                dest_path = os.path.join(install_dir, relative)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with archive.open(member) as src, open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

    _restore_settings(install_dir, settings_backup)


def _sync_repo_git(install_dir: str, git_exe: str) -> None:
    elysium_script = os.path.join(install_dir, "ELYSIUM.py")
    git_dir = os.path.join(install_dir, ".git")
    if os.path.isdir(git_dir):
        result = _git_run(git_exe, ["-C", install_dir, "pull", "--ff-only"])
        if result.returncode != 0 and os.path.isfile(elysium_script):
            return
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(f"Failed to update Elysium from GitHub.\n\n{detail}")
        return

    parent = os.path.dirname(install_dir)
    folder = os.path.basename(install_dir)
    result = _git_run(
        git_exe,
        ["clone", "--depth", "1", ELYSIUM_REPO, folder],
        cwd=parent,
    )
    if result.returncode != 0 and _dir_has_elysium_data(install_dir):
        _init_git_in_existing_dir(git_exe, install_dir)
        return
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"Failed to clone Elysium repository.\n\n{detail}")


def sync_repo(install_dir: str) -> None:
    """Download the latest Elysium code from GitHub into the install directory."""
    if os.environ.get("ELYSIUM_SKIP_GIT") == "1":
        return

    os.makedirs(install_dir, exist_ok=True)
    elysium_script = os.path.join(install_dir, "ELYSIUM.py")
    git_exe = resolve_git_executable()

    if git_exe:
        try:
            _sync_repo_git(install_dir, git_exe)
            return
        except RuntimeError:
            if os.path.isfile(elysium_script) and is_complete_install(install_dir):
                return
            if os.environ.get("ELYSIUM_SKIP_HTTP") == "1":
                raise

    if os.environ.get("ELYSIUM_SKIP_HTTP") == "1":
        if os.path.isfile(elysium_script) and is_complete_install(install_dir):
            return
        raise RuntimeError(
            "Could not update Elysium from GitHub and HTTP fallback is disabled.\n\n"
            "Install Git for Windows from:\nhttps://git-scm.com/download/win"
        )

    last_error: Exception | None = None
    for branch in ("main", "master"):
        try:
            sync_repo_via_http(install_dir, branch=branch)
            return
        except (urllib.error.URLError, OSError, zipfile.BadZipFile, RuntimeError) as exc:
            last_error = exc

    if os.path.isfile(elysium_script) and is_complete_install(install_dir):
        return

    detail = str(last_error) if last_error else "Unknown download error"
    raise RuntimeError(f"Failed to download Elysium from GitHub.\n\n{detail}")


def load_repo_sync_module_from_web():
    """Fetch the bootstrap module from GitHub when the local package is missing."""
    import importlib.util

    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as handle:
        temp_path = handle.name
    try:
        _download_url(REPO_SYNC_RAW_URL, temp_path)
        spec = importlib.util.spec_from_file_location("elysium_bootstrap_repo_sync_web", temp_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("Could not load Elysium bootstrap module from GitHub.")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


def _restart_from(entry_script: str) -> None:
    args = [sys.executable, "-u", entry_script, *sys.argv[1:]]
    os.execv(sys.executable, args)


def ensure_runtime_ready(entry_script: str) -> str:
    """
    Ensure the full Elysium repo is present and this process runs from the
    canonical install copy. Returns the runtime root to place on sys.path.
    """
    entry_script = os.path.abspath(entry_script)
    entry_root = os.path.dirname(entry_script)
    install_dir = resolve_install_dir()
    canonical_script = os.path.join(install_dir, "ELYSIUM.py")

    if is_dev_checkout(entry_script):
        runtime_root = entry_root
    else:
        os.makedirs(install_dir, exist_ok=True)
        sync_repo(install_dir)
        if not is_complete_install(install_dir):
            raise RuntimeError(
                "The Elysium package is missing after syncing the repository.\n\n"
                f"Install directory:\n{install_dir}"
            )
        runtime_root = install_dir

    if runtime_root not in sys.path:
        sys.path.insert(0, runtime_root)

    if not is_dev_checkout(entry_script) and _norm(entry_script) != _norm(canonical_script):
        if os.path.isfile(canonical_script):
            _restart_from(canonical_script)
        raise RuntimeError(
            "ELYSIUM.py was not found in the install directory after syncing.\n\n"
            f"Expected:\n{canonical_script}"
        )

    return runtime_root
