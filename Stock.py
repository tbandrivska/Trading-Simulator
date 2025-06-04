class Stock:
    def __init__(self, name: str, opening_value: float, opening_performance: float = 0.0):
        self.__name = name        
        self.__invested_balance = 0.0
        self.__opening_value = opening_value
        self.__current_value = opening_value  # Starts at the same value as an opening one
        self.__opening_performance = opening_performance
        self.__current_performance = opening_performance
        self.__number_stocks = 0

    # Getters
    def get_name(self):
        return self.__name

    def get_invested_balance(self):
        return self.__invested_balance

    def get_opening_value(self):
        return self.__opening_value

    def get_current_value(self):                         
        return self.__current_value
    
    def get_opening_performance(self):        
        return self.__opening_performance
    
    def get_current_performance(self):
        return self.__current_performance  
    
    def get_number_stocks(self):
        return self.__number_stocks

    # I have added setters with input valisation for it to make sense
    def set_invested_balance(self, value: float):
        if value >= 0:
            self.__invested_balance = value
        else:
            raise ValueError("Invested balance cannot be negative.")

    def set_current_value(self, value: float):
        if value >= 0:
            self.__current_value = value
            self.__update_performance()  # Recalculate performance when value changes
        else:
            raise ValueError("Stock value cannot be negative.")

    def set_number_stocks(self, quantity: int):
        if quantity >= 0:
            self.__number_stocks = quantity
        else:
            raise ValueError("Number of stocks cannot be negative.")

    # Methods
    def __update_performance(self):
        """Recalculate performance based on current vs. opening value."""
        if self.__opening_value == 0:
            self.__current_performance = 0.0
        else:
            self.__current_performance = (
                (self.__current_value - self.__opening_value) / self.__opening_value
            ) * 100.0

    def buy_stocks(self, quantity: int, price: float):
        """Buy more of this stock."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if price <= 0:
            raise ValueError("Price must be positive.")
        
        self.__number_stocks += quantity
        self.__invested_balance += quantity * price

    def sell_stocks(self, quantity: int, price: float):
        """Sell this stock."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if price <= 0:
            raise ValueError("Price must be positive.")
        if quantity > self.__number_stocks:
            raise ValueError("Cannot sell more stocks than owned.")
        
        self.__number_stocks -= quantity
        self.__invested_balance -= quantity * price

    def reset(self):
        """Reset"""
        self.__invested_balance = 0.0
        self.__current_value = self.__opening_value
        self.__number_stocks = 0
        self.__current_performance = self.__opening_performance

    def __str__(self):
        return (
            f"Stock(name={self.__name}, "
            f"shares={self.__number_stocks}, "
            f"invested={self.__invested_balance:.2f}, "
            f"current_value={self.__current_value:.2f}, "
            f"performance={self.__current_performance:.2f}%)"
        )