import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QStackedLayout, QFormLayout, QLineEdit,
    QMessageBox, QFormLayout, QSizePolicy, QScrollArea
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIntValidator, QFont
import sqlite3
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from Stock import Stock
from TradingStrategiesWidget import TradingStrategiesWidget

class loadingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(1200, 600)
        self.setWindowTitle("Trading Simulator")
        self.start_balance = 10000

        title_label = QLabel("TRADING SIMULATOR")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        loading_label = QLabel("...LOADING...")
        loading_label.setFont(QFont("Arial", 18))

        #centre labels in window
        loading_layout = QVBoxLayout()
        loading_layout.addWidget(title_label)
        loading_layout.addWidget(loading_label)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(loading_layout)

        self.show()
        QTimer.singleShot(100, lambda: self.load_simulator(self.start_balance))
    
    def load_simulator(self, starting_balance):
        from TradingSimulator import TradingSimulator
        self.TradingSimulator = TradingSimulator(starting_balance) #Initialise simulator with a default starting balance
        self.startWindow = startWindow(self.TradingSimulator)
        self.startWindow.show()
        self.close()
        

class startWindow(QWidget):
    def __init__(self, tradingSimulator):
        super().__init__()
        self.simulator = tradingSimulator
        self.resize(1200, 600)
        self.setWindowTitle("Start Menu")

        #dispaly application title
        self.title_label = QLabel("TRADING SIMULATOR")
        self.title_label.setFont(QFont("Arial", 26, QFont.Weight.Bold))
        self.title_label.setFixedSize(300, 60)
        #display 3 options in the start menu - new simulation, continue a previous simulation, exit app
        self.newSimButton = QPushButton("New Simulation")
        self.prevSimButton = QPushButton("Previous Simulations")
        self.exitButton = QPushButton("Exit")
        

        #size the buttons and change their font
        for button in [self.newSimButton, self.prevSimButton, self.exitButton]:
            button.setFixedSize(300, 60)
            button.setFont(QFont("Arial", 16))

        #layout: buttons in a vertical line and centred
        vLayout = QVBoxLayout()
        vLayout.addWidget(self.title_label)
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
        self.display_sim_details_obj = displaySimulation(self, sim_id)
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


