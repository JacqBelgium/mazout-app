import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os

# Pagina configuratie
st.set_page_config(
    page_title="Belgische Mazoutprijzen",
    page_icon="🛢️",
    layout="wide"
)

# ---------------------------------------------------------
# DATABASE INSTELLINGEN
DB_FILE = "mazout_data.db"
# ---------------------------------------------------------

st.title("🛢️ Belgische Mazoutprijs Trends")
st.caption("Officiële Belgische maximumprijzen (bij bestellingen vanaf 2.000 liter, incl. btw)")

# 1. Controleer of het databasebestand aanwezig is
if not os.path.exists(DB_FILE):
    st.error(f"⚠️ Het databasebestand '{DB_FILE}' werd niet gevonden in de GitHub repository.")
    st.info("Controleer of het bestand wel in de hoofdmap van de repository staat.")
    st.stop()

# 2. Data ophalen uit SQLite database
@st.cache_data(ttl=3600)
def load_data_from_db():
    conn = sqlite3.connect(DB_FILE)
    
    # Kijken welke tabellen er in de database zitten
    tables_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
    tables = tables_df['name'].tolist()
    
    if not tables:
        conn.close()
        raise Exception("Geen tabellen gevonden in de database.")
    
    # Gebruik de eerste tabel uit de database
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

# Datum omzetten naar datetime
if "datum" in df.columns:
    df["datum"] = pd.to_datetime(df["datum"])
    df = df.sort_values("datum")

# 3. KPI / Samenvatting weergeven
st.subheader("📊 Meest recente prijzen")

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

    # 4. Grafiek opbouwen voor beide types
    st.subheader("📈 Prijsontwikkeling per Liter")

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
            "Mazout Standaard (50ppm)": "#2ea043",
            "Mazout Extra (H0/H7)": "#0969da"
        },
        labels={"datum": "Datum", "Prijs_per_liter": "Prijs (€ / Liter)"}
    )

    fig.update_layout(hovermode="x unified", legend_title_text="Soort Mazout")
    st.plotly_chart(fig, use_container_width=True)

else:
    # Generieke weergave als kolommen anders heten
    st.dataframe(df, use_container_width=True)

# 5. Uitlegbox
st.info(
    """
    ℹ️ **Type stookolie:**
    * **Mazout Standaard (50ppm):** De officiële maximumprijs voor traditionele stookolie.
    * **Mazout Extra (H0 / H7):** Zwavelarme stookolie van dieselkwaliteit voor condensatieketels.
    """
)
