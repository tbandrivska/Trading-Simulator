import sqlite3

class Balance:
    #initialising the instance variables
    def __init__(self, startBalance:float):
        #static instance variables
        self.startBalance = startBalance
        #updated post-trade
        self.currentBalance = startBalance
        self.totalInvestedBalance = 0.0 #cash spent on stocks
        self.totalCashProfit = 0.0 #cash made from selling investments
        #updated daily
        self.portfolioValue = 0.0 #combined value of all stocks
        self.portfolioPerformance = 0.0

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

    def setTotalCashProfit(self, totalCashProfit: float):
        self.totalCashProfit = totalCashProfit
    def getTotalCashProfit(self):
        return self.totalCashProfit

    def setPortfolioValue(self, portfolioValue:float):
        self.portfolioValue = portfolioValue
    def getPortfolioValue(self):
        return self.portfolioValue

    def setPortfolioPerformance(self, balancePerformance: float):
        self.portfolioPerformance = balancePerformance
    def getPortfolioPerformance(self):
        return self.portfolioPerformance

    #purchase method buys stocks and removes the amount from the balance
    def purchase(self, Stock, amount:int):
        price = Stock.get_current_stock_value() * amount
        if self.currentBalance >= price:
            self.currentBalance -= price
            self.totalInvestedBalance += price
            Stock.set_cash_invested(Stock.get_cash_invested() + price)
            Stock.set_number_stocks(Stock.get_number_stocks() + amount)
            Stock.update_cash_profit()
            Stock.update_investment_value()
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
            Stock.set_cash_withdrawn(Stock.get_cash_withdrawn() + price)
            Stock.set_number_stocks(Stock.get_number_stocks() - amount)
            self.totalCashProfit =- Stock.get_cash_profit() #remove previous profit from total
            Stock.update_cash_profit()
            self.totalCashProfit =+ Stock.get_cash_profit() #add new profit to total
            Stock.update_investment_value()
            return True
        else:
            print("Insufficient stocks to sell.")
            return False

    #reset method resets the instance variables to their initial values
    def resetBalance(self):
        self.currentBalance = self.startBalance
        print("current balance reset to: £" + str(self.currentBalance))
        self.portfolioValue = 0.0
        self.totalInvestedBalance = 0.0
        self.portfolioPerformance = 0.0

    def set_balance_from_sim(self, simulation_id: str, Stocks) -> None:
        """Set the balance instance variables based on the first and last date in the simulation data."""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        cursor.execute(f"""
                SELECT current_balance
                FROM {simulation_id}
                WHERE entry_number = (SELECT MIN(entry_number) FROM {simulation_id})
            """)
        result = cursor.fetchone()
        if result is None:
            raise ValueError(f"No starting balance found for simulation {simulation_id}")
        self.startBalance = result[0]

        cursor.execute(f"""
                SELECT current_balance, total_invested_balance
                FROM {simulation_id}
                WHERE entry_number = (SELECT MAX(entry_number) FROM {simulation_id})
            """)
        result = cursor.fetchone()
        conn.close()

        if result is None:
            raise ValueError(f"No ending balance found for simulation {simulation_id}")
        
        self.currentBalance, self.totalInvestedBalance = result
        self.daily_balance_update(simulation_id, Stocks)

    def daily_balance_update(self, simulation_id: str, list_of_stocks):
        """update instance variables which change daily based on stock performance"""
        self.update_portfolio_value(simulation_id, list_of_stocks)
        self.update_portfolio_performance()

    def update_portfolio_value(self, simulation_id, list_of_stocks):
        """calculate portfolio value by combining all stock investment value 
        on the last date in the simulation"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        portfolio_value = 0.0
        for stock in list_of_stocks:
            ticker = stock.get_ticker()
            cursor.execute(f"""
                SELECT investment_value
                FROM {simulation_id}
                WHERE ticker = ?
                ORDER BY entry_number DESC
                LIMIT 1
            """, (ticker,))
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"No investment value found for stock {stock.get_name()}")
            investment_value = result[0]
            portfolio_value += investment_value

        self.portfolioValue = portfolio_value  

    def update_portfolio_performance(self):
        """calculate how much profit has been generated by invested balance"""
        profit = self.portfolioValue - self.totalInvestedBalance
        if self.totalInvestedBalance == 0.0:
            self.portfolioPerformance = 0.0
            return
        
        performance = (profit/self.totalInvestedBalance)*100
        self.portfolioPerformance = performance
        
    def update_total_cash_profit(self, simulation_id: str, Stock):
        """calculate total cash profit by combining all cash profits from each 
        stock on the last date in the simulation"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        ticker = Stock.get_ticker()
        cursor.execute(f"""
            SELECT cash_profit
            FROM {simulation_id}
            WHERE ticker = ?
            ORDER BY entry_number DESC
            LIMIT 1
        """, (ticker,))
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"No cash profit found for stock: {Stock.get_name()}")
        cash_profit = result[0]

        self.total_cash_profit += cash_profit