class displaySimulation(QWidget):
    def __init__(self, startWindow, sim_id):
        super().__init__()
        self.startWindow = startWindow
        self.sim_id = sim_id
        self.simulator = self.startWindow.simulator 
        if self.sim_id is None:
            self.simulator.new_simulation()
            self.sim_id = self.simulator.get_sim_id()
            print("new simulation started")
        else:
            self.simulator.load_prev_simulation(self.sim_id)
            print(f"loading in simulation: {self.sim_id}")
            
        
        self.resize(1200, 600)
        self.setWindowTitle("SIMULATION ID: " + self.sim_id)

        #Total Balance and Cash Balance
        
        cash_balance = self.simulator.balance.getCurrentBalance()
        invested_balance = self.simulator.balance.getTotalInvestedBalance()
        total_balance = cash_balance + invested_balance
        self.total_balance_label = QLabel("TOTAL BALANCE: £" + str(round(total_balance,2)))
        self.cash_balance_label = QLabel("CASH BALANCE: £" + str(round(cash_balance,2)))
        balance_layout = QVBoxLayout()
        balance_layout.addWidget(self.total_balance_label)
        balance_layout.addWidget(self.cash_balance_label)

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
            stock_button.clicked.connect(lambda _, s=Stock: self.displayStockFunc(s))

            stock_performance = round(Stock.get_current_stock_performance(),1)
            performance_label = QLabel(str(stock_performance) + "%")
            stock_details.addWidget(performance_label)

            stock_value = round(Stock.get_current_stock_value(),2)
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
        self.invested_label = QLabel("INVESTED BALANCE: £" + str(round(invested_balance,2)))
        portfolio_performance = self.simulator.balance.getPortfolioPerformance()
        self.portfolio_performance_label = QLabel("PERFORMANCE: "+ str(round(portfolio_performance,1)) +"%")
        portfolio_layout = QVBoxLayout()
        portfolio_layout.addWidget(self.invested_label)
        portfolio_layout.addWidget(self.portfolio_performance_label)

        #simulation graph
        graph_widget = graphWidget(self.simulator, None)
        graph_widget.plot_graph()
        
        #time input
        self.days_input = QLineEdit()
        self.days_input.setValidator(QIntValidator(1, 9999))
        self.days_input.setText("30")  #default value

        time_layout = QFormLayout()
        time_layout.addRow("ENTER RUN TIME (DAYS): ", self.days_input)

        #display balance, performance, graph and time input on the RHS
        right_panel = QVBoxLayout()
        right_panel.addLayout(portfolio_layout)
        right_panel.addWidget(graph_widget)
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
        self.run_button.clicked.connect(self.run_sim)
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
        self.close()

    def run_sim(self):
        days = self.get_days_input()
        if 0 < days < 10000:
            self.simulator.set_timeframe(days)
            self.simulator.run_simulation()
            self.reloadSimWindow()

    def get_days_input(self) -> int:
        text = self.days_input.text()
        if text.isdigit():
            days = int(text)
            if 1 <= days <= 9999:
                return days
        
        QMessageBox.warning(self, "Invalid Input", "Please enter a number between 1 and 9999.")
        return 0  #Indicate invalid input    

    def reloadSimWindow(self):
        """reload window so that it dispalys changes in data"""
        self.new_window = displaySimulation(self.startWindow, self.sim_id)
        self.new_window.show()
        self.close()
       

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

        #stock graph
        graph_widget = graphWidget(self.simulator, self.Stock)
        graph_widget.plot_graph()
        left_panel.addWidget(graph_widget)

        #stock details
        stock_details_grid = QGridLayout()
        #initial investment value
        self.invested_title_label = QLabel("CASH INVESTED")
        self.invested_label = QLabel(str("£" + str(round(self.Stock.get_cash_invested(),2))))
        stock_details_grid.addWidget(self.invested_title_label,0,0)
        stock_details_grid.addWidget(self.invested_label,1,0)
        #current investment value
        investment_value_title_label = QLabel("CURRENT INVESTMENT VALUE")
        investment_value_label = QLabel("£" + str(round(self.Stock.get_investment_value(),2)))
        stock_details_grid.addWidget(investment_value_title_label,0,1)
        stock_details_grid.addWidget(investment_value_label,1,1)
        #investment performance
        performance_title_label = QLabel("INVESTMENT PERFORMANCE")
        investment_performance = round(self.Stock.get_investment_performance(),1)
        performance_label = QLabel(str(investment_performance) + "%")
        stock_details_grid.addWidget(performance_title_label,0,2)
        stock_details_grid.addWidget(performance_label,1,2)
        #Stock performance 
        stock_performance_title_label = QLabel("STOCK PERFORMANCE")
        stock_performance_label = QLabel(str(round(self.Stock.get_current_stock_performance(),1)) + "%")
        stock_details_grid.addWidget(stock_performance_title_label,0,3)
        stock_details_grid.addWidget(stock_performance_label,1,3)
        #Stock value
        stock_value_title_label = QLabel("STOCK VALUE")
        stock_value_label = QLabel("£" + str(round(self.Stock.get_current_stock_value(),2)))
        stock_details_grid.addWidget(stock_value_title_label,0,4)
        stock_details_grid.addWidget(stock_value_label,1,4)

        left_panel.addLayout(stock_details_grid)

        #RHS Panel
        right_panel = QVBoxLayout()

        #status bar - cash balance, number of stocks
        status_bar = QVBoxLayout()
        self.cash_balance_label = QLabel("CASH BALANCE: £" + str(round(self.simulator.balance.getCurrentBalance(),2)))
        self.num_stocks_label = QLabel("NUMBER OF STOCKS OWNED: " + str(self.Stock.get_number_stocks()))
        status_bar.addWidget(self.cash_balance_label)
        status_bar.addWidget(self.num_stocks_label)
        right_panel.addLayout(status_bar)

        #trade bar - num of stock, price of stock, balance after purchase, trade confirmation
        trade_widget = tradeWidget(self)
        right_panel.addWidget(trade_widget)

        #implement trading strategies - trigger displayStrategies
        self.trading_strat_button = QPushButton("IMPLEMENT TRADING STRATEGIES")
        right_panel.addWidget(self.trading_strat_button)
        self.trading_strat_button.clicked.connect(self.displayStrategiesFunc)

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
        self.strat_widget = TradingStrategiesWidget(self.simulator, self)
        self.strat_widget.exec()

    def endTrade(self):
        start_window = self.simWindow.startWindow
        sim_id = self.simulator.get_sim_id()
        newSimWindow = displaySimulation(start_window, sim_id)
        newSimWindow.show()
        self.close()
        

