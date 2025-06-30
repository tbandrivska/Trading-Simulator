from typing import Dict
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
        self.strategies = {
            'take_profit': {
                'active': False,
                'threshold': 0.2,  # 20%
                'action': self._take_profit,
                'description': 'Take profit when gain exceeds threshold'
            },
            'stop_loss': {
                'active': False,
                'threshold': 0.1,  # 10%
                'action': self._stop_loss,
                'description': 'Sell if loss exceeds threshold'
            },
            'dollar_cost_avg': {
                'active': False,
                'shares': 5,
                'interval': 7,
                'action': self._dollar_cost_avg,
                'description': 'Invest a fixed amount regularly'
            }
        }

    def activate(self, strategy_name: str, **params) -> None:
        """Activate a strategy with custom parameters"""
        if strategy_name not in self.strategies:
            raise ValueError(f"Invalid strategy. Available: {list(self.strategies.keys())}")
        
        self.strategies[strategy_name]['active'] = True
        for param, value in params.items():
            if param in self.strategies[strategy_name]:
                self.strategies[strategy_name][param] = value

    def apply(self, stock: Stock, day_index: int = None) -> None:
        """Apply all active strategies to a stock"""
        for strategy in self.strategies.values():
            if strategy['active']:
                strategy['action'](stock, day_index)

 
    # Individual Strategies

    def _take_profit(self, stock: Stock, _) -> None:
        """Sell if stock gains threshold%"""
        if stock.get_current_value() >= (1 + self.strategies['take_profit']['threshold']) * stock.get_opening_value():
            self.balance.sell(stock, stock.get_number_stocks())

    def _stop_loss(self, stock: Stock, _) -> None:
        """Sell if stock loses threshold%"""
        if stock.get_current_value() <= (1 - self.strategies['stop_loss']['threshold']) * stock.get_opening_value():
            self.balance.sell(stock, stock.get_number_stocks())

    def _dollar_cost_avg(self, stock: Stock, day_index: int) -> None:
        """Buy fixed shares at regular intervals"""
        if not isinstance(day_index, int):
            return  

        if day_index % self.strategies['dollar_cost_avg']['interval'] == 0:
            self.balance.purchase(stock, self.strategies['dollar_cost_avg']['shares'])
    def activate(self, name: str, **params):
        """Activate a strategy with parameters"""
        if name in self.strategies:
            self.strategies[name]['active'] = True
            for param, value in params.items():
                if param in self.strategies[name]:
                    self.strategies[name][param] = value

    def deactivate(self, name: str):
        """Deactivate a strategy"""
        if name in self.strategies:
            self.strategies[name]['active'] = False