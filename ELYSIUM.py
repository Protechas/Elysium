import os
import logging
import datetime
import time
import sys

_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))


def _load_repo_bootstrap_module():
    bootstrap_path = os.path.join(_REPO_ROOT, "elysium", "bootstrap", "repo_sync.py")
    if not os.path.isfile(bootstrap_path):
        return None
    import importlib.util

    spec = importlib.util.spec_from_file_location("elysium_bootstrap_repo_sync", bootstrap_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _minimal_repo_bootstrap(entry_script: str) -> str:
    """
    First-run bootstrap when only ELYSIUM.py is present locally.

    Fetches the bootstrap module from GitHub over HTTPS, syncs the full repo,
    then re-launches from the install directory — matching the legacy EXE flow.
    """
    import importlib.util
    import urllib.request
    import tempfile

    url = (
        "https://raw.githubusercontent.com/Protechas/Elysium/main/"
        "elysium/bootstrap/repo_sync.py"
    )
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as handle:
        temp_path = handle.name
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Elysium-Bootstrap"})
        with urllib.request.urlopen(request, timeout=120) as response:
            with open(temp_path, "wb") as out:
                out.write(response.read())
        spec = importlib.util.spec_from_file_location("elysium_bootstrap_repo_sync_web", temp_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("Could not load bootstrap module from GitHub.")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.ensure_runtime_ready(entry_script)
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


def _ensure_repo_runtime() -> str:
    global _REPO_ROOT
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

    bootstrap = _load_repo_bootstrap_module()
    if bootstrap is not None:
        _REPO_ROOT = bootstrap.ensure_runtime_ready(__file__)
    elif os.path.isdir(os.path.join(_REPO_ROOT, "elysium")):
        from elysium.bootstrap.repo_sync import ensure_runtime_ready

        _REPO_ROOT = ensure_runtime_ready(__file__)
    else:
        _REPO_ROOT = _minimal_repo_bootstrap(__file__)

    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)
    return _REPO_ROOT


_REPO_ROOT = _ensure_repo_runtime()


def setup_logging():
    logging.raiseExceptions = False
    logger = logging.getLogger('ElysiumDependencyManager')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(console_handler)
    return logger


logger = setup_logging()

# Stdlib only until third-party dependencies are verified
import subprocess
import re
import shutil
import tempfile
import winreg
import ctypes
import faulthandler
import traceback
from subprocess import Popen, PIPE


def _subprocess_no_window_flags():
    if hasattr(subprocess, 'CREATE_NO_WINDOW'):
        return subprocess.CREATE_NO_WINDOW
    return 0


def restart_application():
    """Restart Elysium after installing dependencies (more reliable than os.execl from EXE wrappers)."""
    subprocess.Popen([sys.executable] + sys.argv, close_fds=False)
    sys.exit(0)


def show_fatal_error(title, message):
    try:
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)
    except Exception:
        print(f"{title}: {message}")


def bootstrap_startup():
    crash_log = get_crash_log_path()

    def excepthook(exc_type, exc_value, exc_tb):
        tb_text = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            with open(crash_log, 'a', encoding='utf-8') as f:
                f.write(f"\n{'=' * 60}\n")
                f.write(datetime.datetime.now().isoformat() + "\n")
                f.write(tb_text)
        except Exception:
            pass
        logger.error(f"Unhandled exception:\n{tb_text}")
        msg = (
            f"ELYSIUM encountered an error and could not continue.\n\n"
            f"Details were saved to:\n{crash_log}\n\n"
            f"{exc_type.__name__}: {exc_value}"
        )
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox
            if QApplication.instance() is None:
                app = QApplication([])
            QMessageBox.critical(None, "ELYSIUM Error", msg)
        except Exception:
            show_fatal_error("ELYSIUM Error", msg)

    sys.excepthook = excepthook

    try:
        crash_file = open(crash_log, 'a', encoding='utf-8')
        faulthandler.enable(crash_file)
    except Exception:
        pass


def check_and_install_elysium_dependencies():
    """Check and install Elysium's own dependencies."""
    logger.info("Checking Elysium's own dependencies")
    
    # List of required packages for Elysium itself
    required_packages = [
        "PyQt5",
        "PySide6",
        "requests",
        "openpyxl",
        "setuptools",
        "platformdirs",
        "pydantic",
        "pyyaml",
    ]

    missing_packages = []
    for package in required_packages:
        try:
            if package == "PyQt5":
                __import__("PyQt5.QtCore")
            elif package == "PySide6":
                __import__("PySide6.QtCore")
            elif package == "setuptools":
                __import__("pkg_resources")
            elif package == "pyyaml":
                __import__("yaml")
            else:
                __import__(package)
            logger.info(f"Package already installed: {package}")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"Package needs installation: {package}")
    
    if not missing_packages:
        logger.info("All Elysium dependencies are already installed")
        return True
    
    # Install missing packages
    logger.info(f"Installing {len(missing_packages)} missing Elysium dependencies: {', '.join(missing_packages)}")
    
    try:
        # Use subprocess to run pip
        process = subprocess.Popen(
            [sys.executable, "-m", "pip", "install"] + missing_packages,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate()
        
        if stdout:
            logger.info(f"Installation output:\n{stdout}")
        if stderr:
            logger.warning(f"Installation stderr:\n{stderr}")
        
        if process.returncode == 0:
            logger.info("Successfully installed all Elysium dependencies")
            return True
        else:
            logger.error(f"Failed to install dependencies, return code: {process.returncode}")
            # Try installing packages one by one
            logger.info("Attempting to install packages individually")
            all_success = True
            for package in missing_packages:
                try:
                    logger.info(f"Installing {package} individually")
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", package],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    logger.info(f"Successfully installed {package}")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to install {package}: {str(e)}")
                    all_success = False
            
            return all_success
    except Exception as e:
        logger.error(f"Error installing Elysium dependencies: {str(e)}", exc_info=True)
        return False

def ensure_elysium_dependencies():
    """Verify third-party packages; install and restart if any are missing."""
    try:
        __import__("requests")
        __import__("PyQt5.QtCore")
        __import__("PySide6.QtCore")
        __import__("openpyxl")
        __import__("pkg_resources")
        __import__("platformdirs")
        __import__("pydantic")
        __import__("yaml")
        logger.info("All required packages are already installed")
        return True
    except ImportError as e:
        logger.warning(f"Missing dependency: {str(e)}")
        print("Some dependencies are missing. Attempting to install them...")
        if check_and_install_elysium_dependencies():
            print("Dependencies installed successfully. Launching Elysium...")
            restart_application()
        else:
            manual_cmd = "pip install PyQt5 PySide6 requests openpyxl setuptools platformdirs pydantic pyyaml"
            print("Failed to install dependencies. Please install them manually:")
            print(manual_cmd)
            show_fatal_error(
                "ELYSIUM - Missing Dependencies",
                f"Required Python packages could not be installed.\n\n"
                f"Open a terminal and run:\n{manual_cmd}"
            )
            sys.exit(1)


ensure_elysium_dependencies()

from elysium.core.paths import get_crash_log_path


def _should_launch_qml_ui() -> bool:
    """Use the QML shell unless legacy is forced or disabled in settings."""
    if os.environ.get("ELYSIUM_FORCE_LEGACY") == "1":
        return False
    try:
        from elysium.core.settings import load_settings

        return bool(load_settings().get("use_qml_ui", True))
    except Exception:
        return True


if __name__ == "__main__" and _should_launch_qml_ui():
    bootstrap_startup()
    try:
        from elysium.main import main as run_qml_main

        sys.exit(run_qml_main())
    except Exception as exc:
        crash_log = get_crash_log_path()
        tb_text = traceback.format_exc()
        try:
            with open(crash_log, "a", encoding="utf-8") as f:
                f.write(f"\n{'=' * 60}\n")
                f.write(datetime.datetime.now().isoformat() + "\n")
                f.write(tb_text)
        except Exception:
            pass
        logger.error("QML launch failed, falling back to legacy UI: %s", tb_text)
        os.environ["ELYSIUM_FORCE_LEGACY"] = "1"
        print(f"QML UI failed ({exc}). Falling back to classic UI...", file=sys.stderr)

