"""
Client-side operations for QShare.

This module handles the client-side logic including:
- File selection
- Device discovery
- File sending
"""

from PyQt6.QtWidgets import QWidget, QFileDialog, QMessageBox, QListWidgetItem, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal
from core.network import FileSenderThread  # Ensure this import is present


class FileSharingClient(QWidget):
    # Signals and slots for client operations
    file_selected = pyqtSignal(list)
    file_sent = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()
        self.file_list = []  # List to store selected files
        self.received_files_dir = "received_files"  # Default directory
        self.init_ui()

    def init_ui(self):
        # Initialize UI components
        layout = QVBoxLayout(self)

        # Add a button to select the directory for received files
        self.select_dir_btn = QPushButton("Select Directory for Received Files")
        self.select_dir_btn.clicked.connect(self.select_directory)
        layout.addWidget(self.select_dir_btn)

        # Add a label to show the current directory
        self.dir_label = QLabel(f"Current Directory: {self.received_files_dir}")
        layout.addWidget(self.dir_label)

        # Other UI components...
        pass  # Add this line if the method is not yet implemented

    def select_directory(self):
        # Open a dialog to select a directory
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", self.received_files_dir)
        if directory:
            self.received_files_dir = directory
            self.dir_label.setText(f"Current Directory: {self.received_files_dir}")

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        if files:
            self.file_list.extend(files)
            self.file_selected.emit(files)
            self.update_send_button_state()

    def send_files(self):
        if not self.file_list:
            QMessageBox.warning(self, "Error", "No files selected!")
            return

        # Logic to send files
        for file_path in self.file_list:
            thread = FileSenderThread(file_path, self.selected_device_ip, self.selected_device_port)
            thread.finished.connect(self.handle_file_sent)
            thread.start()

    def handle_file_sent(self, success, message):
        self.file_sent.emit(success, message)
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Failure", message)

    def update_send_button_state(self):
        # Logic to enable/disable send button based on file selection
        pass  # Add this line if the method is not yet implemented 