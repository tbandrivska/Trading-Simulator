class Balance:
    #initialising the instance variables
    def __init__(self, startBalance:float):
        self.startBalance = startBalance
        self.currentBalance = startBalance
        self.totalInvestedBalance = 0

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


    #purchase method buys stocks and removes the amount from the balance
    def purchase(self, Stock, amount:int):
        price = Stock.get_current_value() * amount
        if self.currentBalance >= price:
            self.currentBalance -= price
            self.totalInvestedBalance += price
            Stock.set_number_stocks(Stock.get_number_stocks() + amount)
            return True
        else:
            print("Insufficient balance to purchase stocks.")
            return False
      
    #sell method sells stocks and adds the profit/loss to the balance
    def sell(self, Stock, amount:int):
        if Stock.get_number_stocks() >= amount:
            price = Stock.get_current_value() * amount
            self.currentBalance += price
            self.totalInvestedBalance -= price
            Stock.set_number_stocks(Stock.get_number_stocks() - amount)
            return True
        else:
            print("Insufficient stocks to sell.")
            return False

    #reset method resets the instance variables to their initial values
    def resetBalance(self):
        self.startBalance = 0
        self.currentBalance = 0
        self.totalInvestedBalance = 0
           