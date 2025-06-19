import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from core.TradingSimulator import TradingSimulation

class TradingSimulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Stock Trading Simulator")
        self.simulator = TradingSimulation(start_balance=10000)
        
        # Configure main window
        self.root.geometry("1000x700")
        self._setup_styles()
        self._create_widgets()

    def _setup_styles(self):
        style = ttk.Style()
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TButton', font=('Helvetica', 10), padding=5)
        style.configure('Header.TLabel', font=('Helvetica', 14, 'bold'))

    def _create_widgets(self):
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header
        ttk.Label(
            self.main_frame, 
            text="TRADING SIMULATOR", 
            style='Header.TLabel'
        ).pack(pady=10)

        # Control Panel
        self._build_control_panel()
        
        # Visualization Area
        self._build_visualization_frame()

    def _build_control_panel(self):
        control_frame = ttk.LabelFrame(self.main_frame, text="Controls")
        control_frame.pack(fill=tk.X, pady=5)

        # Strategy Configuration
        ttk.Button(
            control_frame, 
            text="Configure Strategies", 
            command=self._open_strategy_config
        ).pack(side=tk.LEFT, padx=5)

        # Simulation Controls
        ttk.Button(
            control_frame, 
            text="Run Simulation", 
            command=self._run_simulation
        ).pack(side=tk.LEFT, padx=5)

    def _build_visualization_frame(self):
        viz_frame = ttk.Frame(self.main_frame)
        viz_frame.pack(fill=tk.BOTH, expand=True)

        # Portfolio Summary
        summary_frame = ttk.LabelFrame(viz_frame, text="Portfolio Summary")
        summary_frame.pack(fill=tk.X, pady=5)
        
        self.summary_text = tk.Text(summary_frame, height=10)
        self.summary_text.pack(fill=tk.X)

        # Graph Display
        graph_frame = ttk.LabelFrame(viz_frame, text="Performance")
        graph_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for matplotlib graph
        self.graph_canvas = None  # Will be set when plotting
        # Stock selection listbox
        self.stock_list = ttk.Treeview(
        columns=('Shares', 'Value'), 
        show='headings'
        )
        self.stock_list.heading('#0', text='Stock')
        self.stock_list.pack(fill=tk.BOTH, expand=True)

    def _open_strategy_config(self):
        """Open strategy configuration window"""
        config_win = tk.Toplevel(self.root)
        StrategyConfigWindow(config_win, self.simulator)

    def _run_simulation(self):
        """Execute simulation and update GUI"""
        try:
            self.simulator.run_simulation()
            self._update_summary()
            self._plot_performance()
        except Exception as e:
            self._show_error(f"Simulation failed: {str(e)}")

    def _update_summary(self):
        """Update portfolio summary text"""
        self.summary_text.delete(1.0, tk.END)
        balance = self.simulator.balance.getCurrentBalance()
        invested = sum(
            s.get_current_value() * s.get_number_stocks() 
            for s in self.simulator.stocks.values()
        )
        self.summary_text.insert(tk.END, 
            f"Cash Balance: ${balance:,.2f}\n"
            f"Invested Value: ${invested:,.2f}\n"
            f"Total Portfolio: ${balance + invested:,.2f}"
        )

    def _plot_performance(self):
        """Display performance graph using matplotlib"""
        if self.graph_canvas:
            self.graph_canvas.get_tk_widget().destroy()

        fig = self.simulator.plot_performance(show=False)
        
        self.graph_canvas = FigureCanvasTkAgg(fig, master=self.root)
        self.graph_canvas.draw()
        self.graph_canvas.get_tk_widget().pack(
            fill=tk.BOTH, expand=True
        )

    def _show_error(self, message):
        """Show error message popup"""
        tk.messagebox.showerror("Error", message)

class StrategyConfigWindow:
    def __init__(self, parent, simulator):
        self.parent = parent
        self.simulator = simulator
        self._setup_window()
        self._create_widgets()

    def _setup_window(self):
        self.parent.title("Strategy Configuration")
        self.parent.geometry("500x400")

    def _create_widgets(self):
        # Strategy selection
        ttk.Label(self.parent, text="Select Strategies:").pack(pady=5)
        
        self.strategy_vars = {}
        for name, config in self.simulator.strategies.strategies.items():
            var = tk.BooleanVar(value=config['active'])
            cb = ttk.Checkbutton(
                self.parent, 
                text=f"{name}: {config['description']}", 
                variable=var
            )
            cb.pack(anchor=tk.W, padx=10)
            self.strategy_vars[name] = var

        # Parameter controls would go here...

        # Save button
        ttk.Button(
            self.parent, 
            text="Apply Strategies", 
            command=self._save_strategies
        ).pack(pady=10)

    def _save_strategies(self):
        """Activate/deactivate strategies based on selections"""
        for name, var in self.strategy_vars.items():
            if var.get():
                self.simulator.strategies.activate(name)
            else:
                self.simulator.strategies.strategies[name]['active'] = False
        self.parent.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingSimulatorGUI(root)
    root.mainloop()