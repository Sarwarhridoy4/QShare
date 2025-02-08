import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import FileSharingClient
from utils.helpers import load_font

if __name__ == "__main__":
    app = QApplication(sys.argv)
    load_font(app)
    
    client = FileSharingClient()
    client.show()
    app.exec() 