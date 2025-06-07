import sqlite3
from datetime import datetime
class Stock:
    def __init__(self, name: str, ticker: str, opening_value: float, opening_performance: float = 0.0):
        self.__name = name        
        self.__invested_balance = 0.0
        self.__opening_value = opening_value
        self.__current_value = opening_value  # Starts at the same value as an opening one
        self.__opening_performance = opening_performance
        self.__current_performance = opening_performance
        self.__number_stocks = 0
        self.__ticker = ticker  # New: Store the ticker symbol (e.g., "AAPL")

    # Getters
    def get_name(self):
        return self.__name

    def get_invested_balance(self):
        return self.__invested_balance

    def get_opening_value(self):
        return self.__opening_value

    def get_current_value(self):                         
        return self.__current_value
    
    def get_opening_performance(self):        
        return self.__opening_performance
    
    def get_current_performance(self):
        return self.__current_performance  
    
    def get_number_stocks(self):
        return self.__number_stocks

    # I have added setters with input valisation for it to make sense
    def set_invested_balance(self, value: float):
        if value >= 0:
            self.__invested_balance = value
        else:
            raise ValueError("Invested balance cannot be negative.")

    def set_current_value(self, value: float):
        if value >= 0:
            self.__current_value = value
            self.__update_performance()  # Recalculate performance when value changes
        else:
            raise ValueError("Stock value cannot be negative.")

    def set_number_stocks(self, quantity: int):
        if quantity >= 0:
            self.__number_stocks = quantity
        else:
            raise ValueError("Number of stocks cannot be negative.")


    def __str__(self):
        return (
            f"Stock(name={self.__name}, "
            f"shares={self.__number_stocks}, "
            f"invested={self.__invested_balance:.2f}, "
            f"current_value={self.__current_value:.2f}, "
            f"performance={self.__current_performance:.2f}%)"
        )
     # Database Methods
def __update_performance(self):
    """Recalculate performance percentage."""
    if self.__opening_value == 0:
        self.__current_performance = 0.0
    else:
        self.__current_performance = (
            (self.__current_value - self.__opening_value) / self.__opening_value
        ) * 100.0

    @staticmethod
    def fetch_all_dates(ticker: str) -> list[str]:
        """Get all available dates for a stock (for simulation time range)."""
        conn = sqlite3.connect("stocksDB")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT date 
            FROM historicalData 
            WHERE stock_ticker = ? 
            ORDER BY date
        """, (ticker,))
        
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()
        return dates

    def update_current_value(self, date: str) -> None:
        """Update the stock's current value based on historical data for a given date."""
        data = self.fetch_historical_data(self.__ticker, date)
        self.__current_value = data["close"]
        self.__update_performance()

    #simulation helper methods (?)
    def get_ticker(self) -> str:
        """Return the stock's ticker symbol (e.g., 'AAPL')."""
        return self.__ticker

    def get_price_on_date(self, date: str, price_type: str = "close") -> float:
        """Get the stock's price (open/close/high/low) on a given date."""
        conn = sqlite3.connect("historicalDataDB")
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT {price_type} 
            FROM stockDataTable 
            WHERE stock_ticker = ? AND date = ?
        """, (self.__ticker, date))
        
        price = cursor.fetchone()[0]
        conn.close()
        return price

    