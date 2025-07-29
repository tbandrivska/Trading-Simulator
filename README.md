# Trading Simulator

A desktop application for simulating stock trading, portfolio management, and testing trading strategies. Built with Python, PySide6 for the GUI, and SQLite for persistent storage.

---

## Features

- **Simulate Stock Trading:** Buy and sell stocks using historical data.
- **Portfolio Management:** Track cash, investments, and performance over time.
- **Custom Trading Strategies:** Apply and customize strategies (take profit, stop loss, dollar cost averaging) for each stock individually.
- **Graphical Visualization:** View performance graphs for your portfolio and individual stocks.
- **Simulation Management:** Start new simulations, continue previous ones, rename or delete simulations.
- **User-Friendly GUI:** Modern interface with PySide6.

---

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/tbandrivska/Trading-Simulator
    cd Trading-Simulator
    ```

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Typical requirements:*
    - PySide6
    - matplotlib

3. **Prepare the database:**
    - Ensure you have a `data.db` SQLite database with a `historicalData` table containing your stock data.
    - The app will create simulation tables as needed.

---

## Usage

1. **Run the application:**
    ```bash
    python GUI.py
    ```

2. **Main Workflow:**
    - **Start Menu:** Choose to start a new simulation or continue a previous one.
    - **Simulation:** View your portfolio, run simulations for a set number of days, and see performance graphs.
    - **Stock Details:** Click on a stock to view details, trade, or set custom strategies.
    - **Strategies:** Click "IMPLEMENT TRADING STRATEGIES" to customize strategies for each stock.
    - **Simulation Management:** Rename or delete simulations from the "Previous Simulations" menu.

---

## Project Structure

```
Trading-Simulator/
│
├── GUI.py                    # Main GUI application
├── TradingSimulator.py       # Core simulation logic
├── TradingStrategies.py      # Strategy logic (per-stock)
├── TradingStrategiesWidget.py# GUI for strategy customization
├── Stock.py                  # Stock model
├── Balance.py                # Balance and portfolio logic
├── Database.py               # Database helper
├── data.db                   # SQLite database (not included in repo)
├── __pycache__

---
```
## Custom Trading Strategies

- **Take Profit:** Sell when stock price increases by a set threshold.
- **Stop Loss:** Sell when stock price drops by a set threshold.
- **Dollar Cost Averaging:** Buy a set number of shares at regular intervals.

You can activate/deactivate and configure these strategies for each stock individually via the GUI.

---

## Notes

- The application requires a valid `data.db` with historical stock data.
- All simulation data is stored in new tables within the same database.
- The GUI is designed for desktop use and may not be suitable for mobile devices.

---

## Contributing

Pull requests and suggestions are welcome! Please open an issue for major changes.

---

## Acknowledgements

- [PySide6](https://doc.qt.io/qtforpython/)
- [matplotlib](https://matplotlib.org/)
- SQLite

---

*Happy Trading!*