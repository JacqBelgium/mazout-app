import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from main import run_engine, fetch_market_data
from database import get_historical_data

# Page Configuration
st.set_page_config(
    page_title="Belgian Heating Oil Price Trends",
    page_icon="🛢️",
    layout="wide"
)

# Header Section
st.title("🛢️ Belgian Heating Oil Price Trends & Prognostics")
st.markdown("Automated market analysis & short-term price trend forecasts for the Belgian heating oil market.")
st.markdown("---")

# Run calculation engine
with st.spinner("Fetching latest market data and updating prognostics..."):
    short_term, mid_term, official_price = run_engine()
    df_market = fetch_market_data()

if short_term:
    # --- TOP METRICS CARDS ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Belgian Max Price (>2000L)", 
            value=f"€{official_price:.4f} / L"
        )
        
    with col2:
        st.metric(
            label="Rotterdam Gasoil Spot", 
            value=f"€{short_term['latest_eur_ton']} / ton",
            delta=f"{short_term['change_3d_pct']}% (3d)"
        )
        
    with col3:
        st.metric(
            label="EUR / USD Rate", 
            value=f"${short_term['latest_eurusd']:.4f}"
        )

    with col4:
        st.metric(
            label="Mid-Term Market Trend", 
            value=mid_term['trend'].split()[0]
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # --- ADVICE BANNER ---
    advice = short_term['advice']
    if advice == "BUY NOW":
        st.error(f"### 🚨 SHORT-TERM RECOMMENDATION: **{advice}**")
    elif advice == "WAIT / HOLD":
        st.success(f"### 🟢 SHORT-TERM RECOMMENDATION: **{advice}**")
    else:
        st.info(f"### 🟡 SHORT-TERM RECOMMENDATION: **{advice}**")
        
    st.caption(f"**Analysis:** {short_term['status']}")
    st.caption(f"**Mid-Term Overview:** {mid_term['explanation']}")

    st.markdown("---")

    # --- CHARTS SECTION ---
    st.subheader("📈 Market Price Trend (Rotterdam Gasoil in €/ton)")
    
    if not df_market.empty:
        fig = go.Figure()
        
        # Line plot for Gasoil Price in EUR/ton
        fig.add_trace(go.Scatter(
            x=df_market.index, 
            y=df_market['gasoil_eur_ton'],
            mode='lines+markers',
            name='Gasoil (€/ton)',
            line=dict(color='#0066cc', width=3),
            marker=dict(size=6)
        ))

        # Add moving averages
        df_market['SMA_5'] = df_market['gasoil_eur_ton'].rolling(window=5, min_periods=1).mean()
        df_market['SMA_20'] = df_market['gasoil_eur_ton'].rolling(window=20, min_periods=1).mean()

        fig.add_trace(go.Scatter(
            x=df_market.index, 
            y=df_market['SMA_5'],
            mode='lines',
            name='5-Day Moving Avg',
            line=dict(color='#ff9900', width=1.5, dash='dash')
        ))

        fig.add_trace(go.Scatter(
            x=df_market.index, 
            y=df_market['SMA_20'],
            mode='lines',
            name='20-Day Moving Avg',
            line=dict(color='#9900cc', width=1.5, dash='dot')
        ))

        fig.update_layout(
            height=450,
            xaxis_title="Date",
            yaxis_title="Euro (€) per Ton",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

    # --- HISTORICAL DATA TABLE ---
    with st.expander("📊 View Recorded Snapshot History"):
        df_hist = get_historical_data(limit=30)
        if not df_hist.empty:
            st.dataframe(df_hist, use_container_width=True)

else:
    st.error("Could not load market data. Please check connection.")

# Footer
st.markdown("---")
st.caption("© vandersteen.be — Heating Oil Prognostics Model")