class Stock :
    def __init__(self, name: str, InvestedBalance: float, OpeningValue: float, 
                 CurrentValue: float, OpeningPerfomance: float, 
                 CurrentPerfomance: float, NumberStocks: int ):
        self.__name = name        
        self.__InvestedBalance = 0
        self.__OpeningValue = OpeningValue
        self.__CurrentValue = CurrentValue
        self.__OpeningPerfomance = OpeningPerfomance
        self.__CurrentPerfomance = CurrentPerfomance
        self.__NumberStocks = 0
    # Optional: Getter methods to access private variables
    def get_name(self):
        return self.__name

    def get_InvestedBalance(self):
        return self.__InvestedBalance
    def set_InvestedBalance(self, InvestedBalance: float):
        self.__InvestedBalance = InvestedBalance


    def get_OpeningValue(self):
        return self.__OpeningValue
    def set_OpeningValue(self, OpeningValue: float):
        self.__OpeningValue = OpeningValue

    def get_CurrentValue(self):                         
        return self.__CurrentValue
    def set_CurrentValue(self, CurrentValue: float):
        self.__CurrentValue = CurrentValue
    
    def get_OpeningPerfomance(self):        
        return self.__OpeningPerfomance
    def set_OpeningPerfomance(self, OpeningPerfomance: float):  
        self.__OpeningPerfomance = OpeningPerfomance
    
    def get_CurrentPerfomance(self):
        return self.__CurrentPerfomance  
    def set_CurrentPerfomance(self, CurrentPerfomance: float):
        self.__CurrentPerfomance = CurrentPerfomance    
    
    def get_NumberStocks(self):
        return self.__NumberStocks
    def set_NumberStocks(self, NumberStocks: int):  
        self.__NumberStocks = NumberStocks
    