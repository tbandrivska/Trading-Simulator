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
    def __init__(self, start_balance: float = 10000):
        """Initialise simulation with balance and stocks"""
        self.database = Database()
        self.database.initialiseDatabase()
        
        self.balance = Balance(startBalance=start_balance, currentBalance=start_balance)
        self.stocks: Dict[str, Stock] = {}  # {ticker: Stock}
        self.current_simulation_id = None

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
        self.balance.resetBalance()


    # 3 simulation setup (purchase stocks and set strategies)
    def trade_each_stock(self) -> None:
        #purchase stocks or set trading strategies for each stock before simulation begins
        trading:bool = True
        for ticker in self.database.getTickers():
            while trading:
                print("Would you like to purchase or sell " + self.database.getStockName(ticker) + "?(yes/no)")
                user_input = input().strip().lower()
                if user_input == "yes":
                    print("How many shares would you like to buy or sell? (positive to buy, negative to sell)")
                    try:
                        amount = int(input()) # Convert string input to integer (add input validation later)
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
    def run_simulation(self) -> None:
        """Main simulation loop"""
        if not self.start_date or not self.end_date:
            raise ValueError("Timeframe not set")
        
        self.trade_each_stock()  # Allow user to trade before simulation starts

        dates = self._get_simulation_dates()
        
        for date in dates:
            self._run_daily_cycle(date)

    def _get_simulation_dates(self) -> List[str]:
        """Get all dates between start and end date"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT start_date, end_date FROM simulations WHERE id = ?", (self.current_simulation_id,))
        start, end = cursor.fetchone()
        conn.close()

        if isinstance(start, str):
            start = datetime.strptime(start, "%Y-%m-%d").date()
        if isinstance(end, str):
            end = datetime.strptime(end, "%Y-%m-%d").date()

        delta = end - start
        listOfDays = []
        for i in range(delta.days + 1):
            day = start + timedelta(days=i)
            listOfDays.append(day.strftime("%Y-%m-%d"))
        return listOfDays
    
        #I Changed this funxtion so it returns all the dates in the range because the databse skips weekends and holidays
        # Doesnt the Wall street not work over the weekend and on holidays? So like the stock values don't change on those days?? It's stil fine ig nglno
            # BUT if we want to create a graph that shows the performance of the portfolio over time, 
                # we need to have all the dates in the range, even if there is no data for that date.
                    #but its fine because i made an approximation function to fill in the gaps of missing dates in the graph

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

    def _apply_strategies(self, stock: Stock, date: str) -> None:
        """Execute all active trading strategies"""
        # (Example!!!!) Sell if stock gains 20%
        if stock.get_current_value() >= 1.2 * stock.get_opening_value():
            self.balance.sell(stock.get_ticker(), stock.get_number_stocks())

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

#things to do:
# - Add more trading strategies and allow user to select them
# - add input validation for user inputs (phase 3 functions)
# - create function that sets up the opening_performance of a stock before the simulation starts
    #maybe have it compare the stock value on the simulation start date and the day before (?)
# - add better exception handling to end_simulation function
             