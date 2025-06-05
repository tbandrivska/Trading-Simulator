import sqlite3
import yfinance

conn = sqlite3.connect('stocks.db') #databse name is stocks.db
cursor = conn.cursor()

#Stocks and Tickers to fetch data for
#tickers are just the stock names as they appear in yahoo finance data
stocks = ["Apple Inc.", "Alphabet Inc.", "Microsoft Corporation", "Amazon.com Inc.", "Tesla Inc.", 
          "Meta Platforms Inc.", "NVIDIA Corporation","Berkshire Hathaway Inc.", "Visa Inc.", "Johnson & Johnson"]
tickers = ["AAPL", "GOOGL", "MSFT","AMZN", "TSLA", "META", "NVDA", "BRK-B", "V", "JNJ"]

# Create a table in stocks.dbs for storing stock data
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

# Define the date range for fetching historical data using the earliest and latest dates across all tickers
earliestDates = []
latestDates = []
for ticker in tickers:
    data = yfinance.download(ticker, period="max")
    earliestDates.append(data.index.min())
    latestDates.append(data.index.max())

startDate = max(earliestDates).date()  # Get the earliest shared date across all tickers
endDate = min(latestDates).date()  # Get the latest shared date across all tickers

# Function to download stock data and insert it into the database
def downloadData(startDate, endDate):  
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

#add data to table if table is empty
cursor.execute("SELECT COUNT(*) FROM stockDataTable")
count = cursor.fetchone()[0]  # Fetch the count from the result
if count == 0:
    print("No data found in the database, downloading data...")
    downloadData(startDate, endDate)

#add data to table if new data is available 
cursor.execute("SELECT MAX(date) FROM stockDataTable")
maxDate = cursor.fetchone()[0]  # Fetch the latest date from the result

print("maxdate:", maxDate)
print("latestdate:", str(max(latestDates)))

if maxDate != str(max(latestDates)):
    print("New data available, updating database...")
    downloadData(maxDate, max(latestDates))

cursor.close()    
conn.close()