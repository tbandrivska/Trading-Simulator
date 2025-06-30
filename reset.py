import sqlite3
from Database import Database  # Your existing database class

def reset_database():
    # 1. Connect to existing database
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    
    # 2. List all simulation tables to delete
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'sim_%'")
    sim_tables = cursor.fetchall()
    
    # 3. Delete all simulation data
    for table in sim_tables:
        cursor.execute(f"DROP TABLE {table[0]}")
    
    # 4. Clear historical data while keeping structure
    cursor.execute("DELETE FROM historicalData")
    
    # 5. Reinitialize with fresh data
    db = Database()
    db.initialiseDatabase()  # Your existing initialization
    
    conn.commit()
    conn.close()
    print("Database reset complete! Only schema and stock data remain.")

if __name__ == "__main__":
    reset_database()
