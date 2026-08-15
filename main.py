import yfinance as yf
import pandas as pd
from datetime import datetime
from fod_data import get_belgian_official_price
from database import init_db, save_daily_record

FIXED_MARGINS_ACCIJNS = 0.615  # Vaste opslag & accijnzen per liter
VAT_RATE = 1.21               # 21% BTW

def fetch_market_data():
    """Fetches Rotterdam market data & exchange rates."""
    print("Fetching Rotterdam market data & exchange rates...")
    
    eurusd_ticker = yf.Ticker('EURUSD=X')
    df_eurusd = eurusd_ticker.history(period='3mo')
    
    oil_tickers = ['BZ=F', 'CL=F']
    df_oil = pd.DataFrame()
    used_ticker = ""

    for ticker in oil_tickers:
        try:
            t = yf.Ticker(ticker)
            df_temp = t.history(period='3mo')
            if not df_temp.empty and len(df_temp) > 5:
                df_oil = df_temp
                used_ticker = ticker
                print(f"Market data successfully fetched via ticker: {used_ticker}")
                break
        except Exception:
            continue

    if df_oil.empty or df_eurusd.empty:
        return pd.DataFrame()

    s_oil = df_oil['Close'].rename('oil_usd')
    s_eurusd = df_eurusd['Close'].rename('eurusd')

    s_oil.index = s_oil.index.date
    s_eurusd.index = s_eurusd.index.date

    data = pd.concat([s_oil, s_eurusd], axis=1).sort_index()
    data = data.ffill().bfill().dropna()
    
    # 1. Omrekening naar EUR / ton
    data['gasoil_eur_ton'] = (data['oil_usd'] * 7.33) / data['eurusd']
    
    # 2. Omrekening naar Markt-literprijs excl. taksen (1 ton gasolie ≈ 1190 liter)
    data['market_eur_liter_excl'] = data['gasoil_eur_ton'] / 1190.0
    
    # 3. Geschatte consumentenprijs incl. accijnzen & 21% BTW
    data['estimated_official_liter'] = (data['market_eur_liter_excl'] + FIXED_MARGINS_ACCIJNS) * VAT_RATE
    
    return data

def analyze_short_term(df, official_price):
    """SHORT-TERM PROGNOSTICS (1-5 Days) with 2000L Impact Calculation."""
    latest_ton = df['gasoil_eur_ton'].iloc[-1]
    latest_market_liter = df['market_eur_liter_excl'].iloc[-1]
    
    df['SMA_7_official'] = df['estimated_official_liter'].rolling(window=7, min_periods=1).mean()
    predicted_official = df['SMA_7_official'].iloc[-1]
    
    delta_per_liter = predicted_official - official_price
    
    volume = 2000
    impact_2000l = abs(delta_per_liter) * volume
    
    if delta_per_liter <= -0.010:
        advice = "WACHTEN / HOLD"
        status = (f"Prijsdaling verwacht van ca. € {abs(delta_per_liter):.3f}/L over 1-3 dagen. "
                  f"Wacht nog even met bestellen! Je bespaart ca. € {impact_2000l:.2f} op 2.000 liter.")
    elif delta_per_liter >= 0.010:
        advice = "NU KOPEN / BUY NOW"
        status = (f"Prijsstijging verwacht van ca. € {delta_per_liter:.3f}/L over 1-3 dagen. "
                  f"Bestel vandaag of morgen om ca. € {impact_2000l:.2f} te besparen op 2.000 liter.")
    else:
        advice = "NEUTRAAL"
        status = ("Stabiele markt. Geen significante prijsaanpassing verwacht de komende 48 uur "
                  "(verandering valt binnen de wettelijke FOD-drempelwaarde).")
        
    return {
        "latest_eur_ton": round(latest_ton, 2),
        "latest_market_liter": round(latest_market_liter, 3),
        "predicted_official_liter": round(predicted_official, 4),
        "delta_per_liter": round(delta_per_liter, 4),
        "impact_2000l": round(impact_2000l, 2),
        "latest_eurusd": round(df['eurusd'].iloc[-1], 4),
        "advice": advice,
        "status": status
    }

def analyze_mid_term(df):
    """MID-TERM TREND (Weeks/Months)"""
    df['SMA_5'] = df['gasoil_eur_ton'].rolling(window=5, min_periods=1).mean()
    df['SMA_20'] = df['gasoil_eur_ton'].rolling(window=20, min_periods=1).mean()
    
    sma5 = df['SMA_5'].iloc[-1]
    sma20 = df['SMA_20'].iloc[-1]
    
    if sma5 > sma20:
        trend = "STIJGEND (BULLISH)"
        explanation = "Korte termijn gemiddelde ligt boven het 20-daags gemiddelde (opwaartse druk)."
    else:
        trend = "DALEND (BEARISH)"
        explanation = "Korte termijn gemiddelde ligt onder het 20-daags gemiddelde (neerwaartse druk)."
        
    return {
        "trend": trend,
        "explanation": explanation
    }

def run_engine():
    """Runs calculation engine, saves daily snapshot to SQLite database, and returns analysis."""
    init_db()
    df = fetch_market_data()
    
    if df.empty:
        return None, None, None
        
    official_price = get_belgian_official_price()
    short_term = analyze_short_term(df, official_price)
    mid_term = analyze_mid_term(df)
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    save_daily_record(
        date_str=today_str,
        oil_eur_ton=short_term['latest_eur_ton'],
        eurusd=short_term['latest_eurusd'],
        official_price=official_price,
        advice=short_term['advice'],
        trend=mid_term['trend']
    )
    
    return short_term, mid_term, official_price

if __name__ == "__main__":
    short_term, mid_term, official_price = run_engine()
    if short_term:
        print("\n" + "="*60)
        print("     BELGISCHE MAZOUT PROGNOSE ENGINE")
        print("="*60)
        print(f"Marktkoers Grondstof (excl. tax):  € {short_term['latest_market_liter']} / Liter (€ {short_term['latest_eur_ton']} / ton)")
        print(f"Huidige Officiële Max. Prijs:      € {official_price} / Liter")
        print(f"Verwachte Officiële Prijs (7-SMA): € {short_term['predicted_official_liter']} / Liter")
        print("-" * 60)
        print(f"KORTE TERMIJN ADVIES (1-5 Dagen):  {short_term['advice']}")
        print(f"Financieel Effect op 2.000 Liter:  € {short_term['impact_2000l']:.2f}")
        print(f"Toelichting:                       {short_term['status']}")
        print("-" * 60)
        print(f"MIDDENLANGE TERMIJN TREND:         {mid_term['trend']}")
        print(f"Toelichting:                       {mid_term['explanation']}")
        print("="*60 + "\n")
