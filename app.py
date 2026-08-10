import streamlit as st
import pandas as pd
import plotly.express as px

# Pagina configuratie
st.set_page_config(
    page_title="Belgische Mazoutprijzen",
    page_icon="🛢️",
    layout="wide"
)

st.title("🛢️ Belgische Mazoutprijs Trends")
st.caption("Officiële Belgische maximumprijzen (bij bestellingen vanaf 2.000 liter, incl. btw)")

# Data inladen
df = pd.read_csv("mazout_prijzen.csv")
df["datum"] = pd.to_datetime(df["datum"])

# Meest recente rij en datum ophalen
latest_row = df.sort_values("datum").iloc[-1]
latest_date = latest_row["datum"].strftime("%d-%m-%Y")

# 1. Twee KPI-kaarten naast elkaar voor de huidige prijzen
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

st.write(f"*Laatst bijgewerkt op: {latest_date}*")

st.divider()

# 2. Grafiek met 2 lijnen
st.subheader("📈 Prijsontwikkeling per Liter")

# Data herstructureren voor Plotly met 2 categorieën
df_melted = df.melt(
    id_vars=["datum"], 
    value_vars=["prijs_standaard", "prijs_extra"],
    var_name="Type Stookolie", 
    value_name="Prijs_per_liter"
)

# Nette namen toekennen aan de legende
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

fig.update_layout(hovermode="x unified", legend_title_text="Soort Mazout")
st.plotly_chart(fig, use_container_width=True)

# 3. Informatiebox voor bezoekers
st.info(
    """
    ℹ️ **Waarom zie je twee verschillende prijzen?**
    * **Mazout Standaard (50ppm):** De officiële maximumprijs voor traditionele stookolie.
    * **Mazout Extra (H0 / H7):** Zwavelarme stookolie van dieselkwaliteit. 
    
    *Let op:* De meeste mazoutleveranciers bieden tegenwoordig standaard **Mazout Extra (H0)** aan op hun website vanwege milieueisen en geschiktheid voor moderne condensatieketels.
    """
)
