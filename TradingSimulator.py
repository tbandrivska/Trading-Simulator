import sqlite3
from typing import Dict, List
from datetime import datetime, timedelta, date

import random
from Stock import Stock
from Balance import Balance
from Database import Database
import TradingStrategies as TradingStrategies
from TradingStrategies import TradingStrategies
import re

class TradingSimulator:
    
    #methods that are up for discussion
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
        restart_loop_date = self.get_loop_restart_date()
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

    def get_previous_trading_day(self, date) -> str:
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


    # 1 initialisation
    def __init__(self, start_balance: float = 10000):
        """Initialise simulation with balance and stocks"""
        self.database = Database()
        self.database.initialiseDatabase()

        #default start and end dates match the database dates
        self.start_date = self.database.getStartDate()
        self.end_date = self.database.getEndDate() 
        self.randomiseStartDate()
        
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
            value = Stock.fetchOpeningValue(ticker, self.start_date)
            performance = Stock.fetchStockPerformance(ticker, 30, self.start_date)
            self.stocks[ticker] = Stock(
                name = self.database.getStockName(ticker),
                ticker = ticker,
                opening_value = value,
                opening_performance = performance
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
        self.reset_all(self.start_date)
        self.record_portfolio(self.start_date)

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
            CREATE TABLE IF NOT EXISTS "{self.current_simulation_id}" (
                entry_number INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                current_balance REAL,
                total_invested_balance REAL,
                total_cash_profit REAL,
                portfolio_value REAL,
                portfolio_performance REAL,
                ticker TEXT,
                cash_invested REAL,
                cash_withdrawn REAL,
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
            (date, current_balance, total_invested_balance, total_cash_profit, portfolio_value, portfolio_performance, ticker, cash_invested,
            cash_withdrawn, investment_value, investment_performance, current_stock_performance, number_of_stocks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,(
                date,
                self.balance.getCurrentBalance(),
                self.balance.getTotalInvestedBalance(),
                self.balance.getTotalCashProfit(),
                self.balance.getPortfolioValue(),
                self.balance.getPortfolioPerformance(),
                stock.get_ticker(),
                stock.get_cash_invested(),
                stock.get_cash_withdrawn(),
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
        self.balance.resetBalance()
    

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

        #set new start date to the day after the last date in the simulation
        cursor.execute(f"SELECT date FROM {sim_id} ORDER BY entry_number DESC LIMIT 1")
        last_date = cursor.fetchone()[0]
        if not last_date:
            raise ValueError(f"No data found for simulation {sim_id}")
        self.start_date = self.get_next_day(last_date)

        #set balance
        list_of_stocks = self.stocks.values()
        self.balance.set_balance_from_sim(sim_id, list_of_stocks)
        
        #loop through stocks and set their values based on the simulation ID
        for Stock in self.stocks.values():
            Stock.set_stock_from_simulation(sim_id)
    
        print(f"previous simultion: {sim_id} has been loaded in")


    # 2.3 configuration - timeframe
    def set_timeframe(self, days: int) -> None:
        """Set simulation date range from start date for the given number of days."""
        if not self.start_date:
            raise ValueError("Start date not set")

        # convert start_date to date object
        if isinstance(self.start_date, str):
            start_dt = datetime.strptime(self.start_date, "%Y-%m-%d").date()
        elif isinstance(self.start_date, datetime):
            start_dt = self.start_date.date()
        elif isinstance(self.start_date, date):
            start_dt = self.start_date
        else:
            raise TypeError("self.start_date must be a string, datetime, or date")

        end_dt = start_dt + timedelta(days=days)
        self.start_date = start_dt.strftime("%Y-%m-%d")
        self.end_date = end_dt.strftime("%Y-%m-%d")
        self.current_timeframe_in_days = days
        self.days_left_in_simulation = days

        # validate dates
        self.validDates = self._validate_dates(self.start_date, self.end_date)
        if self.validDates:
            print(f"Simulation timeframe set: {self.start_date} to {self.end_date}")
        else:
            print(f"timeframe exceeds available dates as end date is {self.end_date} - time loop initiated")
        
    def _validate_dates(self, start_date, end_date) -> bool:
        """Check if start date exists and end date is within available data."""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        # Check start date exists
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM historicalData 
                WHERE date = ?
                LIMIT 1
            )
        """, (start_date,))
        start_exists = bool(cursor.fetchone()[0])

        # Check end date exists
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM historicalData 
                WHERE date = ?
                LIMIT 1
            )
        """, (end_date,))
        end_exists = bool(cursor.fetchone()[0])

        if not end_exists:
            # Accept if there is any date >= end_date
            cursor.execute("""
                SELECT MIN(date) FROM historicalData WHERE date >= ?
            """, (end_date,))
            next_date = cursor.fetchone()[0]
            end_exists = next_date is not None

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
        if stock.get_current_stock_value() is None:
            raise ValueError(f"Stock {ticker} has not been initialized with a current value")

        if amount > 0:
            # Buy stocks
            purchase:bool = self.balance.purchase(stock, amount)
            if purchase:
                print(f"Purchased {amount} shares of {ticker}")
                self.record_transaction(stock, self.start_date)

            return purchase
           
        elif amount < 0:
            # Sell stocks
            sell:bool = self.balance.sell(stock, -amount)
            if sell:
                print(f"Sold {-amount} shares of {ticker}")
                self.record_transaction(stock, self.start_date)
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

        #change the start date to be the day AFTER the last date
        self.start_date = self.get_next_day(self.end_date)
        print(f"simulation ended on: {self.end_date}")
        print(f"new start date: {self.start_date}")
        
    def sim_run(self) -> None:
        """Run simulation for the set timeframe"""
        if self.current_timeframe_in_days <= 0:
            raise ValueError("insufficient number of days in timeframe. must be at least 1")

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

        list_of_stocks = self.stocks.values()
        dates = [row[0] for row in rows]
        for date in dates:  # each loop = daily cycle
            for stock in self.stocks.values():
                stock.dailyStockUpdate(date)
                self.strategies.apply(stock, dates.index(date))
                self.balance.daily_balance_update(self.current_simulation_id, list_of_stocks) #type: ignore
                self.record_transaction(stock, date)
        if not self.validDates:
            self.start_date = self.get_loop_restart_date()                           

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

    def get_loop_restart_date(self):
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

    def get_next_day(self, date) -> str:
        """Find the day after a given date"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MIN(date) FROM historicalData 
            WHERE date > ?
        """, (date,))
        next_day = cursor.fetchone()[0]
        conn.close()

        if next_day is None: 
            next_day = self.get_loop_restart_date()

        return next_day 
 

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


    # 6 plot graphs
    def get_sim_graph_data(self) -> dict:
        """
        Plot simulation graph - show progression of portfolio value.
        Returns a dict: { "days": [1, 2, 3, ...], "balances": [1000, 1050, 1025, ...] }
        Only starts counting days after the first investment.
        """
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        #find first entry where simulation has been run 
            #investment_performance only begins updating after simulation run and not during initial trade
        cursor.execute(f"""
            SELECT entry_number
            FROM {self.current_simulation_id}
            WHERE investment_performance != 0
            ORDER BY entry_number ASC
            LIMIT 1
        """)
        results = cursor.fetchone()

        #if no investements have ever been made, return no data
        if results is None:
            return {
            "days": [0],
            "balances": [0]
            }
        first_entry = int(results[0])

        #retrieve portfolio values for each day, starting from when the first investment was made
        cursor.execute(f"""
            SELECT date, portfolio_value
            FROM {self.current_simulation_id}
            WHERE entry_number >= ?
            ORDER BY entry_number ASC
        """,(first_entry,))
        results = cursor.fetchall()
        conn.close()

        balances = []
        current_date = None
        last_portfolio_value = None

        for date, portfolio_value in results:
            if current_date is None:
                # first row
                current_date = date
                last_portfolio_value = portfolio_value
            elif date == current_date:
                # same date -> update last portfolio value to this row
                last_portfolio_value = portfolio_value
            else:
                # date changed -> save last portfolio value for previous date
                if last_portfolio_value is not None:
                    balances.append(float(last_portfolio_value))
                current_date = date
                last_portfolio_value = portfolio_value

        # append portfolio value for last date
        if last_portfolio_value is not None:
            balances.append(float(last_portfolio_value))

        days = list(range(1, len(balances) + 1))

        return {"days": days, "balances": balances}
                    
    def get_stock_graph_data(self, Stock) -> dict:
        """
        get stock graph data - show progression of invested balance of a particular stock
        Returns a dict: { "days": [1, 2, 3, ...], "balances": [1000, 1050, 1025, ...] }
        Only starts counting days after the first investment.
        """
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        ticker = Stock.get_ticker()

       #find first entry where simulation has been run 
            #investment_performance only begins updating after simulation run and not during initial trade
        cursor.execute(f"""
            SELECT entry_number
            FROM {self.current_simulation_id}
            WHERE ticker = ?
            AND investment_performance != 0
            ORDER BY entry_number ASC
            LIMIT 1
        """,(ticker,))
        results = cursor.fetchone()

        #if this stock has never been purchased, return no data
        if results is None:
            data = {
            "days": [0],
            "balances": [0]
            }
            return data

        first_purchase = int(results[0])

        #return investment value for a stock, starting from when the first purchase was made
        cursor.execute(f"""
            SELECT date, investment_value
            FROM {self.current_simulation_id}
            WHERE entry_number >= ?
            AND ticker = ?
        """, (first_purchase, ticker,))
        results = cursor.fetchall()
        conn.close()

        balances = []
        current_date = None
        last_investment_value = None

        for date, investment_value in results:
            if current_date is None:
                # first row
                current_date = date
                last_investment_value = investment_value
            elif date == current_date:
                # same date -> update last portfolio value to this row
                last_investment_value = investment_value
            else:
                # date changed -> save last portfolio value for previous date
                if last_investment_value is not None:
                    balances.append(float(last_investment_value))
                current_date = date
                last_investment_value = investment_value

        # append portfolio value for last date
        if last_investment_value is not None:
            balances.append(float(last_investment_value))

        days = list(range(1, len(balances) + 1))

        return {"days": days, "balances": balances}


    #admin methods
    def rename_simulation(self, sim_id, new_name: str) -> bool:
        """Rename a simulation table"""
        # Allow only letters, digits, spaces, and underscores
        new_name = new_name.strip() # Remove leading/trailing whitespace
        # Check length and character validity
        if len(new_name) > 30:
            print("Simulation name must be 30 characters or less")
            return False
        if not re.fullmatch(r"[A-Za-z0-9_ ]{1,50}", new_name):
            print("Invalid simulation name. Use only letters, numbers, spaces, or underscores.")
            return False
        new_name = new_name.replace('"', '""') # Escape embedded double quotes  

        if not sim_id or not new_name:
            raise ValueError("Simulation ID and new name cannot be empty")
        
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        # Check if simulation exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (sim_id,))
        if not cursor.fetchone():
            print(f"Simulation {sim_id} does not exist")
            return False
        
        # Rename the table
        cursor.execute(f"ALTER TABLE \"{sim_id}\" RENAME TO \"{new_name}\"")
        conn.commit()
        conn.close()
        
        print(f"Simulation {sim_id} renamed to {new_name}")
        return True

    def delete_simulation(self, sim_id: str) -> bool:
        """Delete a simulation by ID"""
        if not sim_id:
            raise ValueError("Simulation ID cannot be empty")
        
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        # Check if simulation exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (sim_id,))
        if not cursor.fetchone():
            print(f"Simulation {sim_id} does not exist")
            return False
        
        # Delete the table
        cursor.execute(f"DROP TABLE \"{sim_id}\"")
        conn.commit()
        conn.close()
        
        print(f"Simulation {sim_id} deleted")
        return True

    def too_many_simulations(self) -> bool:
        """Check if there are too many simulations in the database"""
        sim_limit = 10  # Set your limit here

        # Count the number of simulation tables in the database
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master 
            WHERE type='table' 
            AND name NOT IN ('historicalData', 'sqlite_sequence')
        """)
        count = cursor.fetchone()[0]
        
        conn.close()
        
        if count >= sim_limit:
            print("Too many simulations in the database. Please delete some.")
            return True
        return False
    

    #test methods to run the simulation
    def testRun(self):
        """Run a test simulation with random parameters"""
        # 1 initialisation of startdate and stocks
        print("phase 1 complete: Stocks created and start date set and instance variables initialised.")
        print("starting balance = " + str(self.balance.getStartBalance()))
        print("current balance = " + str(self.balance.getCurrentBalance()))
       
        # 2 cofiguration - new simulation
        if self.too_many_simulations():
            print("Too many simulations in the database. Please delete some.")
            return
        self.new_simulation()
        self.set_timeframe(30)
        print("phase 2 complete: New simulation created with ID 'test_simulation' for 30 days.")
        # self.set_timeframe(365)
        # print("phase 2 complete: New simulation created with ID 'test_simulation' for 365 days.")

        # 2.5 configuration - load previous simulation
        # self.load_prev_simulation('sim_20250724_46828')
        # self.set_timeframe(1)
        # print("phase 2.5 complete: Previous simulation loaded and timeframe set to 30 days.")
        # self.set_timeframe(10000)
        # print("phase 2.5 complete: Previous simulation loaded and timeframe set to 10000 days.")

        # 3 simulation setup (purchase stocks and set strategies)
        # self.trade_each_stock()
        # print("phase 3 complete: Stocks traded and strategies set.")

        # 4 simulation Execution
        self.run_simulation()
        print("phase 4 complete: Simulation executed.")
        #self.load_prev_simulation('sim_20250724_46828')
        self.new_simulation()
        self.set_timeframe(30)  # or any number of days you want
        self.run_simulation()
        print("Simulation ID:", self.current_simulation_id)
        self.set_timeframe(1)

        # # 5 simulation termination
        # self.end_simulation(new_simulation=False, days = 0)
        # print("phase 5 complete: Simulation ended and performance plotted.")

        


if __name__ == "__main__":
    simulation = TradingSimulator(start_balance=10000)
    simulation.testRun()


