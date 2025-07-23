import sqlite3
from datetime import datetime, timedelta, date

class Stock:
    def __init__(self, name: str, ticker: str, opening_value: float, opening_performance: float = 0.0):
        #static instance variables
        self.name = name 
        self.ticker = ticker
        self.opening_stock_value = opening_value
        self.opening_stock_performance = 0.0
        
        #updated post-trade
        self.number_stocks = 0
        self.cash_invested = 0.0
        
        #updated daily
        self.current_stock_value = opening_value
        self.current_stock_performance = opening_performance
        self.investment_value = 0.0
        self.investment_performance = 0.0
        
        
    def __str__(self):
        return (
            f"Stock(name={self.name}, "
            f"current_stock_value=£{self.current_stock_value:.2f}, "
            f"stock_performance={self.current_stock_performance:.2f}%, )"
            f"shares={self.number_stocks}, "
            f"cash_invested=£{self.cash_invested:.2f}, "
            f"investment_value=£{self.investment_value:.2f}, "
            f"investment_performance={self.investment_performance:.2f}% "
            
        )


    # Getters
    def get_name(self) -> str:
        return self.name
    def get_ticker(self) -> str:
        return self.ticker 
    def get_opening_stock_value(self) -> float:
        return self.opening_stock_value
    def get_opening_stock_performance(self) -> float:        
        return self.opening_stock_performance
    def get_number_stocks(self) -> int:
        return self.number_stocks
    def get_cash_invested(self) -> float:
        return self.cash_invested
    def get_current_stock_value(self) -> float:                         
        return self.current_stock_value
    def get_current_stock_performance(self) -> float:
        return self.current_stock_performance  
    def get_investment_value(self) -> float:
        return self.investment_value
    def get_investment_performance(self) -> float:
        return self.investment_performance


    # I have added setters with input valisation for it to make sense
    def set_cash_invested(self, value: float):
        if value >= 0:
            self.cash_invested = value
        else:
            raise ValueError("Invested balance cannot be negative.")
        
    def set_current_value(self, value: float):
        if value >= 0:
            self.current_stock_value = value
            self.update_current_stock_performance()  # Recalculate performance when value changes
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
        self.opening_stock_value = Stock.fetchOpeningValue(self.ticker, date)
        self.current_stock_value = self.opening_stock_value
        self.opening_stock_performance = Stock.fetchOpeningPerformance(self.ticker, date)
        self.current_stock_performance = self.opening_stock_performance
        self.number_stocks = 0

    def update_current_stock_performance(self):
        '''calculate current performance based on opening value and current value'''
        opening = self.get_opening_stock_value()
        current = self.get_current_stock_value()
        if opening == 0:
            performance = 0.0
        performance = ((current - opening) / opening) * 100

        self.current_stock_performance = performance

    def update_investment_value(self):
        """calculate the current value of the investment using stock performance"""
        self.investment_value = self.cash_invested * self.current_stock_value

    def update_investment_performance(self):
        """Calculate the performance of the investment using cash invested and investment value."""
        if self.cash_invested == 0:
            performance = 0.0
        performance = ((self.investment_value - self.cash_invested)/ self.cash_invested) * 100
        self.investment_performance = performance  

    def dailyStockUpdate(self, date) -> None:
        #update the current value and performance of the stock based on the date
        self.set_current_value(Stock.fetchClosingValue(self.ticker, date))
        self.update_current_stock_performance

        # update the investment value and performance
        self.update_investment_value
        self.update_investment_performance

    def set_stock_from_simulation(self, simulation_id) -> None:
        """Set the stock instance variables based on simulation data 
        using the start and end date from the simulation timeline."""
        
        start_date, end_date = self.get_start_and_end_dates(simulation_id)

        with sqlite3.connect("data.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT cash_invested, investment_value, investment_performance, current_stock_performance, number_of_stocks
                FROM {simulation_id}
                WHERE date = ? AND ticker = ?
            """, (end_date, self.ticker))
            data = cursor.fetchone()

        if not data:
            raise ValueError(f"No simulation data found for ID {simulation_id} on {end_date} for ticker {self.ticker}")

        # Set instance variables
        self.cash_invested = data[0]
        self.investment_value = data[1]
        self.investment_performance = data[2]
        self.current_stock_performance = data[3]
        self.number_stocks = data[4]

        # Set value-based fields
        self.opening_stock_value = self.fetchOpeningValue(self.ticker, start_date)
        self.current_stock_value = self.fetchClosingValue(self.ticker, end_date)
        self.opening_stock_performance = Stock.fetchOpeningPerformance(self.ticker, start_date)


    #static methods for fetching historical data from the database
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
    def fetchOpeningPerformance(ticker: str, todays_date) -> float:
        """calculate the opening performance of the stock 
        based on historical data within the the last year."""
        
        
        #find date one year before the given date
        if isinstance(todays_date, str):
            todays_date = datetime.strptime(todays_date, "%Y-%m-%d").date()
            startDate = todays_date - timedelta(days=365)
        elif isinstance(todays_date, datetime):
            startDate = todays_date - timedelta(days=365)
        elif isinstance(todays_date, date):
            startDate = todays_date - timedelta(days=365)
        else:
            raise TypeError("Date must be a string or datetime or date object.")
        #if the start date is before the first date in the database, set it to the first date
        if not Stock.fetchDates(startDate, todays_date, ticker):
            startDate = Stock.get_start_and_end_dates('historicalData')[0]
        
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT open, close 
            FROM historicalData 
            WHERE stock_ticker = ? AND date BETWEEN ? AND ?
            ORDER BY date
        """, (ticker, startDate, todays_date))
        
        data = cursor.fetchall()
        cursor.close()
        conn.close()

        if not data:
            raise ValueError(f"No historical data found for {ticker} between {startDate} and {todays_date}")

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
    def fetchClosingValue(ticker: str, date) -> float:
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
