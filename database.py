import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "mazout_data.db"

def init_db():
    """Initialiseert de SQLite database en maakt de tabel aan als deze nog niet bestaat."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_predictions (
            date TEXT PRIMARY KEY,
            oil_eur_ton REAL,
            eurusd REAL,
            official_belgian_price_liter REAL,
            advice TEXT,
            trend TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_daily_record(date_str, oil_eur_ton, eurusd, official_price, advice, trend):
    """Slaat een dagelijkse meting op of werkt deze bij als de datum al bestaat."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO daily_predictions 
        (date, oil_eur_ton, eurusd, official_belgian_price_liter, advice, trend)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            oil_eur_ton=excluded.oil_eur_ton,
            eurusd=excluded.eurusd,
            official_belgian_price_liter=excluded.official_belgian_price_liter,
            advice=excluded.advice,
            trend=excluded.trend
    ''', (date_str, oil_eur_ton, eurusd, official_price, advice, trend))
    
    conn.commit()
    conn.close()

def get_historical_data(limit=30):
    """Haalt de meest recente opgeslagen data op voor weergave in de grafieken."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(
        f"SELECT * FROM daily_predictions ORDER BY date DESC LIMIT {limit}", 
        conn
    )
    conn.close()
    return df.sort_values(by="date")

if __name__ == "__main__":
    init_db()
    print("Database succesvol geïnitialiseerd!")