########## Starting by installing Python ######################################################### STUFF IN #'S IS A Wip #################################################################################################################################


import subprocess
import sys
import os
 
def install_python():
    # Download Python installer - example URL, needs to be updated to the actual download link
    python_installer_url = "https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe"
    installer_path = "python_installer.exe"
    subprocess.run(["curl", python_installer_url, "-o", installer_path])
    # Install Python silently
    subprocess.run([installer_path, "/quiet", "InstallAllUsers=1", "PrependPath=1"])
    
########## This independent Import below needs to be here, so below in the CLone Github will processess, and cant be used before installing python, or after the Github repo ##########
import shutil
    
def clone_github_repo():
    repo_url = "https://github.com/Romero221/Advanced-Launcher.git"
    clone_path = os.path.join(os.environ["TEMP"], "Advanced Launcher")  # Temporarily clone here
    target_path = "C:\Program Files (x86)"
    
    # Clone the repository
    subprocess.run(["git", "clone", repo_url, clone_path])
    
    # Move the cloned repository to the target location
    # This might require administrative privileges
    if os.path.exists(target_path):
        shutil.rmtree(target_path)  # Remove the target directory if it already exists
    shutil.move(clone_path, target_path)
    print(f"Repository cloned to {target_path}")

def create_shortcut():
    desktop_path = os.path.join(os.environ["USERPROFILE"], "Desktop")
    shortcut_path = os.path.join(desktop_path, "Advanced Launcher.lnk")
    target_path = "C:\\Program Files (x86)\\Advanced Launcher\\<main_executable_or_script>"
    # Adjust <main_executable_or_script> to the actual path of the application's executable or main script
    with open(shortcut_path, 'w') as shortcut_file:
        shortcut_file.write(f'[InternetShortcut]\nURL=file:///{target_path}\n')
    print(f"Shortcut created at {shortcut_path}")
    
########## Installing Required Libraries to run properly #################################################################################################################################################################################################

required_packages = {
    'pymupdf': 'fitz',
    'requests': 'requests',
    'PyQt5': 'PyQt5',
    'numpy': 'numpy',
    'pandas': 'pandas',
    'cx_Freeze': 'cx_Freeze',
    'openpyxl': 'openpyxl',
    'PyPDF2': 'PyPDF2',
    # Add other required packages and their import names here
}
def install_and_import(package, import_name=None):
    if not import_name:
        import_name = package
    try:
        # Try importing the package
        __import__(import_name)
    except ImportError:
        # If the package is not found, install it
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        __import__(import_name)
for package, import_name in required_packages.items():
    install_and_import(package, import_name)
    
########## Executing Program ##########
 
