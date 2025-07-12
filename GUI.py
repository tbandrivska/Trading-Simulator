import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QStackedLayout, QFormLayout, QLineEdit,
    QGroupBox, QSpinBox, QFormLayout, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
import sqlite3
from Stock import Stock
from TradingSimulator import TradingSimulator


class startWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.simulator = TradingSimulator(10000)  #Initialise simulator with a default balance
        self.resize(1200, 600)
        self.setWindowTitle("Start Menu")

        #display 3 options in the start menu - new simulation, continue a previous simulation, exit app
        self.newSimButton = QPushButton("New Simulation")
        self.prevSimButton = QPushButton("Previous Simulations")
        self.exitButton = QPushButton("Exit")

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
        self.newSimButton.clicked.connect(lambda: self.displaySimDetailsFunc(None))
        self.prevSimButton.clicked.connect(self.displaySimsFunc)
        self.exitButton.clicked.connect(QApplication.quit)

    def displaySimDetailsFunc(self, sim_id):
        self.display_sim_details_obj = displaySimDetails(self, sim_id)
        self.display_sim_details_obj.show()
        self.hide()

    def displaySimsFunc(self):
        display_sims_obj = displaySims(self)
        display_sims_obj.show()
        self.hide()

    def backToStartWindow(self, currentWindow):
        """Close the current window and return to the start window."""
        currentWindow.close()
        self.show()


class displaySimDetails(QWidget):
    def __init__(self, startWindow, sim_id):
        super().__init__()
        self.startWindow = startWindow
        self.simulator = self.startWindow.simulator 
        if sim_id is None:
            self.simulator.new_simulation()
        else:
            #self.simulator.load_simulation(current_simulation_id)
            ...
        
        self.resize(1200, 600)
        self.setWindowTitle("SIMULATION ID: " + self.simulator.get_sim_id())

        #Total Balance and Cash Balance
        cash_balance = self.simulator.balance.getCurrentBalance()
        invested_balance = self.simulator.balance.getTotalInvestedBalance()
        total_balance = cash_balance + invested_balance
        total_balance_label = QLabel("TOTAL BALANCE: £" + str(total_balance))
        cash_balance_label = QLabel("CASH BALANCE: £" + str(cash_balance))

        balance_layout = QVBoxLayout()
        balance_layout.addWidget(total_balance_label)
        balance_layout.addWidget(cash_balance_label)

        #Stock tabel: name, performannce, value
        stock_grid = QGridLayout()
        for i in range(4):
            if i%2 == 0:
                stock_grid.setColumnMinimumWidth(i,90)
            else:
                stock_grid.setColumnMinimumWidth(i,60)
        for i in range(5):
            stock_grid.setRowMinimumHeight(i,60)

        for i in range(10):
            Stock = self.get_stock(i)
            stock_details = QVBoxLayout()

            stock_name = Stock.get_name()
            stock_button = QPushButton(stock_name)
            stock_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            stock_button.clicked.connect(lambda _, index=i: self.displayStockFunc(Stock))

            stock_performance = Stock.get_current_performance()
            performance_label = QLabel(str(stock_performance) + "%")
            stock_details.addWidget(performance_label)

            stock_value = round(Stock.get_current_value(),2)
            value_label = QLabel("£" + str(stock_value))
            stock_details.addWidget(value_label)
            
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
        invested_label = QLabel("INVESTED BALANCE: £" + str(invested_balance))
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
        self.end_button.clicked.connect(lambda: self.startWindow.backToStartWindow(self))


    def get_stock(self, index: int) -> Stock: 
        """Get stock object by index."""
        ticker = self.simulator.get_tickers()[index]
        Stock = self.simulator.get_stock(ticker)
        return Stock
    
    def displayStockFunc(self, Stock):
        """Display stock details in a new window."""
        self.stock_display = displayStock(self, self.simulator, Stock)
        self.stock_display.show()
        self.hide()


