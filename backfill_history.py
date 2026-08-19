import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

def backfill_history():
    print("Starten met het ophalen van de afgelopen 90 dagen aan historische data...")
    
    try:
        # Haal historie op voor ruwe olie/gasolie en wisselkoers
        heating_oil = yf.Ticker("HO=F")
        eurusd = yf.Ticker("EURUSD=X")
        
        df_oil = heating_oil.history(period='3m')
        df_eurusd = eurusd.history(period='3m')
        
        if df_oil.empty or df_eurusd.empty:
            print("Geen historische data ontvangen van Yahoo Finance.")
            return

        # Samenvoegen op datum
        df = pd.DataFrame()
        df['oil_close'] = df_oil['Close']
        df['eurusd_close'] = df_eurusd['Close']
        df = df.dropna()

        conn = sqlite3.connect('mazout_data.db')
        cursor = conn.cursor()
        
        # Tabel aanmaken als deze nog niet bestaat
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

        # Basisreferentie voor de officiële FOD-prijs
        base_official = 0.8245
        records_added = 0

        for index, row in df.iterrows():
            date_str = index.strftime('%Y-%m-%d 12:00')
            oil_val = row['oil_close']
            eurusd_val = row['eurusd_close']
            
            # Omrekening USD/gal -> EUR/liter -> EUR/ton
            eur_gal = oil_val / eurusd_val
            eur_liter = eur_gal / 3.78541
            eur_ton = eur_liter * 1190
            
            # Indicatieve berekening voor historische datapunten
            delta = eur_liter - (base_official * 0.5)
            predicted_official = base_official + (delta * 0.3)
            delta_per_liter = predicted_official - base_official
            impact_2000l = delta_per_liter * 2000
            
            if delta_per_liter < -0.003:
                advice = "WACHTEN / HOLD"
                status = f"Prijsdaling verwacht van ca. € {abs(delta_per_liter):.4f}/L."
            elif delta_per_liter > 0.003:
                advice = "NU KOPEN / BUY NOW"
                status = f"Prijsstijging verwacht van ca. € {delta_per_liter:.4f}/L."
            else:
                advice = "NEUTRAAL"
                status = "Stabiele markt."

            # Voeg toe indien het datumrecord nog niet bestaat
            cursor.execute("""
                INSERT OR IGNORE INTO daily_predictions 
                (date, oil_eur_ton, official_belgian_price_liter, predicted_official_liter, advice, status, impact_2000l)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (date_str, round(eur_ton, 2), base_official, round(predicted_official, 4), advice, status, round(impact_2000l, 2)))
            
            if cursor.rowcount > 0:
                records_added += 1

        conn.commit()
        conn.close()
        print(f"Historie succesvol geladen! {records_added} nieuwe datums toegevoegd aan de database.")

    except Exception as e:
        print(f"Fout bij ophalen historie: {e}")

if __name__ == '__main__':
    backfill_history()
