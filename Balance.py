class Balance:
    #initialising the instance variables
    def __init__(self, startBalance=0, currentBalance=0, totalInvestedBalance=0, startDate=None, endDate=None):
        self.balance = balance
        self.currentBalance = currentBalance
        self.totalInvestedBalance = totalInvestedBalance
        self.startDate = startDate
        self.endDate = endDate

    #getter and setter methods for the instance variables
    def setStartBalance(self, startBalance):
        self.startBalance = startBalance
    def getStartBalance(self):
        return self.startBalance

    def setCurrentBalance(self, currentBalance):
        self.currentBalance = currentBalance
    def getCurrentBalance(self):
        return self.currentBalance

    def setTotalInvestedBalance(self, totalInvestedBalance):
        self.totalInvestedBalance = totalInvestedBalance
    def getTotalInvestedBalance(self):
        return self.totalInvestedBalance    

    def setStartDate(self, startDate):
        self.startDate = startDate
    def getStartDate(self):
        return self.startDate   

    def setEndDate(self, endDate):
        self.endDate = endDate
    def getEndDate(self):
        return self.endDate 

    #purchase method buys stocks and removes the amount from the balance
    def purchase(Stock, currentBalance, amount):
        price = Stock.get_CurrentValue()*amount
        if currentBalance >= price:
            currentBalance -= price
            Stock.set_InvestedBalance(Stock.get_InvestedBalance() + price)
            Stock.set_NumberStocks(Stock.get_NumberStocks() + amount)
            return True
        else:
            print("Insufficient balance to purchase stocks.")
            return False
      
    #sell method sells stocks and adds the profit/loss to the balance
    def sell(Stock, currentBalance, amount):
        if Stock.get_NumberStocks() >= amount:
            price = Stock.get_CurrentValue() * amount
            currentBalance += price
            Stock.set_InvestedBalance(Stock.get_InvestedBalance() - price)
            Stock.set_NumberStocks(Stock.get_NumberStocks() - amount)
            return True
        else:
            print("Insufficient stocks to sell.")
            return False

    #reset method resets the instance variables to their initial values
    def resetBalance(self):
        self.startBalance = 0
        self.currentBalance = 0
        self.totalInvestedBalance = 0
        self.startDate = None
        self.endDate = None
           