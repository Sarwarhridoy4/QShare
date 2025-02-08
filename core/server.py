"""
Server-side operations for QShare.

This module handles the server-side logic including:
- Incoming file handling
- Server broadcasting
"""

from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
import socket
import os

class ClientHandler(QThread):
    """Handles incoming file transfers from clients."""
    
    incoming_file = pyqtSignal(str, str, object)  # filename, ip, handler

    def __init__(self, client_socket, save_path):
        super().__init__()
        self.client_socket = client_socket
        self.save_path = save_path
        self.filename = None
        self.response = None

    def run(self):
        try:
            self.filename = self.client_socket.recv(4096).decode()
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
                    data = self.client_socket.recv(4096)
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

class FileSharingServer(QThread):
    incoming_file = pyqtSignal(str, str, object)  # filename, ip, handler
    server_error = pyqtSignal(str)

    def __init__(self, save_path="received_files"):
        super().__init__()
        self.save_path = save_path
        os.makedirs(self.save_path, exist_ok=True)
        self._is_running = True

    def run(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind(('0.0.0.0', 0))
            self.port = server_socket.getsockname()[1]
            server_socket.listen(5)
            while self._is_running:
                client_socket, client_addr = server_socket.accept()
                handler = ClientHandler(client_socket, self.save_path)
                handler.incoming_file.connect(self.incoming_file)
                handler.start()
        except Exception as e:
            self.server_error.emit(f"Server error: {str(e)}")

    def stop(self):
        self._is_running = False 