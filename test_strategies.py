from TradingStrategies import TradingStrategies
from Stock import Stock
from Balance import Balance

def main():
    # starting balance
    balance = Balance(10000)

    
    stock = Stock(name="TestStock", ticker="TEST", opening_value=100)
    stock.set_cash_invested(1000)
    stock.set_number_stocks(10)
    stock.set_current_value(120)  # simulate price increase

   
    strategies = TradingStrategies(balance)

    # testing activating take_profit with custom threshold
    strategies.activate('take_profit', threshold=0.1)
    print("Take profit active:", strategies.strategies['take_profit']['active'])
    print("Take profit threshold:", strategies.strategies['take_profit']['threshold'])

    # Testing applying take_profit strategy
    strategies.apply(stock)
    print("Balance after take_profit:", balance.getCurrentBalance())
    print("Stocks owned after take_profit:", stock.get_number_stocks())

    # Testing activating stop_loss with custom threshold
    strategies.activate('stop_loss', threshold=0.5)
    print("Stop loss active:", strategies.strategies['stop_loss']['active'])
    print("Stop loss threshold:", strategies.strategies['stop_loss']['threshold'])

    #lowering stock value to trigger stop_loss
    stock.set_current_value(40)
    stock.set_number_stocks(10)
    stock.set_cash_invested(1000)
    strategies.apply(stock)
    print("Balance after stop_loss:", balance.getCurrentBalance())
    print("Stocks owned after stop_loss:", stock.get_number_stocks())

    # Testing dollar cost averaging
    strategies.activate('dollar_cost_avg', shares=3, interval=2)
    print("Dollar cost avg active:", strategies.strategies['dollar_cost_avg']['active'])
    print("Dollar cost avg shares:", strategies.strategies['dollar_cost_avg']['shares'])
    print("Dollar cost avg interval:", strategies.strategies['dollar_cost_avg']['interval'])

    # Simulating a day where interval matches
    strategies.apply(stock, day_index=4)
    print("Balance after dollar cost avg:", balance.getCurrentBalance())
    print("Stocks owned after dollar cost avg:", stock.get_number_stocks())

    print("All real strategy tests completed!")

if __name__ == "__main__":
    main()