from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
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

        # Example: Suppose simulator has a list of (date, value) tuples
        history = getattr(simulator, "performance_history", [])
        if history:
            dates, values = zip(*history)
            ax.plot(dates, values, 'b-')
        else:
            ax.plot([], [], 'b-')

        ax.set_title("Portfolio Performance")
        ax.set_xlabel("Date")
        ax.set_ylabel("Portfolio Value")
        self.canvas.draw()