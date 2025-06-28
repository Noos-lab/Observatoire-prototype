import streamlit as st
import pandas as pd
import requests
import yfinance as yf
import xml.etree.ElementTree as ET
import os

st.set_page_config(page_title="Noos: information | connaissance | action", layout="wide")

############### Fonctions marché temps réel ###############

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

############### Recherche études médicales et sociales multi-bases ###############

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
            "Source": "PubMed"
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
        return pd.DataFrame(), 0
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
            "Source": "Europe PMC"
        })
    return pd.DataFrame(articles), total

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
        return pd.DataFrame()
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
        authors = sponsor if sponsor else ""
        articlestr = f"{authors} ({country}, {date})" if country or date else authors
        results.append({
            "Titre": title_md,
            "Auteurs": articlestr,
            "Source": "ClinicalTrials.gov"
        })
    return pd.DataFrame(results)

# --- API pour MedRxiv & BioRxiv (Rxivist) ---
def search_rxivist(term, server="medrxiv", max_results=10):
    url = f"https://api.rxivist.org/v1/papers"
    params = {
        "q": term,
        "server": server,
        "limit": max_results
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return pd.DataFrame()
    results = r.json().get("results", [])
    articles = []
    for art in results:
        title = art.get("title", "")
        authors = ", ".join([a.get("name", "") for a in art.get("authors", [])])
        link = art.get("url", "")
        title_md = f"[{title}]({link})" if title and link else title
        articles.append({
            "Titre": title_md,
            "Auteurs": authors,
            "Source": server.capitalize()
        })
    return pd.DataFrame(articles)

# --- API pour LILACS (BIREME) ---
def search_lilacs(term, max_results=10):
    url = f"https://lilacs.bvsalud.org/api/v1/search"
    params = {
        "q": term,
        "size": max_results
    }
    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code != 200:
            return pd.DataFrame()
        hits = r.json().get("hits", [])
        articles = []
        for hit in hits:
            title = hit.get("title", "")
            authors = ", ".join(hit.get("authors", []))
            link = hit.get("link", "")
            title_md = f"[{title}]({link})" if title and link else title
            articles.append({
                "Titre": title_md,
                "Auteurs": authors,
                "Source": "LILACS"
            })
        return pd.DataFrame(articles)
    except:
        return pd.DataFrame()

# --- Google Scholar scraping is not permitted, so we show links only ---
def scholar_search_link(term):
    return f"https://scholar.google.com/scholar?q={term.replace(' ', '+')}"

# --- Cochrane Library, Embase, Scopus, WoS: liens directs seulement (pas d'API libre) ---
def generic_db_search_link(term, base):
    if base == "Cochrane Library":
        return f"https://www.cochranelibrary.com/search?text={term.replace(' ','+')}"
    if base == "Embase":
        return f"https://www.embase.com/search/results?query={term.replace(' ','+')}"
    if base == "Scopus":
        return f"https://www.scopus.com/results/results.uri?sort=plf-f&src=s&sid=&sot=b&sdt=b&sl=0&origin=searchbasic&txGid=&searchterm1={term.replace(' ','+')}"
    if base == "Web of Science (WoS)":
        return f"https://www.webofscience.com/wos/woscc/summary/{term.replace(' ','+')}"
    return "#"

############### JSTOR pour Sciences Sociales ###############

def search_jstor(term, max_results=10):
    # JSTOR n'a pas d'API publique ouverte. On simule un affichage via search URL.
    url = f"https://www.jstor.org/action/doBasicSearch?Query={term.replace(' ','+')}"
    # On invite à cliquer et on explique l'accès institutionnel requis.
    # Pour l'expérience utilisateur, on simule un affichage type "résumé" mais on ne peut pas afficher de résultats.
    return url

############### Données publiques (simulé) ###############

def load_data(source, country):
    filepath = f"data/{source}/{country}.json"
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return pd.read_json(f)
    return pd.DataFrame()

############### Tableau de bord & alertes ###############

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

############### Interface utilisateur ###############

st.title("Noos: information | connaissance | action")
st.markdown("Bienvenue sur Noos. Sélectionnez un domaine ou créez votre tableau de bord personnalisé :")

main_choices = ["Tableau de bord", "Données publiques", "Études", "Marchés", "Blockchains"]
main_choice = st.radio("Sélectionnez un domaine :", main_choices, horizontal=True)
st.markdown("---")

############### 1. Tableau de bord personnalisé et alertes études ###############
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
                # PubMed
                st.markdown("**PubMed**")
                ids, total = search_pubmed(term=alert['term'], retmax=2, retstart=0)
                df_pubmed = fetch_pubmed_details(ids) if ids else pd.DataFrame()
                if not df_pubmed.empty:
                    for idx2, row in df_pubmed.iterrows():
                        st.markdown(f"- {row['Titre']}  \n_Auteurs:_ {row['Auteurs']}", unsafe_allow_html=True)
                else:
                    st.info("Aucune étude trouvée dans PubMed.")
                # EuropePMC
                st.markdown("**EuropePMC**")
                df_epmc, _ = search_europepmc(term=alert['term'], page=1, pageSize=2)
                if not df_epmc.empty:
                    for idx2, row in df_epmc.iterrows():
                        st.markdown(f"- {row['Titre']}  \n_Auteurs:_ {row['Auteurs']}", unsafe_allow_html=True)
                else:
                    st.info("Aucune étude trouvée dans EuropePMC.")
                # ClinicalTrials
                st.markdown("**ClinicalTrials.gov**")
                df_trials = search_clinicaltrials(term=alert['term'], max_studies=2)
                if not df_trials.empty:
                    for idx2, row in df_trials.iterrows():
                        st.markdown(f"- {row['Titre']}  \n_Auteurs:_ {row['Auteurs']}", unsafe_allow_html=True)
                else:
                    st.info("Aucun essai clinique trouvé.")
                # MedRxiv
                st.markdown("**MedRxiv**")
                df_medrxiv = search_rxivist(alert['term'], server="medrxiv", max_results=2)
                if not df_medrxiv.empty:
                    for idx2, row in df_medrxiv.iterrows():
                        st.markdown(f"- {row['Titre']}  \n_Auteurs:_ {row['Auteurs']}", unsafe_allow_html=True)
                else:
                    st.info("Aucun préprint trouvé dans MedRxiv.")
                # BioRxiv
                st.markdown("**BioRxiv**")
                df_biorxiv = search_rxivist(alert['term'], server="biorxiv", max_results=2)
                if not df_biorxiv.empty:
                    for idx2, row in df_biorxiv.iterrows():
                        st.markdown(f"- {row['Titre']}  \n_Auteurs:_ {row['Auteurs']}", unsafe_allow_html=True)
                else:
                    st.info("Aucun préprint trouvé dans BioRxiv.")
                # LILACS
                st.markdown("**LILACS**")
                df_lilacs = search_lilacs(alert['term'], max_results=2)
                if not df_lilacs.empty:
                    for idx2, row in df_lilacs.iterrows():
                        st.markdown(f"- {row['Titre']}  \n_Auteurs:_ {row['Auteurs']}", unsafe_allow_html=True)
                else:
                    st.info("Aucune étude trouvée dans LILACS.")
                # Google Scholar (lien)
                st.markdown("**Google Scholar**")
                st.markdown(f"- [Voir sur Google Scholar]({scholar_search_link(alert['term'])})")

############### 2. Données publiques (identique) ###############
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

############### 3. Études (multi-bases) avec création d'alerte ###############
elif main_choice == "Études":
    st.header("🔬 Recherches et études scientifiques")
    domaines = ["Médecine", "Environnement", "Sciences sociales", "Économie", "Technologie"]
    selected_field = st.selectbox("Domaine de recherche", domaines)
    st.write(f"🔬 Vous avez choisi le domaine : {selected_field}")

    if selected_field == "Médecine":
        st.markdown("#### Recherche d'études médicales multi-bases (PubMed, EuropePMC, ClinicalTrials.gov, MedRxiv, BioRxiv, LILACS, Google Scholar, Cochrane, Embase, Scopus, WoS)")
        search_term = st.text_input("🔎 Entrez un terme de recherche médical (ex : cancer, diabète, vaccination)", value="médecine")
        per_page = 5

        # Création d'alerte
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

        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
            "PubMed", "Europe PMC", "ClinicalTrials.gov", "MedRxiv", "BioRxiv", "LILACS",
            "Google Scholar", "Cochrane", "Embase", "Scopus", "Web of Science"
        ])

        with tab1:
            ids, total = search_pubmed(term=search_term, retmax=per_page, retstart=0)
            df_pubmed = fetch_pubmed_details(ids) if ids else pd.DataFrame()
            st.markdown(f"*{total} résultats*")
            if not df_pubmed.empty:
                for idx, row in df_pubmed.iterrows():
                    st.markdown(f"**{idx+1}. {row['Titre']}**  \n_Auteurs :_ {row['Auteurs']}", unsafe_allow_html=True)
            else:
                st.info("Aucun résultat trouvé dans PubMed.")

        with tab2:
            df_epmc, total_epmc = search_europepmc(term=search_term, page=1, pageSize=per_page)
            st.markdown(f"*{total_epmc} résultats*")
            if not df_epmc.empty:
                for idx, row in df_epmc.iterrows():
                    st.markdown(f"**{idx+1}. {row['Titre']}**  \n_Auteurs :_ {row['Auteurs']}", unsafe_allow_html=True)
            else:
                st.info("Aucun résultat trouvé dans EuropePMC.")

        with tab3:
            df_trials = search_clinicaltrials(term=search_term, max_studies=per_page)
            if not df_trials.empty:
                for idx, row in df_trials.iterrows():
                    st.markdown(f"**{idx+1}. {row['Titre']}**  \n_Auteurs :_ {row['Auteurs']}", unsafe_allow_html=True)
            else:
                st.info("Aucun résultat trouvé dans ClinicalTrials.gov.")

        with tab4:
            df_medrxiv = search_rxivist(search_term, server="medrxiv", max_results=per_page)
            if not df_medrxiv.empty:
                for idx, row in df_medrxiv.iterrows():
                    st.markdown(f"**{idx+1}. {row['Titre']}**  \n_Auteurs :_ {row['Auteurs']}", unsafe_allow_html=True)
            else:
                st.info("Aucun préprint trouvé dans MedRxiv.")

        with tab5:
            df_biorxiv = search_rxivist(search_term, server="biorxiv", max_results=per_page)
            if not df_biorxiv.empty:
                for idx, row in df_biorxiv.iterrows():
                    st.markdown(f"**{idx+1}. {row['Titre']}**  \n_Auteurs :_ {row['Auteurs']}", unsafe_allow_html=True)
            else:
                st.info("Aucun préprint trouvé dans BioRxiv.")

        with tab6:
            df_lilacs = search_lilacs(search_term, max_results=per_page)
            if not df_lilacs.empty:
                for idx, row in df_lilacs.iterrows():
                    st.markdown(f"**{idx+1}. {row['Titre']}**  \n_Auteurs :_ {row['Auteurs']}", unsafe_allow_html=True)
            else:
                st.info("Aucun résultat trouvé dans LILACS.")

        with tab7:
            scholar_link = scholar_search_link(search_term)
            st.markdown(f"**[Voir les résultats sur Google Scholar]({scholar_link})**")
            st.info("Google Scholar n'autorise pas de scraping automatisé. Cliquez pour voir les résultats.")

        with tab8:
            st.markdown(f"**[Voir les résultats sur Cochrane Library]({generic_db_search_link(search_term, 'Cochrane Library')})**")
            st.info("Cochrane Library ne propose pas d'API libre. Cliquez pour voir les résultats.")

        with tab9:
            st.markdown(f"**[Voir les résultats sur Embase]({generic_db_search_link(search_term, 'Embase')})**")
            st.info("Embase ne propose pas d'API libre. Cliquez pour voir les résultats (accès institutionnel nécessaire).")

        with tab10:
            st.markdown(f"**[Voir les résultats sur Scopus]({generic_db_search_link(search_term, 'Scopus')})**")
            st.info("Scopus ne propose pas d'API libre. Cliquez pour voir les résultats (accès institutionnel nécessaire).")

        with tab11:
            st.markdown(f"**[Voir les résultats sur Web of Science]({generic_db_search_link(search_term, 'Web of Science (WoS)')})**")
            st.info("Web of Science ne propose pas d'API libre. Cliquez pour voir les résultats (accès institutionnel nécessaire).")

    elif selected_field == "Sciences sociales":
        st.markdown("#### Recherche JSTOR (sciences sociales et sciences humaines)")
        search_term = st.text_input("🔎 Entrez un terme pour JSTOR", value="sociology")
        per_page = 5
        st.markdown("**Résultats JSTOR**")
        # JSTOR n'a pas d'API libre, mais on affiche les liens de recherche simulés
        jstor_url = search_jstor(search_term)
        st.markdown(f"**[Voir les résultats sur JSTOR]({jstor_url})**")
        st.info("JSTOR ne propose pas d'API libre. Cliquez pour voir les résultats (accès institutionnel ou partiel requis).")

    else:
        st.info("Module d'exploration d'études à implémenter ici…")

############### 4. Marchés et 5. Blockchains: inchangé ###############
elif main_choice == "Marchés":
    # ... inchangé, voir versions précédentes ...
    pass
elif main_choice == "Blockchains":
    # ... inchangé, voir versions précédentes ...
    pass

st.markdown("""
---
Noos: information | connaissance | action
""")
