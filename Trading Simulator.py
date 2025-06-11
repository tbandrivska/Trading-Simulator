import sqlite3
from typing import Dict, List
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

import Balance
import Database
import Stock
from Stock import Stock

class TradingSimulation:
    def __init__(self, start_balance: float = 10000):
        """Initialise simulation with balance and stocks"""
        self.database = Database()
        self.database.initialiseDatabase()
        
        self.balance = Balance(startBalance=start_balance, currentBalance=start_balance)
        self.stocks: Dict[str, Stock] = {}  # {ticker: Stock}
        self.current_simulation_id = None
        self.start_date = None
        self.end_date = None
        
        self._create_stocks()  


    # 1 initialisation of stocks

    def _create_stocks(self) -> None:
        """Create Stock objects for all tickers in database"""
        for ticker in self.database.getTickers():
            # Get opening price from earliest available date
            opening_price = Stock.fetchOpeningValue(ticker, self.database.getStartDate())
            self.stocks[ticker] = Stock(
                name=self.database.getStockName(ticker),
                ticker=ticker,
                opening_value=opening_price
            )

 
    # 2 setup
    def new_simulation(self, simulation_id: str) -> None:
        """Reset everything for a new simulation"""
        self.current_simulation_id = simulation_id
        self._create_simulation_table()
        self._reset_all()

    def _create_simulation_table(self) -> None:
        """Create table to track daily portfolio changes"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS sim_{self.current_simulation_id} (
                date TEXT,
                start_balance REAL,
                end_balance REAL,
                start_invested REAL,
                end_invested REAL,
                ticker TEXT,
                start_shares INTEGER,
                end_shares INTEGER,
                start_stock_value REAL,
                end_stock_value REAL,
                PRIMARY KEY (date, ticker)
        """)
        conn.commit()
        conn.close()

    def _reset_all(self) -> None:
        """Reset stocks and balance to initial state"""
        for stock in self.stocks.values():
            stock.initialiseStock(self.database.getStartDate())
        self.balance.resetBalance()

    # 3 coonfiguration
    def set_timeframe(self, start_date: str, end_date: str) -> None:
        """Set simulation date range (YYYY-MM-DD)"""
        if not self._validate_dates(start_date, end_date):
            raise ValueError("Invalid date range")
        self.start_date = start_date
        self.end_date = end_date

    def _validate_dates(self, start: str, end: str) -> bool:
        """Check if dates exist in database"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM historicalData 
                WHERE date BETWEEN ? AND ?
                LIMIT 1
            )
        """, (start, end))
        exists = cursor.fetchone()[0]
        conn.close()
        return bool(exists)
    
    # 4 simulation Execution
    def run_simulation(self) -> None:
        """Main simulation loop"""
        if not self.start_date or not self.end_date:
            raise ValueError("Timeframe not set")
        
        dates = self._get_simulation_dates()
        
        for date in dates:
            self._run_daily_cycle(date)

    def _get_simulation_dates(self) -> List[str]:
        """Get all trading days in timeframe"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT date FROM historicalData
            WHERE date BETWEEN ? AND ?
            ORDER BY date
        """, (self.start_date, self.end_date))
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()
        return dates

    def _run_daily_cycle(self, date: str) -> None:
        """Process one day of trading"""
        #  records
        start_values = self._record_portfolio_state(date, "start")
        
    
        for stock in self.stocks.values():
            stock.dailyStockUpdate(date)
            self._apply_strategies(stock, date)
        

        self._record_portfolio_state(date, "end")
        
        # Optional(???) Print daily summary
        print(f"\n{date}:")
        print(f"Portfolio Value: ${self._get_total_value():.2f}")

    def _record_portfolio_state(self, date: str, phase: str) -> None:
        """Save portfolio snapshot to database"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        for ticker, stock in self.stocks.items():
            cursor.execute(f"""
                INSERT OR REPLACE INTO sim_{self.current_simulation_id} VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                date,
                self.balance.getStartBalance() if phase == "start" else None,
                self.balance.getCurrentBalance() if phase == "end" else None,
                self.balance.getTotalInvestedBalance() if phase == "start" else None,
                self.balance.getTotalInvestedBalance() if phase == "end" else None,
                ticker,
                stock.get_number_stocks() if phase == "start" else None,
                stock.get_number_stocks() if phase == "end" else None,
                stock.get_current_value() if phase == "start" else None,
                stock.get_current_value() if phase == "end" else None
            ))
        
        conn.commit()
        conn.close()

    def _apply_strategies(self, stock: Stock, date: str) -> None:
        """Execute all active trading strategies"""
        # (Example!!!!) Sell if stock gains 20%
        if stock.get_current_value() >= 1.2 * stock.get_opening_value():
            self.sell_stock(stock.get_ticker(), stock.get_number_stocks())

    def _get_total_value(self) -> float:
        """Calculate total portfolio value (cash + investments)"""
        total = self.balance.getCurrentBalance()
        for stock in self.stocks.values():
            total += stock.get_current_value() * stock.get_number_stocks()
        return total

    #  5 simulation trrmination
    def end_simulation(self, new_simulation: bool = False) -> None:
        """Clean up and optionally start new simulation"""
        if new_simulation:
            new_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.new_simulation(new_id)
        else:
            print("Simulation ended. Final portfolio value:", self._get_total_value())
            self.plot_performance()

    def plot_performance(self) -> None:
        """Generate performance graph without using pandas"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT date, end_balance, end_invested 
            FROM sim_{self.current_simulation_id}
            WHERE ticker = 'AAPL'
            ORDER BY date
        """)
        
        rows = cursor.fetchall()
        conn.close()

        dates = [datetime.strptime(row[0], "%Y-%m-%d") for row in rows]
        total_values = [row[1] + row[2] for row in rows]

        plt.figure(figsize=(10, 5))
        plt.plot(dates, total_values, marker='o')
        plt.title("Portfolio Value Over Time")
        plt.xlabel("Date")
        plt.ylabel("Total Value")
        plt.grid(True)
        plt.tight_layout()
        plt.show()
