"""
Network components for QShare.

This module contains the core networking functionality including:
- Server broadcaster for device discovery
- Client discovery listener
- File sender thread implementation
"""

import socket
from PyQt6.QtCore import QThread, pyqtSignal
import time
import os

BUFFER_SIZE = 4096
BROADCAST_PORT = 5002

class ServerBroadcaster(QThread):
    """Broadcasts server presence over UDP for device discovery."""
    
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
                time.sleep(2)
            except Exception as e:
                print(f"Broadcast error: {e}")
        sock.close()

    def stop(self):
        self._is_running = False

class ClientDiscoveryListener(QThread):
    """Listens for broadcast messages to discover available devices."""
    
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
    """Handles sending files to a specified IP and port."""
    
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, file_path, ip, port):
        super().__init__()
        self.file_path = file_path
        self.ip = ip
        self.port = port

    def run(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(10)
                sock.connect((self.ip, self.port))
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
                        sock.send(data)
                        sent += len(data)
                        progress = int((sent / filesize) * 100)
                        self.progress_updated.emit(progress)

                self.finished.emit(True, f"File {filename} sent successfully.")
        except Exception as e:
            self.finished.emit(False, f"Transfer error: {str(e)}") 