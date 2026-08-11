import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import os

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Belgian Heating Oil Trends",
    page_icon="🛢️",
    layout="wide"
)

# ---------------------------------------------------------
# VANDESTEEN.BE BRANDING & CUSTOM CSS (COMPACT FONTS)
# ---------------------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    .main-title {
        color: #1E293B;
        font-weight: 700;
        margin-bottom: 25px;
    }

    /* Metric Cards Styling - Vandesteen Orange Accent & Compact Fonts */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-top: 4px solid #D9531E;
        padding: 12px 14px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* Smaller font for Labels to prevent '...' truncation */
    div[data-testid="stMetricLabel"] p {
        color: #475569;
        font-weight: 600;
        font-size: 0.75rem !important;
        white-space: nowrap;
        overflow: visible;
    }
    
    /* Smaller font for Metric Values */
    div[data-testid="stMetricValue"] div {
        color: #0F172A;
        font-weight: 700;
        font-size: 1.25rem !important;
        white-space: nowrap;
    }

    .stAlert {
        border-radius: 8px;
        border-left: 4px solid #D9531E !important;
    }

    .meta-caption {
        color: #64748B;
        font-size: 0.85rem;
        margin-top: 10px;
        margin-bottom: 2px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DATABASE SETTINGS
# ---------------------------------------------------------
DB_FILE = "mazout_data.db"

st.markdown('<h1 class="main-title">🛢️ Belgian Heating Oil Price & Market Advice</h1>', unsafe_allow_html=True)

if not os.path.exists(DB_FILE):
    st.error(f"⚠️ Database file '{DB_FILE}' not found.")
    st.stop()

@st.cache_data(ttl=60)
def load_data_from_db():
    conn = sqlite3.connect(DB_FILE)
    tables_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
    tables = tables_df['name'].tolist()
    
    if not tables:
        conn.close()
        raise Exception("No tables found in database.")
    
    table_name = tables[0]
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

try:
    df = load_data_from_db()
except Exception as e:
    st.error(f"⚠️ Error reading database: {e}")
    st.stop()

if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

# Calculate Moving Averages
if "official_belgian_price_liter" in df.columns:
    df["MA5"] = df["official_belgian_price_liter"].rolling(window=5, min_periods=1).mean()
    df["MA20"] = df["official_belgian_price_liter"].rolling(window=20, min_periods=1).mean()

# ---------------------------------------------------------
# KPI / METRICS OVERVIEW
# ---------------------------------------------------------
st.subheader("📊 Market Overview")

if not df.empty and "official_belgian_price_liter" in df.columns:
    latest_row = df.iloc[-1]
    latest_date = latest_row["date"].strftime("%d-%m-%Y") if "date" in df.columns else "Unknown"

    raw_trend = str(latest_row.get('trend', 'N/A')).upper()
    if "BEARISH" in raw_trend or "DOWN" in raw_trend:
        formatted_trend = "BEARISH ↘"
    elif "BULLISH" in raw_trend or "UP" in raw_trend:
        formatted_trend = "BULLISH ↗"
    else:
        formatted_trend = raw_trend

    raw_advice = str(latest_row.get('advice', 'N/A')).upper()
    if "KOPEN" in raw_advice or "BUY" in raw_advice:
        formatted_advice = "BUY"
    elif "AFWACHTEN" in raw_advice or "WAIT" in raw_advice:
        formatted_advice = "HOLD / WAIT"
    else:
        formatted_advice = raw_advice

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="OFFICIAL PRICE",
            value=f"€ {latest_row['official_belgian_price_liter']:.4f} / L",
            help="Official maximum Belgian price per liter for Gasolie Extra."
        )

    with col2:
        st.metric(
            label="RECOMMENDATION",
            value=formatted_advice,
            help="Automated purchasing advice based on market dynamics."
        )

    with col3:
        st.metric(
            label="MARKET TREND",
            value=formatted_trend,
            help="Current expected market price direction."
        )

    with col4:
        oil_price = latest_row.get('oil_eur_ton', None)
        if oil_price and oil_price < 400:
            oil_price = round(oil_price * 2.08, 2)
            
        if oil_price and pd.notnull(oil_price):
            st.metric(
                label="CRUDE OIL (€/TON)",
                value=f"€ {oil_price:.2f}",
                help="Benchmark crude oil market price per metric ton."
            )
        elif 'eurusd' in latest_row and pd.notnull(latest_row['eurusd']):
            st.metric(
                label="EUR / USD",
                value=f"{latest_row['eurusd']:.4f}",
                help="Exchange rate Euro vs US Dollar."
            )

    st.markdown('<p class="meta-caption">Official Belgian maximum price per liter (Gasolie Extra H0/H7, orders ≥ 2,000L, incl. VAT)</p>', unsafe_allow_html=True)
    st.caption(f"*Last updated on: {latest_date}*")
    st.divider()

    # ---------------------------------------------------------
    # CHART SECTION
    # ---------------------------------------------------------
    st.subheader("📈 Belgian Heating Oil Price Trend (€ / Liter)")

    fig = go.Figure()

    # Official Price Line (Vandesteen Orange)
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["official_belgian_price_liter"],
        mode="lines+markers",
        name="Official Price",
        line=dict(color="#D9531E", width=3),
        marker=dict(size=6)
    ))

    # 5-Day Moving Average
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["MA5"],
        mode="lines",
        name="5-Day Average (MA5)",
        line=dict(color="#3B82F6", width=2, dash="dash")
    ))

    # 20-Day Moving Average
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["MA20"],
        mode="lines",
        name="20-Day Average (MA20)",
        line=dict(color="#10B981", width=2, dash="dot")
    ))

    fig.update_layout(
        hovermode="x unified",
        xaxis_title="Date",
        yaxis_title="Price per Liter (€)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#F1F5F9')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#F1F5F9')

    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------
    # HISTORICAL DATA TABLE
    # ---------------------------------------------------------
    st.divider()
    with st.expander("📋 View full historical data table"):
        df_display = df.copy()
        if "date" in df_display.columns:
            df_display["date"] = df_display["date"].dt.strftime("%Y-%m-%d")
        
        df_display = df_display.rename(columns={
            "date": "Date",
            "official_belgian_price_liter": "Official Price (€/L)",
            "oil_eur_ton": "Crude Oil (€/Ton)",
            "eurusd": "EUR/USD",
            "advice": "Advice",
            "trend": "Trend"
        })
        
        st.dataframe(
            df_display.sort_values("Date", ascending=False), 
            use_container_width=True,
            hide_index=True
        )

else:
    st.warning("No valid price data currently available in database.")

# ---------------------------------------------------------
# FOOTER / INFO
# ---------------------------------------------------------
st.info(
    """
    ℹ️ **About these data:**
    This dashboard displays official Belgian maximum heating oil prices (Gasolie Extra) alongside technical trend indicators (MA5 / MA20) and market predictions.
    """
)
