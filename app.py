import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import os

# ---------------------------------------------------------
# PAGINA CONFIGURATIE
# ---------------------------------------------------------
st.set_page_config(
    page_title="Belgische Mazoutprijzen",
    page_icon="🛢️",
    layout="wide"
)

# ---------------------------------------------------------
# DATABASE INSTELLINGEN
# ---------------------------------------------------------
DB_FILE = "mazout_data.db"

# Header
st.title("🛢️ Belgische Mazoutprijs & Marktadvies")
st.caption("Officiële Belgische maximumprijs per liter (bij bestellingen vanaf 2.000L, incl. btw)")

# 1. Controleer of het databasebestand aanwezig is
if not os.path.exists(DB_FILE):
    st.error(f"⚠️ Het databasebestand '{DB_FILE}' werd niet gevonden in de GitHub repository.")
    st.info("Controleer op GitHub of het bestand 'mazout_data.db' in de hoofdmap staat.")
    st.stop()

# 2. Data ophalen uit SQLite database
@st.cache_data(ttl=3600)
def load_data_from_db():
    conn = sqlite3.connect(DB_FILE)
    tables_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
    tables = tables_df['name'].tolist()
    
    if not tables:
        conn.close()
        raise Exception("Geen tabellen gevonden in de database.")
    
    table_name = tables[0]
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

try:
    df = load_data_from_db()
except Exception as e:
    st.error(f"⚠️ Fout bij het uitlezen van de database: {e}")
    st.stop()

# Datums converteren en sorteren op datum
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

# Bereken de Moving Averages (MA5 en MA20)
if "official_belgian_price_liter" in df.columns:
    df["MA5"] = df["official_belgian_price_liter"].rolling(window=5, min_periods=1).mean()
    df["MA20"] = df["official_belgian_price_liter"].rolling(window=20, min_periods=1).mean()

# ---------------------------------------------------------
# 3. KPI / METRICS OVERZICHT
# ---------------------------------------------------------
st.subheader("📊 Huidige Marktstatus")

if not df.empty and "official_belgian_price_liter" in df.columns:
    latest_row = df.iloc[-1]
    latest_date = latest_row["date"].strftime("%d-%m-%Y") if "date" in df.columns else "Onbekend"

    # Format de trend met nette pijltjes
    raw_trend = str(latest_row.get('trend', 'N/B')).upper()
    if "BEARISH" in raw_trend or "DOWN" in raw_trend:
        formatted_trend = "BEARISH ↘"
    elif "BULLISH" in raw_trend or "UP" in raw_trend:
        formatted_trend = "BULLISH ↗"
    else:
        formatted_trend = raw_trend

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🛢️ Officiële Prijs",
            value=f"€ {latest_row['official_belgian_price_liter']:.4f} / L",
            help="Officiële Belgische maximumprijs per liter."
        )

    with col2:
        st.metric(
            label="💡 Advies",
            value=str(latest_row.get('advice', 'N/B')),
            help="Aankoopadvies op basis van marktanalyse."
        )

    with col3:
        st.metric(
            label="📉 Markt Trend",
            value=formatted_trend,
            help="Huidige verwachte markttrend."
        )

    with col4:
        if 'oil_eur_ton' in latest_row and pd.notnull(latest_row['oil_eur_ton']):
            st.metric(
                label="🌐 Olieprijs (€/Ton)",
                value=f"€ {latest_row['oil_eur_ton']:.2f}",
                help="Marktprijs ruwe olie per ton."
            )
        elif 'eurusd' in latest_row and pd.notnull(latest_row['eurusd']):
            st.metric(
                label="🔱 EUR/USD",
                value=f"{latest_row['eurusd']:.4f}",
                help="Wisselkoers Euro vs Dollar."
            )

    st.caption(f"*Laatst bijgewerkt op: {latest_date}*")
    st.divider()

    # ---------------------------------------------------------
    # 4. GRAFIEK SECTIE (MET MA5 EN MA20)
    # ---------------------------------------------------------
    st.subheader("📈 Prijsverloop Belgische Mazout (€ / Liter)")

    fig = go.Figure()

    # Hoofdlijn: Dagelijkse Prijs
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["official_belgian_price_liter"],
        mode="lines+markers",
        name="Officiële Prijs",
        line=dict(color="#0969da", width=3)
    ))

    # Trendlijn: 5-daags Gemiddelde (MA5)
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["MA5"],
        mode="lines",
        name="5-daags Gemiddelde (MA5)",
        line=dict(color="#ff9900", width=2, dash="dash")
    ))

    # Trendlijn: 20-daags Gemiddelde (MA20)
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["MA20"],
        mode="lines",
        name="20-daags Gemiddelde (MA20)",
        line=dict(color="#28a745", width=2, dash="dot")
    ))

    fig.update_layout(
        hovermode="x unified",
        xaxis_title="Datum",
        yaxis_title="Prijs per Liter (€)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------
    # 5. HISTORISCHE DATATABEL SECTIE
    # ---------------------------------------------------------
    st.divider()
    with st.expander("📋 Bekijk de volledige historie in tabelvorm"):
        df_display = df.copy()
        if "date" in df_display.columns:
            df_display["date"] = df_display["date"].dt.strftime("%Y-%m-%d")
        
        st.dataframe(
            df_display.sort_values("date", ascending=False), 
            use_container_width=True,
            hide_index=True
        )

else:
    st.warning("De database bevat momenteel geen geldige prijsgegevens.")

# ---------------------------------------------------------
# 6. INFO
# ---------------------------------------------------------
st.info(
    """
    ℹ️ **Over deze gegevens:**
    Deze applicatie toont de officiële Belgische maximumprijzen voor stookolie (Gasolie Extra), gecombineerd met 5-daagse en 20-daagse trendlijnen, markttrends en aankoopadviezen.
    """
)
