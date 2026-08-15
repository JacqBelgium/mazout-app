import yfinance as yf
import pandas as pd
from datetime import datetime
from fod_data import get_belgian_official_price
from database import init_db, save_daily_record

def fetch_market_data():
    """Fetches Rotterdam market data & EUR/USD exchange rates."""
    print("Fetching Rotterdam market data & exchange rates...")
    
    eurusd_ticker = yf.Ticker('EURUSD=X')
    df_eurusd = eurusd_ticker.history(period='3mo')
    
    # We gebruiken Brent crude (BZ=F) of WTI (CL=F) om altijd een correcte tonprijs te berekenen
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
    
    # Omrekening naar EUR/ton: Olie in $/vat * 7.33 = $/ton / EURUSD = EUR/ton
    data['gasoil_eur_ton'] = (data['oil_usd'] * 7.33) / data['eurusd']
        
    return data

def analyze_short_term(df):
    """SHORT-TERM PROGNOSTICS (1-5 Days)"""
    total_rows = len(df)
    latest = df['gasoil_eur_ton'].iloc[-1]
    
    compare_idx = -4 if total_rows >= 4 else 0
    prev_3d = df['gasoil_eur_ton'].iloc[compare_idx]
    
    change_3d_pct = ((latest - prev_3d) / prev_3d) * 100
    
    if change_3d_pct < -1.5:
        advice = "WAIT / HOLD"
        status = "Downward market pressure. Belgian maximum price will likely DROP in 1-3 days."
    elif change_3d_pct > 1.5:
        advice = "BUY NOW"
        status = "Rising market price. Belgian maximum price will likely RISE in 1-3 days."
    else:
        advice = "NEUTRAL"
        status = "Stable short-term market. No major price adjustment expected in 1-3 days."
        
    return {
        "latest_eur_ton": round(latest, 2),
        "latest_eurusd": round(df['eurusd'].iloc[-1], 4),
        "change_3d_pct": round(change_3d_pct, 2),
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
        trend = "BULLISH (UPWARD)"
        explanation = "Short-term moving average is above the 20-day average (rising trend)."
    else:
        trend = "BEARISH (DOWNWARD)"
        explanation = "Short-term moving average is below the 20-day average (falling trend)."
        
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
        
    short_term = analyze_short_term(df)
    mid_term = analyze_mid_term(df)
    official_price = get_belgian_official_price()
    
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
        print("\n" + "="*55)
        print("    BELGIAN HEATING OIL PROGNOSTICS ENGINE")
        print("="*55)
        print(f"Latest Market Price:               €{short_term['latest_eur_ton']} / ton")
        print(f"Belgian Official Max Price:       €{official_price} / Liter")
        print(f"3-Day Market Change:               {short_term['change_3d_pct']}%")
        print("-" * 55)
        print(f"SHORT-TERM ADVICE (1-5 Days):      {short_term['advice']}")
        print(f"Reasoning:                         {short_term['status']}")
        print("-" * 55)
        print(f"MID-TERM TREND (Weeks/Months):     {mid_term['trend']}")
        print(f"Reasoning:                         {mid_term['explanation']}")
        print("="*55 + "\n")
