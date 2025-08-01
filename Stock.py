import sqlite3
from datetime import datetime, timedelta, date

class Stock:
    def __init__(self, name: str, ticker: str, opening_value: float, opening_performance: float):
        #static instance variables
        self.name = name 
        self.ticker = ticker
        self.opening_stock_value: float = opening_value
        self.opening_stock_performance: float = opening_performance
        
        #updated post-trade
        self.number_stocks = 0
        self.cash_invested = 0.0 #all cash ever paid into stock
        self.cash_withdrawn = 0.0 #all cash ever taken out of stock
        self.cash_profit = self.cash_withdrawn - self.cash_invested #cash made in excess of what is invested into stock
        self.investment_value = 0.0 #post trade upadates and daily upadates
        
        #updated daily
        self.current_stock_value = opening_value
        self.current_stock_performance = opening_performance
        self.investment_performance = 0.0
        
        
    def __str__(self):
        return (
            f"Stock(name = {self.name}, "
            f"current_stock_value = £{self.current_stock_value:.2f}, "
            f"stock_performance = {self.current_stock_performance:.2f}%, "
            f"shares = {self.number_stocks}, "
            f"cash_invested = £{self.cash_invested:.2f}, "
            f"cash_withdrawn = £{self.cash_withdrawn:.2f}, "
            f"investment_value = £{self.investment_value:.2f}, "
            f"investment_performance = {self.investment_performance:.2f}% "            
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
    def get_cash_withdrawn(self) -> float:
        return self.cash_withdrawn
    def get_cash_profit(self) -> float:
        return self.cash_profit
    def get_current_stock_value(self) -> float:                         
        return self.current_stock_value
    def get_current_stock_performance(self) -> float:
        return self.current_stock_performance  
    def get_investment_value(self) -> float:
        return self.investment_value
    def get_investment_performance(self) -> float:
        return self.investment_performance


    # setters
    def set_cash_invested(self, value: float):
        """cash invested is a reflection of how much money was invested into a stock
        but it cannot reflect cash withdrawn from stock"""
        if value >= 0:
            self.cash_invested = value
        else:
            raise ValueError("cash invested cannot be negative.")
        
    def set_cash_withdrawn(self, value: float):
        if value >= 0:
            self.cash_withdrawn = value
        else:
            raise ValueError("cash withdrawn cannot be negative.")
        
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
   
    def initialise_stock(self, date):
        """Reset the stock instance variables and set opening and current value."""
        self.number_stocks = 0
        self.cash_invested = 0.0
        self.cash_withdrawn = 0.0
        self.cash_profit = 0.0
        self.investment_value = 0.0
        self.investment_performance = 0.0

        self.opening_stock_value = self.fetchOpeningValue(self.ticker, date)
        self.current_stock_value = self.opening_stock_value
        self.opening_stock_performance = self.fetchStockPerformance(self.ticker, 30, date)
        self.current_stock_performance = self.opening_stock_performance   

    def update_cash_profit(self):
        self.cash_profit = self.cash_withdrawn - self.cash_invested

    def update_current_stock_performance(self):
        opening = self.get_opening_stock_value()
        current = self.get_current_stock_value()
        if opening == 0:
            performance = 0.0
        else:
            performance = ((current - opening) / opening) * 100
        self.current_stock_performance = performance

    def update_investment_value(self):
        """calculate the current value of the investment using stock performance"""
        self.investment_value = self.number_stocks * self.current_stock_value

    def update_investment_performance(self):
        """Calculate the performance of the investment using cash invested/withdrawn and investment value."""
        overall_profit = self.investment_value + self.cash_profit

        if self.cash_invested == 0:
            performance = 0.0
        else:
            performance = (overall_profit / self.cash_invested) * 100

        self.investment_performance = performance  

    def dailyStockUpdate(self, date) -> None:
        #update the current value and performance of the stock based on the date
        self.current_stock_value = Stock.fetchOpeningValue(self.ticker, date)
        self.current_stock_performance = Stock.fetchStockPerformance(self.ticker, 30, date)
        self.update_cash_profit()
        self.update_investment_value()
        self.update_investment_performance()

    def set_stock_from_simulation(self, simulation_id) -> None:
        """Set the stock instance variables based on last entry in simulation data."""
        with sqlite3.connect("data.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT cash_invested, cash_withdrawn, investment_value, investment_performance, current_stock_performance, number_of_stocks
                FROM {simulation_id}
                WHERE ticker = ?
                ORDER BY entry_number DESC
                LIMIT 1
            """, (self.ticker,))
            data = cursor.fetchone()

        if not data:
            raise ValueError(f"No simulation data found for ID: {simulation_id} on last entry for ticker: {self.ticker}")

        # Set instance variables
        self.cash_invested = data[0]
        self.cash_withdrawn = data[1]
        self.update_cash_profit()
        self.investment_value = data[2]
        self.investment_performance = data[3]
        self.current_stock_performance = data[4]
        self.number_stocks = data[5]

        # Set value-based fields
        start_date, end_date = self.get_sim_start_and_end_dates(simulation_id)
        self.opening_stock_value = self.fetchOpeningValue(self.ticker, start_date)
        self.current_stock_value = self.fetchOpeningValue(self.ticker, end_date)
        self.opening_stock_performance = self.fetchStockPerformance(self.ticker, 30, start_date)


    #static methods for fetching historical data (and sim data) from the database
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
    def fetchStockPerformance(ticker: str, timeframe: int, todays_date) -> float:
        """calculate the opening performance of the stock 
        based on historical data within the the last month."""
        
        
        #find date one year before the given date
        if isinstance(todays_date, str):
            todays_date = datetime.strptime(todays_date, "%Y-%m-%d").date()
            startDate = todays_date - timedelta(days=timeframe)
        elif isinstance(todays_date, datetime):
            startDate = todays_date - timedelta(days=timeframe)
        elif isinstance(todays_date, date):
            startDate = todays_date - timedelta(days=timeframe)
        else:
            raise TypeError("Date must be a string or datetime or date object.")
        
        #if the start date is before the first date in the database, set it to the first date
        if not Stock.fetchDates(startDate, todays_date, ticker):
            startDate = Stock.get_historical_start_and_end_dates()[0]
        
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
    def get_historical_start_and_end_dates() -> tuple[str, str]:
        """Fetch the start and end dates from the historical data ."""
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        cursor.execute(f"""         
            SELECT MIN(date), MAX(date)
            FROM historicalData
        """)
        dates = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not dates or not all(dates):
            raise ValueError(f"No valid dates found in historical data")
        
        return dates[0], dates[1]

    @staticmethod
    def get_sim_start_and_end_dates(simulation_id) -> tuple[str,str]:
        """Fetch the start and end dates from simulation data"""
        with sqlite3.connect("data.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT date
                FROM {simulation_id}
                WHERE entry_number = (SELECT MIN(entry_number) FROM {simulation_id})
            """)
            start_date = cursor.fetchone()[0]
        
        with sqlite3.connect("data.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT date
                FROM {simulation_id}
                WHERE entry_number = (SELECT MAX(entry_number) FROM {simulation_id})
            """)
            end_date = cursor.fetchone()[0]

        return (start_date, end_date)

        
        