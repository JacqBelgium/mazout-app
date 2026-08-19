import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import streamlit as st

# Streamlit Caching: bewaar data voor 3600 seconden (1 uur) om Yahoo Rate Limits te voorkomen
@st.cache_data(ttl=3600)
def fetch_market_data():
    try:
        # Tickers
        heating_oil = yf.Ticker("HO=F")  # NY Harbor ULSD Futures
        eurusd = yf.Ticker("EURUSD=X")   # EUR/USD Exchange Rate
        
        # Ophalen van data
        df_oil = heating_oil.history(period='3mo')
        df_eurusd = eurusd_ticker.history(period='3mo') if 'eurusd_ticker' in locals() else eurusd.history(period='3mo')
        
        if df_oil.empty or df_eurusd.empty:
            return None
            
        df = pd.DataFrame({
            'oil_usd_gal': df_oil['Close'],
            'eurusd': df_eurusd['Close']
        }).dropna()
        
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def run_engine():
    # Gebruik de SQLite database als terugvaloptie (fallback) als Yahoo tijdelijk blockt
    conn = sqlite3.connect('mazout_data.db')
    cursor = conn.cursor()
    
    # Haal de meest recente rij op uit onze lokale DB
    cursor.execute("SELECT date, oil_eur_ton, official_belgian_price_liter, predicted_official_liter, advice, status, impact_2000l FROM daily_predictions ORDER BY date DESC LIMIT 1")
    last_row = cursor.fetchone()
    
    df = fetch_market_data()
    
    if df is not None and not df.empty:
        # Laatste beursdata verwerken
        latest = df.iloc[-1]
        usd_gal = latest['oil_usd_gal']
        eurusd_rate = latest['eurusd']
        
        # Berekening per liter / ton
        eur_gal = usd_gal / eurusd_rate
        eur_liter = eur_gal / 3.78541
        eur_ton = eur_liter * 1190  # Indicatieve omrekening
        
        # Haal laatste officiële FOD prijs op uit DB
        cursor.execute("SELECT official_belgian_price_liter FROM daily_predictions WHERE official_belgian_price_liter IS NOT NULL ORDER BY date DESC LIMIT 1")
        official_res = cursor.fetchone()
        official_price = official_res[0] if official_res else 0.8500
        
        # Verschil / Drempelberekening
        delta = eur_liter - (official_price * 0.5) # Indicatieve drempel-indicator
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
        # FALLBACK: Als Yahoo blokkeert, toon de laatst opgeslagen DB-data i.p.v. een crash!
        if last_row:
            conn.close()
            short_term = {
                'latest_market_liter': last_row[1] / 1190,
                'latest_eur_ton': last_row[1],
                'predicted_official_liter': last_row[3],
                'delta_per_liter': last_row[3] - last_row[2],
                'impact_2000l': last_row[6],
                'advice': last_row[4],
                'status': last_row[5]
            }
            return short_term, None, last_row[2]
            
        conn.close()
        return None, None, 0.8500
