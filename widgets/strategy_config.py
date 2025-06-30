from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QCheckBox, 
    QDoubleSpinBox, QDialogButtonBox, QWidget
)

class StrategyConfigDialog(QDialog):
    def __init__(self, simulator, parent=None):
        super().__init__(parent)
        self.simulator = simulator
        self.setWindowTitle("Trading Strategies")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Strategy Checkboxes
        self.checkboxes = {}
        for name, config in self.simulator.strategies.strategies.items():
            group = QWidget()
            group_layout = QVBoxLayout(group)
            
            cb = QCheckBox(config.get('description', 'No description'))
            cb.setChecked(config['active'])
            self.checkboxes[name] = cb
            group_layout.addWidget(cb)

            # Add parameter controls
            if 'threshold' in config:
                spin = QDoubleSpinBox()
                spin.setRange(0.01, 1.0)
                spin.setSingleStep(0.01)
                spin.setValue(config['threshold'])
                spin.setPrefix("Threshold: ")
                spin.setSuffix("%")
                group_layout.addWidget(spin)

            layout.addWidget(group)

        # Dialog Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save_strategies)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save_strategies(self):
        for name, cb in self.checkboxes.items():
            if cb.isChecked():
                self.simulator.strategies.activate(name)
            else:
                self.simulator.strategies.deactivate(name)
        self.accept()