from elysium import __version__ as ELYSIUM_VERSION
from elysium.core.logging_config import setup_dependency_logger
from elysium.core.paths import get_base_dir, get_logs_dir, resolve_app_dir
from elysium.core.settings import load_settings
from elysium.core.exceptions import ElysiumError, NodeMissingError
from elysium.services.app_registry import AppRegistry
from elysium.services.diagnostics_service import export_diagnostics
from elysium.services.environment_service import should_use_isolated_env
from elysium.services.git_service import is_git_installed, resolve_git_executable, git_command
from elysium.services.launcher_service import LauncherService
from elysium.services.process_service import (
    close_stale_application_state,
    patch_flow_launcher,
    stop_flow_server,
)
from elysium.windows.titlebar import apply_native_title_bar_theme

logger = setup_dependency_logger()

import requests
import openpyxl
import pkg_resources
from pkg_resources import DistributionNotFound, VersionConflict
from PyQt5.QtCore import QSize, Qt, pyqtSignal, QRect, QThread, QTimer
from PyQt5.QtWidgets import (
    QApplication, QHBoxLayout, QWidget, QVBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QToolButton, QGridLayout,
    QSlider, QProgressBar, QDialog, QTextEdit, QComboBox, QFrame, QScrollArea,
)
from PyQt5.QtGui import (
    QColor, QPixmap, QIcon, QPainter, QFont, QLinearGradient, QPainterPath,
    QFontMetrics, QPen, QBrush, QPalette,
)

from elysium.ui.theme import (
    APP_CARD_HEIGHT,
    APP_CARD_PADDING,
    APP_CARD_WIDTH,
    APP_GRID_COLUMNS,
    APP_GRID_SPACING_H,
    APP_GRID_SPACING_V,
    THEME_DARK,
    THEME_LIGHT,
    UI_FONT,
    apps_grid_minimum_size as _apps_grid_minimum_size,
    build_main_stylesheet,
    build_scroll_stylesheet,
    status_colors as _status_colors,
)


def _set_widget_background(widget, color):
    widget.setAutoFillBackground(True)
    palette = widget.palette()
    palette.setColor(QPalette.Window, QColor(color))
    widget.setPalette(palette)


ICON_DOWNLOAD_TIMEOUT = 8


def download_icon(url, base_dir=None):
    try:
        filename = url.split('/')[-1]
        local_path = os.path.join(base_dir or get_base_dir(), filename)
        if os.path.exists(local_path):
            return local_path
        response = requests.get(url, timeout=ICON_DOWNLOAD_TIMEOUT)
        response.raise_for_status()
        with open(local_path, 'wb') as f:
            f.write(response.content)
        return local_path
    except requests.RequestException as e:
        logger.warning("Failed to download icon from %s: %s", url, e)
        return None


def find_nodejs_bin_dir():
    """Return the directory containing npm.cmd, or None if not found."""
    npm_path = shutil.which('npm')
    if npm_path:
        return os.path.dirname(os.path.abspath(npm_path))

    candidates = [
        r"C:\Program Files\nodejs",
        r"C:\Program Files (x86)\nodejs",
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'node'),
        os.path.join(os.path.expanduser('~'), 'nodejs'),
    ]

    for candidate in candidates:
        if os.path.exists(os.path.join(candidate, 'npm.cmd')):
            return candidate
        if os.path.isdir(candidate):
            try:
                for entry in os.listdir(candidate):
                    subdir = os.path.join(candidate, entry)
                    if os.path.isdir(subdir) and os.path.exists(os.path.join(subdir, 'npm.cmd')):
                        return subdir
            except OSError:
                continue

    return None

def ensure_nodejs_path(env):
    """Prepend Node.js bin directory to PATH in env; returns True if npm is available."""
    node_dir = find_nodejs_bin_dir()
    if not node_dir:
        return False

    path_key = 'PATH'
    current_path = env.get(path_key, '')
    if node_dir.lower() not in current_path.lower():
        env[path_key] = node_dir + os.pathsep + current_path

    return os.path.exists(os.path.join(node_dir, 'npm.cmd'))

