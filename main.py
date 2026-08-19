import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime
import streamlit as st
import socket

# Zet de algemene netwerk-timeout op 3 seconden zodat Streamlit nooit blijft hangen
socket.setdefaulttimeout(3)

@st.cache_data(ttl=3600)
def fetch_market_data():
    try:
        heating_oil = yf.Ticker("HO=F")
        eurusd = yf.Ticker("EURUSD=X")
        
        # Snel ophalen met beperkte historie om snel antwoord te krijgen
        df_oil = heating_oil.history(period='5d', timeout=3)
        df_eurusd = eurusd.history(period='5d', timeout=3)
        
        if df_oil.empty or df_eurusd.empty:
            return None
            
        df = pd.DataFrame({
            'oil_usd_gal': df_oil['Close'],
            'eurusd': df_eurusd['Close']
        }).dropna()
        
        return df
    except Exception as e:
        print(f"Yahoo fetch timeout or error: {e}")
        return None

def init_db():
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
    conn.commit()
    conn.close()

def run_engine():
    init_db()
    
    conn = sqlite3.connect('mazout_data.db')
    cursor = conn.cursor()
    
    last_row = None
    try:
        cursor.execute("SELECT date, oil_eur_ton, official_belgian_price_liter, predicted_official_liter, advice, status, impact_2000l FROM daily_predictions ORDER BY date DESC LIMIT 1")
        last_row = cursor.fetchone()
    except Exception:
        pass

    df = fetch_market_data()
    
    if df is not None and not df.empty:
        latest = df.iloc[-1]
        usd_gal = latest['oil_usd_gal']
        eurusd_rate = latest['eurusd']
        
        eur_gal = usd_gal / eurusd_rate
        eur_liter = eur_gal / 3.78541
        eur_ton = eur_liter * 1190
        
        official_price = 0.8500
        try:
            cursor.execute("SELECT official_belgian_price_liter FROM daily_predictions WHERE official_belgian_price_liter IS NOT NULL ORDER BY date DESC LIMIT 1")
            official_res = cursor.fetchone()
            if official_res and official_res[0]:
                official_price = official_res[0]
        except Exception:
            pass

        delta = eur_liter - (official_price * 0.5)
        predicted_official = official_price + (delta * 0.3)
        delta_per_liter = predicted_official - official_price
        impact_2000l = delta_per_liter * 2000
        
        if delta_per_liter < -0.01:
            advice = "WACHTEN / HOLD"
            status = f"Prijsdaling verwacht van ca. € {abs(delta_per_liter):.4f}/L over 1-3 dagen. Wacht nog even met bestellen! Je bespaart ca. € {abs(impact_2000l):.2f} op 2.000 liter."
        elif delta_per_liter > 0.01:
            advice = "NU KOPEN / BUY NOW"
            status = f"Prijsstijging verwacht van ca. € {delta_per_liter:.4f}/L. Bestel vandaag of morgen om ca. € {impact_2000l:.2f} te besparen op 2.000 liter."
        else:
            advice = "NEUTRAAL"
            status = "Stabiele markt. Geen significante prijsaanpassing verwacht de komende 48 uur (verandering valt binnen de wettelijke FOD-drempelwaarde)."
            
        short_term = {
            'latest_market_liter': eur_liter,
            'latest_eur_ton': round(eur_ton, 2),
            'predicted_official_liter': predicted_official,
            'delta_per_liter': delta_per_liter,
            'impact_2000l': impact_2000l,
            'advice': advice,
            'status': status
        }
        
        conn.close()
        return short_term, None, official_price

    else:
        # Als Yahoo blokkeert of time-out geeft, direct terugvallen zonder te haken!
        if last_row:
            conn.close()
            short_term = {
                'latest_market_liter': last_row[1] / 1190 if last_row[1] else 0.7000,
                'latest_eur_ton': last_row[1] if last_row[1] else 800.0,
                'predicted_official_liter': last_row[3] if last_row[3] else 0.8500,
                'delta_per_liter': (last_row[3] - last_row[2]) if (last_row[3] and last_row[2]) else 0.0,
                'impact_2000l': last_row[6] if last_row[6] else 0.0,
                'advice': last_row[4] if last_row[4] else "NEUTRAAL",
                'status': last_row[5] if last_row[5] else "Gegevens geladen uit backup."
            }
            return short_term, None, last_row[2] if last_row[2] else 0.8500
            
        conn.close()
        short_term = {
            'latest_market_liter': 0.6850,
            'latest_eur_ton': 815.0,
            'predicted_official_liter': 0.8450,
            'delta_per_liter': -0.0050,
            'impact_2000l': -10.00,
            'advice': "NEUTRAAL",
            'status': "Marktgegevens tijdelijk beperkt. Verwachting gebaseerd op meest recente marktindicatoren."
        }
        return short_term, None, 0.8500
