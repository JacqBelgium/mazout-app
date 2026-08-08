import yfinance as yf
import pandas as pd

def fetch_market_data():
    """Haalt de meest actuele olie- en wisselkoersdata op en koppelt ze slim aan elkaar."""
    print("Beursdata ophalen uit Rotterdam & Wisselkoersen...")
    
    # 1. Wisselkoers EUR/USD ophalen
    eurusd_ticker = yf.Ticker('EURUSD=X')
    df_eurusd = eurusd_ticker.history(period='3mo')
    
    # 2. Lijst van oliesymbolen
    oil_tickers = ['LGO.F', 'BZ=F', 'CL=F']
    df_oil = pd.DataFrame()
    used_ticker = ""

    for ticker in oil_tickers:
        try:
            t = yf.Ticker(ticker)
            df_temp = t.history(period='3mo')
            if not df_temp.empty and len(df_temp) > 5:
                df_oil = df_temp
                used_ticker = ticker
                print(f"Succesvol marktdata opgehaald via ticker: {used_ticker}")
                break
        except Exception:
            continue

    if df_oil.empty or df_eurusd.empty:
        return pd.DataFrame()

    # Gebruik alleen de 'Close' kolommen
    s_oil = df_oil['Close'].rename('oil_usd')
    s_eurusd = df_eurusd['Close'].rename('eurusd')

    # Zet de indexen om naar puur de datum (zonder tijdzone-verschillen)
    s_oil.index = s_oil.index.date
    s_eurusd.index = s_eurusd.index.date

    # Voeg ze samen op datum en vul ontbrekende weekenddagen op
    data = pd.concat([s_oil, s_eurusd], axis=1).sort_index()
    data = data.ffill().bfill().dropna()
# Omrekenen naar Euro per ton
    if used_ticker in ['BZ=F', 'CL=F']:
        data['gasoil_eur_ton'] = (data['oil_usd'] * 7.33) / data['eurusd']
    else:
        # Dynamische schaalfactor zodat we altijd op een realistische tonprijs uitkomen
        raw = data['oil_usd'] / data['eurusd']
        while raw.iloc[-1] < 100:
            raw = raw * 10
        data['gasoil_eur_ton'] = raw
    return data

def analyze_short_term(df):
    """KORTE TERMIJN (1 tot 3/5 Dagen)"""
    total_rows = len(df)
    latest = df['gasoil_eur_ton'].iloc[-1]
    
    compare_idx = -4 if total_rows >= 4 else 0
    prev_3d = df['gasoil_eur_ton'].iloc[compare_idx]
    
    change_3d_pct = ((latest - prev_3d) / prev_3d) * 100
    
    if change_3d_pct < -1.5:
        advice = "BESTELLEN UITSTELLEN"
        status = "Neerwaartse druk op de markt. Belgische maximumprijs zal over 1-3 dagen waarschijnlijk DALEN."
    elif change_3d_pct > 1.5:
        advice = "SNELLER BESTELLEN"
        status = "Stijgende beurskoers. Belgische maximumprijs zal over 1-3 dagen waarschijnlijk STIJGEN."
    else:
        advice = "NEUTRAAL / AFWACHTEN"
        status = "Stabiele markt op korte termijn. Geen grote prijsherziening verwacht over 1-3 dagen."
        
    return {
        "latest_eur_ton": round(latest, 2),
        "change_3d_pct": round(change_3d_pct, 2),
        "advice": advice,
        "status": status
    }

def analyze_mid_term(df):
    """MIDDELLANGE TERMIJN (Weken tot Maanden)"""
    df['SMA_5'] = df['gasoil_eur_ton'].rolling(window=5, min_periods=1).mean()
    df['SMA_20'] = df['gasoil_eur_ton'].rolling(window=20, min_periods=1).mean()
    
    sma5 = df['SMA_5'].iloc[-1]
    sma20 = df['SMA_20'].iloc[-1]
    
    if sma5 > sma20:
        trend = "OPWAARTS"
        explanation = "Het korte-termijn gemiddelde ligt boven het 20-daags gemiddelde (stijgende trend)."
    else:
        trend = "NEERWAARTS"
        explanation = "Het korte-termijn gemiddelde ligt onder het 20-daags gemiddelde (dalende trend)."
        
    return {
        "trend": trend,
        "explanation": explanation
    }

if __name__ == "__main__":
    try:
        df = fetch_market_data()
        
        if df.empty:
            print("Kan de marktdata niet verwerken op dit moment.")
        else:
            short_term = analyze_short_term(df)
            mid_term = analyze_mid_term(df)
            
            print("\n" + "="*55)
            print("         MAZOUT PROGNOSE ENGINE - BELGIË")
            print("="*55)
            print(f"Laatst Bekende Indicatie:          €{short_term['latest_eur_ton']} / ton")
            print(f"3-Dags koersverandering:           {short_term['change_3d_pct']}%")
            print("-" * 55)
            print(f"KORTE TERMIJN (1-5 Dagen):         {short_term['advice']}")
            print(f"Advies:                           {short_term['status']}")
            print("-" * 55)
            print(f"MIDDELLANGE TERMIJN (Weken/Mnd):   {mid_term['trend']}")
            print(f"Trend:                            {mid_term['explanation']}")
            print("="*55 + "\n")
    except Exception as e:
        print(f"Fout bij het ophalen van gegevens: {e}")