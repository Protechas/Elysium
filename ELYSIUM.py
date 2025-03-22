import os
import logging
import datetime
import time
import sys
import platform

# Set up basic logging first - MUST BE BEFORE ANY OTHER IMPORTS OR OPERATIONS
def setup_logging():
    try:
        # Initialize logger with just a console handler first
        logger = logging.getLogger('ElysiumDependencyManager')
        logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if not logger.handlers:
            # Always set up console logging first
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(console_handler)
        
        # Try to set up file logging with retries
        max_retries = 3
        retry_delay = 1  # seconds
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'Elysium', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        for attempt in range(max_retries):
            try:
                # Generate unique log filename using timestamp, process ID, and random suffix
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                pid = os.getpid()  # Get the current process ID
                random_suffix = str(int(time.time() * 1000) % 1000)  # Use milliseconds as suffix
                log_file = os.path.join(log_dir, f'dependency_log_{timestamp}_{pid}_{random_suffix}.log')
                
                # Try to open the file to test if it's accessible
                with open(log_file, 'a') as f:
                    pass
                    
                # If successful, add the file handler
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
                logger.addHandler(file_handler)
                return logger
            except (IOError, PermissionError) as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    # Log to console that file logging is disabled
                    logger.warning(f"Could not set up file logging after {max_retries} attempts. Continuing without file logging.")
        return logger
    except Exception as e:
        # If anything fails during logging setup, set up a basic console logger
        basic_logger = logging.getLogger('ElysiumDependencyManager')
        basic_logger.setLevel(logging.INFO)
        if not basic_logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            basic_logger.addHandler(console_handler)
        basic_logger.warning(f"Failed to set up full logging system: {str(e)}. Continuing with console logging only.")
        return basic_logger

# Set up logging immediately
logger = setup_logging()

# Now import everything else
import subprocess
import requests
from PyQt5.QtCore import QSize, Qt, pyqtSignal, QRect, QThread
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QMessageBox, QToolButton, QGridLayout, QSlider, QProgressBar, QDialog, QTextEdit, QComboBox, QShortcut
from PyQt5.QtGui import QColor, QPixmap, QIcon, QPainter, QFont, QLinearGradient, QPainterPath, QFontMetrics, QKeySequence
from PyQt5.QtCore import Qt
from subprocess import Popen, PIPE
import openpyxl
import win32com.client
import re
import pkg_resources
from pkg_resources import DistributionNotFound, VersionConflict
import shutil
import tempfile
import winreg
import git  # type: ignore

# Function to check and install dependencies
def check_and_install_elysium_dependencies():
    """Check and install Elysium's own dependencies."""
    logger.info("Checking Elysium's own dependencies")
    
    # List of required packages for Elysium itself
    required_packages = [
        "PyQt5",
        "requests",
        "openpyxl",
        "pywin32",
        "wmi",
        "setuptools"  # Required for pkg_resources
    ]
    
    # Check which packages need to be installed
    missing_packages = []
    for package in required_packages:
        try:
            if package == "PyQt5":
                # Try to import a specific module from PyQt5
                __import__("PyQt5.QtCore")
            elif package == "pywin32":
                # For pywin32, try to import win32com.client
                __import__("win32com.client")
            elif package == "setuptools":
                # For setuptools, try to import pkg_resources
                __import__("pkg_resources")
            else:
                # For other packages, try to import them directly
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

# Check dependencies before importing them
try:
    # Try to import the required packages
    import requests
    import PyQt5.QtCore
    import openpyxl
    import win32com.client
    import pkg_resources
    # Try to import wmi
    import wmi  # type: ignore
    logger.info("All required packages are already installed")
except ImportError as e:
    # If any package is missing, we need to install it
    logger.warning(f"Missing dependency: {str(e)}")
    print("Some dependencies are missing. Attempting to install them...")
    
    # We can't use QMessageBox here because QApplication isn't created yet
    # So we'll use a simple console message
    if check_and_install_elysium_dependencies():
        print("Dependencies installed successfully. Launching Elysium...")
        # Need to restart the application to use the newly installed packages
        python = sys.executable
        os.execl(python, python, *sys.argv)
    else:
        print("Failed to install dependencies. Please install them manually:")
        print("pip install PyQt5 requests openpyxl pywin32 wmi setuptools")
        sys.exit(1)

# Now that we've ensured dependencies are installed, import everything else
from PyQt5.QtCore import QSize, Qt, pyqtSignal, QRect, QThread
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QMessageBox, QToolButton, QGridLayout, QSlider, QProgressBar, QDialog, QTextEdit, QComboBox, QShortcut
from PyQt5.QtGui import QColor, QPixmap, QIcon, QPainter, QFont, QLinearGradient, QPainterPath, QFontMetrics, QKeySequence
from subprocess import Popen, PIPE
import re
import pkg_resources
from pkg_resources import DistributionNotFound, VersionConflict
import openpyxl
import win32com.client
# Now it's safe to import wmi
import wmi  # type: ignore

def download_icon(url):
    try:
        filename = url.split('/')[-1]  # Extracts file name from URL
        local_path = os.path.join(os.path.expanduser('~'), 'Documents', 'Elysium', filename)
        response = requests.get(url)
        response.raise_for_status()  # Raises HTTPError for bad responses
        with open(local_path, 'wb') as f:
            f.write(response.content)
        return local_path
    except requests.RequestException as e:
        print(f"Failed to download icon: {e}")
        return None

