from PySide6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QPushButton, QLabel, QMessageBox

class TradingStrategiesWidget(QWidget):
    def __init__(self, simulator, parent=None):
        super().__init__(parent)
        self.simulator = simulator
        self.setWindowTitle("Select Trading Strategies")
        self.layout = QVBoxLayout(self)
        self.checkboxes = {}

        # Add a label
        self.layout.addWidget(QLabel("Select strategies to activate:"))

        # Add a checkbox for each strategy
        for name, config in self.simulator.strategies.strategies.items():
            desc = config.get('description', name)
            cb = QCheckBox(desc)
            cb.setChecked(config.get('active', False))
            self.layout.addWidget(cb)
            self.checkboxes[name] = cb

        # Add a save button
        save_btn = QPushButton("Save Strategies")
        save_btn.clicked.connect(self.save_strategies)
        self.layout.addWidget(save_btn)

    def save_strategies(self):
        for name, cb in self.checkboxes.items():
            if cb.isChecked():
                self.simulator.strategies.activate(name)
            else:
                self.simulator.strategies.deactivate(name)
        QMessageBox.information(self, "Saved", "Strategies updated!")
        self.close()