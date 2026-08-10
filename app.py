import streamlit as st
import pandas as pd
import plotly.express as px
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

# Header sectie
st.title("🛢️ Belgische Mazoutprijs & Marktadvies")
st.caption("Officiële Belgische maximumprijs per liter en actuele markttrends")

# 1. Controleer of het databasebestand aanwezig is
if not os.path.exists(DB_FILE):
    st.error(f"⚠️ Het databasebestand '{DB_FILE}' werd niet gevonden in de GitHub repository.")
    st.info("Controleer op GitHub of het bestand 'mazout_data.db' in de hoofdmap staat.")
    st.stop()

# 2. Data ophalen uit SQLite database
@st.cache_data(ttl=3600)
def load_data_from_db():
    conn = sqlite3.connect(DB_FILE)
    
    # Zoek de tabelnaam op in de SQLite database
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

# ---------------------------------------------------------
# 3. MEEST RECENTE PRIJS & ADVIES (KPI's)
# ---------------------------------------------------------
st.subheader("📊 Actuele Status")

if not df.empty:
    latest_row = df.iloc[-1]
    latest_date = latest_row["date"].strftime("%d-%m-%Y") if "date" in df.columns else "Onbekend"

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label=" Officiële Belgische Prijs",
            value=f"€ {latest_row['official_belgian_price_liter']:.3f} / L" if 'official_belgian_price_liter' in latest_row else "N/B",
            help="Officiële maximumprijs per liter in België."
        )

    with col2:
        st.metric(
            label="💡 Advies",
            value=str(latest_row.get('advice', 'N/B')),
            help="Aankoopadvies op basis van marktwaarde."
        )

    with col3:
        st.metric(
            label="📉 Markt Trend",
            value=str(latest_row.get('trend', 'N/B')),
            help="Verwachte markttrend."
        )

    st.caption(f"*Laatst bijgewerkt op: {latest_date}*")
    st.divider()

    # ---------------------------------------------------------
    # 4. GRAFIEK SECTIE
    # ---------------------------------------------------------
    st.subheader("📈 Prijsverloop Belgische Mazout (€ / Liter)")

    if "official_belgian_price_liter" in df.columns and "date" in df.columns:
        fig = px.line(
            df, 
            x="date", 
            y="official_belgian_price_liter",
            labels={"date": "Datum", "official_belgian_price_liter": "Prijs (€ / Liter)"},
            markers=True
        )

        fig.update_traces(line_color="#0969da", line_width=3)

        fig.update_layout(
            hovermode="x unified", 
            xaxis_title="Datum",
            yaxis_title="Prijs per Liter (€)"
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
    st.warning("De database bevat momenteel geen gegevens.")
