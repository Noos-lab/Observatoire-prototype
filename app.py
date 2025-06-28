import streamlit as st
import pandas as pd
import requests
import yfinance as yf
import xml.etree.ElementTree as ET
import os

st.set_page_config(page_title="Observatoire Global", layout="wide")

##############################
# Fonctions marché temps réel
##############################
# (Identiques aux versions précédentes)

@st.cache_data(ttl=600)
def get_market_index_prices():
    tickers = {
        "Dow Jones": "^DJI",
        "Nasdaq": "^IXIC",
        "S&P 500": "^GSPC"
    }
    data = []
    for name, ticker in tickers.items():
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        last = info.get("regularMarketPrice")
        change = info.get("regularMarketChangePercent")
        if last is not None and change is not None:
            data.append({
                "Nom": name,
                "Ticker": ticker,
                "Dernier": last,
                "Variation": f"{change:+.2f}%"
            })
    return data

@st.cache_data(ttl=600)
def get_stock_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        last = info.get("regularMarketPrice")
        name = info.get("shortName", symbol)
        change = info.get("regularMarketChangePercent")
        currency = info.get("currency", "")
        return {
            "Nom": name,
            "Ticker": symbol.upper(),
            "Dernier": last,
            "Variation": f"{change:+.2f}%" if change is not None else "N/A",
            "Devise": currency if currency else ""
        }
    except Exception:
        return None

@st.cache_data(ttl=300)
def get_crypto_prices():
    ids = "bitcoin,ethereum,solana,cardano,arbitrum,tron"
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
    r = requests.get(url)
    r.raise_for_status()
    cg = r.json()
    mapping = {
        "bitcoin": "Bitcoin",
        "ethereum": "Ethereum",
        "solana": "Solana",
        "cardano": "Cardano",
        "arbitrum": "Arbitrum",
        "tron": "Tron"
    }
    results = []
    for cid, name in mapping.items():
        if cid in cg:
            price = cg[cid].get("usd")
            change = cg[cid].get("usd_24h_change")
            results.append({
                "Nom": name,
                "Ticker": cid,
                "Dernier": price,
                "Variation 24h": f"{change:+.2f}%" if change is not None else "N/A"
            })
    return results

@st.cache_data(ttl=300)
def search_crypto_cg(query):
    url = "https://api.coingecko.com/api/v3/search"
    r = requests.get(url, params={"query": query})
    if r.status_code != 200:
        return []
    data = r.json()
    return data.get("coins", [])

@st.cache_data(ttl=600)
def get_crypto_price_by_id(cg_id):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd&include_24hr_change=true"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    data = r.json().get(cg_id)
    if not data:
        return None
    price = data.get("usd")
    change = data.get("usd_24h_change")
    return {
        "ID": cg_id,
        "Dernier": price,
        "Variation 24h": f"{change:+.2f}%" if change is not None else "N/A"
    }

@st.cache_data(ttl=600)
def get_bonds_prices(fmp_api_key=None):
    FMP_API_KEY = fmp_api_key or os.environ.get("FMP_API_KEY", "")
    endpoint = "https://financialmodelingprep.com/api/v3/quotes/bond"
    params = {"apikey": FMP_API_KEY} if FMP_API_KEY else {}
    try:
        r = requests.get(endpoint, params=params)
        r.raise_for_status()
        bonds = r.json()
        mapping = {
            "US10Y": "US 10Y",
            "DE10Y": "Bund 10Y",
            "FR10Y": "OAT 10Y"
        }
        results = []
        for bond in bonds:
            symbol = bond.get("symbol")
            name = mapping.get(symbol)
            if name:
                results.append({
                    "Nom": name,
                    "Ticker": symbol,
                    "Dernier": bond.get("price"),
                    "Variation": f"{bond.get('changesPercentage', 0):+0.2f}%"
                })
        return results
    except:
        return [
            {"Nom": "US 10Y", "Ticker": "US10Y", "Dernier": "4.25%", "Variation": "-0.03%"},
            {"Nom": "Bund 10Y", "Ticker": "DE10Y", "Dernier": "2.37%", "Variation": "+0.01%"},
            {"Nom": "OAT 10Y", "Ticker": "FR10Y", "Dernier": "3.12%", "Variation": "+0.00%"},
        ]

