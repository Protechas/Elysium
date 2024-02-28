import sys
import os
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox
from PyQt5.QtGui import QColor
 
class ProgramUpdater(QWidget):
    def __init__(self):
        super().__init__()
 
        self.programs = ["program1", "program2", "program3"]
        self.selected_program = None
 
        self.init_ui()
 
    def init_ui(self):
        self.setWindowTitle('Program Updater and Launcher')
        self.setGeometry(100, 100, 400, 300)
 
        # Dark theme with light blue accent
        dark_style = '''
            QWidget {
                background-color: #222;
                color: #eee;
            }
 
            QLabel {
                color: #66ccff;  /* Light blue text */
            }
 
            QListWidget {
                background-color: #333;
                color: #eee;
                border: 1px solid #66ccff;  /* Light blue border */
            }
 
            QPushButton {
                background-color: #66ccff;  /* Light blue background */
                color: #222;  /* Dark text */
                border: 1px solid #66ccff;  /* Light blue border */
                padding: 5px;
                margin: 5px;
            }
 
            QPushButton:hover {
                background-color: #3385ff;  /* Lighter blue on hover */
                border: 1px solid #3385ff;  /* Lighter blue border on hover */
            }
        '''
 
        self.setStyleSheet(dark_style)
 
        layout = QVBoxLayout()
 
        label = QLabel('Select a program to launch:')
        layout.addWidget(label)
 
        program_list = QListWidget(self)
        program_list.addItems(self.programs)
        program_list.clicked.connect(self.program_clicked)
        layout.addWidget(program_list)
 
        update_button = QPushButton('Update Program', self)
        update_button.clicked.connect(self.update_program)
        layout.addWidget(update_button)
 
        update_all_button = QPushButton('Update All Programs', self)
        update_all_button.clicked.connect(self.update_all_programs)
        layout.addWidget(update_all_button)
 
        launch_button = QPushButton('Launch Program', self)
        launch_button.clicked.connect(self.launch_program)
        layout.addWidget(launch_button)
 
        self.setLayout(layout)
 
    def program_clicked(self, item):
        self.selected_program = item.text()
 
    def update_program(self):
        if self.selected_program:
            try:
                local_version_file = f"{self.selected_program}/version.txt"
                remote_version_url = f"https://raw.githubusercontent.com/yourusername/yourrepository/main/{self.selected_program}/latest_version.txt"
 
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
                    print(f"Updating {self.selected_program} to version {latest_version}...")
 
                    # Download and Replace Files
                    self.download_file(f"https://raw.githubusercontent.com/yourusername/yourrepository/main/{self.selected_program}/main_script.py",
                                      f"{self.selected_program}/main_script.py")
 
                    # Update Local Version
                    with open(local_version_file, 'w') as file:
                        file.write(latest_version)
                    print(f"{self.selected_program} updated successfully!")
                else:
                    print(f"{self.selected_program} is up to date.")
            except Exception as e:
                print(f"Error updating {self.selected_program}: {e}")
        else:
            QMessageBox.warning(self, 'Error', 'Please select a program to update.')
 
    def update_all_programs(self):
        for program in self.programs:
            self.update_program_direct(program)
 
    def update_program_direct(self, program_name):
        try:
            local_version_file = f"{program_name}/version.txt"
            remote_version_url = f"https://raw.githubusercontent.com/yourusername/yourrepository/main/{program_name}/latest_version.txt"
 
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
                self.download_file(f"https://raw.githubusercontent.com/yourusername/yourrepository/main/{program_name}/main_script.py",
                                  f"{program_name}/main_script.py")
 
                # Update Local Version
                with open(local_version_file, 'w') as file:
                    file.write(latest_version)
                print(f"{program_name} updated successfully!")
            else:
                print(f"{program_name} is up to date.")
        except Exception as e:
            print(f"Error updating {program_name}: {e}")
 
    def download_file(self, url, local_filename):
        try:
            with requests.get(url, stream=True) as r:
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        except requests.RequestException as e:
            print(f"Error downloading file from {url}: {e}")
 
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
 