def is_git_installed():
    """Check if Git is installed by looking for git.exe in PATH or registry."""
    logger.info("Checking if Git is installed...")
    
    # Method 1: Check if git is in PATH
    git_in_path = shutil.which('git') is not None
    if git_in_path:
        logger.info("Git found in PATH")
        return True
        
    # Method 2: Check Windows Registry
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\GitForWindows") as key:
            install_path = winreg.QueryValueEx(key, "InstallPath")[0]
            logger.info(f"Git found in registry at {install_path}")
            
            # Add Git to PATH for this session if it exists but isn't in PATH
            git_exe = os.path.join(install_path, "bin", "git.exe")
            if os.path.exists(git_exe):
                os.environ["PATH"] = os.environ["PATH"] + os.pathsep + os.path.join(install_path, "bin")
                logger.info("Added Git to PATH for this session")
                return True
    except (WindowsError, FileNotFoundError):
        # Registry key not found, try another location
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall") as key:
                # Iterate through installed programs
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                if "Git" in display_name:
                                    logger.info(f"Git found in registry: {display_name}")
                                    return True
                            except (WindowsError, FileNotFoundError):
                                continue
                    except (WindowsError, FileNotFoundError):
                        continue
        except (WindowsError, FileNotFoundError):
            pass
    
    logger.info("Git not found")
    return False

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
        
        # Update PATH to include Git without requiring restart
        # Wait a moment for installer to finish writing registry
        time.sleep(2)
        
        # Try to find Git in common installation locations
        common_git_paths = [
            r"C:\Program Files\Git\bin",
            r"C:\Program Files (x86)\Git\bin"
        ]
        
        # Check registry for installation path
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\GitForWindows") as key:
                install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                git_bin_path = os.path.join(install_path, "bin")
                if git_bin_path not in common_git_paths:
                    common_git_paths.insert(0, git_bin_path)
        except (WindowsError, FileNotFoundError):
            pass
        
        # Add Git to PATH for current session
        for git_path in common_git_paths:
            if os.path.exists(os.path.join(git_path, "git.exe")):
                os.environ["PATH"] = os.environ["PATH"] + os.pathsep + git_path
                logger.info(f"Added {git_path} to PATH for current session")
                break
        
        # Clean up
        try:
            os.remove(installer_path)
            os.rmdir(temp_dir)
            logger.info("Cleaned up temporary files")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary files: {str(e)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error installing Git: {str(e)}", exc_info=True)
        return False

class ProgramIcon(QWidget):
    clicked = pyqtSignal(str)  # Emit the program name as a signal argument

    def __init__(self, program, icon_path, icon_size=(70, 70)):
        super().__init__()
        self.program = program
        self.icon_path = icon_path
        self.icon_size = icon_size  # Added icon_size parameter
        self.highlight = False
        self.setFixedSize(100, 120)  # Increased height to accommodate program name
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.program)  # Emit the program name

    def enterEvent(self, event):
        self.highlight = True
        self.update()

    def leaveEvent(self, event):
        self.highlight = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        pixmap = QPixmap(self.icon_path)

        # Scale pixmap based on icon_size
        pixmap = pixmap.scaled(QSize(*self.icon_size), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        if self.highlight:
            highlight_gradient = QColor(0, 128, 128)  # Teal color
            gradient_rect = event.rect()
            gradient_rect.setHeight(20)  # Height of the gradient border
            gradient = QLinearGradient(gradient_rect.topLeft(), gradient_rect.bottomLeft())
            gradient.setColorAt(0, highlight_gradient)
            gradient.setColorAt(1, QColor(0, 0, 0, 0))  # Fully transparent color
            painter.fillRect(gradient_rect, gradient)

        # Center the pixmap horizontally
        pixmap_x = (self.width() - pixmap.width()) // 2
        painter.drawPixmap(pixmap_x, 5, pixmap)

        # Draw program name below the icon
        painter.setFont(QFont('Arial', 10))
        text_rect = QRect(0, 80, self.width(), 40)
        painter.drawText(text_rect, Qt.AlignCenter, self.program)
 
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
 
class GitUpdateThread(QThread):
    """Thread for updating a Git repository in the background."""
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, program_name, repo_url, repo_dir):
        super().__init__()
        self.program_name = program_name
        self.repo_url = repo_url
        self.repo_dir = repo_dir
        self.lock_file = os.path.join(self.repo_dir, '.update_lock')

    def run(self):
        """Run the update process in a separate thread."""
        try:
            logger.info(f"Starting update for {self.program_name} in thread")
            self.progress_signal.emit(f"Updating {self.program_name}...")
            
            # Make sure the directory structure exists
            os.makedirs(os.path.dirname(self.repo_dir), exist_ok=True)
            
            # Create lock file
            try:
                with open(self.lock_file, 'w') as f:
                    f.write(f"Update in progress at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception as e:
                logger.error(f"Could not create lock file: {str(e)}")
                # Continue anyway
            
            try:
                # Check if the directory already exists
                if not os.path.exists(self.repo_dir):
                    # Clone the repository
                    logger.info(f"Cloning {self.repo_url} to {self.repo_dir}")
                    self.progress_signal.emit(f"Cloning {self.program_name}...")
                    git.Repo.clone_from(self.repo_url, self.repo_dir)
                    logger.info(f"Clone completed")
                else:
                    # Update the repository
                    logger.info(f"Updating {self.program_name} in {self.repo_dir}")
                    self.progress_signal.emit(f"Pulling updates for {self.program_name}...")
                    
                    # Make sure it's a git repository
                    if not os.path.exists(os.path.join(self.repo_dir, '.git')):
                        logger.warning(f"{self.repo_dir} is not a git repository, renaming and cloning fresh")
                        # Rename the existing directory to a backup
                        timestamp = time.strftime("%Y%m%d-%H%M%S")
                        backup_dir = f"{self.repo_dir}_backup_{timestamp}"
                        os.rename(self.repo_dir, backup_dir)
                        logger.info(f"Renamed {self.repo_dir} to {backup_dir}")
                        
                        # Clone the repository fresh
                        git.Repo.clone_from(self.repo_url, self.repo_dir)
                        logger.info(f"Fresh clone completed")
                    else:
                        # Regular update
                        repo = git.Repo(self.repo_dir)
                        
                        # Ensure we're on the default branch
                        default_branch = repo.active_branch.name
                        logger.info(f"Current branch: {default_branch}")
                        
                        # Get current remote URL
                        current_remote_url = repo.remotes.origin.url
                        logger.info(f"Current remote URL: {current_remote_url}")
                        
                        # If remote URL has changed, update it
                        if current_remote_url != self.repo_url:
                            logger.info(f"Updating remote URL from {current_remote_url} to {self.repo_url}")
                            repo.remotes.origin.set_url(self.repo_url)
                        
                        # Fetch latest changes
                        repo.remotes.origin.fetch()
                        
                        # Try to reset to origin/current_branch
                        try:
                            logger.info(f"Attempting to reset to origin/{default_branch}")
                            repo.git.reset('--hard', f'origin/{default_branch}')
                        except git.exc.GitCommandError as e:
                            logger.warning(f"Failed to reset to origin/{default_branch}: {str(e)}")
                            # Try to reset to origin/main or origin/master as fallback
                            try:
                                for branch in ['main', 'master']:
                                    try:
                                        logger.info(f"Attempting to reset to origin/{branch}")
                                        repo.git.reset('--hard', f'origin/{branch}')
                                        logger.info(f"Successfully reset to origin/{branch}")
                                        break
                                    except git.exc.GitCommandError:
                                        continue
                            except Exception as e:
                                logger.error(f"Failed to reset to any branch: {str(e)}")
                                # Continue without resetting
                        
                        # Clean untracked files
                        repo.git.clean('-fd')
                
                self.progress_signal.emit(f"Updated {self.program_name} successfully")
                logger.info(f"Update completed for {self.program_name}")
            except Exception as e:
                error_msg = f"Error updating {self.program_name}: {str(e)}"
                self.progress_signal.emit(error_msg)
                logger.error(error_msg)
            finally:
                # Remove lock file
                if os.path.exists(self.lock_file):
                    try:
                        os.remove(self.lock_file)
                    except Exception as e:
                        logger.error(f"Could not remove lock file: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in update thread for {self.program_name}: {str(e)}", exc_info=True)
            self.progress_signal.emit(f"Error updating {self.program_name}")
        finally:
            # Signal that we're done
            self.finished_signal.emit()

class ProgramUpdater(QWidget):
    light_style = '''
        QWidget {
            background-color: #eee;
            color: #222;
        }
 
        QLabel {
            color: #000000;  /* Dark blue text */
        }
 
        QToolButton {
            background-color: #0066cc;  /* Dark blue background */
            color: #eee;  /* Light text */
            border: 2px solid #0066cc;  /* Dark blue border */
            border-radius: 10px;  /* Border radius for a "pop" effect */
            padding: 10px;  /* Increased padding for a "pop" effect */
            margin: 5px;
        }
 
        QToolButton:hover {
            background-color: #004080;  /* Darker blue on hover */
            border: 2px solid #004080;  /* Darker blue border on hover */
        }
    '''
 
    dark_style = '''
        QWidget {
            background-color: #222;
            color: #eee;
        }
 
        QLabel {
            color: #008080;  /* Light blue text */
        }
 
        QToolButton {
            background-color: #66ccff;  /* Light blue background */
            color: #222;  /* Dark text */
            border: 2px solid #66ccff;  /* Light blue border */
            border-radius: 10px;  /* Border radius for a "pop" effect */
            padding: 10px;  /* Increased padding for a "pop" effect */
            margin: 5px;
        }
 
        QToolButton:hover {
            background-color: #3385ff;  /* Lighter blue on hover */
            border: 2px solid #3385ff;  /* Lighter blue border on hover */
        }
    '''

    def __init__(self):
        # Call the parent constructor
        super().__init__()
        
        # Initialize variables
        self.programs = {}
        self.selected_program = None
        self.user_first_name = get_user_first_name()
        self.active_threads = []  # For tracking update threads
        self.completed_updates = 0
        self.total_updates = 0

        self.base_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'Elysium')
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
        
        self.desktop_icon_url = "https://raw.githubusercontent.com/Protechas/Elysium/main/ELYSIUM_icon.ico"
        self.desktop_icon_path = self.download_icon(self.desktop_icon_url)

        self.programs = {
            "DFR": {
                "icon_url": "https://raw.githubusercontent.com/Protechas/DFR/main/DFR.ico", 
                "script": "DFR.py",
                "repo_url": "https://github.com/Protechas/DFR.git"
            },
            "SI MultiTool": {
                "icon_url": "https://raw.githubusercontent.com/Protechas/SI-MultiTool/main/SI-Multitool.ico", 
                "script": "SI Multitool.py",
                "repo_url": "https://github.com/Protechas/SI-MultiTool.git"
            },
            "Hyper": {
                "icon_url": "https://raw.githubusercontent.com/Protechas/Hyper/master/Hyper.ico",
                "script": "Hyper.py",
                "repo_url": "https://github.com/Protechas/Hyper.git"
            },
            "Analyzer+": {
                "icon_url": "https://raw.githubusercontent.com/Protechas/AnalyzerPlus/main/Analyzer.ico", 
                "script": "Analyzer+.py",
                "repo_url": "https://github.com/Protechas/AnalyzerPlus"
            },
            "SI Op Manager": {
                "icon_url": "https://raw.githubusercontent.com/Protechas/SI-Opportunity-Manager/refs/heads/main/SI%20Opportunity%20Manager%20LOGO.ico",
                "script": "main.py",
                "repo_name": "SI-Opportunity-Manager---Current-State-02-2025",
                "repo_url": "https://github.com/Zmang24/SI-Opportunity-Manager---Current-State-02-2025"
            }
        }

        self.init_ui()
        self.update_all_programs()
        self.setStyleSheet(self.dark_style)

    def init_ui(self):
        self.setWindowTitle('ELYSIUM')
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Add version label to top right
        version_label = QLabel('v1.1', self)
        version_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        version_label.setStyleSheet('''
            QLabel {
                font-size: 8px;
                color: #666666;
                margin: 5px;
            }
        ''')
        layout.addWidget(version_label)

        # Add a welcome message with the user's name
        welcome_label = QLabel(f'Welcome, {self.user_first_name}!', self)
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet('''
            QLabel {
                font-size: 18px;
                color: #008080;
                margin-bottom: 10px;
            }
        ''')
        layout.addWidget(welcome_label)

        header_label = QLabel('ELYSIUM', self)
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet('''
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #008080;
            }
        ''')
        layout.addWidget(header_label)

        grid_layout = QGridLayout()
        grid_layout.setAlignment(Qt.AlignCenter)
        grid_layout.setSpacing(10)
        row = 0
        col = 0

        # Iterate through each program and create ProgramIcon
        for program, info in self.programs.items():
            icon_path = self.download_icon(info["icon_url"])
            if icon_path:
                icon_widget = ProgramIcon(program, icon_path)
                icon_widget.clicked.connect(self.program_clicked)
                grid_layout.addWidget(icon_widget, row, col)
                col += 1
                if col == 3:
                    row += 1
                    col = 0

        layout.addLayout(grid_layout)

        # Add progress bar and status label at the bottom
        self.status_label = QLabel('')
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet('color: #008080; font-size: 12px;')
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet('''
            QProgressBar {
                border: 2px solid #008080;
                border-radius: 5px;
                text-align: center;
                height: 10px;
            }
            QProgressBar::chunk {
                background-color: #008080;
            }
        ''')
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Add dark mode toggle button
        self.dark_mode_toggle_button = QPushButton("Light Mode", self)
        self.dark_mode_toggle_button.clicked.connect(self.toggle_dark_mode)
        self.dark_mode_toggle_button.setFixedSize(100, 40)
        self.dark_mode_toggle_button.setStyleSheet('''
            QPushButton {
                border-radius: 10px;
                background: qradialgradient(cx:0.5, cy:0.5, fx:0.5, fy:0.5, radius: 1, stop:0 teal, stop:1 teal);
                color: white;
                border: 4px solid transparent;
                padding: 15px 5px;
                margin-bottom: 15px;
                width: 200px;
            }
            QPushButton:hover {
                background: qradialgradient(cx:0.5, cy:0.5, fx:0.5, fy:0.5, radius: 1, stop:0 #008080, stop:1 #add8e6);
            }
        ''')
        
        # Add a button to view dependency logs
        self.view_logs_button = QPushButton("View Dependency Logs")
        self.view_logs_button.setFixedSize(150, 40)
        self.view_logs_button.clicked.connect(self.view_dependency_logs)
        self.view_logs_button.setStyleSheet('''
            QPushButton {
                border-radius: 10px;
                background: qradialgradient(cx:0.5, cy:0.5, fx:0.5, fy:0.5, radius: 1, stop:0 #4682B4, stop:1 #4682B4);
                color: white;
                border: 4px solid transparent;
                padding: 15px 5px;
                margin-bottom: 15px;
            }
            QPushButton:hover {
                background: qradialgradient(cx:0.5, cy:0.5, fx:0.5, fy:0.5, radius: 1, stop:0 #4682B4, stop:1 #87CEEB);
            }
        ''')
        
        # Hide the logs button by default
        self.view_logs_button.setVisible(False)
        
        # Create a keyboard shortcut (Shift+F9) to show the logs button
        self.logs_shortcut = QShortcut(QKeySequence("Shift+F9"), self)
        self.logs_shortcut.activated.connect(self.toggle_logs_button)
        
        # Add a button to update Elysium
        self.update_elysium_button = QPushButton("Update Elysium")
        self.update_elysium_button.setFixedSize(120, 40)
        self.update_elysium_button.clicked.connect(self.check_for_elysium_updates)
        self.update_elysium_button.setStyleSheet('''
            QPushButton {
                border-radius: 10px;
                background: qradialgradient(cx:0.5, cy:0.5, fx:0.5, fy:0.5, radius: 1, stop:0 teal, stop:1 teal);
                color: white;
                border: 4px solid transparent;
                padding: 15px 5px;
                margin-bottom: 15px;
                width: 200px;
            }
            QPushButton:hover {
                background: qradialgradient(cx:0.5, cy:0.5, fx:0.5, fy:0.5, radius: 1, stop:0 #008080, stop:1 #add8e6);
            }
        ''')
        
        # Create a horizontal layout for the buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.dark_mode_toggle_button)
        button_layout.addSpacing(10)  # Add spacing between buttons
        button_layout.addWidget(self.view_logs_button)
        button_layout.addSpacing(10)  # Add spacing between buttons
        button_layout.addWidget(self.update_elysium_button)
        button_layout.setAlignment(Qt.AlignCenter)
        button_layout.setContentsMargins(0, 10, 0, 10)  # Add vertical margins
        
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def download_icon(self, url):
        try:
            local_filename = os.path.join(self.base_dir, os.path.basename(url))
            response = requests.get(url)
            response.raise_for_status()
            with open(local_filename, 'wb') as f:
                f.write(response.content)
            return local_filename
        except requests.RequestException as e:
            print(f"Failed to download icon: {e}")
            return None

    def program_clicked(self, program_name):
        QMessageBox.information(self, "Program Selected", f"You selected {program_name}")
 
    def program_clicked(self, program):
        self.selected_program = program
        self.update_and_launch_program()
 
    def toggle_dark_mode(self):
        if self.dark_mode_toggle_button.text() == "Light Mode":
            self.setStyleSheet(self.light_style)
            self.dark_mode_toggle_button.setText("Dark Mode")
        else:
            self.setStyleSheet(self.dark_style)
            self.dark_mode_toggle_button.setText("Light Mode")
 
    def program_clicked(self, program):
        self.selected_program = program
        self.update_and_launch_program()
 
    def update_program_direct(self, program_name, repo_url):
        """Update a program directly from GitHub using Git."""
        try:
            folder_name = self.programs.get(program_name, {}).get('repo_name', program_name)
            elysium_dir = os.path.join(os.environ.get('USERPROFILE', ''), 'Documents', 'Elysium')
            installation_directory = os.path.join(elysium_dir, folder_name)
            lock_file = os.path.join(installation_directory, '.update_lock')
            
            # Create Elysium directory if it doesn't exist
            if not os.path.exists(elysium_dir):
                logger.info(f"Creating Elysium directory at {elysium_dir}")
                os.makedirs(elysium_dir, exist_ok=True)
            
            # Create an update status for the progress bar
            self.status_label.setText(f"Updating {program_name}...")
            
            # Update progress bar
            current_progress = int((self.completed_updates / self.total_updates) * 100)
            self.progress_bar.setValue(current_progress)
            QApplication.processEvents()
                
            # Check if directory exists but is not a git repo
            if os.path.exists(installation_directory) and not os.path.exists(os.path.join(installation_directory, '.git')):
                logger.info(f"Directory exists but not a git repo: {installation_directory}")
                # Rename the existing directory to a backup
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                backup_dir = f"{installation_directory}_backup_{timestamp}"
                logger.info(f"Renaming existing directory to {backup_dir}")
                try:
                    os.rename(installation_directory, backup_dir)
                except Exception as e:
                    logger.error(f"Failed to rename directory: {str(e)}")
                    # Try to delete the directory if we can't rename it
                    shutil.rmtree(installation_directory, ignore_errors=True)
            
            # Check if lock file exists
            if os.path.exists(lock_file):
                logger.warning(f"Update lock file exists for {program_name}, skipping update")
                self.status_label.setText(f"Skipping update for {program_name} (locked)")
                return
            
            # Create lock file
            try:
                with open(lock_file, 'w') as f:
                    f.write(f"Update in progress at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception as e:
                logger.error(f"Could not create lock file: {str(e)}")
                # Continue anyway
            
            try:
                # Check if directory exists
                if not os.path.exists(installation_directory):
                    # Clone the repository
                    logger.info(f"Cloning {repo_url} to {installation_directory}")
                    self.status_label.setText(f"Cloning {program_name}...")
                    git.Repo.clone_from(repo_url, installation_directory)
                    logger.info(f"Successfully cloned {repo_url}")
                else:
                    # Update the repository
                    logger.info(f"Updating {program_name} in {installation_directory}")
                    self.status_label.setText(f"Pulling updates for {program_name}...")
                    repo = git.Repo(installation_directory)
                    
                    # Ensure we're on the default branch
                    default_branch = repo.active_branch.name
                    logger.info(f"Current branch: {default_branch}")
                    
                    # Get current remote URL
                    current_remote_url = repo.remotes.origin.url
                    logger.info(f"Current remote URL: {current_remote_url}")
                    
                    # If remote URL has changed, update it
                    if current_remote_url != repo_url:
                        logger.info(f"Updating remote URL from {current_remote_url} to {repo_url}")
                        repo.remotes.origin.set_url(repo_url)
                    
                    # Fetch latest changes
                    repo.remotes.origin.fetch()
                    
                    # Try to reset to origin/current_branch
                    try:
                        logger.info(f"Attempting to reset to origin/{default_branch}")
                        repo.git.reset('--hard', f'origin/{default_branch}')
                    except git.exc.GitCommandError as e:
                        logger.warning(f"Failed to reset to origin/{default_branch}: {str(e)}")
                        # Try to reset to origin/main or origin/master as fallback
                        try:
                            for branch in ['main', 'master']:
                                try:
                                    logger.info(f"Attempting to reset to origin/{branch}")
                                    repo.git.reset('--hard', f'origin/{branch}')
                                    logger.info(f"Successfully reset to origin/{branch}")
                                    break
                                except git.exc.GitCommandError:
                                    continue
                        except Exception as e:
                            logger.error(f"Failed to reset to any branch: {str(e)}")
                            # Continue without resetting
                    
                    # Clean untracked files
                    repo.git.clean('-fd')
                
                logger.info(f"Successfully updated {program_name}")
                self.status_label.setText(f"Updated {program_name}")
            except Exception as e:
                error_msg = f"Error updating {program_name}: {str(e)}"
                logger.error(error_msg)
                self.status_label.setText(error_msg)
                # Continue with other updates
            finally:
                # Remove lock file
                if os.path.exists(lock_file):
                    try:
                        os.remove(lock_file)
                    except Exception as e:
                        logger.error(f"Could not remove lock file: {str(e)}")
                
                # Mark update as completed for progress
                self.completed_updates += 1
                current_progress = int((self.completed_updates / self.total_updates) * 100)
                self.progress_bar.setValue(current_progress)
                QApplication.processEvents()
                
                # Update requirements if needed
                requirements_file = os.path.join(installation_directory, 'requirements.txt')
                if os.path.exists(requirements_file):
                    try:
                        self.check_dependencies_before_launch(requirements_file)
                    except Exception as e:
                        logger.error(f"Error installing dependencies for {program_name}: {str(e)}")
                        # Continue anyway
        except Exception as e:
            logger.error(f"Unexpected error in update_program_direct for {program_name}: {str(e)}", exc_info=True)
            self.status_label.setText(f"Error updating {program_name}")
            # Make sure we mark as completed for progress bar
            self.completed_updates += 1
            
    def check_dependencies_before_launch(self, requirements_file):
        """Check and install any missing dependencies from requirements.txt."""
        try:
            logger.info(f"Checking dependencies from {requirements_file}")
            self.status_label.setText(f"Checking dependencies...")
            
            # Read requirements file
            with open(requirements_file, 'r') as f:
                required_packages = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Remove inline comments
                        if '#' in line:
                            line = line.split('#')[0].strip()
                        required_packages.append(line)
            
            if not required_packages:
                logger.info("No dependencies found in requirements file.")
                return
                
            # Install dependencies using pip
            try:
                logger.info(f"Installing dependencies: {', '.join(required_packages)}")
                self.status_label.setText("Installing dependencies...")
                
                # Run pip install in a subprocess
                process = subprocess.Popen(
                    [sys.executable, "-m", "pip", "install", "-r", requirements_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                # Get output and errors
                stdout, stderr = process.communicate()
                
                # Log output
                if stdout:
                    logger.info(f"Pip install output: {stdout}")
                if stderr:
                    logger.warning(f"Pip install errors: {stderr}")
                    
                if process.returncode == 0:
                    logger.info("Dependencies installed successfully")
                    self.status_label.setText("Dependencies installed")
                else:
                    # Try installing packages one by one if batch install fails
                    logger.warning(f"Batch installation failed with code {process.returncode}, trying individual packages")
                    self.status_label.setText("Trying individual package installation...")
                    
                    for package in required_packages:
                        try:
                            logger.info(f"Installing individual package: {package}")
                            subprocess.run(
                                [sys.executable, "-m", "pip", "install", package],
                                check=False,  # Don't raise exception on error
                                capture_output=True,
                                text=True
                            )
                        except Exception as pkg_error:
                            logger.error(f"Error installing {package}: {str(pkg_error)}")
                            # Continue with other packages
            except Exception as e:
                logger.error(f"Error installing dependencies: {str(e)}")
                # Continue anyway, as some dependencies might already be installed
        except Exception as e:
            logger.error(f"Error checking dependencies: {str(e)}")
            # Continue with launch anyway

    def view_dependency_logs(self):
        try:
            # Path to logs directory
            log_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'Elysium', 'logs')
            
            # Check if logs directory exists
            if not os.path.exists(log_dir):
                QMessageBox.information(self, 'No Logs', 'No dependency logs found.')
                return
                
            # Get list of log files
            log_files = [f for f in os.listdir(log_dir) if f.startswith('dependency_log_') and f.endswith('.log')]
            
            if not log_files:
                QMessageBox.information(self, 'No Logs', 'No dependency logs found.')
                return
                
            # Sort log files by date (newest first)
            log_files.sort(reverse=True)
            
            # Create a dialog to display logs
            dialog = QDialog(self)
            dialog.setWindowTitle('Dependency Logs')
            dialog.setMinimumSize(800, 600)
            
            layout = QVBoxLayout()
            
            # Create a combo box for selecting log files
            log_selector = QComboBox()
            for log_file in log_files:
                # Extract timestamp from the filename - now with the PID part
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
                        with open(os.path.join(log_dir, selected_file), 'r') as f:
                            content = f.read()
                            log_content.setText(content)
                    except Exception as e:
                        log_content.setText(f"Error loading log file: {str(e)}")
            
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

    def toggle_logs_button(self):
        # Toggle the visibility of the logs button
        current_visibility = self.view_logs_button.isVisible()
        self.view_logs_button.setVisible(not current_visibility)
        
        # Log the action
        if not current_visibility:
            logger.info("Logs button revealed via Shift+F9 shortcut")
            # Optional: Show a brief message to confirm the action
            self.status_label.setText("Logs button revealed (Shift+F9)")
        else:
            logger.info("Logs button hidden via Shift+F9 shortcut")
            self.status_label.setText("")

    def check_for_elysium_updates(self):
        """Check for updates to Elysium itself."""
        try:
            self.status_label.setText("Checking for Elysium updates...")
            
            # Define the Elysium repository URL
            elysium_repo_url = "https://github.com/Protechas/Elysium.git"
            elysium_dir = os.path.join(os.environ['USERPROFILE'], 'Documents', 'Elysium')
            
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
            # Restart the application
            python = sys.executable
            os.execl(python, python, *sys.argv)

    def is_si_op_manager_running(self):
        """Check if SI Op Manager is already running."""
        try:
            logger.info("Checking if SI Op Manager is already running")
            
            # Get the correct repo name and script name for SI Op Manager
            info = self.programs.get("SI Op Manager", {})
            if not info:
                logger.warning("SI Op Manager info not found in programs dictionary")
                return False
                
            script_name = info.get("script", "main.py")
            folder_name = info.get('repo_name', "SI Op Manager")
            
            # Path to the script
            program_path = os.path.join(os.environ.get('USERPROFILE', ''), 'Documents', 'Elysium', folder_name, script_name)
            
            # If the directory doesn't exist, SI Op Manager can't be running
            if not os.path.exists(os.path.dirname(program_path)):
                logger.info(f"SI Op Manager directory doesn't exist: {os.path.dirname(program_path)}")
                return False
            
            # Normalize path for comparison
            program_path = os.path.normpath(program_path)
            
            # Method 1: Try the file lock test first (simpler and more reliable)
            installation_directory = os.path.join(os.environ.get('USERPROFILE', ''), 'Documents', 'Elysium', folder_name)
            if os.path.exists(installation_directory):
                lock_test_file = os.path.join(installation_directory, '.update_lock_test')
                try:
                    # Try to create a temporary file in the directory to check if it's locked
                    with open(lock_test_file, 'w') as f:
                        f.write('test')
                    os.remove(lock_test_file)
                    # We could write to the directory, so it's probably not locked
                    logger.info("SI Op Manager directory is not locked, it's probably not running")
                except (IOError, PermissionError) as e:
                    # If we can't write to the directory, it's likely locked by a running process
                    logger.info(f"SI Op Manager directory is locked: {str(e)}")
                    return True
            
            # Method 2: Use WMI to check for the process (this might fail, so it's our backup)
            try:
                import wmi
                c = wmi.WMI()
                
                # Look for python processes running the script
                for process in c.Win32_Process():
                    try:
                        cmd_line = process.CommandLine or ""
                        # Check if this process is running the SI Op Manager script
                        if program_path in cmd_line.replace('"', ''):
                            logger.info(f"Found SI Op Manager running with PID {process.ProcessId}")
                            return True
                    except Exception as proc_err:
                        # Skip any processes we can't query
                        logger.debug(f"Error checking process: {str(proc_err)}")
                        continue
            except Exception as wmi_err:
                logger.warning(f"WMI check failed: {str(wmi_err)}")
                # Continue even if WMI fails
                pass
                
            # If we get here, SI Op Manager is probably not running
            return False
        except Exception as e:
            logger.error(f"Error in is_si_op_manager_running: {str(e)}", exc_info=True)
            # If there's an error in detection, assume it's not running to allow Elysium to start
            return False

    def thread_finished(self, program_name):
        """Handle a thread finishing."""
        self.completed_updates += 1
        self.progress_bar.setValue(int((self.completed_updates / self.total_updates) * 100))
        
        if self.completed_updates == self.total_updates:
            self.progress_bar.hide()
            self.status_label.setText("All updates completed!")
            self.active_threads.clear()
            self.completed_updates = 0

    def update_status(self, message):
        """Update the status label with a message."""
        self.status_label.setText(message)
        QApplication.processEvents()  # Ensure the UI updates

    def update_program_threaded(self, program_name, git_repo_url):
        """Update a program using a background thread."""
        try:
            # Skip updating SI Op Manager if it's already running
            if program_name == "SI Op Manager":
                try:
                    if self.is_si_op_manager_running():
                        logger.info(f"Skipping update for {program_name} because it appears to be running")
                        self.update_status(f"Skipping update for {program_name} (already running)")
                        self.completed_updates += 1
                        self.progress_bar.setValue(int((self.completed_updates / self.total_updates) * 100))
                        return
                except Exception as e:
                    logger.error(f"Error checking if SI Op Manager is running: {str(e)}")
                    # Continue with update attempt
            
            # Check if Git is installed before attempting to update
            if not is_git_installed():
                logger.warning(f"Cannot update {program_name}: Git is not installed")
                self.update_status(f"Cannot update {program_name}: Git is not installed")
                self.completed_updates += 1
                return
            
            # Get the folder name from program info
            folder_name = self.programs.get(program_name, {}).get('repo_name', program_name)
            program_directory = os.path.join(os.environ.get('USERPROFILE', ''), 'Documents', 'Elysium', folder_name)

            # Create and start the update thread
            update_thread = GitUpdateThread(program_name, git_repo_url, program_directory)
            update_thread.progress_signal.connect(self.update_status)
            update_thread.finished_signal.connect(lambda: self.thread_finished(program_name))
            
            self.active_threads.append(update_thread)
            update_thread.start()
        except Exception as e:
            error_msg = f"Error updating {program_name}: {str(e)}"
            self.update_status(error_msg)
            logger.error(error_msg, exc_info=True)
            # Make sure we count this as completed
            self.completed_updates += 1

    def update_all_programs(self):
        # Check if Git is installed
        if not is_git_installed():
            logger.info("Git not found, prompting user for installation")
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
                    return
            else:
                QMessageBox.warning(
                    self, 
                    'Update Cancelled', 
                    "Cannot update programs without Git."
                )
                return
        
        # Prepare for updates
        self.completed_updates = 0
        self.total_updates = 0
        
        # Get list of programs to update
        programs_to_update = []
        for program_name in self.programs:
            try:
                # Skip SI Op Manager if it's already running
                if program_name == "SI Op Manager":
                    try:
                        is_running = self.is_si_op_manager_running()
                        if is_running:
                            logger.info("Skipping SI Op Manager update during startup (already running)")
                            continue
                    except Exception as e:
                        logger.error(f"Error checking if SI Op Manager is running: {str(e)}")
                        # Skip update on error to be safe
                        continue
                
                # Add program to the update list
                programs_to_update.append(program_name)
            except Exception as e:
                logger.error(f"Error processing program {program_name}: {str(e)}")
                # Continue with other programs
        
        # Update total count
        self.total_updates = len(programs_to_update)
            
        # If no programs to update, exit early
        if self.total_updates == 0:
            logger.info("No programs to update")
            self.status_label.setText("No programs to update")
            return
            
        # Set up progress bar
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        # Launch updates using threads
        for program_name in programs_to_update:
            try:
                self.update_program_threaded(program_name, self.programs[program_name]["repo_url"])
            except Exception as e:
                logger.error(f"Error starting update for {program_name}: {str(e)}")
                # Count as completed to keep the progress bar accurate
                self.completed_updates += 1

    def update_and_launch_program(self):
        if self.selected_program:
            try:
                program_info = self.programs[self.selected_program]
                program_name = self.selected_program
                script_name = program_info["script"]
                folder_name = program_info.get('repo_name', program_name)
                git_repo_url = program_info.get('repo_url', '')

                # Get the installation directory using the correct folder name
                installation_directory = os.path.join(os.environ.get('USERPROFILE', ''), 'Documents', 'Elysium', folder_name)
                
                # Check if SI Op Manager is already running (skip update if it is)
                skip_update = False
                if program_name == "SI Op Manager":
                    try:
                        if self.is_si_op_manager_running():
                            logger.info(f"SI Op Manager appears to be already running")
                            self.status_label.setText("SI Op Manager is already running")
                            skip_update = True
                    except Exception as e:
                        logger.error(f"Error checking if SI Op Manager is running: {str(e)}")
                        # Don't skip update if we can't determine status

                # Check if Git is installed before updating (only if we're not skipping the update)
                if git_repo_url and not skip_update and not is_git_installed():
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
                
                # Update the program before launching (if Git is available and we're not skipping updates)
                # Use direct update for single program launch since we want to wait for completion
                if git_repo_url and not skip_update and is_git_installed():
                    try:
                        # Set up update progress tracking
                        self.completed_updates = 0
                        self.total_updates = 1
                        self.progress_bar.setMaximum(100)
                        self.progress_bar.setValue(0)
                        self.progress_bar.show()
                        
                        # Update directly (not threaded)
                        self.update_program_direct(program_name, git_repo_url)
                        
                        # Hide progress bar when done
                        self.progress_bar.hide()
                    except Exception as e:
                        logger.error(f"Error updating {program_name}: {str(e)}")
                        # Continue to launching the program even if update fails

                # Check for requirements.txt and install dependencies if needed
                requirements_file = os.path.join(installation_directory, 'requirements.txt')
                if os.path.exists(requirements_file) and not skip_update:
                    self.status_label.setText(f"Checking dependencies for {program_name}...")
                    try:
                        self.check_dependencies_before_launch(requirements_file)
                    except Exception as e:
                        logger.error(f"Error checking dependencies: {str(e)}")
                        # Continue to launching the program even if dependency check fails

                # Launch the program
                program_path = os.path.join(installation_directory, script_name)
                if os.path.exists(program_path):
                    try:
                        logger.info(f"Launching {program_name} from {program_path}")
                        self.status_label.setText(f"Launching {program_name}...")
                        
                        # Execute the program using Python
                        python_executable = sys.executable
                        
                        # Pass any additional arguments if specified in program_info
                        args = program_info.get('args', [])
                        
                        # Create a custom environment to pass to the subprocess
                        env = os.environ.copy()
                        
                        # Define the command to run
                        cmd = [python_executable, program_path] + args
                        
                        # Launch the program
                        if platform.system() == 'Windows':
                            # Hide the console window for all Windows programs
                            import subprocess
                            startupinfo = subprocess.STARTUPINFO()
                            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            startupinfo.wShowWindow = 0  # SW_HIDE
                            subprocess.Popen(cmd, env=env, startupinfo=startupinfo)
                        else:
                            # For non-Windows platforms (e.g., Linux, macOS)
                            subprocess.Popen(cmd, env=env)
                        
                        logger.info(f"Successfully launched {program_name}")
                        self.status_label.setText(f"Launched {program_name}")
                    except Exception as e:
                        error_msg = f"Failed to launch {program_name}: {str(e)}"
                        logger.error(error_msg)
                        self.status_label.setText(error_msg)
                        QMessageBox.critical(self, 'Launch Failed', error_msg)
                else:
                    error_msg = f"Cannot find {program_name} at {program_path}"
                    logger.error(error_msg)
                    self.status_label.setText(error_msg)
                    QMessageBox.critical(self, 'Program Not Found', error_msg)
            except Exception as e:
                error_msg = f"Error launching {self.selected_program}: {str(e)}"
                logger.error(error_msg)
                self.status_label.setText(error_msg)
                QMessageBox.critical(self, 'Error', error_msg)
        else:
            QMessageBox.warning(self, 'Error', 'Please select a program to launch.')

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

def main():
    # First, set up basic logging to console (in case file logging fails due to missing dependencies)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Check and install Elysium's own dependencies before creating QApplication
    try:
        # Try to import the required packages
        import requests
        import PyQt5.QtCore
        import openpyxl
        import win32com.client
        import pkg_resources
        # Try to import wmi
        import wmi  # type: ignore
        logger.info("All required packages are already installed")
    except ImportError as e:
        # If any package is missing, we need to install it
        logger.warning(f"Missing dependency: {str(e)}")
        print("Some dependencies are missing. Attempting to install them...")
        
        # We can't use QMessageBox here because QApplication isn't created yet
        # So we'll use a simple console message
        if check_and_install_elysium_dependencies():
            print("Dependencies installed successfully. Launching Elysium...")
            # Need to restart the application to use the newly installed packages
            python = sys.executable
            os.execl(python, python, *sys.argv)
        else:
            print("Failed to install dependencies. Please install them manually:")
            print("pip install PyQt5 requests openpyxl pywin32 wmi setuptools")
            sys.exit(1)
    
    # Now we can safely create the QApplication
    app = QApplication(sys.argv)
    updater = ProgramUpdater()
    
    # Get the screen geometry to calculate the center position
    screen_geometry = app.primaryScreen().geometry()
    window_geometry = updater.geometry()

    # Calculate the center position
    center_x = int((screen_geometry.width() - window_geometry.width()) / 2)
    center_y = int((screen_geometry.height() - window_geometry.height()) / 2)

    # Set the window position to the center
    updater.move(center_x, center_y)
    
    # Retrieve the path to the user's Documents folder and append the 'Elysium' folder name
    icon_path = os.path.join(os.path.expanduser('~'), 'Documents', 'Elysium', 'ELYSIUM_icon.ico')

    # Set the window icon if it exists
    if os.path.exists(icon_path):
        updater.setWindowIcon(QIcon(icon_path))

    updater.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
