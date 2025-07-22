import sqlite3
from typing import Dict, List
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from collections import Counter
import random
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

    def get_total_value(self) -> float:
        """Calculate total portfolio value (cash + investments)"""
        total = self.balance.getCurrentBalance()
        for stock in self.stocks.values():
            total += stock.get_investment_value()
        return total

    def set_and_validate_timeframe(self, days: int):
        """only set the timeframe if days is within the max days range"""
        max_days = self.calc_max_days()
        self.set_timeframe(days)
        while days > max_days:
            print("Invalid number of days. Days must be between 1 and " + str(max_days))
            days = int(input("set simulation timeframe in days: "))
            self.set_timeframe(days)  

    def calc_max_days(self) -> int:
        """calculate the max number of days simulation can run for to avoid repetitive data.
        This allows a the simulation to only loop 3 times max"""
        #get the timeframe in days
        total_days = self.current_timeframe_in_days
        
        #find the restart loop date and historical data end date
        restart_loop_date = self.loop_restart_date()
        historical_data_end_date = self.database.getEndDate() 

        #convert dates to datetime.date objects if they are strings or datetime objects
        if isinstance(restart_loop_date, str):
            restart_loop_date = datetime.strptime(restart_loop_date, "%Y-%m-%d").date()
        if isinstance(restart_loop_date, datetime):
            restart_loop_date = restart_loop_date.date()
        if isinstance(historical_data_end_date, str):
            historical_data_end_date = datetime.strptime(historical_data_end_date, "%Y-%m-%d").date()   
        if isinstance(historical_data_end_date, datetime):
            historical_data_end_date = historical_data_end_date.date()  
        if restart_loop_date is None or historical_data_end_date is None:
            raise ValueError("Restart loop date or historical data end date is not set correctly.")        

        #calculate the number of days between the restart loop date and historical data end date
        loop_days = (historical_data_end_date - restart_loop_date).days + 1  # +1 to include end date

        #calculate maximum days so it only allows simulation loop to occur 3 times
        max_days = total_days + (loop_days * 3)

        if max_days < 30:
            return 30
        
        return max_days


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

        self.current_timeframe_in_days = 0
        self.days_left_in_simulation = 0
        self.prev_random_numbers = [] 
        self.validDates = True
        
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
                entry_number INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                current_balance REAL,
                total_invested_balance REAL,
                ticker TEXT,
                cash_invested REAL,
                investment_value REAL,
                investment_performance REAL,
                current_stock_performance REAL,
                number_of_stocks INTEGER
            )
        """)
        conn.commit()
        conn.close()  

    def record_portfolio(self, date):
        """Record the state of all stocks and balance on a specific day"""
        for stock in self.stocks.values():
            self.record_transaction(stock,date)
        
    def record_transaction(self, stock, date):
        """Record transaction data into database after each stock transaction"""
        # Validate table name to prevent SQL injection
        if not self.current_simulation_id or not self.current_simulation_id.isidentifier():
            raise ValueError("Invalid simulation ID for table name.")

        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT INTO "{self.current_simulation_id}" 
            (date, current_balance, total_invested_balance, ticker, cash_invested,
                investment_value, investment_performance, current_stock_performance, number_of_stocks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,(
                date,
                self.balance.getCurrentBalance(),
                self.balance.getTotalInvestedBalance(),
                stock.get_ticker(),
                stock.get_cash_invested(),
                stock.get_investment_value(),
                stock.get_investment_performance(),
                stock.get_current_stock_performance(),
                stock.get_number_stocks()
            ))
        
        conn.commit()
        conn.close()

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
    def load_prev_simulation(self, sim_id: str) -> None:
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
        self.start_date = str(last_date[0])

        #set balance
        self.balance.set_balance_from_sim(sim_id)
        
        #loop through stocks and set their values based on the simulation ID
        for Stock in self.stocks.values():
            Stock.set_stock_from_simulation(sim_id)
    

    # 2.3 configuration - timeframe
    def set_timeframe(self, days: int) -> None:
        """Set simulation date range from start date"""
        self.current_timeframe_in_days = days
        if not self.start_date:
            raise ValueError("Start date not set")
        
        print(f"self.start_date = {self.start_date}, type = {type(self.start_date)}")
        # Convert start_date string to datetime object
        if isinstance(self.start_date, str):
            self.end_date = datetime.strptime(self.start_date, "%Y-%m-%d").date() + timedelta(days=days)
        elif isinstance(self.start_date, datetime):
            self.end_date = self.start_date.date() + timedelta(days=days)  # Strip time part if needed
        elif isinstance(self.start_date, date):
            self.end_date = self.start_date + timedelta(days=days)
        else:
            raise TypeError("self.start_date must be a string, datetime, or date")

        #convert start date and end date to strings
        if isinstance(self.start_date, date):
            self.start_date = self.start_date.strftime("%Y-%m-%d")
        if isinstance(self.end_date, date):
            self.end_date = self.end_date.strftime("%Y-%m-%d")

        self.days_left_in_simulation = days
        self.validDates = self._validate_dates(self.start_date, self.end_date)

        if self.validDates:
            print(f"Simulation timeframe set: {self.start_date} to {self.end_date}")
        else:
            print("timeframe exceeds available dates, time loop initiated")
        
    def _validate_dates(self, start_date, end_date) -> int:
        """Check if dates exist in database"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM historicalData 
                WHERE date = ?
                LIMIT 1
            )
        """, (start_date,))
        start_exists = bool(cursor.fetchone()[0])
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM historicalData 
                WHERE date = ?
                LIMIT 1
            )
        """, (end_date,))
        end_exists = bool(cursor.fetchone()[0])

        conn.close()
        return start_exists and end_exists  


    # 3 simulation setup (purchase stocks and set strategies)
    def trade_each_stock(self) -> None:
        #purchase stocks or set trading strategies for each stock before simulation begins
        for ticker in self.get_tickers():
            trading: bool = True
            stock: Stock = self.stocks[ticker]
            while trading:
                print("Balance: " + str(self.balance.getCurrentBalance()))
                print(stock.get_name() + " costs: " + str(stock.get_current_stock_value()))
                print("Would you like to purchase or sell " + stock.get_name() + "?(yes/no)")
                user_input = input().strip().lower()
                if user_input == "yes":
                    print("How many shares would you like to buy or sell? (positive to buy, negative to sell)")
                    amount = int(input()) # Convert string input to integer (add input validation later)
                    try:
                        if self.trade_a_stock(ticker, amount):
                            #self.record_transaction(stock, date)
                            trading = False
                    except ValueError:
                        print("Invalid input. Please enter a valid number.")
                elif user_input == "no":
                    #self.record_transaction(stock, date)
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
        if stock.get_current_stock_value() is None:
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
    def run_simulation(self):
        """repeatedly run simulation for the number of days given by the user"""
        print("initial run")
        self.sim_run()
        self.calc_days_left()
        
        count = 2
        while (not self.validDates) and 0 < self.days_left_in_simulation:
            print(f"run: {count}")
            self.calc_days_left()
            print(f"days left: {self.days_left_in_simulation}")
            self.set_timeframe(self.days_left_in_simulation)
            self.sim_run()
            count += 1

        print("simulation runs are now completed")

    def sim_run(self) -> None:
        """Run simulation for the set timeframe"""
        if self.current_timeframe_in_days <= 0:
            print("insufficient number of days. must be at least 1")
            return

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
                #insert - execute strategies
                self.record_transaction(stock, date)

        if not self.validDates:
            self.start_date = self.loop_restart_date()                           

    def calc_days_left(self):
        """calculate the number of days left over after running an incomplete simulation"""
        #calculate incomplete simulation time frame
        start_date = self.start_date
        end_date = self.database.getEndDate()
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        if start_date is None or end_date is None:
            raise ValueError("Start date or end date is not set correctly.")

        sim_days = (end_date - start_date).days + 1  # +1 to include end date 

        days_left = self.current_timeframe_in_days - sim_days
        if days_left < 0:
            days_left = 0

        self.days_left_in_simulation = days_left

    def loop_restart_date(self):
        """If a time frame is longer than we have days for, use the final date we have
        to locate a previous date with similar values. Now, everytime the final date is 
        reached, we continue from this date with similar values"""
        
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        finalDate = self.database.getEndDate() 
        value_range = 0.05
        dates = []

        #find all valid dates where stocks have a similar value 
        while len(dates) == 0:
            for Stock in self.stocks.values():
                ticker = Stock.get_ticker()
                OpeningValue = Stock.fetchOpeningValue(ticker, finalDate)
                upperBound = OpeningValue * (1+value_range)
                lowerBound = OpeningValue * (1-value_range)

                cursor.execute("""
                            SELECT date FROM historicalData 
                            WHERE open >= ? AND open <= ? 
                            AND stock_ticker = ?
                            AND date < ?
                """,(lowerBound ,upperBound, ticker, finalDate))
                
                #add any dates found to the list
                dates = [row[0] for row in cursor.fetchall()]


            #Convert to datetime objects
            date_objects = [datetime.strptime(date, '%Y-%m-%d') for date in dates]
            #Find the earliest
            earliest_date = min(date_objects)
            #Optional: convert back to string
            earliest_date_str = earliest_date.strftime('%Y-%m-%d')
            
            if len(dates) < 10:
                #if not enough dates are returned increase the range by 5% and restart the process
                value_range = value_range + 0.05
                dates = []
        
        conn.close()
        print("loop restart date: " + earliest_date_str)
        return earliest_date_str


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
            self.sim_run
            self.end_simulation(False,0)
        else:
            print("Simulation ended. Final portfolio value:", self.get_total_value())
            #self.plot_performance()
        

      

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
        self.new_simulation()
        # self.set_timeframe(30)
        # print("phase 2 complete: New simulation created with ID 'test_simulation' for 30 days.")
        self.set_timeframe(365)
        print("phase 2 complete: New simulation created with ID 'test_simulation' for 365 days.")

        # # 2.5 configuration - load previous simulation
        # self.load_prev_simulation('sim_20250721_5146')
        # # self.set_timeframe(30)
        # # print("phase 2.5 complete: Previous simulation loaded and timeframe set to 30 days.")
        # self.set_timeframe(10000)
        # print("phase 2.5 complete: Previous simulation loaded and timeframe set to 10000 days.")

        #3 simulation setup (purchase stocks and set strategies)
        self.trade_each_stock()
        print("phase 3 complete: Stocks traded and strategies set.")

        # 4 simulation Execution
        self.run_simulation()
        print("phase 4 complete: Simulation executed.")

        # 5 simulation termination
        self.end_simulation(new_simulation=False, days = 0)
        print("phase 5 complete: Simulation ended and performance plotted.")
        


if __name__ == "__main__":
    simulation = TradingSimulator(start_balance=10000)
    simulation.testRun()