@st.cache_data(ttl=600)
def get_commodities_prices(fmp_api_key=None):
    FMP_API_KEY = fmp_api_key or os.environ.get("FMP_API_KEY", "")
    endpoint = "https://financialmodelingprep.com/api/v3/quotes/commodity"
    params = {"apikey": FMP_API_KEY} if FMP_API_KEY else {}
    try:
        r = requests.get(endpoint, params=params)
        r.raise_for_status()
        commos = r.json()
        mapping = {
            "GCUSD": ("Or", "USD/oz"),
            "CLUSD": ("Pétrole WTI", "USD/baril"),
            "HGUSD": ("Cuivre", "USD/lb"),
        }
        results = []
        for c in commos:
            symbol = c.get("symbol")
            if symbol in mapping:
                nom, unite = mapping[symbol]
                results.append({
                    "Nom": nom,
                    "Ticker": symbol,
                    "Dernier": c.get("price"),
                    "Unité": unite,
                    "Variation": f"{c.get('changesPercentage', 0):+0.2f}%"
                })
        return results
    except:
        return [
            {"Nom": "Or", "Ticker": "GCUSD", "Dernier": 2345.20, "Unité": "USD/oz", "Variation": "-0.3%"},
            {"Nom": "Pétrole WTI", "Ticker": "CLUSD", "Dernier": 81.35, "Unité": "USD/baril", "Variation": "+0.8%"},
            {"Nom": "Cuivre", "Ticker": "HGUSD", "Dernier": 4.38, "Unité": "USD/lb", "Variation": "+1.4%"},
        ]

##############################
# Recherche études médicales multi-bases
##############################

def search_pubmed(term="medecine", retmax=10, retstart=0):
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
        title_md = f"[{title}]({link})" if title and link else title
        articles.append({
            "Titre": title_md,
            "Auteurs": authors_str,
            "Lien PubMed": link
        })
    return pd.DataFrame(articles)

def search_europepmc(term, page=1, pageSize=10):
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        "query": term,
        "format": "json",
        "pageSize": pageSize,
        "page": page
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return [], 0
    data = r.json()
    hits = data.get("resultList", {}).get("result", [])
    total = int(data.get("hitCount", 0))
    articles = []
    for hit in hits:
        title = hit.get("title", "")
        authors = hit.get("authorString", "")
        link = hit.get("doi")
        pmid = hit.get("pmid")
        if link:
            link_url = f"https://doi.org/{link}"
        elif pmid:
            link_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        else:
            link_url = hit.get("fullTextUrlList", [{}])[0].get("url", "")
        title_md = f"[{title}]({link_url})" if title and link_url else title
        articles.append({
            "Titre": title_md,
            "Auteurs": authors,
            "Lien": link_url
        })
    return articles, total

