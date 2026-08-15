import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from main import run_engine

# 1. Page Configuration
st.set_page_config(
    page_title="Belgian Heating Oil Price Trends",
    page_icon="🛢️",
    layout="wide"
)

# 2. Custom CSS for Vandersteen Styling (Full-Width Black Banner, Centered Yellow Text)
st.markdown("""
    <style>
    /* Remove top/side margins to stretch header full width */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 2rem;
        max-width: 100% !important;
    }
    
    /* Full-Width Centered Black Header Banner */
    .vandersteen-full-header {
        background-color: #000000;
        color: #FFD700;
        padding: 3rem 1.5rem;
        text-align: center;
        width: 100vw;
        position: relative;
        left: 50%;
        right: 50%;
        margin-left: -50vw;
        margin-right: -50vw;
        margin-bottom: 2rem;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
    }
    .vandersteen-full-header h1 {
        color: #FFD700 !important;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-weight: 800;
        margin-bottom: 0.8rem;
        font-size: 2.5rem;
        text-align: center;
    }
    .vandersteen-full-header p {
        color: #FFFFFF !important;
        font-size: 1.15rem;
        margin: 0 auto;
        max-width: 900px;
        line-height: 1.5;
        text-align: center;
        opacity: 0.95;
    }
    
    /* Content wrapper for inner margins */
    .main-content {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 1rem;
    }
    
    div[data-testid="stMetricValue"] {
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Full-Width Centered Header Banner
st.markdown("""
    <div class="vandersteen-full-header">
        <h1>🛢️ Belgian Heating Oil Price Trends</h1>
        <p>Maximum Consumer Price by FOD Finance, plus trend based on independent analysis of heating oil prices based on international exchanges.</p>
    </div>
""", unsafe_allow_html=True)

# Container for main content
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# 4. Engine Execution
short_term, mid_term, official_price = run_engine()
today_date_str = datetime.now().strftime('%d/%m/%Y')
is_weekend = datetime.now().weekday() >= 5  # 5 = Saturday, 6 = Sunday

if short_term:
    # --- Top Row: 3 Key Metrics ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Market Crude Value (excl. tax)",
            value=f"€ {short_term['latest_market_liter']:.3f} / L",
            delta=f"€ {short_term['latest_eur_ton']} / ton"
        )
        
    with col2:
        st.metric(
            label=f"Current Max Price (FOD Finance) — {today_date_str}",
            value=f"€ {official_price:.4f} / L"
        )
        
    with col3:
        st.metric(
            label="Estimated Price (1–3 Days)",
            value=f"€ {short_term['predicted_official_liter']:.4f} / L",
            delta=f"{short_term['delta_per_liter']:.4f} €/L"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Financial Impact Directly Below Metrics ---
    st.info(f"💰 **Financial Impact on Standard Order (2,000 Liters):** Estimated gap/difference within 24–48 hours is **€ {short_term['impact_2000l']:.2f}**")

    # --- Weekend Notice if applicable ---
    if is_weekend:
        st.warning("📅 **Weekend Notice:** FOD Finance does not update official prices on weekends. The trend below predicts the expected price adjustment for **Monday morning** based on Friday's market closing prices.")

    st.markdown("---")
    
    # --- Trend Outlook & Translation ---
    trend_title = short_term['advice'].replace("WACHTEN / HOLD", "HOLD / EXPECTED PRICE DROP").replace("NU KOPEN / BUY NOW", "EXPECTED PRICE INCREASE").replace("NEUTRAAL", "STABLE / NEUTRAL")
    
    status_en = short_term['status']
    status_en = status_en.replace("Prijsdaling verwacht van ca.", "Expected price drop of approx.")
    status_en = status_en.replace("over 1-3 dagen. Wacht nog even met bestellen! Je bespaart ca.", "over 1-3 days (24–48h). Potential savings of approx.")
    status_en = status_en.replace("op 2.000 liter.", "on a 2,000-liter order.")
    status_en = status_en.replace("Prijsstijging verwacht van ca.", "Expected price increase of approx.")
    status_en = status_en.replace("Bestel vandaag of morgen om ca.", "Order within 24–48h to save approx.")
    status_en = status_en.replace("te besparen op 2.000 liter.", "on a 2,000-liter order.")
    status_en = status_en.replace("Stabiele markt. Geen significante prijsaanpassing verwacht de komende 48 uur (verandering valt binnen de wettelijke FOD-drempelwaarde).", 
                                  "Stable market. No significant official price adjustment expected within the next 24–48 hours (fluctuations remain within the legal FOD threshold).")

    # Trend Box
    if "HOLD" in short_term['advice'] or "WACHTEN" in short_term['advice']:
        st.success(f"### ⏳ Short-Term Trend Outlook (1–3 Days): {trend_title}\n\n{status_en}")
    elif "KOPEN" in short_term['advice'] or "BUY" in short_term['advice']:
        st.error(f"### 📈 Short-Term Trend Outlook (1–3 Days): {trend_title}\n\n{status_en}")
    else:
        st.info(f"### ⚖️ Short-Term Trend Outlook (1–3 Days): {trend_title}\n\n{status_en}")

st.markdown("---")

# 5. Historical Chart & Data Table
st.subheader("📊 Historical Price Trend & Evolution")

conn = sqlite3.connect('mazout_data.db')
df_hist = pd.read_sql_query("SELECT date, oil_eur_ton, official_belgian_price_liter FROM daily_predictions ORDER BY date ASC", conn)
conn.close()

if not df_hist.empty:
    df_hist['date'] = pd.to_datetime(df_hist['date'])
    df_hist = df_hist.set_index('date')
    
    st.line_chart(
        df_hist[['official_belgian_price_liter']],
        height=350
    )
    
    with st.expander("View Raw Historical Data Table"):
        st.dataframe(df_hist.sort_index(ascending=False), width=1200)

# Legal Footer
st.caption("Disclaimer: This platform provides data-driven statistical market trend forecasts based on public market indicators and official FOD Finance threshold formulas. It does not constitute financial or commercial advice.")

st.markdown('</div>', unsafe_allow_html=True)
