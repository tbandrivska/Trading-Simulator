from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

class PerformanceChart(QWidget):
    def __init__(self):
        super().__init__()
        self.figure = Figure(figsize=(10, 4))
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

    def plot_performance(self, simulator):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Get data from simulator
        dates = []
        values = []
        # ... (implement data fetching)
        
        ax.plot(dates, values, 'b-')
        ax.set_title("Portfolio Performance")
        self.canvas.draw()