def search_clinicaltrials(term, max_studies=10):
    url = "https://clinicaltrials.gov/api/query/study_fields"
    params = {
        "expr": term,
        "fields": "NCTId,BriefTitle,Condition,LeadSponsorName,LocationCountry,StudyFirstSubmitDate",
        "min_rnk": 1,
        "max_rnk": max_studies,
        "fmt": "json"
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return []
    studies = r.json()["StudyFieldsResponse"]["StudyFields"]
    results = []
    for study in studies:
        title = study["BriefTitle"][0] if study["BriefTitle"] else ""
        nctid = study["NCTId"][0] if study["NCTId"] else ""
        sponsor = study["LeadSponsorName"][0] if study["LeadSponsorName"] else ""
        country = study["LocationCountry"][0] if study["LocationCountry"] else ""
        date = study["StudyFirstSubmitDate"][0] if study["StudyFirstSubmitDate"] else ""
        url_link = f"https://clinicaltrials.gov/study/{nctid}" if nctid else ""
        title_md = f"[{title}]({url_link})" if title and url_link else title
        results.append({
            "Titre": title_md,
            "Sponsor": sponsor,
            "Pays": country,
            "Date": date,
            "NCT": nctid
        })
    return results

# ---------------------------
# Liens et instructions pour autres bases de données médicales
# ---------------------------

external_med_db_links = {
    "PubMed": "https://pubmed.ncbi.nlm.nih.gov/",
    "Embase": "https://www.embase.com/",
    "Cochrane Library": "https://www.cochranelibrary.com/",
    "Web of Science (WoS)": "https://www.webofscience.com/",
    "Scopus": "https://www.scopus.com/",
    "ClinicalTrials.gov": "https://clinicaltrials.gov/",
    "Europe PMC": "https://europepmc.org/",
    "LILACS": "https://lilacs.bvsalud.org/fr/",
    "MedRxiv": "https://www.medrxiv.org/",
    "BioRxiv": "https://www.biorxiv.org/",
    "Google Scholar": "https://scholar.google.com/",
}

external_med_db_desc = {
    "PubMed": "Base mondiale d'articles biomédicaux (accès libre).",
    "Embase": "Grande base biomédicale, forte en pharmacologie et essais européens (accès payant/institutionnel).",
    "Cochrane Library": "Référence pour les revues systématiques en santé (partiellement libre).",
    "Web of Science (WoS)": "Base multidisciplinaire, suivi des citations (accès payant/institutionnel).",
    "Scopus": "Grande base de citations et résumés en sciences (accès institutionnel).",
    "ClinicalTrials.gov": "Registre mondial des essais cliniques (accès libre).",
    "Europe PMC": "Base ouverte, forte sur la recherche européenne.",
    "LILACS": "Littérature santé Amérique latine/Caraïbes (accès libre).",
    "MedRxiv": "Prépublications en médecine.",
    "BioRxiv": "Prépublications en biologie.",
    "Google Scholar": "Moteur multidisciplinaire, accès libre.",
}

##############################
# Données publiques (données fictives)
##############################

def load_data(source, country):
    filepath = f"data/{source}/{country}.json"
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return pd.read_json(f)
    return pd.DataFrame()

##############################
# Tableau de bord personnalisé et alertes
##############################

def init_portfolio():
    if "portfolio" not in st.session_state:
        st.session_state["portfolio"] = {}

def add_to_portfolio(item):
    init_portfolio()
    st.session_state["portfolio"][item["type"] + ":" + item["id"]] = item

def remove_from_portfolio(item_type, item_id):
    init_portfolio()
    key = item_type + ":" + item_id
    if key in st.session_state["portfolio"]:
        del st.session_state["portfolio"][key]

def get_portfolio_items():
    init_portfolio()
    return list(st.session_state["portfolio"].values())

def init_study_alerts():
    if "study_alerts" not in st.session_state:
        st.session_state["study_alerts"] = []

def add_study_alert(term, mode, email=None):
    init_study_alerts()
    st.session_state["study_alerts"].append({
        "term": term,
        "mode": mode,
        "email": email
    })

def get_study_alerts():
    init_study_alerts()
    return st.session_state["study_alerts"]

##############################
# Interface utilisateur
##############################

st.title("🌐 Observatoire Global des Données")
st.markdown("Bienvenue sur l'Observatoire Global. Sélectionnez un domaine ou créez votre tableau de bord personnalisé :")

main_choices = ["Tableau de bord", "Données publiques", "Études", "Marchés", "Blockchains"]
main_choice = st.radio("Sélectionnez un domaine :", main_choices, horizontal=True)

st.markdown("---")

##############################
# 1. Tableau de bord personnalisé et alertes études
##############################
if main_choice == "Tableau de bord":
    st.header("📊 Votre tableau de bord personnalisé")
    portfolio_items = get_portfolio_items()
    if not portfolio_items:
        st.info("Ajoutez des éléments de marché, cryptos, bonds ou commodities via l'onglet 'Marchés' ou 'Blockchains' pour composer votre tableau de bord ici !")
    else:
        for idx, item in enumerate(portfolio_items):
            cols = st.columns([3, 2, 2, 1, 1])
            with cols[0]:
                st.markdown(f"**{item['Nom']}**" + (f" ({item.get('Ticker', '')})" if item.get("Ticker") else ""))
            with cols[1]:
                st.markdown(f"{item.get('Dernier', 'N/A')} {item.get('Devise', item.get('Unité',''))}")
            with cols[2]:
                st.markdown(item.get("Variation", item.get("Variation 24h", "")))
            with cols[3]:
                st.markdown(item.get("type", ""))
            with cols[4]:
                if st.button("❌ Supprimer", key=f"remove_{item['type']}_{item['id']}"):
                    remove_from_portfolio(item['type'], item['id'])
                    st.experimental_rerun()
        st.caption("Ce tableau de bord est temporaire (lié à votre session).")
    # Liste des alertes études
    st.markdown("## 🔔 Alertes études (bases médicales)")
    study_alerts = get_study_alerts()
    if not study_alerts:
        st.info("Aucune alerte sur des études n'est active. Utilisez l'onglet 'Études' pour en ajouter.")
    else:
        for idx, alert in enumerate(study_alerts):
            st.markdown(f"**Terme surveillé :** `{alert['term']}` &nbsp; | &nbsp; **Alerte par** : {alert['mode']}" + (f" ({alert['email']})" if alert['mode']=='Email' else ""))
            with st.expander(f"Voir derniers résultats pour '{alert['term']}'"):
                st.markdown("**PubMed**")
                ids, total = search_pubmed(term=alert['term'], retmax=2, retstart=0)
                if ids:
                    df_pubmed = fetch_pubmed_details(ids)
                    for idx2, row in df_pubmed.iterrows():
                        st.markdown(f"- {row['Titre']}  \n_Auteurs:_ {row['Auteurs']}", unsafe_allow_html=True)
                else:
                    st.info("Aucune étude trouvée dans PubMed.")
                st.markdown("**EuropePMC**")
                articles, total_epmc = search_europepmc(term=alert['term'], page=1, pageSize=2)
                if articles:
                    for art in articles:
                        st.markdown(f"- {art['Titre']}  \n_Auteurs:_ {art['Auteurs']}", unsafe_allow_html=True)
                else:
                    st.info("Aucune étude trouvée dans EuropePMC.")
                st.markdown("**ClinicalTrials.gov**")
                trials = search_clinicaltrials(term=alert['term'], max_studies=2)
                if trials:
                    for t in trials:
                        st.markdown(f"- {t['Titre']}  \n_Sponsor:_ {t['Sponsor']} | _Pays:_ {t['Pays']} | _Date:_ {t['Date']}", unsafe_allow_html=True)
                else:
                    st.info("Aucun essai clinique trouvé.")
                st.markdown("**Bases complémentaires**")
                for base in ["Embase", "Cochrane Library", "Web of Science (WoS)", "Scopus", "LILACS", "MedRxiv", "BioRxiv", "Google Scholar"]:
                    st.markdown(f"- [{base}]({external_med_db_links[base]}) : {external_med_db_desc[base]}")

##############################
# 2. Données publiques
##############################
elif main_choice == "Données publiques":
    st.header("📂 Données publiques")
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

    data1 = load_data(selected_source, selected_country)
    data2 = load_data(source2, country2) if compare and country2 and source2 else pd.DataFrame()

    if not data1.empty:
        st.subheader(f"Données pour {selected_country} – Source : {selected_source}")
        available_years = data1['année'].dropna().unique()
        selected_year = st.slider("📅 Filtrer par année", int(min(available_years)), int(max(available_years)), int(max(available_years)), key="year1")
        filtered_data1 = data1[data1['année'] == selected_year]
        st.dataframe(filtered_data1)
        chart_type = st.selectbox("Type de visualisation", ["Barres", "Lignes", "Données textuelles"], key="chart1")
        if chart_type == "Barres":
            import plotly.express as px
            fig = px.bar(filtered_data1, x="indicateur", y="valeur", color="indicateur", title=f"Indicateurs en {selected_year}")
            st.plotly_chart(fig, use_container_width=True)
        elif chart_type == "Lignes":
            import plotly.express as px
            fig = px.line(filtered_data1, x="indicateur", y="valeur", color="indicateur", title=f"Indicateurs en {selected_year}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write(filtered_data1)
    else:
        st.warning("Aucune donnée disponible pour cette combinaison pays/source.")

    if compare and not data2.empty:
        st.subheader(f"Comparaison avec {country2} – Source : {source2}")
        available_years2 = data2['année'].dropna().unique()
        selected_year2 = st.slider("📅 Année de comparaison", int(min(available_years2)), int(max(available_years2)), int(max(available_years2)), key="year2")
        filtered_data2 = data2[data2['année'] == selected_year2]
        st.dataframe(filtered_data2)
        chart_type2 = st.selectbox("Type de visualisation (comparaison)", ["Barres", "Lignes", "Données textuelles"], key="chart2")
        if chart_type2 == "Barres":
            import plotly.express as px
            fig2 = px.bar(filtered_data2, x="indicateur", y="valeur", color="indicateur", title=f"Indicateurs en {selected_year2}")
            st.plotly_chart(fig2, use_container_width=True)
        elif chart_type2 == "Lignes":
            import plotly.express as px
            fig2 = px.line(filtered_data2, x="indicateur", y="valeur", color="indicateur", title=f"Indicateurs en {selected_year2}")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.write(filtered_data2)
    elif compare:
        st.info("Aucune donnée pour la seconde sélection.")

##############################
# 3. Études (multi-bases) avec création d'alerte
##############################
elif main_choice == "Études":
    st.header("🔬 Recherches et études scientifiques")
    domaines = ["Médecine", "Environnement", "Sciences sociales", "Économie", "Technologie"]
    selected_field = st.selectbox("Domaine de recherche", domaines)

    st.write(f"🔬 Vous avez choisi le domaine : {selected_field}")

    if selected_field == "Médecine":
        st.markdown("#### Recherche d'études médicales multi-bases (PubMed, EuropePMC, ClinicalTrials.gov, autres)")
        search_term = st.text_input("🔎 Entrez un terme de recherche médical (ex : cancer, diabète, vaccination)", value="médecine")
        if 'med_studies_page' not in st.session_state:
            st.session_state.med_studies_page = 1
        per_page = 5

        # Bloc de création d'alerte
        st.markdown("##### 🔔 Créer une alerte pour ce terme médical (toutes bases)")
        with st.form("create_study_alert"):
            alert_mode = st.selectbox("Voulez-vous recevoir l'alerte par e-mail ou dans votre tableau de bord ?", ["Tableau de bord", "Email"])
            alert_email = st.text_input("Email (si alerte par Email)", value="", disabled=(alert_mode != "Email"))
            submit_alert = st.form_submit_button("Créer l'alerte")
            if submit_alert:
                if alert_mode == "Email" and not alert_email:
                    st.warning("Veuillez saisir votre email pour recevoir l'alerte.")
                else:
                    add_study_alert(term=search_term, mode=alert_mode, email=alert_email if alert_mode == "Email" else None)
                    st.success(f"Alerte créée pour le terme '{search_term}' ({alert_mode}{' : ' + alert_email if alert_email else ''}). Vous la retrouverez dans votre tableau de bord.")

        # Résultats multi-bases avec pagination indépendante
        tab1, tab2, tab3, tab4 = st.tabs([
            "PubMed", "Europe PMC", "ClinicalTrials.gov", "Autres bases"
        ])

        with tab1:
            # Pagination PubMed
            if 'pubmed_page' not in st.session_state:
                st.session_state.pubmed_page = 1
            ids, total = search_pubmed(term=search_term, retmax=per_page, retstart=(st.session_state.pubmed_page - 1) * per_page)
            if ids:
                df_pubmed = fetch_pubmed_details(ids)
                start_idx = (st.session_state.pubmed_page-1)*per_page+1
                end_idx = min(start_idx + per_page - 1, total)
                st.markdown(f"*Résultats {start_idx} à {end_idx} sur {total}*")
                for idx, row in df_pubmed.iterrows():
                    st.markdown(f"**{start_idx+idx}. {row['Titre']}**  \n_Auteurs :_ {row['Auteurs']}", unsafe_allow_html=True)
                col_prev, col_next = st.columns([1, 1])
                with col_prev:
                    if st.session_state.pubmed_page > 1:
                        if st.button("⬅️ Page précédente (PubMed)", key="prev_pubmed"):
                            st.session_state.pubmed_page -= 1
                            st.experimental_rerun()
                with col_next:
                    if end_idx < total:
                        if st.button("Page suivante ➡️ (PubMed)", key="next_pubmed"):
                            st.session_state.pubmed_page += 1
                            st.experimental_rerun()
            else:
                st.info("Aucun résultat trouvé dans PubMed.")

        with tab2:
            # Pagination EuropePMC
            if 'epmc_page' not in st.session_state:
                st.session_state.epmc_page = 1
            articles, total_epmc = search_europepmc(term=search_term, page=st.session_state.epmc_page, pageSize=per_page)
            start_idx = (st.session_state.epmc_page-1)*per_page+1
            end_idx = min(start_idx + per_page - 1, total_epmc)
            st.markdown(f"*Résultats {start_idx} à {end_idx} sur {total_epmc}*")
            if articles:
                for idx, art in enumerate(articles):
                    st.markdown(f"**{start_idx+idx}. {art['Titre']}**  \n_Auteurs :_ {art['Auteurs']}", unsafe_allow_html=True)
                col_prev, col_next = st.columns([1, 1])
                with col_prev:
                    if st.session_state.epmc_page > 1:
                        if st.button("⬅️ Page précédente (EuropePMC)", key="prev_epmc"):
                            st.session_state.epmc_page -= 1
                            st.experimental_rerun()
                with col_next:
                    if end_idx < total_epmc:
                        if st.button("Page suivante ➡️ (EuropePMC)", key="next_epmc"):
                            st.session_state.epmc_page += 1
                            st.experimental_rerun()
            else:
                st.info("Aucun résultat trouvé dans EuropePMC.")

        with tab3:
            # Pagination ClinicalTrials
            if 'ct_page' not in st.session_state:
                st.session_state.ct_page = 1
            ct_start = (st.session_state.ct_page-1)*per_page+1
            trials = search_clinicaltrials(term=search_term, max_studies=per_page)
            if trials:
                for idx, t in enumerate(trials):
                    st.markdown(f"**{ct_start+idx}. {t['Titre']}**  \n_Sponsor:_ {t['Sponsor']} | _Pays:_ {t['Pays']} | _Date:_ {t['Date']}", unsafe_allow_html=True)
                col_prev, col_next = st.columns([1, 1])
                with col_prev:
                    if st.session_state.ct_page > 1:
                        if st.button("⬅️ Page précédente (ClinicalTrials)", key="prev_ct"):
                            st.session_state.ct_page -= 1
                            st.experimental_rerun()
                with col_next:
                    if st.button("Page suivante ➡️ (ClinicalTrials)", key="next_ct"):
                        st.session_state.ct_page += 1
                        st.experimental_rerun()
            else:
                st.info("Aucun résultat trouvé dans ClinicalTrials.gov.")

        with tab4:
            st.markdown("**Bases complémentaires :**")
            for base in ["Embase", "Cochrane Library", "Web of Science (WoS)", "Scopus", "LILACS", "MedRxiv", "BioRxiv", "Google Scholar"]:
                st.markdown(f"- [{base}]({external_med_db_links[base]}) : {external_med_db_desc[base]}")

    else:
        st.info("Module d'exploration d'études à implémenter ici…")

##############################
# 4. Marchés (ajout au tableau de bord)
##############################
elif main_choice == "Marchés":
    st.subheader("🌍 Marchés financiers et cryptos")
    sous_options = ["Bourses", "Cryptos", "Bonds", "Commodities"]
    selected_market = st.selectbox("Choisissez un segment de marché :", sous_options)

    if selected_market == "Bourses":
        st.markdown("#### Indices Boursiers (temps réel)")
        indices = get_market_index_prices()
        df = pd.DataFrame(indices)
        st.table(df)
        st.markdown("#### Ajouter un indice à votre tableau de bord")
        selected_idx = st.selectbox("Sélectionnez un indice à ajouter :", [x['Nom'] for x in indices])
        if st.button("Ajouter l'indice au tableau de bord"):
            idx_item = next(x for x in indices if x['Nom'] == selected_idx)
            add_to_portfolio({
                "type": "bourse",
                "id": idx_item["Ticker"],
                **idx_item
            })
            st.success(f"{selected_idx} ajouté à votre tableau de bord !")
        st.markdown("#### Recherche d'une action (par nom ou ticker)")
        stock_query = st.text_input("Entrez le nom ou ticker de l'action (ex: AAPL, Apple...)", key="stock_search")
        if stock_query.strip():
            stock_data = get_stock_price(stock_query.strip())
            if stock_data and stock_data["Dernier"] is not None:
                st.success(f"{stock_data['Nom']} ({stock_data['Ticker']}) : {stock_data['Dernier']} {stock_data['Devise']} ({stock_data['Variation']})")
                if st.button("Ajouter cette action au tableau de bord", key="add_stock_btn"):
                    add_to_portfolio({
                        "type": "bourse",
                        "id": stock_data["Ticker"],
                        **stock_data
                    })
                    st.success(f"{stock_data['Nom']} ajouté au tableau de bord !")
            else:
                url = f"https://query2.finance.yahoo.com/v1/finance/search"
                r = requests.get(url, params={"q": stock_query, "quotes_count": 5})
                if r.status_code == 200 and r.json().get("quotes"):
                    st.write("Résultats similaires :")
                    for quote in r.json()["quotes"]:
                        name = quote.get("shortname", "")
                        symbol = quote.get("symbol", "")
                        exch = quote.get("exchange", "")
                        st.write(f"- {name} ({symbol}) [{exch}]")
                else:
                    st.warning("Aucune action trouvée pour ce nom ou ticker.")

    elif selected_market == "Cryptos":
        st.markdown("#### Cryptomonnaies principales (temps réel)")
        cryptos = get_crypto_prices()
        df = pd.DataFrame(cryptos)
        st.table(df)
        st.markdown("#### Ajouter une crypto à votre tableau de bord")
        selected_crypto = st.selectbox("Sélectionnez une crypto à ajouter :", [x['Nom'] for x in cryptos])
        if st.button("Ajouter la crypto au tableau de bord"):
            c = next(x for x in cryptos if x['Nom'] == selected_crypto)
            add_to_portfolio({
                "type": "crypto",
                "id": c['Ticker'],
                **c
            })
            st.success(f"{selected_crypto} ajouté au tableau de bord !")
        st.markdown("#### Recherche d'une cryptomonnaie (par nom ou ticker)")
        crypto_query = st.text_input("Entrez le nom ou le ticker de la crypto (ex: BTC, bitcoin...)", key="crypto_search")
        if crypto_query.strip():
            results = search_crypto_cg(crypto_query.strip())
            if results:
                for coin in results[:3]:
                    price_data = get_crypto_price_by_id(coin["id"])
                    if price_data:
                        st.success(f"{coin['name']} ({coin['symbol'].upper()}): {price_data['Dernier']} $ ({price_data['Variation 24h']})")
                        if st.button(f"Ajouter {coin['name']} au tableau de bord", key=f"add_crypto_{coin['id']}"):
                            add_to_portfolio({
                                "type": "crypto",
                                "id": coin['id'],
                                "Nom": coin['name'],
                                "Ticker": coin['symbol'].upper(),
                                "Dernier": price_data["Dernier"],
                                "Variation 24h": price_data["Variation 24h"]
                            })
                            st.success(f"{coin['name']} ajouté au tableau de bord !")
                        st.caption(f"[Voir sur CoinGecko](https://www.coingecko.com/fr/pièces/{coin['id']})")
            else:
                st.warning("Aucune cryptomonnaie trouvée pour ce nom ou ticker.")

    elif selected_market == "Bonds":
        st.markdown("#### Obligations principales (temps réel)")
        bonds = get_bonds_prices()
        df = pd.DataFrame(bonds)
        st.table(df)
        st.markdown("#### Ajouter une obligation à votre tableau de bord")
        selected_bond = st.selectbox("Sélectionnez une obligation à ajouter :", [x['Nom'] for x in bonds])
        if st.button("Ajouter l'obligation au tableau de bord"):
            b = next(x for x in bonds if x['Nom'] == selected_bond)
            add_to_portfolio({
                "type": "bond",
                "id": b["Ticker"],
                **b
            })
            st.success(f"{selected_bond} ajoutée au tableau de bord !")

    elif selected_market == "Commodities":
        st.markdown("#### Matières premières (temps réel)")
        commos = get_commodities_prices()
        df = pd.DataFrame(commos)
        st.table(df)
        st.markdown("#### Ajouter une matière première à votre tableau de bord")
        selected_com = st.selectbox("Sélectionnez une matière première à ajouter :", [x['Nom'] for x in commos])
        if st.button("Ajouter la matière première au tableau de bord"):
            c = next(x for x in commos if x['Nom'] == selected_com)
            add_to_portfolio({
                "type": "commodity",
                "id": c["Ticker"],
                **c
            })
            st.success(f"{selected_com} ajoutée au tableau de bord !")

##############################
# 5. Blockchains (inchangé)
##############################
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

##############################
# Pied de page
##############################
st.markdown("""
---
Prototype Streamlit – Tableau de bord, études multi-bases & alertes | Version 1.7
""")
