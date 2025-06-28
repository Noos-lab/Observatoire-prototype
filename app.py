import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
import requests
import xml.etree.ElementTree as ET

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

# ---- Recherche PubMed paginée ----
def search_pubmed(term="medecine", retmax=10, retstart=0):
    """Recherche des PMIDs sur PubMed selon le terme, paginée"""
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        f"?db=pubmed&term={term}&retmax={retmax}&retstart={retstart}&retmode=json"
    )
    r = requests.get(url)
    r.raise_for_status()
    result = r.json()["esearchresult"]
    ids = result["idlist"]
    count = int(result.get("count", len(ids)))
    return ids, count

def fetch_pubmed_details(idlist):
    """Récupère les détails pour une liste de PMIDs et retourne un DataFrame"""
    if not idlist:
        return pd.DataFrame()
    ids = ",".join(idlist)
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        f"?db=pubmed&id={ids}&retmode=xml"
    )
    r = requests.get(url)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    articles = []
    for art in root.findall(".//PubmedArticle"):
        title = art.findtext(".//ArticleTitle", "")
        pmid = art.findtext(".//PMID", "")
        authors = []
        for a in art.findall(".//Author"):
            last = a.findtext("LastName")
            first = a.findtext("ForeName")
            if last and first:
                authors.append(f"{first} {last}")
            elif last:
                authors.append(last)
        authors_str = ", ".join(authors)
        link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""
        # Utiliser du markdown pour rendre le titre cliquable
        title_md = f"[{title}]({link})" if title and link else title
        articles.append({
            "Titre": title_md,
            "Auteurs": authors_str,
            "Lien PubMed": link
        })
    return pd.DataFrame(articles)

# ---- Chargement des données simulées ----
def load_data(source, country):
    filepath = f"data/{source}/{country}.json"
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return pd.read_json(f)
    return pd.DataFrame()

# ---- Fonctions pour Marchés (APIs publiques ou stub/demo pour illustration) ----

def get_market_index_prices():
    """Retourne les prix indicatifs pour Dow Jones, Nasdaq, SP500 (données simulées/démo)"""
    # Pour usage réel, utiliser une API financière comme Yahoo Finance, Alpha Vantage, etc.
    # Ici, données fictives ou de démonstration
    return [
        {"Indice": "Dow Jones", "Ticker": "DJI", "Dernier": 39100.45, "Variation": "+0.31%"},
        {"Indice": "Nasdaq", "Ticker": "IXIC", "Dernier": 18170.12, "Variation": "+0.48%"},
        {"Indice": "S&P 500", "Ticker": "GSPC", "Dernier": 5530.77, "Variation": "+0.22%"},
    ]

def get_crypto_prices():
    """Retourne les prix indicatifs pour quelques cryptos (données simulées/démo)"""
    return [
        {"Crypto": "Bitcoin", "Ticker": "BTC", "Dernier": 63450.25, "Variation": "+1.2%"},
        {"Crypto": "Ethereum", "Ticker": "ETH", "Dernier": 3520.80, "Variation": "-0.4%"},
        {"Crypto": "Solana", "Ticker": "SOL", "Dernier": 139.30, "Variation": "+2.6%"},
        {"Crypto": "Cardano", "Ticker": "ADA", "Dernier": 0.385, "Variation": "+0.9%"},
    ]

def get_bonds_prices():
    """Retourne les taux indicatifs de bonds (données simulées/démo)"""
    return [
        {"Bond": "US 10Y", "Dernier": "4.25%", "Variation": "-0.03%"},
        {"Bond": "Bund 10Y", "Dernier": "2.37%", "Variation": "+0.01%"},
        {"Bond": "OAT 10Y", "Dernier": "3.12%", "Variation": "+0.00%"},
    ]

def get_commodities_prices():
    """Retourne les prix indicatifs de commodities (données simulées/démo)"""
    return [
        {"Commodity": "Or", "Ticker": "XAU", "Dernier": 2345.20, "Unité": "USD/oz", "Variation": "-0.3%"},
        {"Commodity": "Pétrole WTI", "Ticker": "CL", "Dernier": 81.35, "Unité": "USD/baril", "Variation": "+0.8%"},
        {"Commodity": "Cuivre", "Ticker": "HG", "Dernier": 4.38, "Unité": "USD/lb", "Variation": "+1.4%"},
    ]

# ---- Page d'accueil : choix principal ----
st.title("🌐 Observatoire Global des Données")
st.markdown("Bienvenue sur l'Observatoire Global. Choisissez un type de recherche pour commencer :")

main_choices = ["— Choisissez un domaine —", "Données publiques", "Études", "Marchés", "Blockchains"]
main_choice = st.radio("Sélectionnez un domaine :", main_choices, horizontal=True)

st.markdown("---")

