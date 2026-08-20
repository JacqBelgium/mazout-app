import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
from main import run_engine

st.set_page_config(
    page_title="Mazout Price Trends Belgium",
    page_icon="🛢️",
    layout="wide"
)

# Header Banner
st.markdown("""
    <style>
    .black-header {
        background-color: #000000;
        padding: 20px;
        border-radius: 8px;
        border-bottom: 4px solid #FF8C00;
        text-align: center;
        margin-bottom: 25px;
    }
    .black-header h1 {
        color: #FFFFFF !important;
        font-family: 'Montserrat', sans-serif;
        font-weight: 800;
        font-size: 2.2rem;
        margin: 0 0 10px 0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .black-header p {
        color: #CCCCCC !important;
        font-size: 0.95rem;
        margin: 4px 0;
        line-height: 1.4;
    }
    </style>
    
    <div class="black-header">
        <h1>🛢️ MAZOUT PRICE TRENDS BELGIUM</h1>
        <p>Maximum Consumer Price by FOD/SPF Finance per day</p>
        <p>Estimated price trend based on independent analysis of heating oil prices international exchanges</p>
        <p>We dont show local suppliers for cheapest delivery</p>
    </div>
""", unsafe_allow_html=True)

# Engine ophalen
short_term, mid_term, official_price = run_engine()

if short_term:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Current Max Price (FOD Finance)",
            value=f"€ {official_price:.4f} / L"
        )
        st.caption(f"Based Date: {short_term.get('as_of_date', 'N/A')}")
        
    with col2:
        st.metric(
            label="Estimated Price (1–3 Days)",
            value=f"€ {short_term['predicted_official_liter']:.4f} / L",
            delta=f"{short_term['delta_per_liter']:.4f} €/L"
        )
        st.caption(" ")
        
    with col3:
        st.metric(
            label="Advice",
            value=short_term['advice']
        )
        impact_val = short_term.get('impact_2000l', short_term.get('delta_per_liter', 0) * 2000)
        st.markdown(f"<div style='font-size: 0.9rem; font-weight: bold; color: #FF8C00; margin-top: 4px;'>Impact >2000 liters: € {impact_val:.2f}</div>", unsafe_allow_html=True)

    st.info(f"⏳ **Short-Term Trend Outlook (1–3 Days):** {short_term['advice']}\n\nInitial market data loaded. The hourly background process automatically refreshes the latest status.")

# SQLite Gegevens
conn = sqlite3.connect('mazout_data.db')
try:
    df = pd.read_sql_query("SELECT date, official_belgian_price_liter, predicted_official_liter FROM daily_predictions ORDER BY date ASC", conn)
except Exception:
    df = pd.DataFrame()
finally:
    conn.close()

if not df.empty:
    st.subheader("📈 Price Trend & History")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'], 
        y=df['official_belgian_price_liter'],
        mode='lines',
        name='Official Price',
        line=dict(color='#888888', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'], 
        y=df['predicted_official_liter'],
        mode='lines',
        name='Predicted Trend',
        line=dict(color='#FF8C00', width=3)
    ))
    
    fig.update_layout(
        hovermode="x unified",
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("View Raw Historical Data Table"):
        st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)
