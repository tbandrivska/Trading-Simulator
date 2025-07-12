import sqlite3
from datetime import datetime

class Stock:
    def __init__(self, name: str, ticker: str, opening_value: float, opening_performance: float = 0.0):
        self.name = name 
        self.ticker = ticker         
        self.cash_invested = 0.0
        self.opening_value = opening_value
        self.current_value = opening_value
        self.investment_value = self.cash_invested * self.current_value
        self.opening_performance = opening_performance
        self.current_performance = self.update_performance()
        self.number_stocks = 0
        
        
    def __str__(self):
        return (
            f"Stock(name={self.name}, "
            f"shares={self.number_stocks}, "
            f"cash_invested={self.cash_invested:.2f}, "
            f"current_value={self.current_value:.2f}, "
            f"investment_value={self.investment_value:.2f}, "
            f"performance={self.current_performance:.2f}%)"
        )


    # Getters
    def get_name(self) -> str:
        return self.name
    def get_cash_invested(self) -> float:
        return self.cash_invested
    def get_opening_value(self) -> float:
        return self.opening_value
    def get_current_value(self) -> float:                         
        return self.current_value
    def get_investment_value(self) -> float:
        return self.investment_value
    def get_opening_performance(self) -> float:        
        return self.opening_performance
    def get_current_performance(self) -> float:
        return self.current_performance  
    def get_number_stocks(self) -> int:
        return self.number_stocks
    def get_ticker(self) -> str:
        return self.ticker     


    # I have added setters with input valisation for it to make sense
    def set_cash_invested(self, value: float):
        if value >= 0:
            self.cash_invested = value
        else:
            raise ValueError("Invested balance cannot be negative.")
        
    def set_current_value(self, value: float):
        if value >= 0:
            self.current_value = value
            self.update_performance()  # Recalculate performance when value changes
        else:
            raise ValueError("Stock value cannot be negative.")
        
    def set_number_stocks(self, quantity: int):
        if quantity >= 0:
            self.number_stocks = quantity
        else:
            raise ValueError("Number of stocks cannot be negative.")
   
    def initialise_stock(self, date) -> None:
        """Reset the stock instance variables and set opening and current value."""
        self.cash_invested = 0.0
        self.opening_value = Stock.fetchOpeningValue(self.ticker, date)
        self.current_value = self.opening_value
        self.opening_performance = Stock.fetchOpeningPerformance(self.ticker, date)
        self.current_performance = 0.0
        self.number_stocks = 0

    def update_performance(self):
        '''calculate current performance based on opening value and current value'''
        opening = self.get_opening_value()
        current = self.get_current_value()
        if opening == 0:
            return 0.0
        return (current - opening) / opening

    def get_investment_performance(self) -> float:
        """Calculate the performance of the investment using invested balance and  investment value."""
        if self.cash_invested == 0:
            return 0.0
        return ((self.investment_value - self.cash_invested)/ self.cash_invested) * 100
    
    #methods for fetching historical data from the database
    @staticmethod
    def fetchDates(startDate, endDate, ticker: str) -> list[str]:
        """Get all available dates for a stock (for simulation time range)."""
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT date 
            FROM historicalData 
            WHERE stock_ticker = ? AND date BETWEEN ? AND ?
            ORDER BY date
        """, (ticker, startDate, endDate))
        
        dates = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return dates

    @staticmethod
    def approximateValue(ticker: str, date: str, openOrClose: str) -> float:
        """
        Fetch the opening value for a stock on a given date.
        If the exact date is not available, it returns the closest previous date's opening value.
        """
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT open, close 
            FROM historicalData 
            WHERE stock_ticker = ? AND date <= ?
            ORDER BY date DESC
        """, (ticker, date))

        data = cursor.fetchone()
        cursor.close()
        conn.close()

        if not data:
            raise ValueError(f"No data found for {ticker} before {date}")

        # Return the requested value based on openOrClose parameter
        return data[0] if openOrClose.lower() == "open" else data[1]
    
    @staticmethod
    def fetchOpeningPerformance(ticker: str, date) -> float:
        """calculate the opening performance of the stock 
        based on historical data within the simulation time range."""
        
        startDate = Stock.get_start_and_end_dates('historicalData')[0]
        
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT open, close 
            FROM historicalData 
            WHERE stock_ticker = ? AND date BETWEEN ? AND ?
            ORDER BY date
        """, (ticker, startDate, date))
        
        data = cursor.fetchall()
        cursor.close()
        conn.close()

        if not data:
            raise ValueError(f"No historical data found for {ticker} between {startDate} and {date}")

        opening_value = data[0][0]
        closing_value = data[-1][1] 

        if opening_value == 0:
            return 0.0
        return ((closing_value - opening_value) / opening_value) * 100.0

    @staticmethod
    def fetchOpeningValue(ticker: str, date) -> float:
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT open
            FROM historicalData 
            WHERE stock_ticker = ? AND date = ?
        """, (ticker, date))
        data = cursor.fetchone()
        cursor.close()
        conn.close()
        if not data:
            return Stock.approximateValue(ticker, date, "open")
        return data[0]
    
    @staticmethod
    def fetchClosingValue(ticker: str, date: str) -> float:
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT close
            FROM historicalData 
            WHERE stock_ticker = ? AND date = ?
        """, (ticker, date))
        data = cursor.fetchone()
        cursor.close()
        conn.close()
        if not data:
            return Stock.approximateValue(ticker, date, "close")
        return data[0]

    # update the stock variables that change daily: current value, performance and invested balance
    def dailyStockUpdate(self,date: str) -> None:
        #update the current value of the stock based on the date
        current_value: float = Stock.fetchClosingValue(self.ticker, date)
        self.set_current_value(current_value)
    
        #update the performance of the stock
        if self.opening_value == 0:
            self.current_performance = 0.0
        else:
            self.current_performance = (
                (self.current_value - self.opening_value) / self.opening_value
            ) * 100.0

        # update the invested balance based on the number of stocks and current value
        invested_balance: float = self.get_number_stocks() * current_value
        self.set_cash_invested(invested_balance)


    #methods for setting stock instance variables from a simulation
    def set_stock_from_simulation(self, simulation_id) -> None:
        """Set the stock instance variables based on simulation data 
        using the start and end date from the simulation timeline."""
        
        start_date, end_date = self.get_start_and_end_dates(simulation_id)

        with sqlite3.connect("data.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT cash_invested, investment_value, current_performance, number_of_stocks
                FROM {simulation_id}
                WHERE date = ? AND ticker = ?
            """, (end_date, self.ticker))
            data = cursor.fetchone()

        if not data:
            raise ValueError(f"No simulation data found for ID {simulation_id} on {end_date} for ticker {self.ticker}")

        # Set instance variables
        self.set_cash_invested(data[0])
        self.investment_value = data[1]
        self.current_performance = data[2]
        self.set_number_stocks(data[3])

        # Set value-based fields
        self.opening_value = self.fetchOpeningValue(self.ticker, start_date)
        self.current_value = self.fetchClosingValue(self.ticker, end_date)
        self.opening_performance = Stock.fetchOpeningPerformance(self.ticker, start_date)


    @staticmethod
    def get_start_and_end_dates(simulation_id) -> tuple[str, str]:
        """Fetch the start and end dates of the simulation ."""
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        cursor.execute(f"""         
            SELECT MIN(date), MAX(date)
            FROM {simulation_id}
        """)
        dates = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not dates or not all(dates):
            raise ValueError(f"No valid dates found for simulation ID {simulation_id}")
        
        return dates[0], dates[1]

    # do we need the method below? 
    # We can use fetchOpeningValue or fetchClosingValue instead ?
    #  I really believe we do, as it allows to get the price on a specific date, so we should include it for the simulation,
    # I am gonna add it back, but commented out for now, while we rethink it, just in case

    def get_price_on_date(self, date: str, price_type: str = "close") -> float:
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT {price_type}
            FROM historicalData
            WHERE stock_ticker = ? AND date = ?
        """, (self.ticker, date))
        data = cursor.fetchone()
        conn.close()
        if not data:
           return Stock.approximateValue(self.ticker, date, price_type)
        return data[0]