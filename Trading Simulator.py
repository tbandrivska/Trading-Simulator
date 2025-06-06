from typing import Dict
import sqlite3
from Balance import Balance  
from Stock import Stock  

class TradingSimulation:
    def __init__(self, balance: Balance):
        self.balance = balance
        self.stocks: Dict[str, Stock] = {}  # maping tickers to Stock objects
        self.current_date = None
        self.simulation_dates = []  # dates to simulate from db

    def add_stock(self, stock: Stock) -> None:
        """Add a stock to the simulation."""
        self.stocks[stock.get_ticker()] = stock

    def fetch_simulation_dates(self, start_date: str, end_date: str) -> None:
        """Fetch all dates in the simulation range from the database."""
        conn = sqlite3.connect("stocksDB")
        cursor = conn.cursor()
        
        # Get dates for any stock (assuming all stocks have the same dates)
        ticker = list(self.stocks.keys())[0] if self.stocks else None
        if not ticker:
            raise ValueError("No stocks added to simulation.")
        
        cursor.execute("""
            SELECT DISTINCT date 
            FROM stockDataTable 
            WHERE stock_ticker = ? AND date BETWEEN ? AND ?
            ORDER BY date
        """, (ticker, start_date, end_date))
        
        self.simulation_dates = [row[0] for row in cursor.fetchall()]
        conn.close()

    def run_simulation(self, start_date: str, end_date: str) -> None:
        """Run the simulation day-by-day."""
        self.balance.setStartDate(start_date)
        self.balance.setEndDate(end_date)
        self.fetch_simulation_dates(start_date, end_date)

        for date in self.simulation_dates:
            self.current_date = date
            print(f"\nSimulating {date}...")
            
            # updating all stock prices for the day
            for ticker, stock in self.stocks.items():
                stock.update_current_value(date)
                print(f"{ticker}: ${stock.get_current_value():.2f}")



    def buy_stock(self, ticker: str, amount: int) -> bool:
        """Buy a stock using the Balance class."""
        if ticker not in self.stocks:
            raise ValueError(f"Stock {ticker} not in simulation.")
        
        stock = self.stocks[ticker]
        return self.balance.purchase(stock, self.balance.getCurrentBalance(), amount)

    def sell_stock(self, ticker: str, amount: int) -> bool:
        """Sell a stock using the Balance class."""
        if ticker not in self.stocks:
            raise ValueError(f"Stock {ticker} not in simulation.")
        
        stock = self.stocks[ticker]
        return self.balance.sell(stock, self.balance.getCurrentBalance(), amount)

    def reset_simulation(self) -> None:
        """Reset the simulation (stocks + balance)."""
        for stock in self.stocks.values():
            stock.reset()
        self.balance.resetBalance()
        self.current_date = None