# ---- Affichage conditionnel : n'affiche que si un domaine est choisi ----
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
    domaines = ["Médecine", "Environnement", "Sciences sociales", "Économie", "Technologie"]
    selected_field = st.selectbox("Domaine de recherche", domaines)

    st.write(f"🔬 Vous avez choisi le domaine : {selected_field}")

    if selected_field == "Médecine":
        st.markdown("#### Recherche d'études PubMed en médecine")
        search_term = st.text_input("🔎 Entrez un terme de recherche médical (ex : cancer, diabète, vaccination)", value="médecine")
        # Pagination avec session state
        if 'pubmed_page' not in st.session_state:
            st.session_state.pubmed_page = 1
        per_page = 10

        # Lancement de la recherche
        if st.button("Lancer la recherche sur PubMed") or search_term:
            # Reset pagination sur nouvelle recherche
            if st.session_state.get("last_search_term", "") != search_term:
                st.session_state.pubmed_page = 1
                st.session_state.last_search_term = search_term

            with st.spinner("Recherche sur PubMed..."):
                # Calcul de l'offset de départ
                page = st.session_state.pubmed_page
                retstart = (page - 1) * per_page
                ids, total = search_pubmed(term=search_term, retmax=per_page, retstart=retstart)
                if ids:
                    df_pubmed = fetch_pubmed_details(ids)
                    if not df_pubmed.empty:
                        # Affichage sous forme de liste de titres cliquables + auteurs
                        start_idx = retstart+1
                        end_idx = min(retstart+per_page, total)
                        st.markdown(f"*Résultats {start_idx} à {end_idx} sur {total}*")
                        for idx, row in df_pubmed.iterrows():
                            st.markdown(f"**{start_idx+idx}. {row['Titre']}**  \n_Auteurs :_ {row['Auteurs']}", unsafe_allow_html=True)
                        # Pagination
                        col_prev, col_next = st.columns([1, 1])
                        with col_prev:
                            if page > 1:
                                if st.button("⬅️ Page précédente", key="prev_pubmed"):
                                    st.session_state.pubmed_page -= 1
                                    st.experimental_rerun()
                        with col_next:
                            if retstart + per_page < total:
                                if st.button("Page suivante ➡️", key="next_pubmed"):
                                    st.session_state.pubmed_page += 1
                                    st.experimental_rerun()
                    else:
                        st.info("Aucun résultat trouvé (PubMed).")
                else:
                    st.info("Aucun résultat trouvé (PubMed).")
        st.caption("Résultats issus de la base PubMed (10 par page, navigation possible).")
    else:
        st.info("Module d'exploration d'études à implémenter ici…")

elif main_choice == "Marchés":
    st.subheader("🌍 Marchés financiers et cryptos")
    sous_options = ["Bourses", "Cryptos", "Bonds", "Commodities"]
    selected_market = st.selectbox("Choisissez un segment de marché :", sous_options)

    if selected_market == "Bourses":
        st.markdown("#### Indices Boursiers")
        indices = get_market_index_prices()
        st.table(pd.DataFrame(indices))
    elif selected_market == "Cryptos":
        st.markdown("#### Cryptomonnaies principales")
        cryptos = get_crypto_prices()
        st.table(pd.DataFrame(cryptos))
    elif selected_market == "Bonds":
        st.markdown("#### Obligations principales")
        bonds = get_bonds_prices()
        st.table(pd.DataFrame(bonds))
    elif selected_market == "Commodities":
        st.markdown("#### Matières premières")
        commos = get_commodities_prices()
        st.table(pd.DataFrame(commos))
    else:
        st.info("Sélectionnez une sous-catégorie pour afficher les prix.")

elif main_choice == "Blockchains":
    blockchains = ["Bitcoin", "Ethereum", "Tezos", "Solana", "Cardano", "Arbitrum", "Tron"]
    selected_blockchain = st.selectbox("Choisissez une blockchain", blockchains)

    st.write(f"⛓️ (Démo) Vous avez choisi : {selected_blockchain}")

    st.info("Module d'exploration blockchain à implémenter ici…")

    st.markdown("---")
    st.markdown("### 🔔 Créer une alerte pour ce réseau Blockchain")
    with st.form(f"alert_form_{selected_blockchain}"):
        alert_type = st.selectbox(
            "Type d'alerte",
            ["Nouvelle transaction importante", "Variation de prix", "Hausse brutale de fees", "Bloc miné", "Autre"]
        )
        threshold = st.text_input("Seuil / Mot-clé / Adresse (optionnel)")
        email_alert = st.text_input("Email pour recevoir l'alerte")
        submit_alert = st.form_submit_button("Créer l'alerte")
        if submit_alert:
            st.success(f"Alerte '{alert_type}' pour {selected_blockchain} enregistrée pour {email_alert} (simulation).")

# ---- Test dynamique StatCan (optionnel, peut être déplacé) ----
if main_choice == "Données publiques":
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
Prototype Streamlit – Données simulées + API StatCan + PubMed + Marchés | Version 1.0
""")
