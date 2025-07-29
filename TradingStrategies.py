
from Stock import Stock
from Balance import Balance

class TradingStrategies:
    """
    A dedicated class for all trading strategies to keep the main simulation clean.
    Usage:
    1. Initialize with strategies dictionary
    2. Call apply() during simulation
    """
    def __init__(self, balance: Balance):
        self.balance = balance
        self.stock_strategies = {}  # {ticker: {strategy_name: config_dict}}

    def set_stock_strategies(self, ticker: str, strategies: dict):
        """Set strategies for a specific stock."""
        self.stock_strategies[ticker] = strategies

    def activate(self, ticker: str, strategy_name: str, **params):
        """Activate a strategy for a specific stock."""
        if ticker not in self.stock_strategies:
            self.stock_strategies[ticker] = {}
        if strategy_name not in self.stock_strategies[ticker]:
            # default config for new strategy
            self.stock_strategies[ticker][strategy_name] = {'active': False}
        self.stock_strategies[ticker][strategy_name]['active'] = True
        for param, value in params.items():
            self.stock_strategies[ticker][strategy_name][param] = value

    def deactivate(self, ticker: str, strategy_name: str):
        if ticker in self.stock_strategies and strategy_name in self.stock_strategies[ticker]:
            self.stock_strategies[ticker][strategy_name]['active'] = False

    def apply(self, stock: Stock, day_index: int = None):
        ticker = stock.get_ticker()
        strategies = self.stock_strategies.get(ticker, {})
        # example for three strategies:
        if strategies.get('take_profit', {}).get('active', False):
            self._take_profit(stock, strategies['take_profit'])
        if strategies.get('stop_loss', {}).get('active', False):
            self._stop_loss(stock, strategies['stop_loss'])
        if strategies.get('dollar_cost_avg', {}).get('active', False):
            self._dollar_cost_avg(stock, strategies['dollar_cost_avg'], day_index)

    # Individual strategies now take config as argument
    def _take_profit(self, stock: Stock, config: dict):
        threshold = config.get('threshold', 0.2)
        if stock.get_number_stocks() > 0 and \
            stock.get_current_stock_value() >= (1 + threshold) * stock.get_opening_stock_value():
            self.balance.sell(stock, stock.get_number_stocks())

    def _stop_loss(self, stock: Stock, config: dict):
        threshold = config.get('threshold', 0.1)
        if stock.get_current_stock_value() <= (1 - threshold) * stock.get_opening_stock_value():
            self.balance.sell(stock, stock.get_number_stocks())

    def _dollar_cost_avg(self, stock: Stock, config: dict, day_index: int):
        shares = config.get('shares', 5)
        interval = config.get('interval', 7)
        if isinstance(day_index, int) and day_index % interval == 0:
            self.balance.purchase(stock, shares)