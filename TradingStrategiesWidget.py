import sqlite3
import Stock
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QCheckBox, QPushButton, QLabel, QMessageBox, QDoubleSpinBox, QSpinBox, QHBoxLayout
)

class TradingStrategiesWidget(QDialog):
    def __init__(self, simulator, stock, parent=None):
        super().__init__(parent)
        self.simulator = simulator
        self.stock = stock
        self.ticker = stock.get_ticker()
        self.setMinimumSize(300, 200)
        self.resize(400, 300)
        self.setWindowTitle("Select Trading Strategies")
        self.layout = QVBoxLayout(self)
        self.checkboxes = {}
        self.param_widgets = {}

        self.layout.addWidget(QLabel("Select strategies to activate and set parameters:"))

        # Get strategies for this stock, or use defaults if not set yet
        stock_strats = self.simulator.strategies.stock_strategies.get(self.ticker, {})
        default_strats = {
            'take_profit': {'description': 'Take Profit', 'threshold': 0.2, 'active': False},
            'stop_loss': {'description': 'Stop Loss', 'threshold': 0.1, 'active': False},
            'dollar_cost_avg': {'description': 'Dollar Cost Avg', 'shares': 5, 'interval': 7, 'active': False}
        }
        for name, config in default_strats.items():
            # Use stock-specific config if it exists
            config = {**config, **stock_strats.get(name, {})}
            row = QHBoxLayout()
            desc = config.get('description', name)
            cb = QCheckBox(desc)
            cb.setChecked(config.get('active', False))
            row.addWidget(cb)
            self.checkboxes[name] = cb
            params = {}
            if 'threshold' in config:
                spin = QDoubleSpinBox()
                spin.setDecimals(2)
                spin.setSingleStep(0.01)
                spin.setRange(0.01, 1.0)
                spin.setValue(config['threshold'])
                spin.setSuffix(" (as fraction, e.g. 0.2 for 20%)")
                row.addWidget(spin)
                params['threshold'] = spin
            if 'shares' in config:
                spin = QSpinBox()
                spin.setRange(1, 1000)
                spin.setValue(config['shares'])
                row.addWidget(QLabel("Shares:"))
                row.addWidget(spin)
                params['shares'] = spin
            if 'interval' in config:
                spin = QSpinBox()
                spin.setRange(1, 365)
                spin.setValue(config['interval'])
                row.addWidget(QLabel("Interval:"))
                row.addWidget(spin)
                params['interval'] = spin

            self.param_widgets[name] = params
            self.layout.addLayout(row)

        save_btn = QPushButton("Save Strategies")
        save_btn.clicked.connect(self.save_strategies)
        self.layout.addWidget(save_btn)

        self.setMinimumSize(400, 200)
        self.resize(500, 300)

    def save_strategies(self):
        for name, cb in self.checkboxes.items():
            params = {}
            for param, widget in self.param_widgets[name].items():
                params[param] = widget.value()
            if cb.isChecked():
                self.simulator.strategies.activate(self.ticker, name, **params)
            else:
                self.simulator.strategies.deactivate(self.ticker, name)
        QMessageBox.information(self, "Saved", "Strategies updated for this stock!")
        self.accept()
        parent = self.parent()
        if hasattr(parent, "simWindow") and hasattr(parent.simWindow, "update_balances"):
            parent.simWindow.update_balances()
            self.simulator.strategies.save_to_db(self.simulator.get_sim_id())
    
