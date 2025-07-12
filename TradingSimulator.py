import sqlite3
from typing import Dict, List
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from collections import Counter
import random
from datetime import datetime
from Stock import Stock
from Balance import Balance
from Database import Database
import TradingStrategies as TradingStrategies
from TradingStrategies import TradingStrategies

class TradingSimulator:
    
    #methods that are up for discussion
    def _get_previous_trading_day(self, date: str) -> str:
        """Find the most recent trading day before given date"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MAX(date) FROM historicalData 
            WHERE date < ?
        """, (date))
        result = cursor.fetchone()[0]
        conn.close()
        return result if result else date  # Fallback to same date if no previous found

    def get_user_strategy_choice(self):
            """
            Allow user to select a trading strategy from available options.
            """
            strategies = ['take_profit', 'stop_loss', 'dollar_cost_avg']  # Example strategies
            print("Available strategies:")
            for i, strat in enumerate(strategies, 1):
                print(f"{i}: {strat}")
            while True:
                try:
                    choice = int(input("Select a strategy by number: "))
                    if 1 <= choice <= len(strategies):
                        return strategies[choice - 1]
                    else:
                        print("Invalid selection. Try again.")
                except ValueError:
                    print("Please enter a valid number.")

    def validate_user_input(self, prompt, input_type=str):
        """
        General input validation function for user input.
        """
        while True:
            try:
                value = input_type(input(prompt))
                return value
            except ValueError:
                print(f"Invalid input. Please enter a {input_type.__name__}.")


    # 1 initialisation
    def __init__(self, start_balance: float = 10000):
        """Initialise simulation with balance and stocks"""
        self.database = Database()
        self.database.initialiseDatabase()

        #default start and end dates match the database dates
        self.start_date = self.database.getStartDate()
        self.end_date = self.database.getEndDate() 
        
        self.start_balance = start_balance
        self.balance = Balance(start_balance)
        self.strategies = TradingStrategies(self.balance)
        
        self.stocks: Dict[str, Stock] = {}  # {ticker: Stock}
        self.create_stocks()

        self.current_simulation_id = None
        self.active_strategies: Dict[str, dict] = {} 
        self.performance_history = []

        self.prev_random_numbers = [] 
        
    def create_stocks(self) -> None:
        """Create Stock objects for all tickers in database"""
        for ticker in self.database.getTickers():
            # Get opening price from simulation start date
            opening_price = Stock.fetchOpeningValue(ticker, self.start_date)
            self.stocks[ticker] = Stock(
                name = self.database.getStockName(ticker),
                ticker = ticker,
                opening_value = opening_price
            )

            print("Stock created:" + self.stocks[ticker].get_name())


    #1.5 getter methods
    def get_tickers(self) -> List[str]:
        """Get list of all stock tickers in database"""
        return self.database.getTickers()

    def get_stock(self, ticker: str) -> Stock:
        """Get Stock object by ticker"""
        if ticker not in self.stocks:
            raise ValueError(f"Stock {ticker} not found in portfolio")
        return self.stocks[ticker]
    
    def get_sim_id(self) -> str:
        """Get current simulation ID"""
        if not self.current_simulation_id:
            raise ValueError("No simulation ID set")
        return self.current_simulation_id


    # 2.1 cofiguration - new: sim name, table start date and reset stocks
    def new_simulation(self) -> None:
        """Initialize a new simulation with valid ID"""
        simulation_id = self.generate_simulation_id()
        self.current_simulation_id = simulation_id
        self.create_simulation_table()  # Must be called before run!
        self.randomiseStartDate()
        self.record_portfolio(self.start_date)
        self.reset_all(self.start_date)

    def generate_simulation_id(self) -> str:
        """Generate a unique simulation ID"""
        todays_date = datetime.now().strftime("%Y%m%d")
        Bool = True
        while Bool:
            random_number = str(self.get_new_random_number())
            ID = f"sim_{todays_date}_{random_number}"

            # Check if ID already exists in database
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (ID,))
            exists = cursor.fetchone() is not None
            conn.close()
            if exists:
                Bool = True
            else:
                Bool = False
        return ID

    def create_simulation_table(self) -> None:
        """Create table to track daily balance and stock changes"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.current_simulation_id} (
                date TEXT,
                current_balance REAL,
                total_invested_balance REAL,
                ticker TEXT,
                cash_invested REAL,
                investment_value REAL,
                current_performance REAL,
                number_of_stocks INTEGER,
                random_number INTEGER,
                PRIMARY KEY (date, ticker, random_number)
            )
        """)
        conn.commit()
        conn.close()  

    def record_portfolio(self, date) -> List[int]:
        """Record the state of stocks and balance on a specific day"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        for ticker, stock in self.stocks.items():
            # Validate table name to prevent SQL injection
            if not self.current_simulation_id or not self.current_simulation_id.isidentifier():
                raise ValueError("Invalid simulation ID for table name.")
            
            # Generate a unique random number for this entry
            random_number = self.get_new_random_number()
            
            cursor.execute(f"""
                INSERT INTO "{self.current_simulation_id}" 
                (date, current_balance, total_invested_balance, ticker, cash_invested,
                  investment_value, current_performance, number_of_stocks, random_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,(
                date,
                self.balance.getCurrentBalance(),
                self.balance.getTotalInvestedBalance(),
                ticker,
                stock.get_cash_invested(),
                stock.get_investment_value(),
                stock.get_current_performance(),
                stock.get_number_stocks(),
                random_number
            ))
        
        conn.commit()
        conn.close()

        return random_numbers

    def get_new_random_number(self) -> int:
        """Generate a random number not in the previous_numbers list"""
        while True:
            random_number = random.randint(1, 100000)
            if random_number not in self.prev_random_numbers:
                self.prev_random_numbers.append(random_number)
                return random_number

    def randomiseStartDate(self) -> None:
            """Set a random start date within the available historical data"""
            startDate = self.database.getStartDate()
            endDate = self.database.getEndDate()

            if startDate is None:
                raise ValueError(f"Stock {startDate} has not been initialized with a current value")
            if endDate is None:
                raise ValueError(f"Stock {endDate} has not been initialized with a current value")

            delta = endDate - startDate
            random_days = timedelta(days=int(delta.days * random.random()))
            self.start_date = startDate + random_days + timedelta(days=1)  # Add one day to avoid starting on the first day of data

    def reset_all(self, date) -> None:
        """Reset stocks and balance to initial state"""
        for stock in self.stocks.values():
            stock.initialise_stock(date)
        self.balance.resetBalance(self.start_balance)
    

    # 2.2 configuration - previous simulation
    def load_previous_simulation(self, sim_id: str) -> None:
        """Load a previous simulation by ID"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (sim_id,))
        if not cursor.fetchone():
            raise ValueError(f"Simulation {sim_id} does not exist")
        
        #set simulation ID
        self.current_simulation_id = sim_id

        #set new start date to the last date in the simulation
        cursor.execute(f"SELECT date FROM {sim_id} ORDER BY date DESC LIMIT 1")
        last_date = cursor.fetchone()
        if not last_date:
            raise ValueError(f"No data found for simulation {sim_id}")
        self.start_date = last_date[0]

        #set balance
        self.balance.set_balance_from_sim(sim_id)
        
        #loop through stocks and set their values based on the simulation ID
        for Stock in self.stocks.values():
            Stock.set_stock_from_simulation(sim_id)
    

    # 2.3 configuration - timeframe
    def set_timeframe(self, days: int) -> None:
        """Set simulation date range from start date"""
        if not self.start_date:
            raise ValueError("Start date not set")
        
        #need to change this so it loops instead of erroring if the date range is invalid
        start_date_obj = datetime.strptime(self.start_date, "%Y-%m-%d").date()
        end_date = start_date_obj + timedelta(days=days)
        #end_date = end_date.strftime("%Y-%m-%d")

        if not self._validate_dates(self.start_date, end_date):
            raise ValueError("Invalid date range")
        
        self.end_date = end_date.strftime("%Y-%m-%d")
        print(f"Simulation timeframe set: {self.start_date} to {self.end_date}")
        
    def _validate_dates(self, start, end) -> bool:
        """Check if dates exist in database"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM historicalData 
                WHERE date BETWEEN ? AND ?
                LIMIT 1
            )
        """, (start, end))
        exists = cursor.fetchone()[0]
        conn.close()
        return bool(exists)

    #ignore for now - needs rewriting and debugging
    def loop_dates(self):
        """If a time frame is longer than we have days for, use the final date we have
        to locate a previous date with similar values. Now everytime the final date is reached,
        we continue from this date"""
        
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        dates = []
        #find all valid dates where stocks have the same value 
        for Stock in self.stocks.values():
            ticker = Stock.get_ticker()
            OpeningValue = Stock.fetchOpeningValue(ticker, self.end_date)
            cursor.execute("""
                           SELECT date WHERE open EQUALS ?
                           AND ticker = ?
            """,(OpeningValue, ticker))
            dates = cursor.fetchone()[0]

        #if a date occurs 3 or more times, its valid for use and should be returned
        date_counts = Counter(dates) # Count occurrences
        frequent_dates = [date for date, count in date_counts.items() if count >= 5] # Filter dates with 5 or more occurrences
        if len(frequent_dates) != 0:
            if frequent_dates[0] != finalDate:
                return frequent_dates[0]
        
        for date in dates:
            count = 0
            for Stock in self.stocks:
                ticker = Stock.get_ticker()
                cursor.execute("""
                                SELECT open WHERE date EQUALS ?
                               AND ticker = ?
                """,(date,ticker))
                OpeningValue = cursor.fetchone()[1]

                if Stock.fetchOpeningValue(date) * 0.95 <= OpeningValue <= Stock.fetchOpeningValue(date) * 1.05:
                    count = count + 1
                if 5 <= count: #if 5 or more stocks on a date have a oepning value within the 5% range, return the date
                    if frequent_dates[0] != finalDate:
                        return date


    # 3 simulation setup (purchase stocks and set strategies)
    def trade_each_stock(self) -> None:
        #purchase stocks or set trading strategies for each stock before simulation begins
        for ticker in self.database.getTickers():
            trading:bool = True
            stock: Stock = self.stocks[ticker]
            while trading:
                print("Balance: " + str(self.balance.getCurrentBalance()))
                print(stock.get_name() + " costs: " + str(stock.get_current_value()))
                print("Would you like to purchase or sell " + stock.get_name() + "?(yes/no)")
                user_input = input().strip().lower()
                if user_input == "yes":
                    print("How many shares would you like to buy or sell? (positive to buy, negative to sell)")
                    amount = int(input()) # Convert string input to integer (add input validation later)
                    try:
                        if self.trade_a_stock(ticker, amount):
                            trading = False
                    except ValueError:
                        print("Invalid input. Please enter a valid number.")
                elif user_input == "no":
                    trading = False
                else:
                    print("Invalid input. Please enter 'yes' or 'no'.")
                      
        #insert another loop here to apply strategies to each stock  

    def trade_a_stock(self, ticker: str, amount: int) -> bool:
        """Buy or sell stocks based on current balance"""
        if ticker not in self.stocks:
            raise ValueError(f"Stock {ticker} not found in portfolio")
        
        # Get the stock object from the dictionary
        stock = self.stocks[ticker]

        # Check if the stock has been initialized
        if stock.get_current_value() is None:
            raise ValueError(f"Stock {ticker} has not been initialized with a current value")

        if amount > 0:
            # Buy stocks
            purchase:bool = self.balance.purchase(stock, amount)
            if purchase:
                print(f"Purchased {amount} shares of {ticker}")

            return purchase
           
        elif amount < 0:
            # Sell stocks
            sell:bool = self.balance.sell(stock, -amount)
            if sell:
                print(f"Sold {-amount} shares of {ticker}")
            return sell
        else:
            return False


    # 4 simulation Execution
    def run_simulation(self) -> None:
        """Run simulation for the set timeframe"""
        # Generate all trading dates between start and end date (inclusive)
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT date FROM historicalData
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC
        """, (self.start_date, self.end_date))
        rows = cursor.fetchall()
        conn.close()

        dates = [row[0] for row in rows]
        for date in dates: #each loop = daily cycle
            #update stock values and apply strategies to each stock
            for stock in self.stocks.values():
                stock.dailyStockUpdate(date)
            
            self.record_portfolio(date)              
        
    def get_total_value(self) -> float:
        """Calculate total portfolio value (cash + investments)"""
        total = self.balance.getCurrentBalance()
        for stock in self.stocks.values():
            total += stock.get_investment_value()
        return total


    #  5 simulation termination
    def end_simulation(self, new_simulation: bool, days: int) -> None:
        """Clean up and optionally start new simulation"""
        if new_simulation & days <= 0:
            print("Simulation must be 1 day or longer")
            return
            #add better exception handling here
        if new_simulation:
            self.new_simulation()
            self.set_timeframe(days)
            self.trade_each_stock
            self.run_simulation
            self.end_simulation(False,0)
        else:
            print("Simulation ended. Final portfolio value:", self.get_total_value())
            self.plot_performance()
    
    # def calc_portfolio_performance(self, date) -> float:
    #     """Calculate overall portfolio performance as a percentage on a specific date"""
           
        

      

    #test methods to run the simulation
    def testRun(self):
        """Run a test simulation with random parameters"""
        # 1 initialisation of startdate and stocks
        self.randomiseStartDate()
        self.create_stocks()
        print("phase 1 complete: Stocks created and start date set.")
        print("starting balance = " + str(self.balance.getStartBalance()))
        print("current balance = " + str(self.balance.getCurrentBalance()))
       
        # 2 cofiguration - new simulation
        # self.new_simulation()
        # self.set_timeframe(30)
        # print("phase 2 complete: New simulation created with ID 'test_simulation' for 30 days.")

        # 2.5 configuration - load previous simulation
        self.load_previous_simulation('sim_20250712_695')
        self.set_timeframe(30)
        print("phase 2.5 complete: Previous simulation loaded and timeframe set to 30 days.")

        # 3 simulation setup (purchase stocks and set strategies)
        self.trade_each_stock()
        print("phase 3 complete: Stocks traded and strategies set.")

        # 4 simulation Execution
        self.run_simulation()
        print("phase 4 complete: Simulation executed.")

        # 5 simulation termination
        self.end_simulation(new_simulation=False, days = 0)
        print("phase 5 complete: Simulation ended and performance plotted.")
        self.strategies.activate('take_profit', threshold=0.2)



if __name__ == "__main__":
    simulation = TradingSimulator(start_balance=10000)
    simulation.testRun()
# In TradingSimulation.py
from matplotlib.figure import Figure

