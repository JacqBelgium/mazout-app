import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.graph_objects as go
from main import run_engine

# 1. Page Configuration
st.set_page_config(
    page_title="Belgian Heating Oil Price Trends",
    page_icon="🛢️",
    layout="wide"
)

# 2. Custom CSS for Vandersteen Styling
st.markdown("""
    <style>
    .block-container {
        padding-top: 0rem;
        padding-bottom: 2rem;
        max-width: 100% !important;
    }
    .vandersteen-full-header {
        background-color: #000000;
        color: #FFD700;
        padding: 2.5rem 1.5rem;
        text-align: center;
        width: 100vw;
        position: relative;
        left: 50%;
        right: 50%;
        margin-left: -50vw;
        margin-right: -50vw;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
    }
    .vandersteen-full-header h1 {
        color: #FFD700 !important;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-weight: 800;
        margin-bottom: 0.5rem;
        font-size: 2.3rem;
        text-align: center;
    }
    .vandersteen-full-header p {
        color: #FFFFFF !important;
        font-size: 1.1rem;
        margin: 0 auto;
        max-width: 950px;
        line-height: 1.4;
        text-align: center;
        opacity: 0.95;
    }
    .main-content {
        max-width: 1300px;
        margin: 0 auto;
        padding: 0 1.5rem;
    }
    div[data-testid="stMetricValue"] {
        font-weight: 700;
    }
    .date-subtext {
        font-size: 0.85rem;
        color: #666666;
        margin-top: -0.5rem;
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Full-Width Centered Header Banner
st.markdown("""
    <div class="vandersteen-full-header">
        <h1>🛢️ Belgian Heating Oil Price Trends</h1>
        <p>Maximum Consumer Price by FOD/SPF Finance per day<br>Estimated price trend based on independent analysis of heating oil prices international exchanges<br>We dont show local suppliers for cheapest delivery</p>
    </div>
""", unsafe_allow_html=True)

st.markdown('<div class="main-content">', unsafe_allow_html=True)

# 4. Engine Execution
short_term, mid_term, official_price = run_engine()
today_date_str = datetime.now().strftime('%d-%m-%Y')
is_weekend = datetime.now().weekday() >= 5

if short_term:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Market Crude Value (excl. tax)",
            value=f"€ {short_term.get('crude_price', 0):.4f} / L"
        )
        st.caption(" ")

    with col2:
        st.metric(
            label="Current Max Price (FOD Finance)",
            value=f"€ {official_price:.4f} / L"
        )
        st.caption(f"Based Date: {short_term.get('as_of_date', 'N/A')}")

    with col3:
        st.metric(
            label="Estimated Price (1–3 Days)",
            value=f"€ {short_term['predicted_official_liter']:.4f} / L",
            delta=f"{short_term['delta_per_liter']:.4f} €/L"
        )
        impact_val = short_term.get('impact_2000l', short_term.get('delta_per_liter', 0) * 2000)
        st.markdown(f"<div style='font-size: 0.85rem; font-weight: bold; color: #FF8C00; margin-top: -4px;'>Impact >2000 liters: € {impact_val:.2f}</div>", unsafe_allow_html=True)

    info_msg = f"⏳ **Short-Term Trend Outlook (1–3 Days):** {short_term['advice']} - Initial market data loaded. The hourly background process automatically refreshes the latest status."
    st.info(info_msg)

    # Prijsopbouw / Details Expander
    with st.expander("🔍 Bekijk Prijsopbouw & Details"):
        st.write(f"**Ruwe olie / Brent basis:** € {short_term.get('crude_price', 0):.4f} / L")
        st.write(f"**Berekende schatting per liter:** € {short_term['predicted_official_liter']:.4f} / L")
        st.write(f"**Huidige officiële max. prijs:** € {official_price:.4f} / L")
        st.write(f"**Verwachte afwijking (Delta):** {short_term['delta_per_liter']:.4f} €/L")
        st.write(f"**Impact op bestelling (>2000L):** € {impact_val:.2f}")


conn = sqlite3.connect('mazout_data.db')
df_hist = pd.read_sql_query("SELECT date, official_belgian_price_liter FROM daily_predictions ORDER BY date ASC", conn)
conn.close()

if not df_hist.empty:
    df_hist['date'] = pd.to_datetime(df_hist['date'])
    
    # Period Filter Radio/Knoppenrij
    period_choice = st.radio(
        "Select Time Period:",
        options=["30 Days", "90 Days", "All Range"],
        horizontal=True,
        index=0
    )
    
    max_date = df_hist['date'].max()
    if period_choice == "30 Days":
        filtered_df = df_hist[df_hist['date'] >= (max_date - timedelta(days=30))]
    elif period_choice == "90 Days":
        filtered_df = df_hist[df_hist['date'] >= (max_date - timedelta(days=90))]
    else:
        filtered_df = df_hist

    # Plotly Figure
    fig = go.Figure()
    
    # Slanke gouden lijn met hele zachte donkere schaduw (geen felblauw vlak)
    fig.add_trace(go.Scatter(
        x=filtered_df['date'],
        y=filtered_df['official_belgian_price_liter'],
        mode='lines',
        name='Official Max Price (€/L)',
        line=dict(color='#DAA520', width=2.5),
        fill='tozeroy',
        fillcolor='rgba(218, 165, 32, 0.06)'
    ))

    fig.update_layout(
        height=260,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(200, 200, 200, 0.2)',
            title=""
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(200, 200, 200, 0.2)',
            title="€ / Liter",
            tickformat=".3f"
        ),
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("View Raw Historical Data Table"):
        st.dataframe(df_hist.sort_values(by='date', ascending=False), width=1200)

st.caption("Disclaimer: This platform provides data-driven statistical market trend forecasts based on public market indicators and official FOD Finance threshold formulas. It does not constitute financial or commercial advice.")

st.markdown('</div>', unsafe_allow_html=True)
