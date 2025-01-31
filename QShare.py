import sys
import os
import socket
import threading
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QListWidget, QProgressBar, QLabel, QMessageBox, QHBoxLayout, QSpacerItem,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QMetaObject, pyqtSlot, Q_ARG, QSettings
from PyQt6.QtGui import QFont, QPixmap, QIcon, QFontDatabase, QCloseEvent
from PyQt6.QtWidgets import QComboBox

# Server Configuration
HOST = "0.0.0.0"
BUFFER_SIZE = 4096
BROADCAST_PORT = 5002
BROADCAST_INTERVAL = 2  # Seconds

class FileSharingClient(QWidget):
    def __init__(self):
        super().__init__()
        self.discovered_devices = dict()
        self.selected_device = None
        self.local_ip = self.get_local_ip()
        self.current_theme = "dark"  # Default theme
        self.init_ui()
        self.init_server()
        self.init_network()
        self.active_transfers = 0
        self.load_settings()

class FileSharingServer(QThread):
    incoming_file = pyqtSignal(str, str, object)  # filename, ip, handler
    server_error = pyqtSignal(str)

    def __init__(self, save_path="received_files"):
        super().__init__()
        self.save_path = save_path
        self.port = 0
        self._is_running = True
        os.makedirs(self.save_path, exist_ok=True)

    def run(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((HOST, 0))
            self.port = server_socket.getsockname()[1]
            server_socket.listen(5)
            server_socket.settimeout(1)  # Allow periodic checking of running flag

            while self._is_running:
                try:
                    client_socket, client_addr = server_socket.accept()
                    handler = ClientHandler(client_socket, self.save_path)
                    handler.incoming_file.connect(self.incoming_file)
                    handler.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    self.server_error.emit(f"Server error: {str(e)}")
            
            server_socket.close()
        except Exception as e:
            self.server_error.emit(f"Failed to start server: {str(e)}")

    def stop(self):
        self._is_running = False

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

        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            self.client_socket.close()

    def save_file(self):
        try:
            filepath = os.path.join(self.save_path, self.filename)
            with open(filepath, "wb") as f:
                while True:
                    data = self.client_socket.recv(BUFFER_SIZE)
                    if not data:
                        break
                    f.write(data)
            print(f"Received: {self.filename}")
        except Exception as e:
            print(f"File save error: {e}")

    @pyqtSlot(bool)
    def set_response(self, response):
        self.response = response
        self.quit()

class ServerBroadcaster(QThread):
    def __init__(self, port):
        super().__init__()
        self.port = port
        self._is_running = True

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while self._is_running:
            try:
                message = f"FILE_SHARE_SERVER:{self.port}".encode()
                sock.sendto(message, ('<broadcast>', BROADCAST_PORT))
                time.sleep(BROADCAST_INTERVAL)
            except Exception as e:
                print(f"Broadcast error: {e}")
        sock.close()

    def stop(self):
        self._is_running = False

class ClientDiscoveryListener(QThread):
    device_discovered = pyqtSignal(str, int)  # ip, port
    discovery_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._is_running = True

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', BROADCAST_PORT))
        sock.settimeout(1)

        while self._is_running:
            try:
                data, addr = sock.recvfrom(1024)
                if data.startswith(b"FILE_SHARE_SERVER:"):
                    _, port_str = data.split(b':')
                    port = int(port_str)
                    self.device_discovered.emit(addr[0], port)
            except socket.timeout:
                continue
            except Exception as e:
                self.discovery_error.emit(f"Discovery error: {str(e)}")
        sock.close()

    def stop(self):
        self._is_running = False

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
                sock.settimeout(10)
                try:
                    sock.connect((self.ip, self.port))
                except (ConnectionRefusedError, socket.timeout) as e:
                    self.finished.emit(False, "Connection failed. Device might be offline.")
                    return

                filename = os.path.basename(self.file_path)
                sock.send(filename.encode())

                response = sock.recv(BUFFER_SIZE)
                if response != b"ACCEPT":
                    self.finished.emit(False, "Transfer rejected by recipient.")
                    return

                filesize = os.path.getsize(self.file_path)
                sent = 0

                with open(self.file_path, "rb") as f:
                    while (data := f.read(BUFFER_SIZE)):
                        try:
                            sock.send(data)
                            sent += len(data)
                            progress = int((sent / filesize) * 100)
                            self.progress_updated.emit(progress)
                        except (BrokenPipeError, ConnectionResetError):
                            self.finished.emit(False, "Connection lost during transfer.")
                            return

                self.finished.emit(True, f"File {filename} sent successfully.")
        except Exception as e:
            self.finished.emit(False, f"Transfer error: {str(e)}")

class FileSharingClient(QWidget):
    def __init__(self):
        super().__init__()
        self.discovered_devices = dict()  # {device_id: (ip, port, last_seen)}
        self.selected_device = None
        self.local_ip = self.get_local_ip()
        self.init_ui()
        self.init_server()
        self.init_network()
        self.active_transfers = 0

    def init_ui(self):
        self.setWindowTitle("QShare")
        self.setMinimumSize(600, 700)
        
        # Load application icon
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, "res", "app_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Configure UI styling
        self.setStyleSheet("""
            QWidget {
                background-color: #1A1A1A;
                color: #FFFFFF;
                font-family: 'Segoe UI';
            }
            QPushButton {
                background-color: #2D2D2D;
                border: 1px solid #3D3D3D;
                padding: 12px;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
                border-color: #4D4D4D;
            }
            QPushButton:disabled {
                background-color: #252525;
                color: #666666;
            }
            QListWidget {
                background-color: #252525;
                border: 1px solid #3D3D3D;
                border-radius: 4px;
                padding: 8px;
            }
            QProgressBar {
                background: #252525;
                border: 1px solid #3D3D3D;
                border-radius: 4px;
                padding: 2px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: #4CAF50;
                border-radius: 3px;
            }
            QLabel {
                color: #CCCCCC;
                padding: 4px 0;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

         # Logo and theme selector
        logo_layout = QHBoxLayout()
        
        # Logo
        self.logo_label = QLabel()
        logo_path = os.path.join(base_dir, "res", "app_logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatio)
            self.logo_label.setPixmap(pixmap)
        logo_layout.addWidget(self.logo_label)

        # Theme switcher
        theme_layout = QVBoxLayout()
        self.theme_label = QLabel("Theme:")
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Dark", "Light", "Blue", "High Contrast"])
        self.theme_selector.currentTextChanged.connect(self.change_theme)
        theme_layout.addWidget(self.theme_label)
        theme_layout.addWidget(self.theme_selector)
        logo_layout.addLayout(theme_layout)

        layout.addLayout(logo_layout)
        # Device list
        layout.addWidget(QLabel("Available Devices:"))
        self.device_list = QListWidget()
        self.device_list.setMinimumHeight(150)
        self.device_list.itemClicked.connect(self.select_device)
        layout.addWidget(self.device_list)

        # File selection
        file_layout = QHBoxLayout()
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(150)
        file_buttons = QVBoxLayout()
        self.select_btn = QPushButton("Select Files")
        self.select_btn.clicked.connect(self.select_files)
        self.clear_btn = QPushButton("Clear Files")
        self.clear_btn.clicked.connect(self.clear_files)
        file_buttons.addWidget(self.select_btn)
        file_buttons.addWidget(self.clear_btn)
        file_buttons.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        file_layout.addWidget(self.file_list)
        file_layout.addLayout(file_buttons)
        layout.addLayout(file_layout)

        # Progress bar
        layout.addWidget(QLabel("Transfer Progress:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_bar)

        # Send button
        self.send_btn = QPushButton("Send Files")
        self.send_btn.clicked.connect(self.send_files)
        self.send_btn.setEnabled(False)
        layout.addWidget(self.send_btn)

        self.setLayout(layout)
    
    def change_theme(self, theme_name):
        theme_name = theme_name.lower()
        self.current_theme = theme_name
        self.apply_theme(theme_name)
        self.save_settings()

    def apply_theme(self, theme_name):
        themes = {
            "dark": """
                QWidget { background-color: #1A1A1A; color: #FFFFFF; }
                QPushButton { background-color: #2D2D2D; border: 1px solid #3D3D3D; }
                QPushButton:hover { background-color: #3D3D3D; }
                QListWidget { background-color: #252525; border: 1px solid #3D3D3D; }
                QProgressBar { background: #252525; border: 1px solid #3D3D3D; }
                QProgressBar::chunk { background: #4CAF50; }
                QLabel { color: #CCCCCC; }
            """,
            "light": """
                QWidget { background-color: #FFFFFF; color: #333333; }
                QPushButton { background-color: #F0F0F0; border: 1px solid #CCCCCC; }
                QPushButton:hover { background-color: #E0E0E0; }
                QListWidget { background-color: #FAFAFA; border: 1px solid #CCCCCC; }
                QProgressBar { background: #FAFAFA; border: 1px solid #CCCCCC; }
                QProgressBar::chunk { background: #2196F3; }
                QLabel { color: #666666; }
            """,
            "blue": """
                QWidget { background-color: #0A1929; color: #B2BAC2; }
                QPushButton { background-color: #173A5E; border: 1px solid #1E4A76; }
                QPushButton:hover { background-color: #1E4A76; }
                QListWidget { background-color: #12263D; border: 1px solid #1E4A76; }
                QProgressBar { background: #12263D; border: 1px solid #1E4A76; }
                QProgressBar::chunk { background: #3D8FD1; }
                QLabel { color: #8D9BA8; }
            """,
            "high contrast": """
                QWidget { background-color: #000000; color: #FFFFFF; }
                QPushButton { background-color: #222222; border: 2px solid #FFFFFF; }
                QPushButton:hover { background-color: #444444; }
                QListWidget { background-color: #111111; border: 2px solid #FFFFFF; }
                QProgressBar { background: #111111; border: 2px solid #FFFFFF; }
                QProgressBar::chunk { background: #FFD700; }
                QLabel { color: #FFFFFF; font-weight: bold; }
            """
        }
        
        self.setStyleSheet(themes.get(theme_name, themes["dark"]))
        self.update()  # Force UI refresh

    def load_settings(self):
        settings = QSettings("QShare", "Settings")
        theme = settings.value("Theme", "dark")
        self.theme_selector.setCurrentText(theme.capitalize())
        self.apply_theme(theme)

    def save_settings(self):
        settings = QSettings("QShare", "Settings")
        settings.setValue("Theme", self.current_theme)

    def closeEvent(self, event: QCloseEvent):
        self.save_settings()

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def init_server(self):
        self.server = FileSharingServer()
        self.server.incoming_file.connect(self.handle_incoming_file)
        self.server.server_error.connect(self.show_error)
        self.server.start()

        self.broadcaster = ServerBroadcaster(self.server.port)
        self.broadcaster.start()

    def init_network(self):
        self.discovery_listener = ClientDiscoveryListener()
        self.discovery_listener.device_discovered.connect(self.update_devices)
        self.discovery_listener.discovery_error.connect(self.show_error)
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
        now = time.time()
        device_id = f"{ip}:{port}"
        
        # Ignore self device
        if ip == self.local_ip and port == self.server.port:
            return

        # Update last seen time
        self.discovered_devices[device_id] = (ip, port, now)

        # Remove stale devices (older than 15 seconds)
        current_time = time.time()
        stale = [k for k, v in self.discovered_devices.items() if (current_time - v[2]) > 15]
        for k in stale:
            del self.discovered_devices[k]

        # Update list widget
        current_items = {self.device_list.item(i).text() for i in range(self.device_list.count())}
        updated_items = set(self.discovered_devices.keys())

        # Remove missing items
        for item in current_items - updated_items:
            for i in range(self.device_list.count()):
                if self.device_list.item(i).text() == item:
                    self.device_list.takeItem(i)
                    break

        # Add new items
        for item in updated_items - current_items:
            self.device_list.addItem(item)

    def select_device(self, item):
        self.selected_device = item.text()
        self.update_send_button_state()

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        if files:
            self.file_list.addItems(files)
            self.update_send_button_state()

    def clear_files(self):
        self.file_list.clear()
        self.update_send_button_state()

    def update_send_button_state(self):
        has_files = self.file_list.count() > 0
        has_selection = self.selected_device is not None
        self.send_btn.setEnabled(has_files and has_selection)

    def send_files(self):
        if not self.selected_device:
            QMessageBox.warning(self, "Error", "Please select a device first!")
            return

        # Check if selected device is self
        selected_ip, selected_port = self.selected_device.split(':')
        if selected_ip == self.local_ip and int(selected_port) == self.server.port:
            QMessageBox.warning(self, "Invalid Selection", 
                              "You've selected your own device. Please choose another recipient.")
            return

        # Confirm before sending
        confirm = QMessageBox.question(
            self,
            "Confirm Transfer",
            f"Send {self.file_list.count()} files to {self.selected_device}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.active_transfers += 1
        self.set_ui_enabled(False)

        ip, port = selected_ip, int(selected_port)
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            file_path = item.text()
            thread = FileSenderThread(file_path, ip, port)
            thread.progress_updated.connect(self.progress_bar.setValue)
            thread.finished.connect(self.handle_transfer_complete)
            thread.start()

    def handle_transfer_complete(self, success, msg):
        self.active_transfers -= 1
        if self.active_transfers == 0:
            self.set_ui_enabled(True)
            self.progress_bar.setValue(0)

        if success:
            QMessageBox.information(self, "Transfer Complete", msg)
        else:
            QMessageBox.critical(self, "Transfer Failed", msg)

    def set_ui_enabled(self, enabled):
        self.select_btn.setEnabled(enabled)
        self.clear_btn.setEnabled(enabled)
        self.send_btn.setEnabled(enabled and self.file_list.count() > 0)
        self.device_list.setEnabled(enabled)

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def closeEvent(self, event: QCloseEvent):
        # Gracefully stop all network components
        self.server.stop()
        self.broadcaster.stop()
        self.discovery_listener.stop()
        
        # Wait for threads to finish
        self.server.wait(2000)
        self.broadcaster.wait(2000)
        self.discovery_listener.wait(2000)
        
        event.accept()

def load_font(app):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(base_dir, "res", "Roboto-Regular.ttf")
    
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            app.setFont(QFont(font_family, 10))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    load_font(app)
    
    client = FileSharingClient()
    client.show()
    app.exec()