class displayStock(QWidget):
    def __init__(self, simWindow, simulator, Stock):
        super().__init__()
        self.simWindow = simWindow
        self.simulator = simulator
        self.Stock = Stock

        self.resize(1200, 600)
        self.setWindowTitle(self.Stock.get_name())

        #LHS Panel
        left_panel = QVBoxLayout()

        #stock name
        stock_name_label = QLabel(self.Stock.get_name())
        left_panel.addWidget(stock_name_label)

        #placeholder for graph
        graph_placeholder = QLabel()
        graph_placeholder.setFixedSize(400, 400)
        graph_placeholder.setStyleSheet("background-color: lightgray; border: 1px solid black;")
        left_panel.addWidget(graph_placeholder)

        #stock details
        stock_details_grid = QGridLayout()
        #initial investment value
        invested_title_label = QLabel("CASH INVESTED")
        invested_label = QLabel(str("£" + str(self.Stock.get_cash_invested())))
        stock_details_grid.addWidget(invested_title_label,0,0)
        stock_details_grid.addWidget(invested_label,1,0)
        #current investment value
        current_value_title_label = QLabel("CURRENT INVESTMENT VALUE")
        current_value_label = QLabel("£" + str(self.Stock.get_current_value()))
        stock_details_grid.addWidget(current_value_title_label,0,1)
        stock_details_grid.addWidget(current_value_label,1,1)
        #investment performance
        performance_title_label = QLabel("INVESTMENT PERFORMANCE")
        performance_label = QLabel(str(self.Stock.get_investment_performance()) + "%")
        stock_details_grid.addWidget(performance_title_label,0,2)
        stock_details_grid.addWidget(performance_label,1,2)
        #Stock performance 
        stock_performance_title_label = QLabel("STOCK PERFORMANCE")
        stock_performance_label = QLabel(str(self.Stock.get_current_performance()) + "%")
        stock_details_grid.addWidget(stock_performance_title_label,0,3)
        stock_details_grid.addWidget(stock_performance_label,1,3)

        left_panel.addLayout(stock_details_grid)

        #RHS Panel
        right_panel = QVBoxLayout()

        #status bar - cash balance, number of stocks
        status_bar = QVBoxLayout()
        cash_balance_label = QLabel("CASH BALANCE: £" + str(self.simulator.balance.getCurrentBalance()))
        num_stocks_label = QLabel("NUMBER OF STOCKS OWNED: " + str(self.Stock.get_number_stocks()))
        status_bar.addWidget(cash_balance_label)
        status_bar.addWidget(num_stocks_label)
        right_panel.addLayout(status_bar)

        #trade bar - num of stock, price of stock, balance after purchase, trade confirmation
        trade_widget = TradeWidget()
        right_panel.addWidget(trade_widget)

        #implement trading strategies - trigger displayStrategies
        self.trading_strat_button = QPushButton("IMPLEMENT TRADING STRATEGIES")
        right_panel.addWidget(self.trading_strat_button)
        #self.trading_strat_button.clicked.connect(self.displayStrategiesFunc)

        #end trade
        self.end_trade_button = QPushButton("END TRADE")
        right_panel.addWidget(self.end_trade_button)
        self.end_trade_button.clicked.connect(self.endTrade)

        #final layout
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_panel)
        main_layout.addLayout(right_panel)  
        self.setLayout(main_layout)

    def displayStrategiesFunc(self):
        self.display_strategies_obj = displayStrategies(self)
        self.display_strategies_obj.show()
        self.hide()

    def endTrade(self):
        self.close()
        self.simWindow.show()


class TradeWidget(QWidget):
    def __init__(self):
        super().__init__()

        #tab buttons (PURCHASE / SELL)
        button_layout = QHBoxLayout()
        self.purchase_tab_btn = QPushButton("PURCHASE")
        self.sell_tab_btn = QPushButton("SELL")
        self.purchase_tab_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.sell_tab_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        button_layout.addWidget(self.purchase_tab_btn)
        button_layout.addWidget(self.sell_tab_btn)

        #stack Layout for switching between purchase/sell
        self.stack = QStackedLayout()
        self.stack.addWidget(self.create_tab("PURCHASE"))
        self.stack.addWidget(self.create_tab("SELL"))

        #combine stack and buttons
        layout = QVBoxLayout()
        layout.addLayout(button_layout)
        layout.addLayout(self.stack)
        self.setLayout(layout)

    def create_tab(self, mode):
        widget = QWidget()
        layout = QVBoxLayout()

        stock_input = QLineEdit()
        stock_input.setPlaceholderText("Enter number of stocks")

        price_label = QLabel("PRICE: £...")
        balance_label = QLabel("BALANCE AFTER: £...")

        confirm_button = QPushButton(f"CONFIRM {mode}")

        layout.addWidget(QLabel("NUMBER OF STOCK"))
        layout.addWidget(stock_input)
        layout.addWidget(price_label)
        layout.addWidget(balance_label)
        layout.addWidget(confirm_button)
        widget.setLayout(layout)
        return widget


class displayStrategies(QWidget):
    n = None


class displaySims(QWidget):
    def __init__(self, startWindow):
        super().__init__()
        self.startWindow = startWindow
        self.resize(1200, 600)
        self.setWindowTitle("Previous Simulations")

        #display all the simulations
        layout = QVBoxLayout()
        #loop through all the simulations and display their names
        self.sim_IDS = self.get_sim_IDS()
        for sim_id in self.sim_IDS:
            button = QPushButton(sim_id)
            button.setFixedSize(200, 40)
            button.clicked.connect(lambda checked=False, n=sim_id: self.startWindow.displaySimDetailsFunc(sim_id))
            layout.addWidget(button)

        #back button
        back_button = QPushButton("GO BACK")
        back_button.clicked.connect(lambda: self.startWindow.backToStartWindow(self))
        layout.addWidget(back_button)

        #set the layout
        main_layout = QHBoxLayout()
        main_layout.addLayout(layout)
        self.setLayout(main_layout)

    def get_sim_IDS(self):
        """Fetch simulation IDs from the database."""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        sims = cursor.fetchall()

        sim_names = []
        for sim in sims:
            sim_names.append(sim[0])

        #remove historical data table
        if "historicalData" in sim_names:
            sim_names.remove("historicalData")
        
        conn.close()
        return sim_names



# Test function
if __name__ == "__main__":
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    window = startWindow()
    window.show()
    sys.exit(app.exec())
