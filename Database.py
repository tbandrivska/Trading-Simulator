import sqlite3
import yfinance

class historicalData:
    
    def __init__(self, startDate, endDate):
        self.stocks = ["Apple Inc.", "Alphabet Inc.", "Microsoft Corporation", "Amazon.com Inc.", "Tesla Inc.", 
            "Meta Platforms Inc.", "NVIDIA Corporation","Berkshire Hathaway Inc.", "Visa Inc.", "Johnson & Johnson"]
        self.tickers = ["AAPL", "GOOGL", "MSFT","AMZN", "TSLA", "META", "NVDA", "BRK-B", "V", "JNJ"]
        self.startDate = startDate
        self.endDate = endDate

    # Connect to the SQLite database (or create it if it doesn't exist)
    def createDatabase():
        # Connect to the SQLite database (or create it if it doesn't exist)
        conn = sqlite3.connect('historicalData.db') #databse name is historicalData.db
        cursor = conn.cursor()

        # Create a table in historicalData.dbs for storing stock data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stockDataTable (
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
    def defineDates(tickers):
        earliestDates = []
        latestDates = []

        for ticker in tickers:
            data = yfinance.download(ticker, period="max")
            earliestDates.append(data.index.min())
            latestDates.append(data.index.max())

        startDate = max(earliestDates).date()  # Get the earliest shared date across all tickers
        endDate = min(latestDates).date()  # Get the latest shared date across all tickers

        self.startDate = startDate
        self.endDate = endDate


    # Function to download stock data and insert it into the database
    def downloadData(startDate, endDate, tickers, stocks):  
        # Connect to the SQLite database
        conn = sqlite3.connect('historicalData.db')
        cursor = conn.cursor()

        #fetch data for each ticker
        for ticker in tickers:
            try:
                #access yfinance and download the data for a stock (using its ticker)
                stockData = yfinance.download(ticker, start=startDate, end=endDate)
                
                #loop through each date in the stock data
                for date in stockData.index:
                    row = stockData.loc[date]
                    #insert data into the 'stocksDB' database
                    cursor.execute("""
                        INSERT OR IGNORE INTO stockDataTable (
                            date, open, high, low, close, stock_ticker, stock_name
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        (date.date()), #.date() converts datetime to date
                        (float(row["Open"].iloc[0])), #convert series to float
                        (float(row["High"].iloc[0])), 
                        (float(row["Low"].iloc[0])),
                        (float(row["Close"].iloc[0])),
                        ticker,
                        stocks[tickers.index(ticker)]  # Get the corresponding stock name
                    ))
                
                conn.commit() # Commit the changes to the database

            except Exception as e:
                print(f"Error downloading or inserting data for {ticker}: {e}")

        cursor.close()    
        conn.close()

    # Function to check if the database is empty or if new data is available, and update accordingly
    def updateData(startDate, endDate):
        # Connect to the SQLite database
        conn = sqlite3.connect('historicalData.db')
        cursor = conn.cursor()

        #add data to table if table is empty
        cursor.execute("SELECT COUNT(*) FROM stockDataTable")
        count = cursor.fetchone()[0]  # Fetch the count from the result
        if count == 0:
            print("No data found in the database, downloading data...")
            downloadData(startDate, endDate, self.tickers, self.stocks)

        #add data to table if new data is available 
        cursor.execute("SELECT MAX(date) FROM stockDataTable")
        maxDate = cursor.fetchone()[0]  # Fetch the latest date from the result

        if maxDate != str(endDate):
            print("New data available, updating database...")
            downloadData(maxDate, endDate, self.tickers, self.stocks)

        cursor.close()    
        conn.close()

    def main():
        # Create the database and table if they don't exist
        createDatabase()

        # Define the date range for fetching historical data
        defineDates(self.tickers)

        # upload data
        updateData(self.startDate, self.endDate)




    