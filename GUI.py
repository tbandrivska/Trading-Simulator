import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QLineEdit, QGroupBox, QSpinBox,
    QFormLayout, QSizePolicy, 
)
from PySide6.QtCore import Qt
import sqlite3

app = QApplication(sys.argv)

class startWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(1200, 600)
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
        self.display_sim_details_obj = displaySimDetails(self)
        self.display_sim_details_obj.show()
        self.hide()

    def displaySimsFunc(self):
        display_sims_obj = displaySims()

class displaySimDetails(QWidget):
    def __init__(self, startWindow, current_simulation_id = None):
        super().__init__()
        self.startWindow = startWindow
        self.resize(1200, 600)
        self.setWindowTitle("SIMULATION ID: ...")

        #Total Balance and Cash Balance
        total_balance_label = QLabel("TOTAL BALANCE: £...")
        cash_balance_label = QLabel("CASH BALANCE: £...")

        balance_layout = QVBoxLayout()
        balance_layout.addWidget(total_balance_label)
        balance_layout.addWidget(cash_balance_label)

        #Stock tabel: name, performannce, value
            #stock name is a button - trigger displayStock
        stock_grid = QGridLayout()
        for i in range(4):
            if i%2 == 0:
                stock_grid.setColumnMinimumWidth(i,90)
            else:
                stock_grid.setColumnMinimumWidth(i,60)
        for i in range(5):
            stock_grid.setRowMinimumHeight(i,60)

        for i in range(10): #change to loop through tickers???
            stock_button = QPushButton(f"STOCK {i+1}")
            stock_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            performance_label = QLabel("± x%")
            #performance_label.setStyleSheet("border: 1px solid gray")
            value_label = QLabel("£....")
            #value_label.setStyleSheet("border: 1px solid gray")

            stock_details = QVBoxLayout()
            stock_details.addWidget(value_label)
            stock_details.addWidget(performance_label)

            if(i<5):
                stock_grid.addWidget(stock_button,i,0)
                stock_grid.addLayout(stock_details,i,1)
            else:
                stock_grid.addWidget(stock_button,(i-5),2)
                stock_grid.addLayout(stock_details,(i-5),3)

        #display balances and stocks on the LHS
        left_panel = QVBoxLayout()
        left_panel.addLayout(balance_layout)
        left_panel.addLayout(stock_grid)

        #Invested balance, portforlio performance
        invested_label = QLabel("INVESTED BALANCE: £...")
        portfolio_performance_label = QLabel("PERFORMANCE: + x%")
        portfolio_layout = QVBoxLayout()
        portfolio_layout.addWidget(invested_label)
        portfolio_layout.addWidget(portfolio_performance_label)

        #placeholder for graph
        graph_placeholder = QLabel()
        graph_placeholder.setFixedSize(800, 400)
        graph_placeholder.setStyleSheet("background-color: lightgray; border: 1px solid black;")

        #time input
        time_layout = QFormLayout()
        time_layout.addRow("ENTER RUN TIME (DAYS): ", QLineEdit())

        #display balance, performance, graph and time input on the RHS
        right_panel = QVBoxLayout()
        right_panel.addLayout(portfolio_layout)
        right_panel.addWidget(graph_placeholder)
        right_panel.addLayout(time_layout)

        #run/end simulation
        self.run_button = QPushButton("RUN SIMULATION")
        self.end_button = QPushButton("END SIMULATION")
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.end_button)

        #final layout
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_panel)
        main_layout.addLayout(right_panel)
        final_layout = QVBoxLayout()
        final_layout.addLayout(main_layout)
        final_layout.addLayout(button_layout)

        self.setLayout(final_layout)

        #button actions
        self.end_button.clicked.connect(self.endSim)

    def endSim(self):
        self.close()
        self.startWindow.show()

class displayStock(QWidget):
    def __init__(self, Stock):
        super().__init__()
        self.resize(1200, 600)
        #change so it takes the stock name as title
        self.setWindowTitle('...')
    
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
        self.resize(1200, 600)
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

    # def display_sim_names(self):
    #     for name in self.sim_names:
    #         button = QPushButton(name)
    #         button.clicked.connect(lambda checked=False, n=name: self.runSim(...)) #change when runSim is sorted
    #         self.layout.addWidget(button)


# Test function
if __name__ == "__main__":
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    window = startWindow()
    window.show()
    sys.exit(app.exec())
