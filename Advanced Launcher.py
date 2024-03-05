#####################################################################################################################################################################################################
#                                                                                                                                                                                                   #
#                                                                                                                                                                                                   #
#                                                                                                                                                                                                   #
#                                                                     Installing The Proper Packages before Using DFR and Multitool                                                                 #
#                                                                                                                                                                                                   #
#                                                                                                                                                                                                   #
#                                                                                                                                                                                                   #
#####################################################################################################################################################################################################

import pkg_resources
import subprocess
import sys
import os
import requests
from PyQt5.QtCore import QSize, Qt, pyqtSignal, QRect
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QMessageBox, QToolButton, QGridLayout, QSlider
from PyQt5.QtGui import QColor, QPixmap, QIcon, QPainter, QFont, QLinearGradient
from PyQt5.QtCore import Qt
from subprocess import Popen

required_packages = {
    
    'pymupdf': 'fitz',
    'requests' : 'requests',
    'PyQt5' : 'PyQt5',
    'numpy' : 'numpy',
    'pandas' : 'pandas',
    'cx_Freeze' : 'cx_Freeze',
    'openpyxl' : 'openpyxl',
 
    # Add other required packages and their import names here
    # ('package_name': 'import_name',)
}

def install_and_import(package, import_name=None):
    if not import_name:
        import_name = package
    try:
        # Try importing the package
        pkg_resources.require(package)
        __import__(import_name)
    except ImportError:
        # If the package is not found, install it
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        __import__(import_name)

for package, import_name in required_packages.items():
    install_and_import(package, import_name)


#####################################################################################################################################################################################################
#                                                                                                                                                                                                   #
#                                                                                                                                                                                                   #
#                                                                                                                                                                                                   #
#                                                                                      Running the Advanced Launcher                                                                                #
#                                                                                                                                                                                                   #
#                                                                                                                                                                                                   #
#                                                                                                                                                                                                   #
#####################################################################################################################################################################################################


class ProgramUpdater(QWidget):
    def __init__(self):
        super().__init__()
        # Updated programs dictionary to include script names
        self.programs = {
            "DFR": {"icon": "icon.jpg", "script": "DFR.py"},
            "SI MultiTool": {"icon": "icon2.jpg", "script": "SI Multitool.py"},
            "program3": {"icon": "icon3.jpg", "script": "script3.py"}  # Example entry
        }
        self.selected_program = None
        self.init_ui()

        # Update programs from GitHub
        self.update_program_direct("DFR", "https://github.com/Romero221/DFR.git")
        self.update_program_direct("SI MultiTool", "https://github.com/ShaneProtech/SI-MultiTool.git")


    def init_ui(self):
        self.setWindowTitle('Program Updater and Launcher')
        self.setGeometry(100, 100, 400, 300)

        # Dark theme with light blue accent
        self.dark_style = '''
            QWidget {
                background-color: #222;
                color: #eee;
            }

            QLabel {
                color: #66ccff;  /* Light blue text */
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
        self.light_style = '''
            QWidget {
                background-color: #eee;
                color: #222;
            }

            QLabel {
                color: #0066cc;  /* Dark blue text */
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
        self.setStyleSheet(self.dark_style)

        layout = QGridLayout()

        label = QLabel('Select a program to launch:')
        layout.addWidget(label, 0, 0, 1, 3)  # Row 0, Column 0, Span 1 row and 3 columns

        row = 1
        col = 0

        for program, icon_path in self.programs.items():
            button = QToolButton(self)
            button.setText(program)
            button.clicked.connect(lambda _, p=program: self.program_clicked(p))
            layout.addWidget(button, row, col)

            # Increment the column index for the next button
            col += 1

        self.setLayout(layout)

        # Toggle button for dark/light mode
        self.dark_mode_toggle_button = QPushButton("Dark Mode", self)
        self.dark_mode_toggle_button.clicked.connect(self.toggle_dark_mode)
        layout.addWidget(self.dark_mode_toggle_button, 0, 2, 1, 1)

    def toggle_dark_mode(self):
        if self.dark_mode_toggle_button.text() == "Dark Mode":
            self.setStyleSheet(self.light_style)
            self.dark_mode_toggle_button.setText("Light Mode")
        else:
            self.setStyleSheet(self.dark_style)
            self.dark_mode_toggle_button.setText("Dark Mode")

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
                # Pull the latest changes if the directory exists
                print(f"Updating {program_name}...")
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
                subprocess.Popen(['python', program_path])

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
    updater.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
