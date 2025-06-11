import sqlite3
import yfinance

class Database:
    
    def __init__(self, startDate=None, endDate=None):
        self.stocks = ["Apple Inc.", "Alphabet Inc.", "Microsoft Corporation", "Amazon.com Inc.", "Tesla Inc.", 
            "Meta Platforms Inc.", "NVIDIA Corporation","Berkshire Hathaway Inc.", "Visa Inc.", "Johnson & Johnson"]
        self.tickers = ["AAPL", "GOOGL", "MSFT","AMZN", "TSLA", "META", "NVDA", "BRK-B", "V", "JNJ"]
        self.startDate = startDate
        self.endDate = endDate

    #getter methods
    def getStocks(self):
        return self.stocks
    def getTickers(self):
        return self.tickers
    def getStockName(self, ticker):
        if ticker in self.tickers:
            return self.stocks[self.tickers.index(ticker)]
        else:
            raise ValueError(f"Ticker {ticker} not found in the list of stocks.")
    def getStartDate(self):
        return self.startDate
    def getEndDate(self):
        return self.endDate

    # Connect to the SQLite database (or create it if it doesn't exist)
    @staticmethod
    def createDatabase(self) -> None:
        # Connect to the SQLite database (or create it if it doesn't exist)
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        # Create a table datasbase for storing historical data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historicalData (
                date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                stock_ticker TEXT,
                stock_name TEXT,
                PRIMARY KEY (stock_ticker, date)
            )
        """)

        cursor.close()    
        conn.close()

    # Define the date range for fetching historical data using the earliest and latest dates across all tickers
    def defineDates(self) -> None:
        earliestDates = []
        latestDates = []

        for ticker in self.tickers:
            data = yfinance.download(ticker, period="max")
            earliestDates.append(data.index.min())
            latestDates.append(data.index.max())

        startDate = max(earliestDates).date()  # Get the earliest shared date across all tickers
        endDate = min(latestDates).date()  # Get the latest shared date across all tickers

        self.startDate = startDate
        self.endDate = endDate

    # download stock data and insert it into the database
    def downloadData(self, startDate, endDate) -> None:  
        # Connect to the SQLite database
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        #fetch data for each ticker
        for ticker in self.tickers:
            try:
                #access yfinance and download the data for a stock (using its ticker)
                stockData = yfinance.download(ticker, start=startDate, end=endDate)
                
                #loop through each date in the stock data
                for date in stockData.index:
                    row = stockData.loc[date]
                    #insert data into the histroicalData table
                    cursor.execute("""
                        INSERT OR IGNORE INTO historicalData (
                            date, open, high, low, close, stock_ticker, stock_name
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        (date.date()), #.date() converts datetime to date
                        (float(row["Open"].iloc[0])), #convert series to float
                        (float(row["High"].iloc[0])), 
                        (float(row["Low"].iloc[0])),
                        (float(row["Close"].iloc[0])),
                        ticker,
                        self.stocks[self.tickers.index(ticker)]  # Get the corresponding stock name
                    ))
                
                conn.commit() # Commit the changes to the database

            except Exception as e:
                print(f"Error downloading or inserting data for {ticker}: {e}")

        cursor.close()    
        conn.close()

    # Function to check if the database is empty or if new data is available, and update accordingly
    def updateData(self) -> None:
        # Connect to the SQLite database
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        #add data to table if table is empty
        cursor.execute("SELECT COUNT(*) FROM historicalData")
        count = cursor.fetchone()[0]  # Fetch the count from the result
        if count == 0:
            print("No data found in the database, downloading data...")
            self.downloadData(self.startDate, self.endDate)

        #add data to table if new data is available 
        cursor.execute("SELECT MAX(date) FROM historicalData")
        maxDate = cursor.fetchone()[0]  # Fetch the latest date from the result

        if maxDate != str(self.endDate):
            print("New data available, updating database...")
            self.downloadData(maxDate, self.endDate)

        cursor.close()    
        conn.close()

    # Main function to initialize the database and update data
    def initialiseDatabase(self) -> None:
        # Create the database and table if they don't exist
        Database.createDatabase()

        # Define the date range for fetching historical data
        self.defineDates()

        # upload data
        self.updateData()

    
test:Database = Database()
test.initialiseDatabase()