class tradeWidget(QWidget):
    def __init__(self, stockWindow):
        super().__init__()
        self.stockWindow = stockWindow
        self.Stock = stockWindow.Stock
        self.simulator = stockWindow.simulator
        self.stock_inputs = {}
        self.price_outputs = {}
        self.balance_outputs = {}

        #tab buttons (PURCHASE / SELL)
        button_layout = QHBoxLayout()
        #PURCHASE
        self.purchase_tab_btn = QPushButton("PURCHASE")
        self.active_button_style(True, self.purchase_tab_btn)
        self.purchase_tab_btn.clicked.connect(lambda: self.click_tab_btn(0))
        button_layout.addWidget(self.purchase_tab_btn)
        #SELL
        self.sell_tab_btn = QPushButton("SELL")
        self.active_button_style(False, self.sell_tab_btn)
        self.sell_tab_btn.clicked.connect(lambda: self.click_tab_btn(1))
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
        #mode = PURCHASE or SELLL
        widget = QWidget()

        lhs_layout = QVBoxLayout()
        num_of_stock_label = QLabel("NUMBER OF STOCK:")
        price_label = QLabel("PRICE:")
        balance_label = QLabel("BALANCE AFTER:")
        lhs_layout.addWidget(num_of_stock_label)
        lhs_layout.addWidget(price_label)
        lhs_layout.addWidget(balance_label)

        rhs_layout = QVBoxLayout()
        stock_input = QLineEdit()
        stock_input.setPlaceholderText("Enter number of stocks")
        stock_input.setValidator(QIntValidator(1, 1000000))
        stock_input.textChanged.connect(lambda text, m=mode: self.update_labels(text, m))
        rhs_layout.addWidget(stock_input)
        
        price_output = QLineEdit()
        price_output.setReadOnly(True)
        price_output.setPlaceholderText("£0.00")
        rhs_layout.addWidget(price_output)

        balance_output = QLineEdit()
        balance_output.setReadOnly(True)
        balance_output.setPlaceholderText("£0.00")
        rhs_layout.addWidget(balance_output)

        self.stock_inputs[mode] = stock_input
        self.price_outputs[mode] = price_output
        self.balance_outputs[mode] = balance_output

        combined_layout = QHBoxLayout()
        combined_layout.addLayout(lhs_layout)
        combined_layout.addLayout(rhs_layout)
        
        #confirm trade button
        confirm_button = QPushButton(f"CONFIRM {mode}")
        confirm_button.clicked.connect(lambda _, m=mode: self.trade_stock(m))

        final_layout = QVBoxLayout()
        final_layout.addLayout(combined_layout)
        final_layout.addWidget(confirm_button)
        widget.setLayout(final_layout)
        return widget

    def update_labels(self, stock_input: str, mode):
        if not stock_input.strip().isdigit():
            self.price_outputs[mode].clear()
            self.balance_outputs[mode].clear()
            return

        num_stocks = int(stock_input)
        stock_price = self.stockWindow.Stock.get_current_stock_value()
        total_price = num_stocks * stock_price
        cash_balance = self.stockWindow.simulator.balance.getCurrentBalance()

        if mode == "PURCHASE":
            new_balance = cash_balance - total_price
        elif mode == "SELL":
            new_balance = cash_balance + total_price
        
        self.price_outputs[mode].setText(f"£{total_price:,.2f}")
        self.balance_outputs[mode].setText(f"£{new_balance:,.2f}")

    def click_tab_btn(self, index: int):
        self.stack.setCurrentIndex(index)
        #change the style of buttons to indicate which tab is open
        if index == 0:
            active = True
        else:
            active = False
        self.active_button_style(active, self.purchase_tab_btn)
        self.active_button_style((not active), self.sell_tab_btn)

    def active_button_style(self, active_or_innactive: bool, button):
        if active_or_innactive:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #007BFF;     /* Modern blue */
                    color: white;                  /* Text color */
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: bold;
                }

                QPushButton:hover {
                    background-color: #3399FF;     /* Lighter blue on hover */
                }

                QPushButton:pressed {
                    background-color: #0066CC;     /* Darker blue when pressed */
                }
            """)
        if not active_or_innactive:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #cccccc;     /* Light grey background */
                    color: #333333;                /* Darker grey text */
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: semi-bold;
                }

                QPushButton:hover {
                    background-color: #bbbbbb;     /* Slightly darker on hover */
                }

                QPushButton:pressed {
                    background-color: #aaaaaa;     /* Darker still when pressed */
                }
            """)

    def trade_stock(self, mode):
        text = self.stock_inputs[mode].text()
        if not text.strip().isdigit():
            print("Invalid input: please enter a number")
            #open micro window: Invalid input
            return

        amount = int(text)
        if mode == "SELL":
            amount = -amount

        ticker = self.Stock.get_ticker()
        confirmed = self.simulator.trade_a_stock(ticker, amount)
        if not confirmed:
            print("Trade unsuccesful: insufficient balance to purchase stocks.")
            #open micro window: trade unsuccesful
        else:
            print("Trade succesful")
            #open micro window: trade succesful
            #open and close stock window to update change
            self.reloadStockWindow()

    def reloadStockWindow(self):
        """reload window so that it dispalys changes in data"""
        self.new_window = displayStock(self.stockWindow.simWindow, self.stockWindow.simulator, self.Stock)
        self.new_window.show()
        self.close()


