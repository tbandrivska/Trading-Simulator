from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLabel,
    QTabWidget
)
import sqlite3
from datetime import datetime
from PySide6.QtCore import Qt
from widgets.strategy_config import StrategyConfigDialog
from widgets.performance_chart import PerformanceChart
from TradingSimulator import TradingSimulator

class TradingSimulatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.simulator = TradingSimulator()
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Trading Simulator")
        self.resize(1200, 800)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Control Bar
        control_bar = QHBoxLayout()
        self.btn_strategies = QPushButton("Configure Strategies")
        self.btn_run = QPushButton("Run Simulation")
        control_bar.addWidget(self.btn_strategies)
        control_bar.addWidget(self.btn_run)
        main_layout.addLayout(control_bar)

        # Tab Interface
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Portfolio Tab
        portfolio_tab = QWidget()
        self.tabs.addTab(portfolio_tab, "Portfolio")
        self._setup_portfolio_tab(portfolio_tab)

        # Connect Signals
        self.btn_strategies.clicked.connect(self._open_strategy_config)
        self.btn_run.clicked.connect(self._run_simulation)

    def _setup_portfolio_tab(self, tab):
        layout = QVBoxLayout(tab)
        
        # Summary Widget
        self.summary_label = QLabel()
        self.summary_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.summary_label)

        # Performance Chart
        self.chart = PerformanceChart()
        layout.addWidget(self.chart)
        #Update the UI
        self._update_ui()
    

    def _open_strategy_config(self):
        dialog = StrategyConfigDialog(self.simulator, self)
        dialog.exec()
        #Update the UI
        self._update_ui()
    

    def _run_simulation(self):
        try:
            # 1. Initialize simulation first
            sim_id = f"sim_{datetime.now().strftime('%H%M%S')}"
            self.simulator.new_simulation(sim_id, days=30)
        
            # 2. Then run
            self.simulator.run_simulation()
             # 3. Update the UI
            self._update_ui()
    
        
        except sqlite3.Error as e:
            self._show_error(f"Database error: {str(e)}")

    def _update_ui(self):
        # Update summary
        balance = self.simulator.balance.getCurrentBalance()
        invested = sum(
            s.get_current_value() * s.get_number_stocks() 
            for s in self.simulator.stocks.values()
        )
        self.summary_label.setText(
            f"<b>Portfolio Summary</b><br>"
            f"Cash: ${balance:,.2f}<br>"
            f"Invested: ${invested:,.2f}<br>"
            f"Total: ${balance + invested:,.2f}"
        )

        # Update chart
        self.chart.plot_performance(self.simulator)

    def _show_error(self, message):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Error", message)

   
    