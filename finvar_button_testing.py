import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import joblib
import requests

API_KEY = st.secrets["FMP_API_KEY"]
BASE_URL = "https://financialmodelingprep.com/api/v3"
model = joblib.load("final_eps_predictor.pkl")

if 'ticker_data_cache' not in st.session_state:
    st.session_state.ticker_data_cache = {}

@st.cache_data(ttl=3600)
def get_ticker_info(ticker_symbol):
    ticker_symbol = ticker_symbol.upper()
    if ticker_symbol in st.session_state.ticker_data_cache and 'info' in st.session_state.ticker_data_cache[ticker_symbol]:
        return st.session_state.ticker_data_cache[ticker_symbol]['info']

    try:
        profile_url = f"{BASE_URL}/profile/{ticker_symbol}?apikey={API_KEY}"
        quote_url = f"{BASE_URL}/quote/{ticker_symbol}?apikey={API_KEY}"
        profile_data = requests.get(profile_url).json()
        quote_data = requests.get(quote_url).json()

        if not profile_data or not quote_data:
            raise ValueError("Invalid data returned from FMP API.")

        profile = profile_data[0]
        quote = quote_data[0]

        info = {
            "longName": profile.get("companyName", "N/A"),
            "industry": profile.get("industry", "N/A"),
            "description": profile.get("description", "N/A"),
            "currentPrice": quote.get("price", None),
            "previousClose": quote.get("previousClose", None),
            "trailingPE": profile.get("pe", None),
            "epsTrailingTwelveMonths": profile.get("eps", None)
        }

        st.session_state.ticker_data_cache.setdefault(ticker_symbol, {})['info'] = info
        return info
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=3600)
def get_financials_with_fallback(ticker_symbol):
    ticker_symbol = ticker_symbol.upper()
    if ticker_symbol in st.session_state.ticker_data_cache and 'financials' in st.session_state.ticker_data_cache[ticker_symbol]:
        return st.session_state.ticker_data_cache[ticker_symbol]['financials']

    try:
        income_url = f"{BASE_URL}/income-statement/{ticker_symbol}?limit=5&apikey={API_KEY}"
        balance_url = f"{BASE_URL}/balance-sheet-statement/{ticker_symbol}?limit=5&apikey={API_KEY}"
        cashflow_url = f"{BASE_URL}/cash-flow-statement/{ticker_symbol}?limit=5&apikey={API_KEY}"

        income_df = pd.DataFrame(requests.get(income_url).json()).set_index("date").T
        balance_df = pd.DataFrame(requests.get(balance_url).json()).set_index("date").T
        cashflow_df = pd.DataFrame(requests.get(cashflow_url).json()).set_index("date").T
        history_df = pd.DataFrame()

        for df in [income_df, balance_df, cashflow_df]:
            df.columns = pd.to_datetime(df.columns)
            df = df.apply(pd.to_numeric, errors='coerce')

        result = (income_df, balance_df, cashflow_df, history_df)
        st.session_state.ticker_data_cache.setdefault(ticker_symbol, {})['financials'] = result
        return result
    except Exception as e:
        return (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

st.set_page_config(page_title="FinVAR", layout="centered")

if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'ticker' not in st.session_state:
    st.session_state.ticker = ''

def go_home():
    st.session_state.page = 'home'

def go_app():
    st.session_state.page = 'app'

def set_page(name):
    st.session_state.page = name

def fresh_start():
    st.session_state.ticker = ''
    st.session_state.page = 'fresh'

if st.session_state.page == 'home':
    st.image("FinVAR.png", width=300)
    st.title("📊 FinVAR – Financial Assistant Referee")
    st.markdown("""
    Your financial assistant referee – reviewing every ticker, flagging every risk.

    🧠 **Understand the market.**  
    🚨 **Flag the risks.**  
    💼 **Make smarter investment moves.**
    ---
    ## 🚀 What is FinVAR?
    FinVAR is a financial visualization and analysis tool that not only presents key profitability, growth, leverage, and liquidity metrics, but also uses Machine Learning to predict the future Earnings Per Share (EPS) of companies — helping investors and analysts make better-informed decisions.

    ---
    ## 📈 Key Features
    - **Company Insights:** Real-time company descriptions and financials.
    - **Profitability Overview:** ROE, Gross Margin, Net Margin, Asset Turnover, Financial Leverage.
    - **Growth Overview:** Revenue Growth and EBITDA Growth visualization.
    - **Leverage and Liquidity Overview:** Debt Ratios and Free Cash Flow.
    - **Stock Price and Volatility Analysis:** 1-year trend analysis and volatility.
    - **EPS Prediction Engine:** Trained ML model forecasts future EPS based on real-time financials.
    ---
    Click the button below to start!""")
    st.button("🚀 Enter FinVAR App", on_click=go_app)

elif st.session_state.page == 'app':
    st.title("🔍 FinVAR – Start Analysis")
    st.session_state.ticker = st.text_input("Enter a Stock Ticker (e.g., AAPL, MSFT):", value=st.session_state.ticker)

    if st.session_state.ticker:
        info = get_ticker_info(st.session_state.ticker)

        if 'error' in info:
            st.error(f"Error fetching data: {info['error']}")
        else:
            st.success(f"Company: {info['longName']}")
            st.write("Sector:", info.get("industry", "N/A"))
            st.write("📘 Description:", info.get("description", "N/A"))

            if info['currentPrice'] is not None and info['previousClose'] is not None:
                change = info['currentPrice'] - info['previousClose']
                pct = (change / info['previousClose']) * 100 if info['previousClose'] != 0 else 0
                st.metric("Price", f"${info['currentPrice']:.2f}", f"{pct:+.2f}%")
            else:
                st.warning("Price data unavailable.")

            st.subheader("📂 Select an Analysis Section:")
            if st.button("📝 Show Description"):
                set_page('description')
            if st.button("💰 Current Price"):
                set_page('price')
            # More buttons can be added here as new sections are implemented
            if st.button("🧹 Fresh Start"):
                fresh_start()

elif st.session_state.page == 'description':
    st.title("📝 Company Description")
    info = get_ticker_info(st.session_state.ticker)
    if 'error' in info:
        st.error("⚠️ Unable to fetch company description. API issue.")
    else:
        st.markdown(f"**{info['description']}**")
    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == 'price':
    st.title("💰 Current Stock Price")
    info = get_ticker_info(st.session_state.ticker)
    if 'error' in info:
        st.error("⚠️ Unable to fetch price data. API issue.")
    elif info['currentPrice'] is not None and info['previousClose'] is not None:
        change = info['currentPrice'] - info['previousClose']
        pct_change = (change / info['previousClose']) * 100
        st.metric("Current Price (USD)", f"${info['currentPrice']:.2f}", f"{pct_change:+.2f}%")
    else:
        st.warning("Price data not available.")
    st.button("⬅️ Back", on_click=go_app)
