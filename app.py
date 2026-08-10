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
st.title("🛢️ Belgische Mazoutprijs Trends")
st.caption("Officiële Belgische maximumprijzen (bij bestellingen vanaf 2.000 liter, incl. btw)")

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

# Datums converteren en sorteren
if "datum" in df.columns:
    df["datum"] = pd.to_datetime(df["datum"])
    df = df.sort_values("datum")

# ---------------------------------------------------------
# 3. KPI / CURRENT PRICES SECTIE
# ---------------------------------------------------------
st.subheader("📊 Huidige Maximumprijzen")

if "prijs_standaard" in df.columns and "prijs_extra" in df.columns:
    latest_row = df.iloc[-1]
    latest_date = latest_row["datum"].strftime("%d-%m-%Y") if "datum" in df.columns else "Onbekend"

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="🟢 Mazout Standaard (50ppm)",
            value=f"€ {latest_row['prijs_standaard']:.4f} / L",
            help="Klassieke stookolie voor standaard branders."
        )

    with col2:
        st.metric(
            label="🔵 Mazout Extra (H0 / H7)",
            value=f"€ {latest_row['prijs_extra']:.4f} / L",
            help="Zwavelarme stookolie van dieselkwaliteit voor moderne condensatieketels."
        )

    st.caption(f"*Laatst bijgewerkt op: {latest_date}*")
    st.divider()

    # ---------------------------------------------------------
    # 4. GRAFIEK SECTIE
    # ---------------------------------------------------------
    st.subheader("📈 Prijsverloop over de Tijd")

    # Omvormen van data naar lang formaat voor Plotly Express
    df_melted = df.melt(
        id_vars=["datum"], 
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
        x="datum", 
        y="Prijs_per_liter", 
        color="Type Stookolie",
        color_discrete_map={
            "Mazout Standaard (50ppm)": "#2ea043",  # Groen
            "Mazout Extra (H0/H7)": "#0969da"        # Blauw
        },
        labels={"datum": "Datum", "Prijs_per_liter": "Prijs (€ / Liter)"}
    )

    fig.update_layout(
        hovermode="x unified", 
        legend_title_text="Soort Mazout",
        xaxis_title="Datum",
        yaxis_title="Prijs per Liter (€)"
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------
    # 5. HISTORISCHE DATATABEL SECTIE
    # ---------------------------------------------------------
    st.divider()
    with st.expander("📋 Bekijk de volledige prijshistorie in tabelvorm"):
        df_display = df.copy()
        df_display["datum"] = df_display["datum"].dt.strftime("%Y-%m-%d")
        st.dataframe(
            df_display.sort_values("datum", ascending=False), 
            use_container_width=True,
            hide_index=True
        )

else:
    # Terugvaloptie als de kolomnamen in de database afwijken
    st.warning("De verwachte kolommen ('prijs_standaard' en 'prijs_extra') zijn niet gevonden in de database.")
    st.dataframe(df, use_container_width=True)

# ---------------------------------------------------------
# 6. INFORMATIEBOX EN FOOTER
# ---------------------------------------------------------
st.info(
    """
    ℹ️ **Verschil tussen de twee types stookolie:**
    * **Mazout Standaard (50ppm):** De officiële basisprijs voor traditionele stookolie.
    * **Mazout Extra (H0 / H7):** Zwavelarme stookolie van dieselkwaliteit. 
    
    *Let op:* De meeste mazoutleveranciers bieden tegenwoordig standaard **Mazout Extra (H0)** aan op hun website vanwege strengere milieueisen en geschiktheid voor moderne condensatieketels.
    """
)
