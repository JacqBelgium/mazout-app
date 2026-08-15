import streamlit as st
import pandas as pd
import sqlite3
from main import run_engine

st.set_page_config(
    page_title="Belgische Mazout Prijs Trends",
    page_icon="🛢️",
    layout="wide"
)

st.title("🛢️ Belgische Mazout Prijs Prognose")
st.write("Onafhankelijke analyse van de stookolieprijs op basis van de internationale beurzen en het Belgische FOD-kliksysteem.")

# Engine uitvoeren voor live gegevens
short_term, mid_term, official_price = run_engine()

if short_term:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Marktkoers Grondstof (excl. tax)",
            value=f"€ {short_term['latest_market_liter']:.3f} / L",
            delta=f"€ {short_term['latest_eur_ton']} / ton"
        )
        
    with col2:
        st.metric(
            label="Huidige Max. Prijs (FOD)",
            value=f"€ {official_price:.4f} / L"
        )
        
    with col3:
        st.metric(
            label="Verwachte Prijs (1-3 Dagen)",
            value=f"€ {short_term['predicted_official_liter']:.4f} / L",
            delta=f"{short_term['delta_per_liter']:.4f} €/L"
        )

    st.markdown("---")
    
    # Korte termijn Advies Box
    if "WACHTEN" in short_term['advice']:
        st.success(f"### ⏳ Advies: {short_term['advice']}\n\n{short_term['status']}")
    elif "KOPEN" in short_term['advice']:
        st.error(f"### 🚀 Advies: {short_term['advice']}\n\n{short_term['status']}")
    else:
        st.info(f"### ⚖️ Advies: {short_term['advice']}\n\n{short_term['status']}")
        
    # Financieel effect bij 2.000 Liter
    st.subheader("💰 Impact op een standaard bestelling (2.000 Liter)")
    st.write(f"Geschat voordeel / nadeel bij bestellen over 24-48u: **€ {short_term['impact_2000l']:.2f}**")

st.markdown("---")

# Historie tonen uit SQLite
st.subheader("📊 Historische Trend")
conn = sqlite3.connect('mazout_data.db')
df_hist = pd.read_sql_query("SELECT date, oil_eur_ton, official_belgian_price_liter FROM daily_predictions ORDER BY date DESC LIMIT 30", conn)
conn.close()

if not df_hist.empty:
    st.dataframe(df_hist, width=1200)
