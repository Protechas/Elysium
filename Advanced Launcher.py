import sys
import os
import requests
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QMessageBox, QToolButton, QGridLayout, QSlider
from PyQt5.QtGui import QColor, QPixmap, QIcon
from PyQt5.QtCore import Qt
from subprocess import Popen



class ProgramUpdater(QWidget):
    def __init__(self):
        super().__init__() 

        self.programs = {"DFR": "icon.jpg", "SI Multi-Tool": "icon2.jpg", "program3": "icon3.jpg"}
        self.selected_program = None
        self.init_ui()
        
        # Update programs from Github
        self.update_program_direct("DFR", "https://raw.githubusercontent.com/Romero221/DFR/main/DFR.py")
        self.update_program_direct("SI Multi-Tool", "https://raw.githubusercontent.com/Romero221/Advanced-Launcher/main")

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
            button.setIcon(QIcon(icon_path))
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

    def update_and_launch_program(self):
        if self.selected_program:
            try:
                # Update the program before launching
                self.update_program_direct(self.selected_program)

                # Launch the program (replace the path with the actual path to your program)
                program_path = os.path.join(os.getcwd(), self.selected_program, 'main_script.py')
                Popen(['python', program_path])

                QMessageBox.information(self, 'Launch', f"Launching {self.selected_program}...")
                self.close()
            except Exception as e:
                print(f"Error updating or launching {self.selected_program}: {e}")
        else:
            QMessageBox.warning(self, 'Error', 'Please select a program to launch.')

def update_program_direct(self, program_name, remote_version_url):
    try:
        local_version_file = f"{program_name}/version.txt"

        # Read Local Version
        if os.path.exists(local_version_file):
            with open(local_version_file, 'r') as file:
                local_version = file.read().strip()
        else:
            local_version = "0"

        # Fetch Remote Version
        response = requests.get(remote_version_url)
        response.raise_for_status()
        latest_version = response.text.strip()

        # Compare Versions
        if latest_version != local_version:
            print(f"Updating {program_name} to version {latest_version}...")

            # Download and Replace Files
            self.download_file(f"{remote_version_url}/main_script.py",
                              f"{program_name}/main_script.py")

            # Update Local Version
            with open(local_version_file, 'w') as file:
                file.write(latest_version)
            print(f"{program_name} updated successfully!")
        else:
            print(f"{program_name} is up to date.")
    except Exception as e:
        print(f"Error updating {program_name}: {e}")

    def launch_program(self):
        self.update_all_programs()  # Update all programs before launching
        if self.selected_program:
            QMessageBox.information(self, 'Launch', f"Launching {self.selected_program}...")
            # Add code to launch the program here
            self.close()
        else:
            QMessageBox.warning(self, 'Error', 'Please select a program to launch.')

def main():
    app = QApplication(sys.argv)
    updater = ProgramUpdater()
    updater.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
