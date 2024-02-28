

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QProgressBar, QMenuBar, QAction, QStatusBar
from PyQt5.QtCore import Qt
 
class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
 
    def initUI(self):
        self.setWindowTitle('My Program Launcher')
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet("background-color: #2c2c2c; color: #ffffff;")
 
        # Main layout
        layout = QVBoxLayout()
 
        # Update status label
        self.update_status = QLabel('Checking for updates...')
        layout.addWidget(self.update_status)
 
        # Program buttons
        self.program_buttons = []
        for i in range(3):
            btn = QPushButton(f'Program {i + 1}')
            btn.setStyleSheet("background-color: #3c3c3c; border: none;")
            btn.clicked.connect(self.launch_program)
            self.program_buttons.append(btn)
            layout.addWidget(btn)
 
        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
 
        # Set central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
 
        # Menu bar
        menu_bar = QMenuBar()
        file_menu = menu_bar.addMenu('File')
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        self.setMenuBar(menu_bar)
 
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Ready')
 
    def launch_program(self):
        sender = self.sender()
        program_name = sender.text()
        self.status_bar.showMessage(f'Launching {program_name}...')
        # Add code to launch the program here
 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Launcher()
    ex.show()
    sys.exit(app.exec_())
