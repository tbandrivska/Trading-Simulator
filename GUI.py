import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QLineEdit, QGroupBox, QSpinBox
)
from PySide6.QtCore import Qt
import sqlite3

app = QApplication(sys.argv)

class startWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(1200, 800)
        self.setWindowTitle("Start Menu")

        #display 3 options in the start menu
        #1 - new simulation
        self.newSimButton = QPushButton("New Simulation")
        #2 - continue a previous simulation
        self.prevSimButton = QPushButton("Previous Simulations")
        #3 - exit
        self.exitButton = QPushButton("Exit")
        #4 - dispaly all simulation performance levels (optional)

        #size the buttons
        for button in [self.newSimButton, self.prevSimButton, self.exitButton]:
            button.setFixedSize(200, 40)

        #layout: buttons in a vertical line and centred
        vLayout = QVBoxLayout()
        vLayout.addWidget(self.newSimButton)
        vLayout.addWidget(self.prevSimButton)
        vLayout.addWidget(self.exitButton)
        hLayout = QHBoxLayout()
        hLayout.addLayout(vLayout)
        self.setLayout(hLayout)

        #button actions
        self.newSimButton.clicked.connect(self.displaySimDetailsFunc)
        #self.prevSimButton.clicked.connect(self.displaySimsFunc())
        self.exitButton.clicked.connect(QApplication.quit)

    def displaySimDetailsFunc(self):
        self.display_sim_details_obj = displaySimDetails()
        self.display_sim_details_obj.show()

    def displaySimsFunc(self):
        display_sims_obj = displaySims()


class displaySimDetails(QWidget):
    def __init__(self, current_simulation_id = None):
        super().__init__()
        self.resize(1200, 800)
        self.setWindowTitle("Stock Trading Simulator")

        # === TOP BAR ===
        #Total balance
        total_balance_label = QLabel("TOTAL BALANCE: £...")
        #Cash balance
        balance_label = QLabel("BALANCE: £...")

        top_bar = QVBoxLayout()
        top_bar.addWidget(total_balance_label)
        top_bar.addWidget(balance_label)

        # === STOCK TABLE ===
         #stock name, performannce, value (x10)
            #stock name is a button - trigger displayStock
        stock_grid = QGridLayout()
        for i in range(10):
            stock_label = QLabel(f"STOCK {i+1}")
            change_label = QLabel("± x%")
            value_label = QLabel("£....")
            stock_grid.addWidget(stock_label, i, 0)
            stock_grid.addWidget(change_label, i, 1)
            stock_grid.addWidget(value_label, i, 2)

        stock_group = QGroupBox()
        stock_group.setLayout(stock_grid)

        # === GRAPH + STATS SECTION ===
        #invested balance
        invested_label = QLabel("INVESTED BALANCE: £...")
        #portfolio perfomance
        performance_label = QLabel("PERFORMANCE: + x%")
        graph_placeholder = QLabel()
        graph_placeholder.setFixedSize(250, 200)
        graph_placeholder.setStyleSheet("background-color: lightgray; border: 1px solid black;")

        #display graph
        graph_layout = QVBoxLayout()
        graph_layout.addWidget(invested_label)
        graph_layout.addWidget(performance_label)
        graph_layout.addWidget(graph_placeholder)

        # === TIME INPUTS ===
        #"select run time"
            #number
            #days, months, years
        time_layout = QHBoxLayout()
        time_label = QLabel("SELECT RUN TIME")
        months_input = QSpinBox()
        days_input = QSpinBox()
        months_input.setPrefix("Months: ")
        days_input.setPrefix("Days: ")
        time_layout.addWidget(time_label)
        time_layout.addWidget(months_input)
        time_layout.addWidget(days_input)

        # === BUTTONS ===
        #run simulation
        #exit simulation
        run_button = QPushButton("RUN SIMULATION")
        reset_button = QPushButton("RESET SIMULATION")

        button_layout = QVBoxLayout()
        button_layout.addLayout(time_layout)
        button_layout.addWidget(run_button)
        button_layout.addWidget(reset_button)

        # === RIGHT SIDE COMBINED ===
        right_side = QVBoxLayout()
        right_side.addLayout(graph_layout)
        right_side.addLayout(button_layout)

        # === MAIN LAYOUT ===
        main_layout = QHBoxLayout()
        left_panel = QVBoxLayout()
        left_panel.addLayout(top_bar)
        left_panel.addWidget(stock_group)
        main_layout.addLayout(left_panel)
        main_layout.addLayout(right_side)

        self.setLayout(main_layout)
        #window.show()
        #sys.exit(app.exec())

class displayStock(QWidget):
    def __init__(self, Stock):
        super().__init__()
        self.resize(1200, 800)
        #change so it takes the stock name as title
        self.setWindowTitle(...)
    
        #stock name
        #performance (is this the same as gain/loss or...?)
        #plot graph

        #initial investment value
        #current investment value
        #gain/loss (%)

        #cash balance
        #num of stock

        #"purchase/sell/trade"
        # num of stock
        # cost
        # balance after
        # "confirm purchase"
            #trigger display stock

        #implement trading strategies - trigger displayStrategies

        #end trade
    
#class displayStrategies(QWidget):

class displaySims(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(1200, 800)
        self.setWindowTitle("Previous Simulations")

        layout = QVBoxLayout()
        self.sim_names = self.get_sim_names()
        self.display_sim_names()
        self.setLayout(layout)

    #get the names of all the simulations
    def get_sim_names(self):
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        sims = cursor.fetchall()

        sim_names = []
        for sim in sims:
            sim_names.append(sim[0])

        conn.close()

        return sim_names

    def display_sim_names(self):
        for name in self.sim_names:
            button = QPushButton(name)
            button.clicked.connect(lambda checked=False, n=name: self.runSim(...)) #change when runSim is sorted
            self.layout.addWidget(button)


# Test function
if __name__ == "__main__":
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    window = startWindow()
    window.show()
    sys.exit(app.exec())