class displaySims(QWidget):
    def __init__(self, startWindow):
        super().__init__()
        self.startWindow = startWindow
        self.resize(1200, 600)
        self.setWindowTitle("Previous Simulations")

        vlayout = QVBoxLayout()
        #loop through all the simulations and display their names
        self.sim_IDS = self.get_sim_IDS()
        for sim_id in self.sim_IDS:
            prev_sim_button = QPushButton(sim_id)
            prev_sim_button.setFixedSize(200, 40)
            prev_sim_button.clicked.connect(lambda checked=False, id=sim_id: self.displayPrevSimFunc(id))
            vlayout.addWidget(prev_sim_button)

        #back button
        back_button = QPushButton("GO BACK")
        back_button.setFixedSize(200, 40)
        back_button.clicked.connect(lambda: self.startWindow.backToStartWindow(self))
        vlayout.addWidget(back_button)

        #centre buttons in layout
        main_layout = QHBoxLayout()
        main_layout.addLayout(vlayout)

        #make the layout into a scrollable widget
        container_widget = QWidget()
        container_widget.setLayout(main_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container_widget)

        final_layout = QVBoxLayout()
        final_layout.addWidget(scroll_area)
        self.setLayout(final_layout)


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
        if "sqlite_sequence" in sim_names:
            sim_names.remove("sqlite_sequence")
        
        conn.close()
        return sim_names
    
    def displayPrevSimFunc(self, sim_id):
        self.startWindow.displaySimDetailsFunc(sim_id)
        self.close()


class graphWidget(QWidget):
    def __init__(self, simulator, Stock):
        super().__init__()
        self.simulator = simulator
        self.Stock = Stock

        self.type = "STOCK"
        if self.Stock is None:
            self.type = "SIMULATION"

        self.figure = Figure(figsize=(5, 5), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def plot_graph(self):
        """Plot graph data on specified graph."""
        if self.type == "SIMULATION":
            balance_type = "VALUE OF PORTFOLIO"
            data = self.simulator.get_sim_graph_data()
        elif self.type == "STOCK":
            balance_type = "VALUE OF STOCK"
            data = self.simulator.get_stock_graph_data(self.Stock)
        else: 
            raise ValueError(f"type: {self.type} is invalid when initialising graphWidget. 'SIMULATION' or 'STOCK' only")

        day_data = data["days"]
        balance_data = data["balances"]

        self.ax.clear()  # Clear previous plots
        self.ax.plot(day_data, balance_data, marker='x')
        self.ax.set_title(self.type + " PERFORMANCE")
        self.ax.set_xlabel("Day")
        self.ax.set_ylabel(balance_type)
        self.ax.grid(True)
        self.canvas.draw()
        

            



# Test function
if __name__ == "__main__":
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    window = loadingWindow()
    window.show()
    sys.exit(app.exec())
