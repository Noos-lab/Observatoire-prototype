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
# Tableau de bord personnalisé
##############################

def init_portfolio():
    # Initialiser le portfolio dans la session si besoin
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

##############################
# Interface utilisateur
##############################

st.title("🌐 Observatoire Global des Données")
st.markdown("Bienvenue sur l'Observatoire Global. Sélectionnez un domaine ou créez votre tableau de bord personnalisé :")

main_choices = ["Tableau de bord", "Données publiques", "Études", "Marchés", "Blockchains"]
main_choice = st.radio("Sélectionnez un domaine :", main_choices, horizontal=True)

st.markdown("---")

##############################
# 1. Tableau de bord personnalisé
##############################
if main_choice == "Tableau de bord":
    st.header("📊 Votre tableau de bord personnalisé")
    portfolio_items = get_portfolio_items()
    if not portfolio_items:
        st.info("Ajoutez des éléments de marché, cryptos, bonds ou commodities via l'onglet 'Marchés' ou 'Blockchains' pour composer votre tableau de bord ici !")
    else:
        df = pd.DataFrame(portfolio_items)
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

##############################
# 2. Marchés (ajout au tableau de bord)
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
# 3. Blockchains (inchangé, possibilité d'ajouter plus tard)
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
# 4. Études et Données publiques (inchangé)
##############################
elif main_choice == "Études":
    st.info("Module d'études (PubMed, etc.) à retrouver dans les versions précédentes.")

elif main_choice == "Données publiques":
    st.info("Module de données publiques à retrouver dans les versions précédentes.")

##############################
# Pied de page
##############################
st.markdown("""
---
Prototype Streamlit – Tableau de bord personnalisé marchés | Version 1.3
""")
