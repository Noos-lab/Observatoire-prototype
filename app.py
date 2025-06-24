import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
import requests

# ---- Configuration ----
st.set_page_config(page_title="Observatoire Global", layout="wide")
st.title("🌐 Observatoire Global des Données Publiques")

# ---- API Statistique Canada ----
@st.cache_data(show_spinner=False)
def get_all_statcan_cubes():
    url = "https://www150.statcan.gc.ca/t1/wds/rest/getAllCubesList"
    response = requests.get(url)
    return response.json().get("object", [])

@st.cache_data(show_spinner=False)
def get_cube_metadata(product_id):
    url = f"https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata/{product_id}"
    response = requests.get(url)
    return response.json().get("object", {})

@st.cache_data(show_spinner=False)
def get_vector_data(vector_id):
    url = f"https://www150.statcan.gc.ca/t1/wds/rest/getDataFromVector/{vector_id}"
    response = requests.get(url)
    return pd.DataFrame(response.json().get("object", []))

# ---- Recherche interactive dans Statistique Canada ----
with st.sidebar:
    st.header("🔍 Recherche Statistique Canada")
    search_term = st.text_input("Mot-clé (ex: GDP, employment, Québec)", "Québec")
    if search_term:
        cubes = get_all_statcan_cubes()
        filtered = [cube for cube in cubes if search_term.lower() in cube['cubeTitleEn'].lower()]
        selected_cube = st.selectbox("Résultats disponibles", [f"{c['productId']} – {c['cubeTitleEn']}" for c in filtered])

        if selected_cube:
            product_id = selected_cube.split(" – ")[0]
            metadata = get_cube_metadata(product_id)
            vector_ids = metadata.get("vectorIds", [])[:3]  # 3 vecteurs max pour début

            for vector_id in vector_ids:
                df = get_vector_data(vector_id)
                if not df.empty:
                    st.markdown(f"### 📊 Données du vecteur {vector_id}")
                    st.dataframe(df.head())

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
Prototype Streamlit – Données simulées + API StatCan | Version 0.2
""")
