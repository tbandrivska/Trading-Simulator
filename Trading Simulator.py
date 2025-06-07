from typing import Dict, List
import sqlite3
from Balance import Balance
from Stock import Stock

class TradingSimulation:
    def __init__(self, balance: Balance, db_path: str = "historicalData.db"):
        """
        Initialize the trading simulation.
        
        Args:
            balance (Balance): User's balance object.
            db_path (str): Path to the SQLite database. Defaults to "historicalData.db".
        """
        self.balance = balance
        self.stocks: Dict[str, Stock] = {}  # Maps tickers to Stock objects
        self.current_date = None
        self.simulation_dates: List[str] = []
        self.db_path = db_path

    def add_stock(self, stock: Stock) -> None:
        """Add a stock to the simulation."""
        if not isinstance(stock, Stock):
            raise TypeError("Only Stock objects can be added.")
        self.stocks[stock.get_ticker()] = stock

    def fetch_simulation_dates(self, start_date: str, end_date: str) -> None:
        """
        Fetch all unique dates within the simulation range from the database.
        
        Args:
            start_date (str): Start date in 'YYYY-MM-DD' format.
            end_date (str): End date in 'YYYY-MM-DD' format.
        """
        if not self.stocks:
            raise ValueError("No stocks added to simulation.")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT date 
                FROM stockDataTable
                WHERE date BETWEEN ? AND ?
                ORDER BY date
            """, (start_date, end_date))
            
            self.simulation_dates = [row[0] for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            conn.close()

    def run_simulation(self, start_date: str, end_date: str) -> None:
        """
        Run the simulation day-by-day within the specified date range.
        
        Args:
            start_date (str): Start date in 'YYYY-MM-DD' format.
            end_date (str): End date in 'YYYY-MM-DD' format.
        """
        self.balance.setStartDate(start_date)
        self.balance.setEndDate(end_date)
        self.fetch_simulation_dates(start_date, end_date)

        if not self.simulation_dates:
            print("No data available for the selected date range.")
            return

        for date in self.simulation_dates:
            self.current_date = date
            print(f"\nSimulating {date}...")
            
            # Update all stock prices for the day
            for ticker, stock in self.stocks.items():
                try:
                    stock.update_current_value(date)
                    print(f"{ticker}: ${stock.get_current_value():.2f}")
                except ValueError as e:
                    print(f"Error updating {ticker}: {e}")

    def buy_stock(self, ticker: str, amount: int) -> bool:
        """
        Buy a specified amount of a stock.
        
        Args:
            ticker (str): Stock ticker symbol (e.g., "AAPL").
            amount (int): Number of shares to buy.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if ticker not in self.stocks:
            raise ValueError(f"Stock {ticker} not in simulation.")
        return self.balance.purchase(self.stocks[ticker], amount)

    def sell_stock(self, ticker: str, amount: int) -> bool:
        """
        Sell a specified amount of a stock.
        
        Args:
            ticker (str): Stock ticker symbol (e.g., "AAPL").
            amount (int): Number of shares to sell.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if ticker not in self.stocks:
            raise ValueError(f"Stock {ticker} not in simulation.")
        return self.balance.sell(self.stocks[ticker], amount)

    def reset_simulation(self) -> None:
        """Reset the simulation (stocks, balance, and dates)."""
        for stock in self.stocks.values():
            stock.reset()
        self.balance.resetBalance()
        self.current_date = None
        self.simulation_dates = []
# Test
if __name__ == "__main__":
    # Initialize balance and simulation
    balance = Balance(startBalance=10_000, currentBalance=10_000)
    sim = TradingSimulation(balance, db_path="historicalData.db")
    
    # Add a stock (ensure Stock.py and Balance.py are in the same directory)
    apple = Stock("Apple Inc.", "AAPL", opening_value=150.0)
    sim.add_stock(apple)
    
    # Run simulation for a date range
    sim.run_simulation("2023-01-01", "2023-01-10")
    
    # Buy/sell during simulation
    sim.buy_stock("AAPL", 5)  # Buy 5 shares
    sim.sell_stock("AAPL", 2)  # Sell 2 shares

