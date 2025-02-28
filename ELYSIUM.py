import subprocess
import sys
import os
import requests
from PyQt5.QtCore import QSize, Qt, pyqtSignal, QRect, QThread
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QMessageBox, QToolButton, QGridLayout, QSlider, QProgressBar
from PyQt5.QtGui import QColor, QPixmap, QIcon, QPainter, QFont, QLinearGradient, QPainterPath, QFontMetrics
from PyQt5.QtCore import Qt
from subprocess import Popen, PIPE
import openpyxl
import win32com.client
import re

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
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, program_name, git_repo_url, program_directory):
        super().__init__()
        self.program_name = program_name
        self.git_repo_url = git_repo_url
        self.program_directory = program_directory

    def run(self):
        try:
            if not os.path.exists(self.program_directory) or not os.listdir(self.program_directory):
                self.progress_signal.emit(f"Cloning {self.program_name}...")
                # Use shallow clone (--depth 1) and single branch for faster cloning
                process = subprocess.Popen(
                    ['git', 'clone', '--depth', '1', '--single-branch', self.git_repo_url, self.program_directory],
                    stdout=PIPE, stderr=PIPE, universal_newlines=True
                )
            else:
                self.progress_signal.emit(f"Updating {self.program_name}...")
                # Fetch only the latest changes
                process = subprocess.Popen(
                    ['git', '-C', self.program_directory, 'pull', '--depth', '1', '--no-tags'],
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
            else:
                self.progress_signal.emit(f"Error updating {self.program_name}.")

        except Exception as e:
            self.progress_signal.emit(f"Error: {str(e)}")
        finally:
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
        super().__init__()
        self.base_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'Elysium')
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

        self.desktop_icon_url = "https://raw.githubusercontent.com/Protechas/Elysium/main/ELYSIUM_icon.ico"
        self.desktop_icon_path = self.download_icon(self.desktop_icon_url)
        
        self.active_threads = []
        self.completed_updates = 0
        self.total_updates = 0

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
                "script": "run.py",
                "repo_name": "SI Opportunity Manager",
                "repo_url": "https://github.com/Protechas/SI-Opportunity-Manager"
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
        layout.addWidget(self.dark_mode_toggle_button)

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
 
    def update_program_direct(self, program_name, git_repo_url):
        try:
            base_directory = os.path.join(os.environ['USERPROFILE'], 'Documents', 'Elysium')
            folder_name = self.programs[program_name].get('repo_name', program_name)
            program_directory = os.path.join(base_directory, folder_name)

            # Create and start the update thread
            update_thread = GitUpdateThread(program_name, git_repo_url, program_directory)
            update_thread.progress_signal.connect(self.update_status)
            update_thread.finished_signal.connect(lambda: self.thread_finished(program_name))
            
            self.active_threads.append(update_thread)
            update_thread.start()

        except Exception as e:
            self.update_status(f"Error updating {program_name}: {str(e)}")

    def thread_finished(self, program_name):
        self.completed_updates += 1
        self.progress_bar.setValue(int((self.completed_updates / self.total_updates) * 100))
        
        if self.completed_updates == self.total_updates:
            self.progress_bar.hide()
            self.status_label.setText("All updates completed!")
            self.active_threads.clear()
            self.completed_updates = 0

    def update_status(self, message):
        self.status_label.setText(message)

    def update_all_programs(self):
        self.completed_updates = 0
        self.total_updates = len(self.programs)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        for program_name, info in self.programs.items():
            self.update_program_direct(program_name, info["repo_url"])

    def update_and_launch_program(self):
        if self.selected_program:
            try:
                program_info = self.programs[self.selected_program]
                program_name = self.selected_program
                script_name = program_info["script"]
                folder_name = program_info.get('repo_name', program_name)
                git_repo_url = program_info.get('repo_url', '')

                # Update the program before launching
                if git_repo_url:
                    self.update_program_direct(program_name, git_repo_url)

                # Get the installation directory using the correct folder name
                installation_directory = os.path.join(os.environ['USERPROFILE'], 'Documents', 'Elysium', folder_name)

                # Launch the program
                program_path = os.path.join(installation_directory, script_name)
                
                if not os.path.exists(program_path):
                    raise FileNotFoundError(f"Could not find {script_name} in {installation_directory}")

                # Pass the dark mode style sheet to the launched program
                launch_env = os.environ.copy()
                launch_env['LAUNCHER_STYLE'] = self.dark_style
                launch_env['PYTHONPATH'] = installation_directory

                # Special handling for SI Op Manager
                if program_name == "SI Op Manager":
                    python_path = sys.executable  # Use the same Python that's running ELYSIUM
                    
                    subprocess.Popen(
                        [python_path, program_path],
                        env=launch_env,
                        cwd=installation_directory,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    # Original launch method for all other programs
                    subprocess.Popen(
                        ['python', program_path],
                        env=launch_env,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )

                QMessageBox.information(self, 'Launch', f"Launching {program_name}...")

            except Exception as e:
                QMessageBox.warning(self, 'Error', f"Error updating or launching {program_name}: {e}")
        else:
            QMessageBox.warning(self, 'Error', 'Please select a program to launch.')

def main():
    app = QApplication(sys.argv)
    updater = ProgramUpdater()  # Assuming ProgramUpdater is a QWidget or similar
    
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

    # Set the window icon
    updater.setWindowIcon(QIcon(icon_path))

    updater.show()
        
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
