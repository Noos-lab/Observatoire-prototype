import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
import requests

# ---- Configuration ----
st.set_page_config(page_title="Observatoire Global", layout="wide")
st.title("🌐 Observatoire Global des Données Publiques")

# ---- API Statistique Canada corrigée ----
@st.cache_data(show_spinner=False)
def get_all_statcan_cubes():
    url = "https://www150.statcan.gc.ca/t1/wds/rest/getAllCubesList"
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        if "object" in result:
            return result["object"]
        else:
            st.error("Réponse inattendue de Statistique Canada (aucun champ 'object').")
            return []
    except Exception as e:
        st.error(f"Erreur lors de la connexion à Statistique Canada : {e}")
        return []

@st.cache_data(show_spinner=False)
def get_cube_metadata(product_id):
    url = f"https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata/{product_id}"
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json().get("object", {})
    except Exception as e:
        st.error(f"Erreur lors de la récupération du metadata : {e}")
        return {}

@st.cache_data(show_spinner=False)
def get_vector_data(vector_id):
    url = f"https://www150.statcan.gc.ca/t1/wds/rest/getDataFromVector/{vector_id}"
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return pd.DataFrame(response.json().get("object", []))
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données : {e}")
        return pd.DataFrame()

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

# ---- Affichage des données simulées ----
data = load_data(selected_source, selected_country)

if not data.empty:
    st.subheader(f"Données pour {selected_country} – Source : {selected_source}")

    available_years = data['année'].dropna().unique()
    selected_year = st.slider("📅 Filtrer par année", int(min(available_years)), int(max(available_years)), int(max(available_years)))
    filtered_data = data[data['année'] == selected_year]

    st.dataframe(filtered_data)
    fig = px.bar(filtered_data, x="indicateur", y="valeur", color="indicateur", title=f"Indicateurs en {selected_year}")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Aucune donnée disponible pour cette combinaison pays/source.")

# ---- Test dynamique StatCan ----
st.markdown("## 🧪 Test dynamique Statistique Canada")

try:
    cubes = get_all_statcan_cubes()

    if not cubes:
        st.error("Aucune donnée de cubes reçue de Statistique Canada.")
    else:
        filtered = [c for c in cubes if "gdp" in c["cubeTitleEn"].lower()]
        if not filtered:
            st.warning("Aucun cube trouvé correspondant à 'GDP'.")
        else:
            cube_id = filtered[0]["productId"]
            st.info(f"Cube trouvé : {cube_id} - {filtered[0]['cubeTitleEn']}")

            metadata = get_cube_metadata(cube_id)
            if metadata:
                vector_ids = metadata.get("vectorIds", [])[:3]
                if vector_ids:
                    for vector_id in vector_ids:
                        df = get_vector_data(vector_id)
                        if not df.empty:
                            st.markdown(f"### Données du vecteur {vector_id}")
                            st.dataframe(df.head())
                        else:
                            st.info(f"Vecteur {vector_id} vide.")
                else:
                    st.warning("Ce cube ne contient aucun vecteur.")
            else:
                st.warning("Impossible de récupérer le metadata pour ce cube.")
except Exception as e:
    st.error(f"Erreur lors de la récupération dynamique : {e}")

# ---- Note pied de page ----
st.markdown("""
---
Prototype Streamlit – Données simulées + API StatCan | Version 0.4
""")
