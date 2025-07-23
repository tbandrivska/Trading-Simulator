import sqlite3

class Balance:
    #initialising the instance variables
    def __init__(self, startBalance:float):
        self.startBalance = startBalance
        self.currentBalance = startBalance
        self.totalInvestedBalance = 0
        self.balancePerformance = 0.0

    #getter and setter methods for the instance variables
    def setStartBalance(self, startBalance:float):
        if startBalance < 0:
            raise ValueError("Start balance cannot be negative.")
        if startBalance == 0:
            raise ValueError("Start balance cannot be zero.")
        self.startBalance = startBalance
    def getStartBalance(self):
        return self.startBalance

    def setCurrentBalance(self, currentBalance:float):
        if currentBalance < 0:
            raise ValueError("Current balance cannot be negative.")
        self.currentBalance = currentBalance
    def getCurrentBalance(self):
        return self.currentBalance

    def setTotalInvestedBalance(self, totalInvestedBalance:float):
        if totalInvestedBalance < 0:
            raise ValueError("Total invested balance cannot be negative.")
        self.totalInvestedBalance = totalInvestedBalance
    def getTotalInvestedBalance(self):
        return self.totalInvestedBalance    

    def setBalancePerformance(self, balancePerformance: float):
        self.balancePerformance = balancePerformance
    def getBalancePerformance(self):
        return self.balancePerformance

    #purchase method buys stocks and removes the amount from the balance
    def purchase(self, Stock, amount:int):
        price = Stock.get_current_stock_value() * amount
        if self.currentBalance >= price:
            self.currentBalance -= price
            self.totalInvestedBalance += price
            Stock.set_cash_invested(Stock.get_cash_invested() + price)
            Stock.set_number_stocks(Stock.get_number_stocks() + amount)
            return True
        else:
            print("Insufficient balance to purchase stocks.")
            return False
      
    #sell method sells stocks and adds the profit/loss to the balance
    def sell(self, Stock, amount:int):
        if Stock.get_number_stocks() >= amount:
            price = Stock.get_current_stock_value() * amount
            self.currentBalance += price
            self.totalInvestedBalance -= price
            Stock.set_cash_invested(Stock.get_cash_invested() - price)
            Stock.set_number_stocks(Stock.get_number_stocks() - amount)
            return True
        else:
            print("Insufficient stocks to sell.")
            return False

    #reset method resets the instance variables to their initial values
    def resetBalance(self, start_balance:float):
        self.startBalance = start_balance
        self.currentBalance = start_balance
        self.totalInvestedBalance = 0

    def set_balance_from_sim(self, simulation_id: str) -> None:
        """Set the balance instance variables based on the first and last date in the simulation data."""
        start_date, end_date = Balance.get_start_and_end_dates(simulation_id)

        results = {}

        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        for label, date in [("start", start_date), ("end", end_date)]:
            cursor.execute(f"""
                SELECT current_balance, total_invested_balance, balance_performance
                FROM {simulation_id}
                WHERE date = ?
            """, (date,))
            
            data = cursor.fetchone()
            if not data:
                raise ValueError(f"No simulation data found for ID {simulation_id} on {date}")
            
            results[label] = data

        conn.close()

        self.startBalance = results["start"][0]
        self.currentBalance = results["end"][0]
        self.totalInvestedBalance = results["end"][1]
        self.balancePerformance = results["end"][2]

    def update_performance(self):
        total_balance = self.currentBalance + self.totalInvestedBalance
        performance = (total_balance - self.startBalance / self.startBalance) * 100
        return performance
   
    #copy and pasted from Stock.py - maybe should be moved to a common utility module    
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
        conn.close()
        
        if not dates or not all(dates):
            raise ValueError(f"No valid dates found for simulation ID {simulation_id}")
        
        return dates[0], dates[1]