def install_git():
    """Download and install Git for Windows."""
    logger.info("Starting Git installation...")
    
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory: {temp_dir}")
        
        # Git for Windows download URL (latest stable version)
        git_url = "https://github.com/git-for-windows/git/releases/download/v2.42.0.windows.2/Git-2.42.0.2-64-bit.exe"
        
        # Download Git installer
        installer_path = os.path.join(temp_dir, "git_installer.exe")
        logger.info(f"Downloading Git installer from {git_url}")
        
        # Show download status to user
        QMessageBox.information(None, "Git Installation", "Downloading Git for Windows...\nThis may take a few minutes.")
        
        # Download with progress tracking
        response = requests.get(git_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 Kibibyte
        
        with open(installer_path, 'wb') as f:
            for data in response.iter_content(block_size):
                f.write(data)
        
        logger.info("Git installer downloaded successfully")
        
        # Run the installer silently
        logger.info("Running Git installer...")
        QMessageBox.information(None, "Git Installation", "Installing Git for Windows...\nThis may take a few minutes.")
        
        # Silent install parameters
        # /VERYSILENT: Very silent installation
        # /NORESTART: Don't restart after installation
        # /NOCANCEL: Prevent user from cancelling
        # /SP-: Disables the "This will install..." prompt
        # /CLOSEAPPLICATIONS: Closes applications using Git
        # /RESTARTAPPLICATIONS: Restart applications after install
        # /COMPONENTS: Select components to install
        install_args = [
            installer_path,
            "/VERYSILENT",
            "/NORESTART",
            "/NOCANCEL",
            "/SP-",
            "/CLOSEAPPLICATIONS",
            "/RESTARTAPPLICATIONS",
            '/COMPONENTS="icons,ext\reg\shellhere,assoc,assoc_sh"'
        ]
        
        process = subprocess.Popen(
            install_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = process.communicate()
        
        if stdout:
            logger.info(f"Installer stdout: {stdout.decode('utf-8', errors='replace')}")
        if stderr:
            logger.warning(f"Installer stderr: {stderr.decode('utf-8', errors='replace')}")
        
        if process.returncode != 0:
            logger.error(f"Git installer failed with return code {process.returncode}")
            return False
        
        logger.info("Git installation completed successfully")

        time.sleep(2)
        git_ready = resolve_git_executable() is not None

        try:
            os.remove(installer_path)
            os.rmdir(temp_dir)
            logger.info("Cleaned up temporary files")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary files: {str(e)}")

        return git_ready

    except Exception as e:
        logger.error(f"Error installing Git: {str(e)}", exc_info=True)
        return False

class ProgramIcon(QWidget):
    clicked = pyqtSignal(str)

    def __init__(self, program, icon_path, icon_size=(64, 64), status_text="", dark=True):
        super().__init__()
        self.program = program
        self.icon_path = icon_path
        self.icon_size = icon_size
        self.status_text = status_text
        self.highlight = False
        self._dark = dark
        self._cached_pixmap = None
        self.setFixedSize(APP_CARD_WIDTH, APP_CARD_HEIGHT)
        self.setCursor(Qt.PointingHandCursor)

    def set_dark_mode(self, dark):
        self._dark = dark
        self.update()

    def set_status(self, status_text):
        self.status_text = status_text
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.program)  # Emit the program name

    def enterEvent(self, event):
        self.highlight = True
        self.update()

    def leaveEvent(self, event):
        self.highlight = False
        self.update()

    def set_icon_path(self, icon_path):
        self.icon_path = icon_path
        self._cached_pixmap = None
        self.update()

    def _load_icon_pixmap(self):
        if self._cached_pixmap is not None and not self._cached_pixmap.isNull():
            return self._cached_pixmap
        if not self.icon_path:
            self._cached_pixmap = QPixmap()
            return self._cached_pixmap

        icon = QIcon(self.icon_path)
        source = icon.pixmap(QSize(256, 256))
        if source.isNull():
            source = QPixmap(self.icon_path)
        if source.isNull():
            self._cached_pixmap = source
            return source

        image = source.toImage().convertToFormat(source.toImage().Format_ARGB32)
        width, height = image.width(), image.height()
        min_x, min_y = width, height
        max_x, max_y = 0, 0
        found_pixels = False

        for y in range(height):
            for x in range(width):
                if image.pixelColor(x, y).alpha() > 10:
                    found_pixels = True
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)

        if found_pixels:
            source = source.copy(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)

        self._cached_pixmap = source.scaled(
            QSize(*self.icon_size),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        return self._cached_pixmap

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        theme = THEME_DARK if self._dark else THEME_LIGHT
        card_rect = QRect(
            APP_CARD_PADDING,
            APP_CARD_PADDING,
            self.width() - (APP_CARD_PADDING * 2),
            self.height() - (APP_CARD_PADDING * 2),
        )
        border_color = QColor(theme["border_active"] if self.highlight else theme["border"])
        if self.highlight:
            top = QColor(theme["surface_hover"])
            bottom = QColor(theme["card_top"])
        else:
            top = QColor(theme["card_top"])
            bottom = QColor(theme["card_bottom"])

        card_gradient = QLinearGradient(card_rect.topLeft(), card_rect.bottomLeft())
        card_gradient.setColorAt(0, top)
        card_gradient.setColorAt(1, bottom)

        painter.setPen(Qt.NoPen)
        painter.setBrush(card_gradient)
        painter.drawRoundedRect(card_rect, 12, 12)

        pen = QPen(border_color)
        pen.setWidth(2 if self.highlight else 1)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(card_rect, 12, 12)

        pixmap = self._load_icon_pixmap()
        icon_area_height = 72
        icon_top = card_rect.top() + 10

        if pixmap.isNull():
            painter.setFont(QFont(UI_FONT, 16, QFont.Bold))
            painter.setPen(QColor(theme["accent"]))
            initials = ''.join(word[0] for word in self.program.split()[:2]).upper()
            painter.drawText(
                QRect(card_rect.left(), icon_top, card_rect.width(), icon_area_height),
                Qt.AlignCenter,
                initials or "?",
            )
        else:
            pixmap_x = card_rect.left() + (card_rect.width() - pixmap.width()) // 2
            pixmap_y = icon_top + max(0, (icon_area_height - pixmap.height()) // 2)
            painter.drawPixmap(pixmap_x, pixmap_y, pixmap)

        painter.setFont(QFont(UI_FONT, 9, QFont.DemiBold))
        painter.setPen(QColor(theme["text"]))
        name_rect = QRect(card_rect.left() + 4, card_rect.top() + 88, card_rect.width() - 8, 28)
        painter.drawText(name_rect, Qt.AlignCenter | Qt.TextWordWrap, self.program)

        if self.status_text:
            bg, fg = _status_colors(self.status_text)
            painter.setFont(QFont(UI_FONT, 8, QFont.Medium))
            metrics = QFontMetrics(painter.font())
            badge_text = self.status_text
            badge_w = min(metrics.horizontalAdvance(badge_text) + 16, card_rect.width() - 12)
            badge_h = 18
            badge_x = card_rect.left() + (card_rect.width() - badge_w) // 2
            badge_y = card_rect.bottom() - badge_h - 10
            badge_rect = QRect(badge_x, badge_y, badge_w, badge_h)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(bg))
            painter.drawRoundedRect(badge_rect, 9, 9)
            painter.setPen(QColor(fg))
            painter.drawText(badge_rect, Qt.AlignCenter, badge_text)
 
class RoundedTextLabel(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
 
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # Enable antialiasing for smoother edges
 
        font = painter.font()
        font.setPointSize(24)  # Set the font size
        painter.setFont(font)
 
        metrics = QFontMetrics(font)
        text_width = metrics.width(self.text)
        text_height = metrics.height()
 
        # Draw rounded rectangle for each letter
        x = 0
        y = 0
        corner_radius = 10  # Adjust the corner radius as needed
        for char in self.text:
            painter_path = QPainterPath()
            painter_path.addRoundedRect(x, y, metrics.width(char), text_height, corner_radius, corner_radius)
            painter.setClipPath(painter_path)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#007bff"))  # Blue color for text
            painter.drawText(x, y + text_height, char)
            x += metrics.width(char)
 
        painter.end()
 
class IconDownloadThread(QThread):
    finished_signal = pyqtSignal(str, str)

    def __init__(self, program_name, icon_url, base_dir):
        super().__init__()
        self.program_name = program_name
        self.icon_url = icon_url
        self.base_dir = base_dir

    def run(self):
        icon_path = download_icon(self.icon_url, base_dir=self.base_dir)
        if icon_path:
            self.finished_signal.emit(self.program_name, icon_path)


class StartupInitThread(QThread):
    """Run blocking startup cleanup off the UI thread."""
    status_signal = pyqtSignal(str, int)
    finished_signal = pyqtSignal()

    def run(self):
        try:
            self.status_signal.emit("Closing previous sessions...", 15)
            close_stale_application_state()
            self.status_signal.emit("Preparing workspace...", 55)
            AppRegistry()
            self.status_signal.emit("Finishing setup...", 85)
        except Exception as exc:
            logger.warning("Startup cleanup encountered an issue: %s", exc)
        self.finished_signal.emit()


class StartupSplash(QWidget):
    """Lightweight splash shown while startup work runs."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.setFixedSize(460, 260)
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a0f18, stop:1 #05070b
                );
                color: #f1f5f9;
                font-family: "{UI_FONT}";
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)

        title = QLabel("ELYSIUM")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            'font-size: 34px; font-weight: 700; color: #3ee0cf; letter-spacing: 3px;'
        )
        layout.addWidget(title)

        subtitle = QLabel(f"Version {ELYSIUM_VERSION}")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        layout.addWidget(subtitle)

        layout.addSpacing(12)

        self.status_label = QLabel("Starting...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 13px; color: #94a3b8;")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #1e293b;
            }
            QProgressBar::chunk {
                background-color: #3ee0cf;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)

        hint = QLabel("Initializing launcher")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("font-size: 10px; color: #475569;")
        layout.addWidget(hint)

    def center_on_screen(self, app):
        screen = app.primaryScreen().geometry()
        self.move(
            screen.x() + (screen.width() - self.width()) // 2,
            screen.y() + (screen.height() - self.height()) // 2,
        )

    def set_progress(self, message, percent):
        self.status_label.setText(message)
        self.progress_bar.setValue(max(0, min(100, percent)))
        QApplication.processEvents()


class GitUpdateThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, program_name, git_repo_url, program_directory, icon_basename=None):
        super().__init__()
        self.program_name = program_name
        self.git_repo_url = git_repo_url
        self.program_directory = program_directory
        self.icon_basename = icon_basename

    def run(self):
        try:
            if not os.path.exists(self.program_directory) or not os.listdir(self.program_directory):
                self.progress_signal.emit(f"Cloning {self.program_name}...")
                # Use shallow clone (--depth 1) and single branch for faster cloning
                process = subprocess.Popen(
                    git_command('clone', '--depth', '1', '--single-branch', self.git_repo_url, self.program_directory),
                    stdout=PIPE, stderr=PIPE, universal_newlines=True
                )
            else:
                self.progress_signal.emit(f"Updating {self.program_name}...")
                process = subprocess.Popen(
                    git_command('-C', self.program_directory, 'pull', '--depth', '1', '--no-tags'),
                    stdout=PIPE, stderr=PIPE, universal_newlines=True
                )

            while True:
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.progress_signal.emit(output.strip())

            if process.returncode == 0:
                self.progress_signal.emit(f"{self.program_name} update completed successfully.")

                if self.program_name == "Flow":
                    patch_flow_launcher(self.program_directory)

                if self.icon_basename:
                    source_icon = os.path.join(self.program_directory, self.icon_basename)
                    if os.path.exists(source_icon):
                        dest_icon = os.path.join(
                            os.path.dirname(self.program_directory),
                            self.icon_basename,
                        )
                        shutil.copy2(source_icon, dest_icon)
                
                # Check for requirements.txt and install dependencies
                requirements_file = os.path.join(self.program_directory, 'requirements.txt')
                if os.path.exists(requirements_file):
                    self.progress_signal.emit(f"Checking dependencies for {self.program_name}...")
                    self.check_and_install_dependencies(requirements_file)
            else:
                self.progress_signal.emit(f"Error updating {self.program_name}.")

        except Exception as e:
            self.progress_signal.emit(f"Error: {str(e)}")
        finally:
            self.finished_signal.emit()
            
    def check_and_install_dependencies(self, requirements_file):
        try:
            logger.info(f"Starting dependency check for {self.program_name} using {requirements_file}")
            
            # Read requirements file
            with open(requirements_file, 'r') as f:
                # Handle both full-line comments and inline comments
                required_packages = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Remove inline comments
                        if '#' in line:
                            line = line.split('#')[0].strip()
                        required_packages.append(line)
            
            logger.info(f"Found {len(required_packages)} required packages: {', '.join(required_packages)}")
            
            if not required_packages:
                self.progress_signal.emit("No dependencies found in requirements file.")
                logger.info("No dependencies found in requirements file.")
                return
                
            # Check which packages need to be installed
            missing_packages = []
            installed_packages = []
            for package_req in required_packages:
                # Handle package with version specifier and strip inline comments
                package_req_clean = package_req.split('#')[0].strip()
                package_name = package_req_clean.split('==')[0].split('>')[0].split('<')[0].strip()
                try:
                    # Use the clean version for requirement checking
                    pkg_resources.require(package_req_clean)
                    installed_packages.append(package_req_clean)
                    logger.info(f"Package already satisfied: {package_req}")
                except (DistributionNotFound, VersionConflict) as e:
                    missing_packages.append(package_req_clean)
                    logger.warning(f"Package needs installation: {package_req} - Reason: {str(e)}")
            
            if not missing_packages:
                self.progress_signal.emit("All dependencies are already satisfied.")
                logger.info("All dependencies are already satisfied.")
                return
            
            logger.info(f"Need to install {len(missing_packages)} packages: {', '.join(missing_packages)}")
                
            # Try batch installation first
            self.progress_signal.emit(f"Installing {len(missing_packages)} dependencies in batch mode...")
            logger.info(f"Attempting batch installation of {len(missing_packages)} packages")
            
            try:
                process = subprocess.Popen(
                    [sys.executable, '-m', 'pip', 'install'] + missing_packages,
                    stdout=PIPE, stderr=PIPE, universal_newlines=True
                )
                
                # Log the exact command being run
                logger.info(f"Running command: {sys.executable} -m pip install {' '.join(missing_packages)}")
                
                # Collect all output for logging
                all_output = []
                
                # Monitor the installation process
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        output = output.strip()
                        self.progress_signal.emit(output)
                        all_output.append(output)
                
                # Also collect any stderr output
                stderr_output = process.stderr.read() if process.stderr else ""
                if stderr_output:
                    logger.warning(f"Stderr from batch installation: {stderr_output}")
                
                # Log all collected output
                if all_output:
                    logger.info("Batch installation output:\n" + "\n".join(all_output))
                
                if process.returncode == 0:
                    self.progress_signal.emit("All dependencies installed successfully.")
                    logger.info("Batch installation completed successfully")
                    return
                else:
                    self.progress_signal.emit("Batch installation failed. Trying individual installations...")
                    logger.warning(f"Batch installation failed with return code {process.returncode}. Falling back to individual installations.")
            except Exception as e:
                error_msg = f"Batch installation error: {str(e)}. Trying individual installations..."
                self.progress_signal.emit(error_msg)
                logger.error(error_msg, exc_info=True)
            
            # If batch installation fails, try installing packages individually
            logger.info("Starting individual package installations")
            successful_installs = 0
            failed_packages = []
            
            for package in missing_packages:
                try:
                    self.progress_signal.emit(f"Installing {package}...")
                    logger.info(f"Attempting to install {package}")
                    
                    # Try to install the package with multiple retry strategies if needed
                    success, output = self.install_package_with_retries(package)
                    
                    if success:
                        successful_installs += 1
                        logger.info(f"Successfully installed {package}")
                    else:
                        failed_packages.append(package)
                        logger.error(f"Failed to install {package} after all retry attempts")
                        self.progress_signal.emit(f"Failed to install {package} after multiple attempts")
                except Exception as e:
                    failed_packages.append(package)
                    error_msg = f"Error installing {package}: {str(e)}"
                    self.progress_signal.emit(error_msg)
                    logger.error(error_msg, exc_info=True)
            
            status_msg = f"Dependency installation completed. {successful_installs}/{len(missing_packages)} packages installed successfully."
            self.progress_signal.emit(status_msg)
            
            if failed_packages:
                logger.warning(f"Failed to install these packages: {', '.join(failed_packages)}")
            
            logger.info(status_msg)
            
        except Exception as e:
            error_msg = f"Error checking dependencies: {str(e)}"
            self.progress_signal.emit(error_msg)
            logger.error(error_msg, exc_info=True)
            
    def install_package_with_retries(self, package):
        """Try multiple strategies to install a package with retries."""
        # Strategy 1: Standard pip install
        self.progress_signal.emit(f"Trying standard installation for {package}...")
        logger.info(f"Strategy 1: Standard pip install for {package}")
        success, output = self.try_install_package(package)
        if success:
            return True, output
            
        # Strategy 2: Try with --no-cache-dir option
        self.progress_signal.emit(f"Retrying {package} with --no-cache-dir...")
        logger.info(f"Strategy 2: Trying pip install with --no-cache-dir for {package}")
        success, output = self.try_install_package(package, ["--no-cache-dir"])
        if success:
            return True, output
            
        # Strategy 3: Try with --no-deps option
        self.progress_signal.emit(f"Retrying {package} with --no-deps...")
        logger.info(f"Strategy 3: Trying pip install with --no-deps for {package}")
        success, output = self.try_install_package(package, ["--no-deps"])
        if success:
            return True, output
            
        # Strategy 4: Try with --user option
        self.progress_signal.emit(f"Retrying {package} with --user...")
        logger.info(f"Strategy 4: Trying pip install with --user for {package}")
        success, output = self.try_install_package(package, ["--user"])
        if success:
            return True, output
            
        # Strategy 5: Try with an alternative index URL (PyPI mirror)
        self.progress_signal.emit(f"Retrying {package} with alternative index...")
        logger.info(f"Strategy 5: Trying pip install with alternative index for {package}")
        success, output = self.try_install_package(package, ["--index-url", "https://pypi.org/simple"])
        if success:
            return True, output
            
        # Strategy 6: Try with --trusted-host option if it might be a certificate issue
        self.progress_signal.emit(f"Retrying {package} with trusted-host option...")
        logger.info(f"Strategy 6: Trying pip install with trusted-host for {package}")
        success, output = self.try_install_package(package, ["--trusted-host", "pypi.org", "--trusted-host", "files.pythonhosted.org"])
        if success:
            return True, output
            
        # All strategies failed
        return False, output
        
    def try_install_package(self, package, extra_args=None):
        """Try to install a package with the given extra arguments."""
        try:
            # Clean the package name by removing any comments
            package_clean = package.split('#')[0].strip()
            
            cmd = [sys.executable, '-m', 'pip', 'install', package_clean]
            if extra_args:
                cmd.extend(extra_args)
                
            logger.info(f"Running command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=PIPE, stderr=PIPE, universal_newlines=True
            )
            
            stdout, stderr = process.communicate()
            
            # Log the output
            if stdout:
                logger.info(f"Output from installing {package}:\n{stdout}")
            if stderr:
                logger.warning(f"Error output for {package}:\n{stderr}")
                
            if process.returncode == 0:
                return True, stdout
            else:
                return False, stderr
        except Exception as e:
            logger.error(f"Exception during installation of {package}: {str(e)}", exc_info=True)
            return False, str(e)

class ProgramUpdater(QWidget):
    def __init__(self, defer_app_status=False):
        super().__init__()
        self.setObjectName("elysiumMain")
        self._dark_mode = True
        self._defer_app_status = defer_app_status
        self.base_dir = get_base_dir()
        self.app_registry = AppRegistry()
        self.launcher_service = LauncherService(self.app_registry)
        self.program_icons = {}

        self.user_first_name = get_user_first_name()
        logger.info(f"User first name: {self.user_first_name}")

        self.desktop_icon_url = "https://raw.githubusercontent.com/Protechas/Elysium/main/ELYSIUM_icon.ico"
        self.desktop_icon_path = None

        self.active_threads = []
        self.icon_download_threads = []
        self.completed_updates = 0
        self.total_updates = 0
        self.programs = self.app_registry.legacy_programs_dict()

        self.init_ui()
        self.apply_theme(True)
        logger.info("ELYSIUM UI initialized")

    def current_launcher_style(self):
        return build_main_stylesheet(self._dark_mode)

    def apply_theme(self, dark=True):
        self._dark_mode = dark
        t = THEME_DARK if dark else THEME_LIGHT
        self.setStyleSheet(build_main_stylesheet(dark))
        for icon in self.program_icons.values():
            icon.set_dark_mode(dark)
        if hasattr(self, "apps_scroll"):
            self.apps_scroll.setStyleSheet(build_scroll_stylesheet(dark))
            _set_widget_background(self.apps_scroll.viewport(), t["surface"])
            self.apps_grid_host.setStyleSheet("background: transparent;")
        QTimer.singleShot(0, lambda: apply_native_title_bar_theme(self, dark))

    def showEvent(self, event):
        super().showEvent(event)
        apply_native_title_bar_theme(self, self._dark_mode)

    def init_ui(self):
        self.setWindowTitle('ELYSIUM')
        self.setMinimumSize(640, 820)
        self.resize(660, 860)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(14)

        header = QFrame()
        header.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 18, 14)

        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        header_title = QLabel("ELYSIUM")
        header_title.setObjectName("headerTitle")
        header_subtitle = QLabel(f"Welcome back, {self.user_first_name}")
        header_subtitle.setObjectName("headerSubtitle")
        title_block.addWidget(header_title)
        title_block.addWidget(header_subtitle)
        header_layout.addLayout(title_block)
        header_layout.addStretch()

        version_label = QLabel(f'v{ELYSIUM_VERSION}')
        version_label.setObjectName("versionBadge")
        version_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(version_label)
        root.addWidget(header)

        apps_frame = QFrame()
        apps_frame.setObjectName("appsFrame")
        apps_layout = QVBoxLayout(apps_frame)
        apps_layout.setContentsMargins(16, 16, 16, 16)

        self.apps_grid_host = QWidget()
        self.apps_grid_host.setObjectName("appsGridHost")

        grid_layout = QGridLayout(self.apps_grid_host)
        grid_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        grid_layout.setContentsMargins(4, 4, 4, 8)
        grid_layout.setHorizontalSpacing(APP_GRID_SPACING_H)
        grid_layout.setVerticalSpacing(APP_GRID_SPACING_V)

        self.program_grid_layout = grid_layout
        self.program_grid_row = 0
        self.program_grid_col = 0
        self.displayed_programs = set()

        for program, info in self.programs.items():
            self._add_program_to_grid(program, info, allow_download=False)

        self._update_apps_grid_minimum_size()

        self.apps_scroll = QScrollArea()
        self.apps_scroll.setObjectName("appsScroll")
        self.apps_scroll.setWidget(self.apps_grid_host)
        self.apps_scroll.setWidgetResizable(True)
        self.apps_scroll.setFrameShape(QFrame.NoFrame)
        self.apps_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.apps_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.apps_scroll.viewport().setObjectName("appsScrollViewport")
        apps_layout.addWidget(self.apps_scroll)
        root.addWidget(apps_frame, 1)

        self.status_label = QLabel('')
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        root.addWidget(self.progress_bar)

        footer = QFrame()
        footer.setObjectName("footerFrame")
        button_layout = QHBoxLayout(footer)
        button_layout.setContentsMargins(12, 10, 12, 10)
        button_layout.setSpacing(8)

        self.dark_mode_toggle_button = QPushButton("Light Mode")
        self.dark_mode_toggle_button.setObjectName("secondaryButton")
        self.dark_mode_toggle_button.clicked.connect(self.toggle_dark_mode)

        self.view_logs_button = QPushButton("Logs")
        self.view_logs_button.setObjectName("secondaryButton")
        self.view_logs_button.clicked.connect(self.view_dependency_logs)

        self.export_diagnostics_button = QPushButton("Export Diagnostics")
        self.export_diagnostics_button.setObjectName("secondaryButton")
        self.export_diagnostics_button.clicked.connect(self.export_diagnostics_bundle)

        self.update_elysium_button = QPushButton("Update Elysium")
        self.update_elysium_button.setObjectName("primaryButton")
        self.update_elysium_button.clicked.connect(self.check_for_elysium_updates)

        button_layout.addWidget(self.dark_mode_toggle_button)
        button_layout.addWidget(self.view_logs_button)
        button_layout.addWidget(self.export_diagnostics_button)
        button_layout.addStretch()
        button_layout.addWidget(self.update_elysium_button)
        root.addWidget(footer)

    def get_placeholder_icon_path(self):
        candidates = [
            os.path.join(self.base_dir, "ELYSIUM_icon.ico"),
            os.path.join(_REPO_ROOT, "ELYSIUM_icon.ico"),
            os.path.join(_REPO_ROOT, "combiner_icon.ico"),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def download_icon(self, url):
        return download_icon(url, base_dir=self.base_dir)

    def resolve_program_icon_path(self, program, info, allow_download=False):
        if "icon_path" in info:
            icon_path = info["icon_path"]
            if icon_path and os.path.exists(icon_path):
                return icon_path
            return None

        icon_url = info.get("icon_url")
        if not icon_url:
            return None

        cached = os.path.join(self.base_dir, os.path.basename(icon_url))
        if os.path.exists(cached):
            return cached

        folder_name = info.get("repo_name", program)
        app_id = info.get("id", "")
        if app_id:
            app_dir = resolve_app_dir(app_id, folder_name)
        else:
            app_dir = os.path.join(self.base_dir, folder_name)
        repo_icon = os.path.join(app_dir, os.path.basename(icon_url))
        if os.path.exists(repo_icon):
            return repo_icon

        if allow_download:
            icon_path = self.download_icon(icon_url)
            if icon_path and os.path.exists(icon_path):
                return icon_path

        return None

    def _add_program_to_grid(self, program, info, allow_download=False):
        icon_path = self.resolve_program_icon_path(program, info, allow_download=allow_download)
        if not icon_path:
            icon_path = self.get_placeholder_icon_path()
        status = "Loading" if self._defer_app_status else self.get_program_status(program, info)

        if icon_path and os.path.exists(icon_path):
            icon_widget = ProgramIcon(
                program, icon_path, status_text=status, dark=self._dark_mode
            )
        else:
            icon_widget = ProgramIcon(
                program, "", status_text=status or program, dark=self._dark_mode
            )

        icon_widget.clicked.connect(self.program_clicked)
        self.program_icons[program] = icon_widget
        self.program_grid_layout.addWidget(
            icon_widget, self.program_grid_row, self.program_grid_col
        )
        self.displayed_programs.add(program)
        self.program_grid_col += 1
        if self.program_grid_col == APP_GRID_COLUMNS:
            self.program_grid_row += 1
            self.program_grid_col = 0
        self._update_apps_grid_minimum_size()

    def _update_apps_grid_minimum_size(self):
        if not hasattr(self, "apps_grid_host"):
            return
        count = max(len(self.displayed_programs), len(self.programs))
        width, height = _apps_grid_minimum_size(count)
        self.apps_grid_host.setMinimumSize(width, height)

    def start_background_icon_downloads(self):
        for program, info in self.programs.items():
            icon_url = info.get("icon_url")
            if not icon_url:
                continue
            if self.resolve_program_icon_path(program, info, allow_download=False):
                continue
            thread = IconDownloadThread(program, icon_url, self.base_dir)
            thread.finished_signal.connect(self._on_icon_downloaded)
            self.icon_download_threads.append(thread)
            thread.start()

    def _on_icon_downloaded(self, program_name, icon_path):
        icon_widget = self.program_icons.get(program_name)
        if icon_widget and icon_path and os.path.exists(icon_path):
            icon_widget.set_icon_path(icon_path)

    def load_desktop_icon_async(self):
        cached = os.path.join(self.base_dir, os.path.basename(self.desktop_icon_url))
        if os.path.exists(cached):
            self.setWindowIcon(QIcon(cached))
            return

        def _apply(path):
            if path and os.path.exists(path):
                self.setWindowIcon(QIcon(path))

        thread = IconDownloadThread("__desktop__", self.desktop_icon_url, self.base_dir)
        thread.finished_signal.connect(lambda _name, path: _apply(path))
        self.icon_download_threads.append(thread)
        thread.start()

    def refresh_app_statuses(self):
        for program, info in self.programs.items():
            self.set_program_status(program, self.get_program_status(program, info))

    def begin_post_show_startup(self):
        """Non-blocking tasks after the main window is visible."""
        self.start_background_icon_downloads()
        self.load_desktop_icon_async()
        QTimer.singleShot(0, self.refresh_app_statuses)
        QTimer.singleShot(200, lambda: self.update_all_programs(interactive=False))

    def get_program_status(self, program, info):
        app = self.app_registry.get_by_name(program)
        if not app:
            return ""
        if info.get("requires_node") and not find_nodejs_bin_dir():
            return "Needs Node"
        if not self.app_registry.is_installed(app):
            return "Not installed"
        return "Ready"

    def refresh_program_icons(self):
        if not hasattr(self, "program_grid_layout"):
            return

        for program, info in self.programs.items():
            if program in self.displayed_programs:
                icon_path = self.resolve_program_icon_path(program, info, allow_download=False)
                icon_widget = self.program_icons.get(program)
                if icon_widget and icon_path and os.path.exists(icon_path):
                    icon_widget.set_icon_path(icon_path)
                continue

            self._add_program_to_grid(program, info, allow_download=False)

    def set_program_status(self, program, status):
        icon = self.program_icons.get(program)
        if icon:
            icon.set_status(status)

    def program_clicked(self, program):
        self.selected_program = program
        self.update_and_launch_program()

    def toggle_dark_mode(self):
        if self.dark_mode_toggle_button.text() == "Light Mode":
            self.apply_theme(False)
            self.dark_mode_toggle_button.setText("Dark Mode")
        else:
            self.apply_theme(True)
            self.dark_mode_toggle_button.setText("Light Mode")
 
    def update_program_direct(self, program_name, git_repo_url):
        try:
            # Check if Git is installed before attempting to update
            if not is_git_installed():
                logger.warning(f"Cannot update {program_name}: Git is not installed")
                self.update_status(f"Cannot update {program_name}: Git is not installed")
                return

            program_info = self.programs[program_name]
            app_id = program_info.get("id", "")
            folder_name = program_info.get("repo_name", program_name)
            if app_id:
                program_directory = resolve_app_dir(app_id, folder_name)
            else:
                program_directory = os.path.join(self.base_dir, folder_name)
            icon_basename = None
            if program_info.get("icon_url"):
                icon_basename = os.path.basename(program_info["icon_url"])

            self.set_program_status(program_name, "Updating")
            update_thread = GitUpdateThread(
                program_name, git_repo_url, program_directory, icon_basename
            )
            update_thread.progress_signal.connect(self.update_status)
            update_thread.finished_signal.connect(lambda: self.thread_finished(program_name))
            
            self.active_threads.append(update_thread)
            update_thread.start()

        except Exception as e:
            error_msg = f"Error updating {program_name}: {str(e)}"
            self.update_status(error_msg)
            logger.error(error_msg, exc_info=True)

    def thread_finished(self, program_name):
        self.completed_updates += 1
        self.progress_bar.setValue(int((self.completed_updates / self.total_updates) * 100))
        self.set_program_status(program_name, "Ready")
        
        if self.completed_updates == self.total_updates:
            self.progress_bar.hide()
            self.status_label.setText("All updates completed!")
            self.refresh_program_icons()
            self.active_threads.clear()
            self.completed_updates = 0

    def update_status(self, message):
        self.status_label.setText(message)

    def update_all_programs(self, interactive=True):
        if not is_git_installed():
            logger.info("Git not found during startup update check")
            if interactive:
                reply = QMessageBox.question(
                    self,
                    'Git Required',
                    "Git is required to update programs but is not installed. Would you like to install it now?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )

                if reply == QMessageBox.Yes:
                    self.status_label.setText("Installing Git...")
                    if install_git():
                        self.status_label.setText("Git installed successfully.")
                    else:
                        QMessageBox.critical(
                            self,
                            'Installation Failed',
                            "Failed to install Git. Please install it manually from https://git-scm.com/download/win"
                        )
                        return
                else:
                    QMessageBox.warning(
                        self,
                        'Update Cancelled',
                        "Cannot update programs without Git."
                    )
                    return
            else:
                self.status_label.setText("Background updates skipped (Git not installed)")
                return
        git_programs = {name: info for name, info in self.programs.items() if info.get("repo_url")}
        
        self.completed_updates = 0
        self.total_updates = len(git_programs)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        for program_name, info in git_programs.items():
            self.update_program_direct(program_name, info["repo_url"])

    def update_and_launch_program(self):
        if self.selected_program:
            try:
                program_info = self.programs[self.selected_program]
                program_name = self.selected_program
                script_name = program_info["script"]
                folder_name = program_info.get('repo_name', program_name)
                git_repo_url = program_info.get('repo_url', '')
                local_dir = program_info.get('local_dir', '')
                app_def = self.app_registry.get_by_name(program_name)
                app_id = program_info.get("id", "")

                if git_repo_url and not is_git_installed():
                    logger.info(f"Git not found when launching {program_name}, prompting user for installation")
                    reply = QMessageBox.question(
                        self, 
                        'Git Required', 
                        "Git is required to update programs but is not installed. Would you like to install it now?",
                        QMessageBox.Yes | QMessageBox.No, 
                        QMessageBox.Yes
                    )
                    
                    if reply == QMessageBox.Yes:
                        self.status_label.setText("Installing Git...")
                        if install_git():
                            self.status_label.setText("Git installed successfully.")
                            # Git should now be in PATH for this session
                        else:
                            QMessageBox.critical(
                                self, 
                                'Installation Failed', 
                                "Failed to install Git. Please install it manually from https://git-scm.com/download/win"
                            )
                            # Continue without updating
                    else:
                        # Continue without updating
                        pass
                
                if git_repo_url and is_git_installed():
                    self.update_program_direct(program_name, git_repo_url)

                if local_dir:
                    installation_directory = local_dir
                elif app_id:
                    installation_directory = resolve_app_dir(app_id, folder_name)
                else:
                    installation_directory = os.path.join(self.base_dir, folder_name)

                requirements_file = os.path.join(installation_directory, 'requirements.txt')
                use_isolated = app_id and should_use_isolated_env(app_id)
                if os.path.exists(requirements_file) and not use_isolated:
                    self.status_label.setText(f"Checking dependencies for {program_name}...")
                    self.check_dependencies_before_launch(requirements_file)

                launch_env = os.environ.copy()
                launch_env['LAUNCHER_STYLE'] = self.current_launcher_style()

                if program_name == "Flow":
                    if not ensure_nodejs_path(launch_env):
                        self.set_program_status(program_name, "Needs Node")
                        QMessageBox.critical(
                            self,
                            'Node.js Required',
                            "Node.js is required to run Flow but was not found.\n\n"
                            "Install Node.js from https://nodejs.org and restart Elysium, "
                            "or ensure npm is available on your PATH."
                        )
                        return

                    patch_flow_launcher(installation_directory)
                    stop_flow_server(self.app_registry)

                    program_path = os.path.join(installation_directory, script_name)
                    if not os.path.exists(program_path):
                        raise FileNotFoundError(f"Could not find {script_name} in {installation_directory}")

                    subprocess.Popen(
                        ['wscript.exe', program_path],
                        cwd=installation_directory,
                        env=launch_env,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                elif use_isolated:
                    self.launcher_service.launch(program_name, extra_env=launch_env)
                else:
                    program_path = os.path.join(installation_directory, script_name)
                    if not os.path.exists(program_path):
                        raise FileNotFoundError(f"Could not find {script_name} in {installation_directory}")

                    launch_env['PYTHONPATH'] = installation_directory
                    subprocess.Popen(
                        [sys.executable, program_path],
                        env=launch_env,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )

                self.set_program_status(program_name, "Ready")
                QMessageBox.information(self, 'Launch', f"Launching {program_name} for {self.user_first_name}...")

            except ElysiumError as e:
                error_msg = str(e)
                QMessageBox.warning(self, 'Error', error_msg)
                logger.error(error_msg, exc_info=True)
                if self.selected_program:
                    self.set_program_status(self.selected_program, "Failed")
            except Exception as e:
                error_msg = f"Error updating or launching {program_name}: {str(e)}"
                QMessageBox.warning(self, 'Error', error_msg)
                logger.error(error_msg, exc_info=True)
                self.set_program_status(program_name, "Failed")
        else:
            QMessageBox.warning(self, 'Error', 'Please select a program to launch.')
            
    def check_dependencies_before_launch(self, requirements_file):
        try:
            program_name = self.selected_program
            logger.info(f"Checking dependencies before launching {program_name} using {requirements_file}")
            
            # Read requirements file
            with open(requirements_file, 'r') as f:
                # Handle both full-line comments and inline comments
                required_packages = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Remove inline comments
                        if '#' in line:
                            line = line.split('#')[0].strip()
                        required_packages.append(line)
            
            logger.info(f"Found {len(required_packages)} required packages: {', '.join(required_packages)}")
            
            if not required_packages:
                logger.info("No dependencies found in requirements file.")
                return
                
            # Check which packages need to be installed
            missing_packages = []
            installed_packages = []
            
            # Make sure pkg_resources is available
            try:
                import pkg_resources
                from pkg_resources import DistributionNotFound, VersionConflict
                
                for package_req in required_packages:
                    # Handle package with version specifier and strip inline comments
                    package_req_clean = package_req.split('#')[0].strip()
                    package_name = package_req_clean.split('==')[0].split('>')[0].split('<')[0].strip()
                    try:
                        # Use the clean version for requirement checking
                        pkg_resources.require(package_req_clean)
                        installed_packages.append(package_req_clean)
                        logger.info(f"Package already satisfied: {package_req}")
                    except (DistributionNotFound, VersionConflict) as e:
                        missing_packages.append(package_req_clean)
                        logger.warning(f"Package needs installation: {package_req} - Reason: {str(e)}")
            except ImportError:
                # If pkg_resources is not available, assume all packages need to be installed
                logger.warning("pkg_resources not available, assuming all packages need installation")
                missing_packages = required_packages
            
            if not missing_packages:
                self.status_label.setText("All dependencies are already satisfied.")
                logger.info("All dependencies are already satisfied.")
                return
            
            logger.info(f"Need to install {len(missing_packages)} packages for {program_name}: {', '.join(missing_packages)}")
                
            # Ask user if they want to install missing dependencies
            reply = QMessageBox.question(
                self, 
                'Missing Dependencies', 
                f"Some dependencies are missing. Do you want to install them now?\n\nMissing packages: {', '.join(missing_packages)}",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                logger.info("User chose to install missing dependencies")
                
                # Try batch installation
                self.status_label.setText("Installing dependencies...")
                logger.info(f"Attempting batch installation of {len(missing_packages)} packages")
                
                try:
                    # Log the exact command being run
                    cmd = f"{sys.executable} -m pip install {' '.join(missing_packages)}"
                    logger.info(f"Running command: {cmd}")
                    
                    process = subprocess.Popen(
                        [sys.executable, '-m', 'pip', 'install'] + missing_packages,
                        stdout=PIPE, stderr=PIPE, universal_lines=True
                    )
                    
                    output, error = process.communicate()
                    
                    # Log the output
                    if output:
                        logger.info(f"Batch installation output:\n{output}")
                    if error:
                        logger.warning(f"Batch installation stderr:\n{error}")
                    
                    if process.returncode == 0:
                        self.status_label.setText("All dependencies installed successfully.")
                        logger.info("Batch installation completed successfully")
                    else:
                        # If batch installation fails, try individual installations
                        error_msg = f"Batch installation failed with return code {process.returncode}. Trying individual installations."
                        self.status_label.setText("Batch installation failed. Trying individual installations...")
                        logger.warning(error_msg)
                        
                        successful_installs = 0
                        failed_packages = []
                        
                        # Create a temporary GitUpdateThread just to use its retry methods
                        temp_thread = GitUpdateThread("temp", "", "")
                        # Connect the progress signal to update the status
                        temp_thread.progress_signal.connect(lambda msg: self.status_label.setText(msg))
                        
                        for package in missing_packages:
                            try:
                                logger.info(f"Attempting to install {package} individually with retries")
                                self.status_label.setText(f"Installing {package}...")
                                
                                # Use the retry mechanism
                                success, output = temp_thread.install_package_with_retries(package)
                                
                                if success:
                                    successful_installs += 1
                                    logger.info(f"Successfully installed {package}")
                                else:
                                    failed_packages.append(package)
                                    logger.error(f"Failed to install {package} after multiple retry strategies")
                            except Exception as e:
                                failed_packages.append(package)
                                logger.error(f"Error installing {package}: {str(e)}", exc_info=True)
                        
                        if failed_packages:
                            error_msg = f"Failed to install {len(failed_packages)} packages: {', '.join(failed_packages)}"
                            self.status_label.setText(error_msg)
                            logger.error(error_msg)
                            
                            QMessageBox.warning(
                                self, 
                                'Installation Failed', 
                                f"Failed to install some dependencies: {', '.join(failed_packages)}\n\nYou may need to install them manually."
                            )
                        else:
                            success_msg = f"Successfully installed all {successful_installs} packages"
                            self.status_label.setText(success_msg)
                            logger.info(success_msg)
                except Exception as e:
                    error_msg = f"Error installing dependencies: {str(e)}"
                    self.status_label.setText(error_msg)
                    logger.error(error_msg, exc_info=True)
                    
                    QMessageBox.warning(
                        self, 
                        'Installation Error', 
                        f"Error installing dependencies: {str(e)}"
                    )
            else:
                logger.info("User chose not to install missing dependencies")
                self.status_label.setText("Dependency installation skipped.")
                
                QMessageBox.warning(
                    self, 
                    'Dependencies Required', 
                    f"The program may not work correctly without the required dependencies."
                )
        except Exception as e:
            error_msg = f"Error checking dependencies: {str(e)}"
            self.status_label.setText(error_msg)
            logger.error(error_msg, exc_info=True)

    def view_dependency_logs(self):
        try:
            log_dir = get_logs_dir()
            
            # Check if logs directory exists
            if not os.path.exists(log_dir):
                QMessageBox.information(self, 'No Logs', 'No dependency logs found.')
                return
                
            # Get list of log files
            log_files = [f for f in os.listdir(log_dir) if f.startswith('dependency_log_') and f.endswith('.log')]
            
            if not log_files:
                QMessageBox.information(self, 'No Logs', 'No dependency logs found.')
                return
                
            # Sort log files by modification time (newest first)
            log_files.sort(
                key=lambda name: os.path.getmtime(os.path.join(log_dir, name)),
                reverse=True,
            )
            
            # Create a dialog to display logs
            dialog = QDialog(self)
            dialog.setWindowTitle('Dependency Logs')
            dialog.setMinimumSize(800, 600)
            
            layout = QVBoxLayout()
            
            # Create a combo box for selecting log files
            log_selector = QComboBox()
            for log_file in log_files:
                pid_match = re.match(r'^dependency_log_(\d+)\.log$', log_file)
                if pid_match:
                    pid_str = pid_match.group(1)
                    mtime = os.path.getmtime(os.path.join(log_dir, log_file))
                    formatted_date = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    log_selector.addItem(f"{formatted_date} (PID: {pid_str})", log_file)
                    continue

                parts = log_file.replace('dependency_log_', '').replace('.log', '').split('_')
                if len(parts) >= 2:  # Should have at least timestamp and PID
                    date_str = parts[0]
                    pid_str = parts[1] if len(parts) > 1 else "unknown"
                    try:
                        # Try to parse and format the date
                        date_obj = datetime.datetime.strptime(date_str, "%Y%m%d%H%M%S")
                        formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
                        log_selector.addItem(f"{formatted_date} (PID: {pid_str})", log_file)
                    except:
                        # If parsing fails, just use the original string
                        log_selector.addItem(f"{date_str} (PID: {pid_str})", log_file)
                else:
                    # Fallback for any files with the old naming convention
                    log_selector.addItem(log_file, log_file)
            
            layout.addWidget(QLabel("Select log file:"))
            layout.addWidget(log_selector)
            
            # Create a text area for displaying log content
            log_content = QTextEdit()
            log_content.setReadOnly(True)
            log_content.setLineWrapMode(QTextEdit.NoWrap)
            log_content.setFont(QFont("Courier New", 10))
            layout.addWidget(log_content)
            
            # Function to load selected log file
            def load_log_file():
                selected_file = log_selector.currentData()
                if selected_file:
                    try:
                        log_path = os.path.join(log_dir, selected_file)
                        try:
                            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                                content = f.read()
                        except OSError:
                            with open(log_path, 'r', encoding='utf-8', errors='replace', buffering=1) as f:
                                content = f.read()
                        log_content.setText(content)
                    except Exception as e:
                        log_content.setText(
                            f"Error loading log file: {str(e)}\n\n"
                            "The log may be locked by a running ELYSIUM instance. "
                            "Close other ELYSIUM windows and try again."
                        )
            
            # Connect the combo box to the load function
            log_selector.currentIndexChanged.connect(load_log_file)
            
            # Add buttons
            button_layout = QHBoxLayout()
            
            # Open logs folder button
            open_folder_button = QPushButton("Open Logs Folder")
            open_folder_button.clicked.connect(lambda: os.startfile(log_dir))
            button_layout.addWidget(open_folder_button)
            
            # Copy to clipboard button
            copy_button = QPushButton("Copy to Clipboard")
            copy_button.clicked.connect(lambda: QApplication.clipboard().setText(log_content.toPlainText()))
            button_layout.addWidget(copy_button)
            
            # Close button
            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            button_layout.addWidget(close_button)
            
            layout.addLayout(button_layout)
            
            dialog.setLayout(layout)
            
            # Load the first log file
            if log_selector.count() > 0:
                load_log_file()
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.warning(self, 'Error', f"Error viewing logs: {str(e)}")
            logger.error(f"Error viewing logs: {str(e)}", exc_info=True)

    def export_diagnostics_bundle(self):
        try:
            self.status_label.setText("Exporting diagnostics...")
            zip_path = export_diagnostics()
            self.status_label.setText("Diagnostics exported.")
            QMessageBox.information(
                self,
                "Export Diagnostics",
                f"Diagnostics bundle saved to:\n{zip_path}",
            )
        except Exception as e:
            error_msg = f"Failed to export diagnostics: {e}"
            self.status_label.setText(error_msg)
            QMessageBox.warning(self, "Export Failed", error_msg)
            logger.error(error_msg, exc_info=True)

    def check_for_elysium_updates(self):
        """Check for updates to Elysium itself."""
        try:
            self.status_label.setText("Checking for Elysium updates...")
            
            # Define the Elysium repository URL
            elysium_repo_url = "https://github.com/Protechas/Elysium.git"
            elysium_dir = get_base_dir()
            
            # Check if Git is installed
            if not is_git_installed():
                reply = QMessageBox.question(
                    self, 
                    'Git Required', 
                    "Git is required to update Elysium but is not installed. Would you like to install it now?",
                    QMessageBox.Yes | QMessageBox.No, 
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self.status_label.setText("Installing Git...")
                    if install_git():
                        self.status_label.setText("Git installed successfully.")
                    else:
                        QMessageBox.critical(
                            self, 
                            'Installation Failed', 
                            "Failed to install Git. Please install it manually from https://git-scm.com/download/win"
                        )
                        return
                else:
                    self.status_label.setText("Elysium update cancelled.")
                    return
            
            # Create and start the update thread
            update_thread = GitUpdateThread("Elysium", elysium_repo_url, elysium_dir)
            update_thread.progress_signal.connect(self.update_status)
            update_thread.finished_signal.connect(self.elysium_update_finished)
            
            self.active_threads.append(update_thread)
            update_thread.start()
            
        except Exception as e:
            error_msg = f"Error checking for Elysium updates: {str(e)}"
            self.status_label.setText(error_msg)
            logger.error(error_msg, exc_info=True)

    def elysium_update_finished(self):
        """Called when Elysium update is finished."""
        self.status_label.setText("Elysium update completed.")
        
        # Ask if the user wants to restart Elysium to apply updates
        reply = QMessageBox.question(
            self, 
            'Restart Elysium', 
            "Elysium has been updated. Would you like to restart it now to apply the updates?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            restart_application()

def get_user_first_name():
    """Get the user's first name using multiple methods."""
    logger.info("Attempting to get user's first name")
    
    # Method 1: Try getting display name from environment variables
    try:
        # On some Windows systems, this might contain the full name
        display_name = os.environ.get('USERPROFILE', '').split('\\')[-1]
        if display_name and display_name != os.environ.get('USERNAME', ''):
            logger.info(f"Found display name from USERPROFILE: {display_name}")
            # If it looks like a full name, extract first name
            if " " in display_name:
                first_name = display_name.split(" ")[0]
                logger.info(f"Extracted first name: {first_name}")
                return first_name
            return display_name
    except Exception as e:
        logger.warning(f"Error getting display name: {str(e)}")
    
    # Method 2: Try Windows registry
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Volatile Environment") as key:
            username = winreg.QueryValueEx(key, "USERNAME")[0]
            logger.info(f"Found username from registry: {username}")
            return username
    except Exception as e:
        logger.warning(f"Error getting name from registry: {str(e)}")
    
    # Method 3: Fallback to USERNAME environment variable
    try:
        username = os.environ.get('USERNAME', '')
        if username:
            logger.info(f"Using USERNAME environment variable: {username}")
            return username
    except Exception as e:
        logger.warning(f"Error getting USERNAME: {str(e)}")
    
    # Final fallback
    logger.warning("Could not determine user name, using default")
    return "User"

def _apply_window_icon(window):
    icon_path = os.path.join(get_base_dir(), 'ELYSIUM_icon.ico')
    if not os.path.exists(icon_path):
        icon_path = os.path.join(_REPO_ROOT, 'ELYSIUM_icon.ico')
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))