import requests
from PyQt5.QtCore import QSize, Qt, pyqtSignal, QRect
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QMessageBox, QToolButton, QGridLayout, QSlider
from PyQt5.QtGui import QColor, QPixmap, QIcon, QPainter, QFont, QLinearGradient, QPainterPath, QFontMetrics
from PyQt5.QtCore import Qt
from subprocess import Popen
import openpyxl
 
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
        pixmap = pixmap.scaled(QSize(*self.icon_size), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
 
        if self.highlight:
            highlight_gradient = QColor(0, 128, 128)  # Teal color
            highlight_gradient.setAlpha(255)  # Set opacity (fully opaque)
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
        text_rect = QRect(0, 60, self.width(), 40)
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
        super().__init__()
        # Updated programs dictionary to include script names and icon paths
        self.programs = {
            "DFR": {"icon": "C:\\Users\\SEang\\Desktop\\excel_formatting_icon.ico", "script": "DFR.py"},
            "SI MultiTool": {"icon": "C:\\Users\\SEang\\Desktop\\pdf_multitool_icon.ico", "script": "SI Multitool.py"},
            "program3": {"icon": "C:\\Users\\SEang\\Desktop\\practice_icon.ico", "script": "script3.py"},#########################
            "program4": {"icon": "C:\\Users\\SEang\\Desktop\\ELYSIUM_icon.ico", "script": "script4.py"},#########################
            "program5": {"icon": "icon5.jpg", "script": "script5.py"},#########################
            ################################
            # ADD ADDITIONAL PROGRAMS HERE #
            ################################
        }
        self.selected_program = None
        self.init_ui()
 
        # Update programs from GitHub
        self.update_program_direct("DFR", "https://github.com/Romero221/DFR.git")
        self.update_program_direct("SI MultiTool", "https://github.com/ShaneProtech/SI-MultiTool.git")
 
        # Set dark mode by default
        self.setStyleSheet(self.dark_style)
 
    def init_ui(self):
        self.setWindowTitle('ELYSIUM')
        self.setGeometry(100, 100, 400, 300)
 
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)  # Center the header label vertically
 
        # Header label
        header_label = QLabel('ELYSIUM', self)
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet('''
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #008080; /* Blue text */
            }
        ''')
        layout.addWidget(header_label)
 
        # Create a grid layout for the icons
        grid_layout = QGridLayout()
        grid_layout.setAlignment(Qt.AlignCenter)
        grid_layout.setSpacing(10)  # Adjust spacing between icons
        row = 0
        col = 0
 
        for program, program_info in self.programs.items():
            icon_widget = ProgramIcon(program, program_info["icon"])
            icon_widget.clicked.connect(self.program_clicked)  # Connect to the program_clicked method directly
            grid_layout.addWidget(icon_widget, row, col)
            col += 1
            if col == 3:
                row += 1
                col = 0
 
        layout.addLayout(grid_layout)
 
        # Add Dark Mode/Light Mode button
        self.dark_mode_toggle_button = QPushButton("Light Mode", self)
        self.dark_mode_toggle_button.clicked.connect(self.toggle_dark_mode)
        self.dark_mode_toggle_button.setFixedSize(100, 40)
        self.dark_mode_toggle_button.setStyleSheet('''
            QPushButton {
                border-radius: 10px;
                background: qradialgradient(cx:0.5, cy:0.5, fx:0.5, fy:0.5, radius: 1, stop:0 teal, stop:1 teal);
                color: white; /* White text */
                border: 4px solid transparent; /* Transparent border */
                padding: 15px 5px; /* Larger padding */
                margin-bottom: 15px; /* Add margin at the bottom */
                width: 200px; /* Set width */
            }
            QPushButton:hover {
                background: qradialgradient(cx:0.5, cy:0.5, fx:0.5, fy:0.5, radius: 1, stop:0 #008080, stop:1 #add8e6); /* Darker teal on hover */
            }
        ''')
        layout.addWidget(self.dark_mode_toggle_button)
 
        self.setLayout(layout)
 
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
 
    def update_program_direct(self, program_name, git_repo_url):
        program_directory = os.path.join(os.getcwd(), program_name)
        try:
            if not os.path.exists(program_directory):
                # Clone the repo if the directory does not exist
                print(f"Cloning {program_name} from {git_repo_url}...")
                subprocess.check_call(['git', 'clone', git_repo_url, program_directory])
                print(f"{program_name} cloned successfully.")
            else:
                # Stash local changes or reset to HEAD before pulling updates
                print(f"Updating {program_name}...")
                subprocess.check_call(['git', '-C', program_directory, 'stash'])  # Stash local changes
                subprocess.check_call(['git', '-C', program_directory, 'pull'])
                print(f"{program_name} updated successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error updating {program_name}: {e}")
 
    def update_and_launch_program(self):
        if self.selected_program:
            try:
                program_info = self.programs[self.selected_program]
                git_repo_url = "https://github.com/placeholder/repo.git"  # Placeholder URL
                program_name = self.selected_program
                script_name = program_info["script"]
                # Update the program before launching
                self.update_program_direct(program_name, git_repo_url)
 
                # Launch the program
                program_path = os.path.join(os.getcwd(), program_name, script_name)
                launch_command = ['python', program_path]
 
                # Pass the dark mode style sheet to the launched program
                launch_env = os.environ.copy()
                launch_env['LAUNCHER_STYLE'] = self.dark_style
 
                subprocess.Popen(launch_command, env=launch_env)
 
                QMessageBox.information(self, 'Launch', f"Launching {program_name}...")
                self.close()
            except Exception as e:
                QMessageBox.warning(self, 'Error', f"Error updating or launching {program_name}: {e}")
        else:
            QMessageBox.warning(self, 'Error', 'Please select a program to launch.')
 
    def download_file(self, url, local_filename):
        try:
            with requests.get(url, stream=True) as r:
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        except requests.RequestException as e:
            print(f"Error downloading file from {url}: {e}")
 
def main():
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
    
    updater.show()
    updater.setWindowIcon(QIcon(r"C:\\Users\\SEang\\Desktop\\ELYSIUM_icon.ico"))

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
    install_python()
    clone_github_repo()
    create_shortcut()
