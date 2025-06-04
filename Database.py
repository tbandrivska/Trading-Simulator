import sqlite3
import yfinance

conn = sqlite3.connect('stocksDB') #databse name is stocksDB
cursor = conn.cursor()

#Stocks and Tickers to fetch data for
#tickers are just the stock names as they appear in yahoo finance data
stocks = ["Apple Inc.", "Alphabet Inc.", "Microsoft Corporation", "Amazon.com Inc.", "Tesla Inc.", 
          "Meta Platforms Inc.", "NVIDIA Corporation","Berkshire Hathaway Inc.", "Visa Inc.", "Johnson & Johnson"]
tickers = ["AAPL", "GOOGL", "MSFT","AMZN", "TSLA", "META", "NVDA", "BRK-B", "V", "JNJ"]

# Define the date range for fetching historical data using the earliest and latest dates across all tickers
earliestDates = []
latestDates = []
for ticker in tickers:
    earliestDate = yfinance.download(ticker, period="max").index.min()
    earliestDates.append(earliestDate)
    latestDate = yfinance.download(ticker, period="max").index.max()
    latestDates.append(latestDate)

startDate = max(earliestDates).date()  # Get the earliest shared date across all tickers
endDate = min(latestDates).date()  # Get the latest shared date across all tickers

# Create a table in stocksDB for storing stock data
# Column titles: date, open, high, low, close, stock_ticker, stock_name
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
    
# Loop through tickers and fetch data
for ticker in tickers:
    try:
        #access yfinance and download the data for a stock (using its ticker)
        stockData = yfinance.download(ticker, start=startDate, end=endDate)
        
        #reset index to get 'Date' as a column
        # stockData.reset_index(inplace=True)
        
        #loop through each date in the stock data
        for date in stockData.index:
            row = stockData.loc[date]
            #insert data into the 'stocksDB' database
            cursor.execute("""
                INSERT OR IGNORE INTO stockDataTable (
                    date, open, high, low, close, stock_ticker, stock_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                (date.date()),  #.date() converts datetime to date
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