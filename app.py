import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
import requests

# ---- Configuration ----
st.set_page_config(page_title="Observatoire Global", layout="wide")

# ---- Fonctions API Statistique Canada (inchangées) ----
@st.cache_data(show_spinner=False)
def get_all_statcan_cubes():
    url = "https://www150.statcan.gc.ca/t1/wds/rest/getAllCubesList"
    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result.get("object", [])
    except Exception as e:
        st.error(f"Erreur lors de la connexion à Statistique Canada : {e}")
        return []

@st.cache_data(show_spinner=False)
def get_cube_metadata(product_id):
    url = f"https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata/{product_id}"
    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
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
    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
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

# ---- Page d'accueil : choix principal ----
st.title("🌐 Observatoire Global des Données")
st.markdown("Bienvenue sur l'Observatoire Global. Choisissez un type de recherche pour commencer :")

main_choices = ["Données publiques", "Études", "Blockchains"]
main_choice = st.radio("Sélectionnez un domaine :", main_choices, horizontal=True)

st.markdown("---")

# ---- Navigation selon le choix principal ----
if main_choice == "Données publiques":
    # Options spécifiques pour Données publiques
    pays_options = [
        "Canada", "Québec", "France", "États-Unis", "Chine", "Inde",
        "ONU", "OMS", "UNESCO"
    ]
    source_options = ["Banque mondiale", "OMS", "UNESCO"]

    col1, col2 = st.columns(2)
    with col1:
        selected_country = st.selectbox("🌍 Choisissez un pays ou une organisation", pays_options, key="country1")
    with col2:
        selected_source = st.selectbox("📚 Source de données", source_options, key="source1")

    # Option de comparaison
    st.markdown("#### 🔄 Comparer avec un autre pays/organisation (optionnel)")
    compare = st.checkbox("Activer la comparaison")
    if compare:
        col3, col4 = st.columns(2)
        with col3:
            country2 = st.selectbox("Deuxième pays/organisation", pays_options, index=1, key="country2")
        with col4:
            source2 = st.selectbox("Source pour le deuxième", source_options, key="source2")
    else:
        country2, source2 = None, None

    # Chargement et affichage des données
    data1 = load_data(selected_source, selected_country)
    data2 = load_data(source2, country2) if compare and country2 and source2 else pd.DataFrame()

    # Visualisation(s)
    if not data1.empty:
        st.subheader(f"Données pour {selected_country} – Source : {selected_source}")
        available_years = data1['année'].dropna().unique()
        selected_year = st.slider("📅 Filtrer par année", int(min(available_years)), int(max(available_years)), int(max(available_years)), key="year1")
        filtered_data1 = data1[data1['année'] == selected_year]
        st.dataframe(filtered_data1)
        chart_type = st.selectbox("Type de visualisation", ["Barres", "Lignes", "Données textuelles"], key="chart1")
        if chart_type == "Barres":
            fig = px.bar(filtered_data1, x="indicateur", y="valeur", color="indicateur", title=f"Indicateurs en {selected_year}")
            st.plotly_chart(fig, use_container_width=True)
        elif chart_type == "Lignes":
            fig = px.line(filtered_data1, x="indicateur", y="valeur", color="indicateur", title=f"Indicateurs en {selected_year}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write(filtered_data1)
    else:
        st.warning("Aucune donnée disponible pour cette combinaison pays/source.")

    # Visualisation comparaison
    if compare and not data2.empty:
        st.subheader(f"Comparaison avec {country2} – Source : {source2}")
        available_years2 = data2['année'].dropna().unique()
        selected_year2 = st.slider("📅 Année de comparaison", int(min(available_years2)), int(max(available_years2)), int(max(available_years2)), key="year2")
        filtered_data2 = data2[data2['année'] == selected_year2]
        st.dataframe(filtered_data2)
        chart_type2 = st.selectbox("Type de visualisation (comparaison)", ["Barres", "Lignes", "Données textuelles"], key="chart2")
        if chart_type2 == "Barres":
            fig2 = px.bar(filtered_data2, x="indicateur", y="valeur", color="indicateur", title=f"Indicateurs en {selected_year2}")
            st.plotly_chart(fig2, use_container_width=True)
        elif chart_type2 == "Lignes":
            fig2 = px.line(filtered_data2, x="indicateur", y="valeur", color="indicateur", title=f"Indicateurs en {selected_year2}")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.write(filtered_data2)
    elif compare:
        st.info("Aucune donnée pour la seconde sélection.")

elif main_choice == "Études":
    # Options pour Études
    domaines = ["Médecine", "Environnement", "Sciences sociales", "Économie", "Technologie"]
    selected_field = st.selectbox("Domaine de recherche", domaines)
    st.write(f"🔬 (Démo) Vous avez choisi le domaine : {selected_field}")
    # Ici tu pourras brancher ton système d'indexation PubMed ou autre
    st.info("Module d'exploration d'études à implémenter ici…")

elif main_choice == "Blockchains":
    blockchains = ["Bitcoin", "Ethereum", "Tezos", "Solana"]
    selected_blockchain = st.selectbox("Choisissez une blockchain", blockchains)
    st.write(f"⛓️ (Démo) Vous avez choisi : {selected_blockchain}")
    # Ici tu pourras ajouter l'affichage d'indicateurs ou d'explorateur de blocs
    st.info("Module d'exploration blockchain à implémenter ici…")

# ---- Test dynamique StatCan (optionnel, peut être déplacé) ----
with st.expander("🧪 Test dynamique Statistique Canada (debug/dev)"):
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

# ---- Pied de page ----
st.markdown("""
---
Prototype Streamlit – Données simulées + API StatCan | Version 0.5
""")
