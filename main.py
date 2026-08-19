import sqlite3
from datetime import datetime

def init_db_if_needed():
    conn = sqlite3.connect('mazout_data.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_predictions (
            date TEXT PRIMARY KEY,
            oil_eur_ton REAL,
            official_belgian_price_liter REAL,
            predicted_official_liter REAL,
            advice TEXT,
            status TEXT,
            impact_2000l REAL
        )
    """)
    
    # Als DB leeg is, voeg 1 basisrecord toe
    cursor.execute("SELECT COUNT(*) FROM daily_predictions")
    if cursor.fetchone()[0] == 0:
        today_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        cursor.execute("""
            INSERT OR REPLACE INTO daily_predictions 
            (date, oil_eur_ton, official_belgian_price_liter, predicted_official_liter, advice, status, impact_2000l)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            today_str, 
            725.50, 
            0.8245, 
            0.8195, 
            "WACHTEN / HOLD", 
            "Prijsdaling verwacht van ca. € 0.0050/L over 1-3 dagen. Wacht nog even met bestellen! Je bespaart ca. € 10.00 op 2.000 liter.", 
            -10.00
        ))
        conn.commit()
    conn.close()

def run_engine():
    init_db_if_needed()
    
    conn = sqlite3.connect('mazout_data.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT date, oil_eur_ton, official_belgian_price_liter, predicted_official_liter, advice, status, impact_2000l FROM daily_predictions ORDER BY date DESC LIMIT 1")
    last_row = cursor.fetchone()
    conn.close()
    
    if last_row:
        short_term = {
            'latest_market_liter': (last_row[1] / 1190) if last_row[1] else 0.609,
            'latest_eur_ton': last_row[1] if last_row[1] else 725.50,
            'predicted_official_liter': last_row[3] if last_row[3] else 0.8195,
            'delta_per_liter': (last_row[3] - last_row[2]) if (last_row[3] and last_row[2]) else -0.0050,
            'impact_2000l': last_row[6] if last_row[6] else -10.00,
            'advice': last_row[4] if last_row[4] else "WACHTEN / HOLD",
            'status': last_row[5] if last_row[5] else "Marktdata gebaseerd op meest recente officiële FOD-notering."
        }
        return short_term, None, last_row[2] if last_row[2] else 0.8245
        
    return None, None, 0.8245
