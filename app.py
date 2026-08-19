import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from main import run_engine

st.set_page_config(
    page_title="Mazout Price Trends Belgium",
    page_icon="🛢️",
    layout="wide"
)

st.title("🛢️ Mazout Price Trends Belgium")
st.markdown("Real-time indicatieve mazoutprijs prognoses en historiek.")

# Engine aanroepen
short_term, mid_term, official_price = run_engine()

if short_term:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Huidige FOD Officiële Prijs",
            value=f"€ {official_price:.4f} / L"
        )
        
    with col2:
        st.metric(
            label="Verwachte Officiële Prijs",
            value=f"€ {short_term['predicted_official_liter']:.4f} / L",
            delta=f"{short_term['delta_per_liter']:.4f} / L"
        )
        
    with col3:
        st.metric(
            label="Advies",
            value=short_term['advice']
        )

    st.info(f"**Status:** {short_term['status']}")

# Historie ophalen uit SQLite
conn = sqlite3.connect('mazout_data.db')
try:
    df = pd.read_sql_query("SELECT date, oil_eur_ton, official_belgian_price_liter, predicted_official_liter FROM daily_predictions ORDER BY date ASC", conn)
finally:
    conn.close()

if not df.empty:
    st.subheader("📈 Prijsverloop & Trend")
    
    # Plotly grafiek opbouwen
    fig = px.line(
        df, 
        x='date', 
        y=['predicted_official_liter', 'official_belgian_price_liter'],
        labels={'value': 'Prijs in €/Liters', 'date': 'Datum', 'variable': 'Legende'},
        title="Prognose vs Officiële FOD Prijs"
    )
    
    # Inzoomen op de Y-as (voorkomt vlakke lijn doordat 0 niet het startpunt is)
    fig.update_yaxes(zeroline=False)
    fig.update_layout(
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("Bekijk Historische Datatabel"):
        st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)
else:
    st.warning("Nog geen historische data beschikbaar in de database.")
