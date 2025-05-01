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
        if 'info' not in st.session_state.ticker_data_cache.get(st.session_state.ticker, {}):
            st.session_state.ticker_data_cache.setdefault(st.session_state.ticker, {})['info'] = get_ticker_info(st.session_state.ticker)
        info = st.session_state.ticker_data_cache[st.session_state.ticker]['info']

        if 'error' in info:
            st.error(f"Error fetching data: {info['error']}")
        else:
            st.success(f"Company: {info['longName']}")
            

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
            if st.button("📘 Profitability Ratios"):
                set_page('profitability')
            # More buttons can be added here as new sections are implemented
            if st.button("🧹 Fresh Start"):
                fresh_start()

elif st.session_state.page == 'description':
    st.title("📝 Company Description")
    info = st.session_state.ticker_data_cache[st.session_state.ticker]['info']
    if 'error' in info:
        st.error("⚠️ Unable to fetch company description. API issue.")
    else:
        st.markdown(f"**{info['description']}**")
    st.button("⬅️ Back", on_click=go_app)
  
elif st.session_state.page == 'price':
    st.title("💰 Current Stock Price")
    info = st.session_state.ticker_data_cache[st.session_state.ticker]['info']
    if 'error' in info:
        st.error("⚠️ Unable to fetch price data. API issue.")
    elif info['currentPrice'] is not None and info['previousClose'] is not None:
        change = info['currentPrice'] - info['previousClose']
        pct_change = (change / info['previousClose']) * 100
        st.metric("Current Price (USD)", f"${info['currentPrice']:.2f}", f"{pct_change:+.2f}%")
    else:
        st.warning("Price data not available.")
    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == 'profitability':
    st.title("📘 Profitability Ratios Overview")
    if 'financials' not in st.session_state.ticker_data_cache.get(st.session_state.ticker, {}):
        st.session_state.ticker_data_cache.setdefault(st.session_state.ticker, {})['financials'] = get_financials_with_fallback(st.session_state.ticker)
    income_df, balance_df, _, _ = st.session_state.ticker_data_cache[st.session_state.ticker]['financials']

    if income_df.empty or balance_df.empty:
        st.warning("⚠️ Financial data not available for this ticker.")
        st.button("⬅️ Back", on_click=go_app)
    else:
        df = pd.DataFrame()
        df['Net Income'] = income_df.loc['netIncome']
        df['Gross Profit'] = income_df.loc['grossProfit']
        df['Revenue'] = income_df.loc['revenue']
        df['EBITDA'] = income_df.loc['ebitda']
        df['EBIT'] = income_df.loc['operatingIncome']
        df['Equity'] = balance_df.loc['totalStockholdersEquity']
        df['Assets'] = balance_df.loc['totalAssets']
        df['Liabilities'] = balance_df.loc['totalLiabilities']

        df = df.dropna().T
        df.columns = df.columns.year
        df = df.T
        df = df.apply(pd.to_numeric, errors='coerce')

        df['ROE (%)'] = (df['Net Income'] / df['Equity']) * 100
        df['Gross Margin (%)'] = (df['Gross Profit'] / df['Revenue']) * 100
        df['Net Margin (%)'] = (df['Net Income'] / df['Revenue']) * 100
        df['Asset Turnover'] = df['Revenue'] / df['Assets']
        df['Financial Leverage'] = df['Assets'] / df['Equity']

        st.plotly_chart(px.line(df, x=df.index, y='ROE (%)', title='Return on Equity (%)', markers=True, template='plotly_dark'), use_container_width=True)
        st.plotly_chart(px.bar(df, x=df.index, y='Gross Margin (%)', title='Gross Profit Margin (%)', template='plotly_dark'), use_container_width=True)
        st.plotly_chart(px.line(df, x=df.index, y='Net Margin (%)', title='Net Profit Margin (%)', markers=True, template='plotly_dark'), use_container_width=True)
        st.plotly_chart(px.area(df, x=df.index, y='Asset Turnover', title='Asset Turnover', template='plotly_dark'), use_container_width=True)
        st.plotly_chart(px.scatter(df, x=df.index, y='Financial Leverage', title='Financial Leverage', size='Financial Leverage', template='plotly_dark'), use_container_width=True)
        latest_year = df.index.max()
        roe_latest = df.loc[latest_year, 'ROE (%)']
        gross_margin_latest = df.loc[latest_year, 'Gross Profit Margin (%)']
        net_margin_latest = df.loc[latest_year, 'Net Profit Margin (%)']
        asset_turnover_latest = df.loc[latest_year, 'Asset Turnover']
        summary_text = ""
        if roe_latest > 15:
            summary_text += f"✅ Strong ROE of {roe_latest:.2f}% indicates efficient use of equity.\n\n"
        else:
            summary_text += f"⚠️ ROE of {roe_latest:.2f}% is below ideal; check company's return generation.\n\n"
        if gross_margin_latest > 40:
            summary_text += f"✅ Excellent Gross Margin ({gross_margin_latest:.2f}%) suggests strong pricing power.\n\n"
        elif gross_margin_latest > 20:
            summary_text += f"✅ Moderate Gross Margin ({gross_margin_latest:.2f}%), acceptable for most industries.\n\n"
        else:
            summary_text += f"⚠️ Weak Gross Margin ({gross_margin_latest:.2f}%) — may face margin pressure.\n\n"
        if net_margin_latest > 10:
            summary_text += f"✅ Net Profit Margin of {net_margin_latest:.2f}% is healthy.\n\n"
        else:
            summary_text += f"⚠️ Thin Net Profit Margin ({net_margin_latest:.2f}%) could be a concern.\n\n"
        if asset_turnover_latest > 1:
            summary_text += f"✅ High Asset Turnover ({asset_turnover_latest:.2f}) — efficient asset use.\n\n"
        else:
            summary_text += f"⚠️ Low Asset Turnover ({asset_turnover_latest:.2f}) — inefficient use of assets.\n\n"
        st.subheader("🔍 FinVAR Summary: Profitability Overview")
        st.info(summary_text)

        st.button("⬅️ Back", on_click=go_app)

