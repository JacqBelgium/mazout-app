import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime

def fetch_and_update():
    print(f"[{datetime.now()}] Starten van de uurlijkse marktdata update...")
    
    try:
        heating_oil = yf.Ticker("HO=F")
        eurusd = yf.Ticker("EURUSD=X")
        
        df_oil = heating_oil.history(period='5d', timeout=10)
        df_eurusd = eurusd.history(period='5d', timeout=10)
        
        if df_oil.empty or df_eurusd.empty:
            print("Geen data ontvangen van Yahoo Finance. Update geannuleerd.")
            return

        latest_oil = df_oil['Close'].iloc[-1]
        latest_eurusd = df_eurusd['Close'].iloc[-1]
        
        # Omrekening USD/gal -> EUR/liter -> EUR/ton
        eur_gal = latest_oil / latest_eurusd
        eur_liter = eur_gal / 3.78541
        eur_ton = eur_liter * 1190
        
        conn = sqlite3.connect('mazout_data.db')
        cursor = conn.cursor()
        
        # Tabel initialiseren indien nodig
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
        
        # Haal de meest recente officiële FOD prijs op uit de DB
        official_price = 0.8245
        cursor.execute("SELECT official_belgian_price_liter FROM daily_predictions WHERE official_belgian_price_liter IS NOT NULL ORDER BY date DESC LIMIT 1")
        res = cursor.fetchone()
        if res and res[0]:
            official_price = res[0]
            
        # Drempel- en prognoseberekening
        delta = eur_liter - (official_price * 0.5)
        predicted_official = official_price + (delta * 0.3)
        delta_per_liter = predicted_official - official_price
        impact_2000l = delta_per_liter * 2000
        
        if delta_per_liter < -0.003:
            advice = "WACHTEN / HOLD"
            status = f"Prijsdaling verwacht van ca. € {abs(delta_per_liter):.4f}/L over 1-3 dagen. Wacht nog even met bestellen! Je bespaart ca. € {abs(impact_2000l):.2f} op 2.000 liter."
        elif delta_per_liter > 0.003:
            advice = "NU KOPEN / BUY NOW"
            status = f"Prijsstijging verwacht van ca. € {delta_per_liter:.4f}/L. Bestel vandaag of morgen om ca. € {impact_2000l:.2f} te besparen op 2.000 liter."
        else:
            advice = "NEUTRAAL"
            status = "Stabiele markt. Geen significante prijsaanpassing verwacht de komende 48 uur (verandering valt binnen de wettelijke FOD-drempelwaarde)."
            
        today_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        cursor.execute("""
            INSERT OR REPLACE INTO daily_predictions 
            (date, oil_eur_ton, official_belgian_price_liter, predicted_official_liter, advice, status, impact_2000l)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (today_str, round(eur_ton, 2), official_price, round(predicted_official, 4), advice, status, round(impact_2000l, 2)))
        
        conn.commit()
        conn.close()
        print(f"[{datetime.now()}] Update succesvol afgerond! Niveaus opgeslagen.")

    except Exception as e:
        print(f"Fout tijdens data-update: {e}")

if __name__ == '__main__':
    fetch_and_update()
