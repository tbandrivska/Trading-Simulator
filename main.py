import sys
import os
from PySide6.QtWidgets import QApplication
from app import TradingSimulatorApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TradingSimulatorApp()
    window.show()
    sys.exit(app.exec())