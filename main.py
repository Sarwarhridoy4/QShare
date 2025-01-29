import sys
import os
import socket
import threading
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QListWidget, QProgressBar, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QMetaObject, pyqtSlot, Q_ARG
from PyQt6.QtGui import QFont

# Server Configuration
HOST = "0.0.0.0"
BUFFER_SIZE = 4096
BROADCAST_PORT = 5002
BROADCAST_INTERVAL = 2  # Seconds


class FileSharingServer(QThread):
    incoming_file = pyqtSignal(str, str, object)  # filename, ip, handler

    def __init__(self, save_path="received_files"):
        super().__init__()
        self.save_path = save_path
        self.port = 0
        os.makedirs(self.save_path, exist_ok=True)

    def run(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((HOST, 0))
        self.port = server_socket.getsockname()[1]
        server_socket.listen(5)
        print(f"Server listening on {HOST}:{self.port}")

        while True:
            client_socket, client_addr = server_socket.accept()
            handler = ClientHandler(client_socket, self.save_path)
            handler.incoming_file.connect(self.incoming_file)
            handler.start()


class ClientHandler(QThread):
    incoming_file = pyqtSignal(str, str, object)  # filename, ip, handler

    def __init__(self, client_socket, save_path):
        super().__init__()
        self.client_socket = client_socket
        self.save_path = save_path
        self.filename = None
        self.response = None

    def run(self):
        try:
            self.filename = self.client_socket.recv(BUFFER_SIZE).decode()
            ip = self.client_socket.getpeername()[0]
            self.incoming_file.emit(self.filename, ip, self)
            self.exec()  # Wait for user response

            if self.response:
                self.client_socket.send(b"ACCEPT")
                self.save_file()
            else:
                self.client_socket.send(b"REJECT")
                self.client_socket.close()

        except Exception as e:
            print(f"Error: {e}")
            self.client_socket.close()

    def save_file(self):
        filepath = os.path.join(self.save_path, self.filename)
        with open(filepath, "wb") as f:
            while True:
                data = self.client_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                f.write(data)
        print(f"Received: {self.filename}")

    @pyqtSlot(bool)
    def set_response(self, response):
        self.response = response
        self.quit()


class ServerBroadcaster(QThread):
    def __init__(self, port):
        super().__init__()
        self.port = port

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while True:
            try:
                message = f"FILE_SHARE_SERVER:{self.port}".encode()
                sock.sendto(message, ('<broadcast>', BROADCAST_PORT))
                time.sleep(BROADCAST_INTERVAL)
            except Exception as e:
                print(f"Broadcast error: {e}")


class ClientDiscoveryListener(QThread):
    device_discovered = pyqtSignal(str, int)  # ip, port

    def __init__(self):
        super().__init__()

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', BROADCAST_PORT))
        sock.settimeout(1)

        while True:
            try:
                data, addr = sock.recvfrom(1024)
                if data.startswith(b"FILE_SHARE_SERVER:"):
                    _, port_str = data.split(b':')
                    port = int(port_str)
                    self.device_discovered.emit(addr[0], port)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Discovery error: {e}")


class FileSenderThread(QThread):
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, file_path, ip, port):
        super().__init__()
        self.file_path = file_path
        self.ip = ip
        self.port = port

    def run(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.ip, self.port))
                filename = os.path.basename(self.file_path)
                sock.send(filename.encode())

                response = sock.recv(BUFFER_SIZE)
                if response != b"ACCEPT":
                    self.finished.emit(False, "Transfer rejected.")
                    return

                filesize = os.path.getsize(self.file_path)
                sent = 0

                with open(self.file_path, "rb") as f:
                    while (data := f.read(BUFFER_SIZE)):
                        sock.send(data)
                        sent += len(data)
                        progress = int((sent / filesize) * 100)
                        self.progress_updated.emit(progress)

                self.finished.emit(True, f"File {filename} sent successfully.")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


class FileSharingClient(QWidget):
    def __init__(self):
        super().__init__()
        self.discovered_devices = set()
        self.selected_device = None
        self.init_ui()
        self.init_server()
        self.init_network()

    def init_ui(self):
        self.setWindowTitle("FileShare")
        self.setGeometry(100, 100, 500, 500)
        self.setStyleSheet("""
            QWidget { background-color: #2E3440; color: #D8DEE9; }
            QPushButton { 
                background-color: #5E81AC; 
                padding: 10px; 
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #81A1C1; }
            QListWidget { 
                background-color: #4C566A; 
                border-radius: 5px; 
                padding: 5px;
            }
            QProgressBar {
                background: #3B4252;
                border-radius: 5px;
                color: white;
            }
            QProgressBar::chunk {
                background: #88C0D0;
                border-radius: 5px;
            }
        """)

        layout = QVBoxLayout()

        self.device_list = QListWidget()
        self.device_list.itemClicked.connect(self.select_device)
        layout.addWidget(QLabel("Available Devices:"))
        layout.addWidget(self.device_list)

        self.file_list = QListWidget()
        layout.addWidget(QLabel("Selected Files:"))
        layout.addWidget(self.file_list)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        btn_layout = QVBoxLayout()
        self.select_btn = QPushButton("Select Files")
        self.select_btn.clicked.connect(self.select_files)
        self.send_btn = QPushButton("Send Files")
        self.send_btn.clicked.connect(self.send_files)
        self.send_btn.setEnabled(False)

        btn_layout.addWidget(self.select_btn)
        btn_layout.addWidget(self.send_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def init_server(self):
        self.server = FileSharingServer()
        self.server.incoming_file.connect(self.handle_incoming_file)
        self.server.start()

        self.broadcaster = ServerBroadcaster(self.server.port)
        self.broadcaster.start()

    def init_network(self):
        self.discovery_listener = ClientDiscoveryListener()
        self.discovery_listener.device_discovered.connect(self.update_devices)
        self.discovery_listener.start()

    def handle_incoming_file(self, filename, ip, handler):
        response = QMessageBox.question(
            self,
            "Incoming File",
            f"Accept {filename} from {ip}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        handler.set_response(response == QMessageBox.StandardButton.Yes)

    def update_devices(self, ip, port):
        device_id = f"{ip}:{port}"
        if device_id not in self.discovered_devices:
            self.discovered_devices.add(device_id)
            self.device_list.addItem(device_id)

    def select_device(self, item):
        self.selected_device = item.text()
        self.send_btn.setEnabled(self.file_list.count() > 0)

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        if files:
            self.file_list.clear()
            self.file_list.addItems(files)
            self.send_btn.setEnabled(bool(self.selected_device))

    def send_files(self):
        if not self.selected_device:
            QMessageBox.warning(self, "Error", "Please select a device first!")
            return

        ip, port = self.selected_device.split(':')
        port = int(port)

        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            file_path = item.text()
            thread = FileSenderThread(file_path, ip, port)
            thread.progress_updated.connect(self.progress_bar.setValue)
            thread.finished.connect(lambda success, msg: self.on_send_finished(success, msg))
            thread.start()

    def on_send_finished(self, success, msg):
        if success:
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.critical(self, "Error", msg)
        self.progress_bar.setValue(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = FileSharingClient()
    client.show()
    app.exec()