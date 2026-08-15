import sqlite3
from datetime import datetime, timedelta
import random

conn = sqlite3.connect("mazout_data.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS daily_predictions;")
cursor.execute('''
    CREATE TABLE daily_predictions (
        date TEXT PRIMARY KEY,
        oil_eur_ton REAL,
        eurusd REAL,
        official_belgian_price_liter REAL,
        advice TEXT,
        trend TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

base_price = 1.2250
start_date = datetime.now() - timedelta(days=60)

for i in range(60):
    current_date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
    base_price = round(base_price + random.uniform(-0.008, 0.008), 4)
    base_price = max(1.1500, min(1.3500, base_price))
    
    oil = round(640.0 + random.uniform(-20, 20), 2)
    eurusd = round(1.0850 + random.uniform(-0.01, 0.01), 4)
    advice = "AFWACHTEN" if base_price > 1.2300 else "KOPEN"
    trend = "BEARISH (DOWNWARD)" if i % 2 == 0 else "BULLISH (UPWARD)"

    cursor.execute('''
        INSERT INTO daily_predictions (date, oil_eur_ton, eurusd, official_belgian_price_liter, advice, trend)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_date, oil, eurusd, base_price, advice, trend))

conn.commit()
conn.close()
print("60 dagen mooie historie opgebouwd in mazout_data.db!")
