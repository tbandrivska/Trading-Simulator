import sqlite3
from typing import Dict, List
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import random
from datetime import datetime
from Stock import Stock
from Balance import Balance
from Database import Database

class TradingSimulation:
    """
    STRATEGIES: A dictionary defining available trading strategies.

    Each strategy contains:
    - 'description': A brief explanation of the strategy.
    - 'params': Parameters that can be adjusted to customize the strategy.

    Users can interact with or modify these strategies by:
    - Adding new strategies with a similar structure.
    - Adjusting the 'params' values to fit their trading preferences.
    - Using these strategies during the simulation to automate trading decisions.

    Example:
    To modify the 'take_profit' strategy threshold to 30%, update:
    STRATEGIES['take_profit']['params']['threshold'] = 0.3
    """
    STRATEGIES = {
        'take_profit': {
            'description': 'Sell when stock gains X%',
            'params': {'threshold': 0.2}  # Default 20%
        },
        'stop_loss': {
            'description': 'Sell when stock loses X%',
            'params': {'threshold': 0.1}  # Default 10%
        },
        'dollar_cost_avg': {
            'description': 'Buy X shares every Y days',
            'params': {'shares': 5, 'interval': 7}  # Buy 5 shares every 7 days
        }
    }

    def __init__(self, start_balance: float = 10000):
        """Initialise simulation with balance and stocks"""
        self.database = Database()
        self.database.initialiseDatabase()

        self.start_balance = start_balance
        self.balance = Balance(start_balance)

        self.stocks: Dict[str, Stock] = {}  # {ticker: Stock}
        self.current_simulation_id = None
        self.active_strategies: Dict[str, dict] = {} 

        #default start and end dates match the database dates
        self.start_date = self.database.getStartDate()
        self.end_date = self.database.getEndDate() 


    # 1 initialisation of startdate and stocks
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
        
        print(f"Random start date set: {self.start_date.strftime('%Y-%m-%d')}")

    def _create_stocks(self) -> None:
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


    # 2 cofiguration
    def new_simulation(self, simulation_id: str, days: int) -> None:
        """Reset everything for a new simulation"""
        self.current_simulation_id = simulation_id
        self.set_timeframe(days) 
        self._create_simulation_table()
        self._reset_all()

    def _create_simulation_table(self) -> None:
        """Create table to track daily portfolio changes"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS sim_{self.current_simulation_id} (
                date TEXT,
                start_balance REAL,
                end_balance REAL,
                ticker TEXT,
                start_invested REAL,
                end_invested REAL,
                start_shares INTEGER,
                end_shares INTEGER,
                start_stock_value REAL,
                end_stock_value REAL,
                PRIMARY KEY (date, ticker)
            )
        """)
        conn.commit()
        conn.close()  

    def setup_opening_performance(self):
        """
        Calculate and store the opening performance for each stock before the simulation starts.
        Compares the stock value on the simulation start date with the previous day.
        """
        for stock in self.stocks:
            start_date = self.simulation_start
            prev_date = start_date - timedelta(days=1)
            current_price = stock.get_price(start_date)
            previous_price = stock.get_price(prev_date)
            if current_price and previous_price:
                opening_performance = (current_price - previous_price) / previous_price
                stock.opening_performance = opening_performance
            else:
                stock.opening_performance = None

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

    def add_strategy(self, strategy_name: str, **params) -> None:
        """Add a trading strategy with custom parameters"""
        if strategy_name not in self.STRATEGIES:
            raise ValueError(f"Invalid strategy. Available: {list(self.STRATEGIES.keys())}")
        
        # Validate parameters
        valid_params = self.STRATEGIES[strategy_name]['params']
        for param, value in params.items():
            if param not in valid_params:
                raise ValueError(f"Invalid parameter '{param}' for strategy '{strategy_name}'")
            if isinstance(valid_params[param], float) and not 0 <= value <= 1:
                raise ValueError(f"Parameter '{param}' must be between 0 and 1")
        
        self.active_strategies[strategy_name] = {
            **self.STRATEGIES[strategy_name]['params'],
            **params
        }

    def set_timeframe(self, days: int) -> None:
        """Set simulation date range from start date"""
        if not self.start_date:
            raise ValueError("Start date not set")
        
        #need to change this so it loops instead of erroring if the date range is invalid
        end_date = self.start_date + timedelta(days=days)
        if not self._validate_dates(self.start_date, end_date):
            raise ValueError("Invalid date range")
        
        self.end_date = end_date.strftime("%Y-%m-%d")
        print(f"Simulation timeframe set: {self.start_date} to {self.end_date}")

    def _validate_dates(self, start: str, end: str) -> bool:
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
    
    def _reset_all(self) -> None:
        """Reset stocks and balance to initial state"""
        for stock in self.stocks.values():
            start_value:float = Stock.fetchOpeningValue(stock.get_ticker(), self.start_date)
            stock.initialise_stock(start_value)
        self.balance.resetBalance(self.start_balance)


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
                        if self.trade_stock(ticker, amount):
                            trading = False
                    except ValueError:
                        print("Invalid input. Please enter a valid number.")
                elif user_input == "no":
                    trading = False
                else:
                    print("Invalid input. Please enter 'yes' or 'no'.")
                      
        #insert another loop here to apply strategies to each stock  

    def trade_stock(self, ticker: str, amount: int) -> bool:
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

    def _apply_strategies(self, stock: Stock, date: str, day_index: int = None) -> None:
        """Execute all active trading strategies"""
        current_value = stock.get_current_value()
        opening_value = stock.get_opening_value()
        
        # Take profit strategy
        if 'take_profit' in self.active_strategies:
            threshold = self.active_strategies['take_profit']['threshold']
            if current_value >= (1 + threshold) * opening_value:
                self.trade_stock(stock.get_ticker(), -stock.get_number_stocks())
        
        # Stop loss strategy
        if 'stop_loss' in self.active_strategies:
            threshold = self.active_strategies['stop_loss']['threshold']
            if current_value <= (1 - threshold) * opening_value:
                self.trade_stock(stock.get_ticker(), -stock.get_number_stocks())
        
        # Dollar-cost averaging (only if day_index is provided)
        if day_index is not None and 'dollar_cost_avg' in self.active_strategies:
            strategy = self.active_strategies['dollar_cost_avg']['params']
            if day_index % strategy['interval'] == 0:
                self.trade_stock(stock.get_ticker(), strategy['shares'])
                      
    def run_simulation(self) -> None:
        """Main simulation loop"""
        if not self.start_date or not self.end_date:
            raise ValueError("Timeframe not set")

        # Generate all trading dates between start and end date (inclusive)
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT date FROM historicalData
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC
        """, (self.start_date.strftime("%Y-%m-%d"), self.end_date))
        rows = cursor.fetchall()
        conn.close()

        dates = [row[0] for row in rows]
        for i, date in enumerate(dates):
            for stock in self.stocks.values():
                stock.dailyStockUpdate(date)
                self._apply_strategies(stock, date, i)
            self._run_daily_cycle(date)

    def _get_simulation_dates(self) -> List[str]:
        """Get all dates between start and end date from the simulation table"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT date FROM sim_{self.current_simulation_id} 
            WHERE date BETWEEN ? AND ? 
            ORDER BY date ASC
        """, (self.start_date, self.end_date))

        rows = cursor.fetchall()
        conn.close()

        # Extract the dates as strings
        listOfDays = [row[0] for row in rows]
        return listOfDays

        # Doesnt the Wall street not work over the weekend and on holidays? So like the stock values don't change on those days?? It's stil fine ig nglno
            # yup - but stock graphs still show the dates of the weekends and holidays for continuency
            # stock prices stay the same and the approximation function replicates that

    def _run_daily_cycle(self, date: str) -> None:
        """Process one day of trading"""
        #records values at the start of the day (before trading)
        self._record_portfolio_state(date, "start")            
                
        for stock in self.stocks.values():
            stock.dailyStockUpdate(date)
            self._apply_strategies(stock, date)

        self._record_portfolio_state(date, "end")
        
        # Optional(???) Print daily summary
        print(f"\n{date}:")
        print(f"Portfolio Value: ${self._get_total_value():.2f}")

    def _record_portfolio_state(self, date: str, phase: str) -> None:
        """Save portfolio snapshot to database"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        for ticker, stock in self.stocks.items():
            cursor.execute(f"""
                INSERT OR REPLACE INTO sim_{self.current_simulation_id} VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                date,
                self.balance.getStartBalance() if phase == "start" else None,
                self.balance.getCurrentBalance() if phase == "end" else None,
                self.balance.getTotalInvestedBalance() if phase == "start" else None,
                self.balance.getTotalInvestedBalance() if phase == "end" else None,
                ticker,
                stock.get_number_stocks() if phase == "start" else None,
                stock.get_number_stocks() if phase == "end" else None,
                stock.get_current_value() if phase == "start" else None,
                stock.get_current_value() if phase == "end" else None
            ))
        
        conn.commit()
        conn.close()  


    def _get_total_value(self) -> float:
        """Calculate total portfolio value (cash + investments)"""
        total = self.balance.getCurrentBalance()
        for stock in self.stocks.values():
            total += stock.get_current_value() * stock.get_number_stocks()
        return total


    #  5 simulation termination
    def end_simulation(self, new_simulation: bool, days: int) -> None:
        """Clean up and optionally start new simulation"""
        if new_simulation & days <= 0:
            print("Simulation must be 1 day or longer")
            return
            #add better exception handling here
        if new_simulation:
            new_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.new_simulation(new_id, days)
        else:
            print("Simulation ended. Final portfolio value:", self._get_total_value())
            self.plot_performance()

    def plot_performance(self) -> None:
        """Generate performance graph without using pandas"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT date, end_balance, end_invested 
            FROM sim_{self.current_simulation_id}
            WHERE ticker = 'AAPL'
            ORDER BY date
        """)
        
        rows = cursor.fetchall()
        conn.close()

        dates = [datetime.strptime(row[0], "%Y-%m-%d") for row in rows]
        total_values = [row[1] + row[2] for row in rows]

        plt.figure(figsize=(10, 5))
        plt.plot(dates, total_values, marker='o')
        plt.title("Portfolio Value Over Time")
        plt.xlabel("Date")
        plt.ylabel("Total Value")
        plt.grid(True)
        plt.tight_layout()
        plt.show()


    #test method to run the simulation
    def testRun(self):
        """Run a test simulation with random parameters"""
        # 1 initialisation of startdate and stocks
        self.randomiseStartDate()
        self._create_stocks()
        print("phase 1 complete: Stocks created and start date set.")
        print("starting balance = " + str(self.balance.getStartBalance()))
        print("current balance = " + str(self.balance.getCurrentBalance()))
        # 2 cofiguration
        self.new_simulation("test_simulation", days=30)
        print("phase 2 complete: New simulation created with ID 'test_simulation' for 30 days.")
        # 3 simulation setup (purchase stocks and set strategies)
        self.trade_each_stock()
        print("phase 3 complete: Stocks traded and strategies set.")
        # 4 simulation Execution
        self.run_simulation()
        print("phase 4 complete: Simulation executed.")
        # 5 simulation termination
        self.end_simulation(new_simulation=False, days = 0)
        print("phase 5 complete: Simulation ended and performance plotted.")

if __name__ == "__main__":
    simulation = TradingSimulation(start_balance=10000)
    simulation.testRun()
