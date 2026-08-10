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

# Header
st.title("🛢️ Belgische Mazoutprijs & Marktadvies")
st.caption("Officiële Belgische maximumprijzen per liter (bij bestellingen vanaf 2.000L, incl. btw)")

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

# ---------------------------------------------------------
# 3. DATA VERRIJKEN VOOR 2 TYPES STOOKOLIE
# ---------------------------------------------------------
if not df.empty and "official_belgian_price_liter" in df.columns:
    
    # Basisprijs is Standaard Mazout (50ppm)
    df["prijs_standaard"] = df["official_belgian_price_liter"]

    # Als er nog geen 'prijs_extra' kolom in de DB zit, berekenen we deze met de standaard H0-toeslag
    if "prijs_extra" not in df.columns:
        df["prijs_extra"] = df["prijs_standaard"] + 0.3751  # H0/H7 marktverschil

    latest_row = df.iloc[-1]
    latest_date = latest_row["date"].strftime("%d-%m-%Y") if "date" in df.columns else "Onbekend"

    # ---------------------------------------------------------
    # 4. KPI KAARTEN BOVENAAN
    # ---------------------------------------------------------
    st.subheader("📊 Huidige Maximumprijzen & Marktstatus")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🟢 Standaard (50ppm)",
            value=f"€ {latest_row['prijs_standaard']:.4f} / L",
            help="Officiële FOD maximumprijs voor gewone stookolie."
        )

    with col2:
        st.metric(
            label="🔵 Mazout Extra (H0 / H7)",
            value=f"€ {latest_row['prijs_extra']:.4f} / L",
            help="Maximumprijs voor zwavelarme stookolie (dieselkwaliteit)."
        )

    with col3:
        st.metric(
            label="💡 Advies",
            value=str(latest_row.get('advice', 'N/B')),
            help="Aankoopadvies op basis van marktanalyse."
        )

    with col4:
        st.metric(
            label="📉 Markt Trend",
            value=str(latest_row.get('trend', 'N/B')),
            help="Huidige markttrend."
        )

    st.caption(f"*Laatst bijgewerkt op: {latest_date}*")
    st.divider()

    # ---------------------------------------------------------
    # 5. GRAFIEK MET 2 LIJNEN
    # ---------------------------------------------------------
    st.subheader("📈 Prijsontwikkeling per Liter")

    # Data omvormen voor Plotly (2 lijnen)
    df_melted = df.melt(
        id_vars=["date"], 
        value_vars=["prijs_standaard", "prijs_extra"],
        var_name="Type Stookolie", 
        value_name="Prijs_per_liter"
    )

    df_melted["Type Stookolie"] = df_melted["Type Stookolie"].map({
        "prijs_standaard": "Mazout Standaard (50ppm)",
        "prijs_extra": "Mazout Extra (H0/H7)"
    })

    fig = px.line(
        df_melted, 
        x="date", 
        y="Prijs_per_liter", 
        color="Type Stookolie",
        color_discrete_map={
            "Mazout Standaard (50ppm)": "#2ea043",  # Groen
            "Mazout Extra (H0/H7)": "#0969da"        # Blauw
        },
        labels={"date": "Datum", "Prijs_per_liter": "Prijs (€ / Liter)"},
        markers=True
    )

    fig.update_layout(
        hovermode="x unified", 
        legend_title_text="Soort Mazout",
        xaxis_title="Datum",
        yaxis_title="Prijs per Liter (€)"
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------
    # 6. HISTORISCHE DATATABEL
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

# ---------------------------------------------------------
# 7. UTLEG / FOOTER
# ---------------------------------------------------------
st.info(
    """
    ℹ️ **Waarom zie je twee prijzen?**
    * **Mazout Standaard (50ppm):** De officiële basismaximumprijs voor traditionele stookolie.
    * **Mazout Extra (H0 / H7):** Zwavelarme stookolie van dieselkwaliteit voor moderne condensatieketels.
    
    *Let op:* De meeste mazoutleveranciers bieden tegenwoordig standaard **Mazout Extra (H0)** aan op hun website.
    """
)