def _center_window(window, app):
    screen_geometry = app.primaryScreen().geometry()
    window_geometry = window.geometry()
    center_x = screen_geometry.x() + (screen_geometry.width() - window_geometry.width()) // 2
    center_y = screen_geometry.y() + (screen_geometry.height() - window_geometry.height()) // 2
    window.move(center_x, center_y)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ELYSIUM")

    splash = StartupSplash()
    _apply_window_icon(splash)
    splash.center_on_screen(app)
    splash.show()
    splash.set_progress("Starting ELYSIUM...", 5)
    app.processEvents()

    init_thread = StartupInitThread()
    main_window = {'updater': None}

    def open_main_window():
        splash.set_progress("Loading interface...", 92)
        app.processEvents()

        updater = ProgramUpdater(defer_app_status=True)
        main_window['updater'] = updater
        _apply_window_icon(updater)
        _center_window(updater, app)

        splash.set_progress("Ready", 100)
        app.processEvents()

        def reveal_main_window():
            splash.close()
            updater.show()
            apply_native_title_bar_theme(updater, updater._dark_mode)
            updater.raise_()
            updater.activateWindow()
            updater.begin_post_show_startup()

        QTimer.singleShot(250, reveal_main_window)

    init_thread.status_signal.connect(splash.set_progress)
    init_thread.finished_signal.connect(open_main_window)
    init_thread.start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    bootstrap_startup()
    try:
        main()
    except Exception as e:
        crash_log = get_crash_log_path()
        tb_text = traceback.format_exc()
        try:
            with open(crash_log, 'a', encoding='utf-8') as f:
                f.write(f"\n{'=' * 60}\n")
                f.write(datetime.datetime.now().isoformat() + "\n")
                f.write(tb_text)
        except Exception:
            pass
        logger.error(f"Fatal error in main(): {tb_text}")
        msg = (
            f"ELYSIUM failed to start.\n\n"
            f"Details were saved to:\n{crash_log}\n\n"
            f"{type(e).__name__}: {e}"
        )
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox
            if QApplication.instance() is None:
                app = QApplication([])
            QMessageBox.critical(None, "ELYSIUM Error", msg)
        except Exception:
            show_fatal_error("ELYSIUM Error", msg)
        sys.exit(1)
