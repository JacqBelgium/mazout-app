import streamlit as st
import pandas as pd
import sqlite3
from main import run_engine

st.set_page_config(
    page_title="Belgian Heating Oil Price Trends",
    page_icon="🛢️",
    layout="wide"
)

st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    .vandersteen-header {
        background-color: #000000;
        color: #FFD700;
        padding: 2.5rem 2rem;
        border-radius: 8px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
    }
    .vandersteen-header h1 {
        color: #FFD700 !important;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-weight: 700;
        margin-bottom: 0.5rem;
        font-size: 2.3rem;
    }
    .vandersteen-header p {
        color: #FFFFFF !important;
        font-size: 1.1rem;
        margin: 0;
        opacity: 0.9;
    }
    div[data-testid="stMetricValue"] {
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="vandersteen-header">
        <h1>🛢️ Belgian Heating Oil Price Trends</h1>
        <p>Independent analysis of heating oil prices based on international exchanges and the official Belgian FPS Economy threshold system.</p>
    </div>
""", unsafe_allow_html=True)

short_term, mid_term, official_price = run_engine()

if short_term:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Market Crude Value (excl. tax)",
            value=f"€ {short_term['latest_market_liter']:.3f} / L",
            delta=f"€ {short_term['latest_eur_ton']} / ton"
        )
        
    with col2:
        st.metric(
            label="Current Max Price (FPS Official)",
            value=f"€ {official_price:.4f} / L"
        )
        
    with col3:
        st.metric(
            label="Estimated Price (1-3 Days)",
            value=f"€ {short_term['predicted_official_liter']:.4f} / L",
            delta=f"{short_term['delta_per_liter']:.4f} €/L"
        )

    st.markdown("---")
    
    trend_title = short_term['advice'].replace("WACHTEN / HOLD", "HOLD / EXPECTED PRICE DROP").replace("NU KOPEN / BUY NOW", "EXPECTED PRICE INCREASE").replace("NEUTRAAL", "STABLE / NEUTRAL")
    
    status_en = short_term['status']
    status_en = status_en.replace("Prijsdaling verwacht van ca.", "Expected price drop of approx.")
    status_en = status_en.replace("over 1-3 dagen. Wacht nog even met bestellen! Je bespaart ca.", "over 1-3 days. Potential savings of approx.")
    status_en = status_en.replace("op 2.000 liter.", "on a 2,000-liter order.")
    status_en = status_en.replace("Prijsstijging verwacht van ca.", "Expected price increase of approx.")
    status_en = status_en.replace("Bestel vandaag of morgen om ca.", "Order in time to save approx.")
    status_en = status_en.replace("te besparen op 2.000 liter.", "on a 2,000-liter order.")
    status_en = status_en.replace("Stabiele markt. Geen significante prijsaanpassing verwacht de komende 48 uur (verandering valt binnen de wettelijke FOD-drempelwaarde).", 
                                  "Stable market. No significant official price adjustment expected within the next 48 hours (fluctuations remain within the legal threshold).")

    if "HOLD" in short_term['advice'] or "WACHTEN" in short_term['advice']:
        st.info(f"### ⏳ Short-Term Trend Outlook: {trend_title}\n\n{status_en}")
    elif "KOPEN" in short_term['advice'] or "BUY" in short_term['advice']:
        st.warning(f"### 📈 Short-Term Trend Outlook: {trend_title}\n\n{status_en}")
    else:
        st.info(f"### ⚖️ Short-Term Trend Outlook: {trend_title}\n\n{status_en}")
        
    st.subheader("💰 Financial Impact on Standard Order (2,000 Liters)")
    st.write(f"Estimated financial gap/difference within 24–48h: **€ {short_term['impact_2000l']:.2f}**")

st.markdown("---")

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

st.caption("Disclaimer: This platform provides data-driven statistical market trend forecasts based on public market indicators and official threshold formulas. It does not constitute financial or commercial advice.")
