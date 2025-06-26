import sys
import os
from PySide6.QtWidgets import QApplication
import app
from app import TradingSimulatorApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TradingSimulatorApp()
    window.show()
    sys.exit(app.exec())