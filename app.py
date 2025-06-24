import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json

# ---- Configuration ----
st.set_page_config(page_title="Observatoire Global", layout="wide")
st.title("🌐 Observatoire Global des Données Publiques")

# ---- Chargement des données simulées ----
def load_data(source, country):
    filepath = f"data/{source}/{country}.json"
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return pd.read_json(f)
    return pd.DataFrame()

# ---- Sélection pays/institution ----
pays_options = [
    "Canada", "Québec", "France", "États-Unis", "Chine", "Inde",
    "ONU", "OMS", "UNESCO"
]
source_options = ["Banque mondiale", "OMS", "UNESCO"]

selected_country = st.selectbox("🌍 Choisissez un pays ou une organisation", pays_options)
selected_source = st.selectbox("📚 Source de données", source_options)

# ---- Affichage des données ----
data = load_data(selected_source, selected_country)

if not data.empty:
    st.subheader(f"Données pour {selected_country} – Source : {selected_source}")

    # Filtres
    available_years = data['année'].dropna().unique()
    selected_year = st.slider("📅 Filtrer par année", int(min(available_years)), int(max(available_years)), int(max(available_years)))
    filtered_data = data[data['année'] == selected_year]

    # Affichage tableau + graphique
    st.dataframe(filtered_data)

    fig = px.bar(filtered_data, x="indicateur", y="valeur", color="indicateur", title=f"Indicateurs en {selected_year}")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Aucune donnée disponible pour cette combinaison pays/source.")

# ---- Note pied de page ----
st.markdown("""
---
Prototype Streamlit – Données simulées | Version 0.1
""")
