import finnhub
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import joblib

# Initialize Finnhub client with secure API key
finnhub_client = finnhub.Client(api_key=st.secrets["finnhub_api_key"])
model = joblib.load("final_eps_predictor.pkl")

# Reset ticker cache
if 'ticker_data_cache' not in st.session_state:
    st.session_state.ticker_data_cache = {}

# Cache company info (profile + quote) for a ticker
@st.cache_data(ttl=3600)
def get_ticker_info(ticker_symbol):
    ticker_symbol = ticker_symbol.upper()
    if ticker_symbol in st.session_state.ticker_data_cache and 'info' in st.session_state.ticker_data_cache[ticker_symbol]:
        return st.session_state.ticker_data_cache[ticker_symbol]['info']

    try:
        profile = finnhub_client.company_profile2(symbol=ticker_symbol)
        quote = finnhub_client.quote(symbol=ticker_symbol)

        info = {
            "longName": profile.get("name", "N/A"),
            "industry": profile.get("finnhubIndustry", "N/A"),
            "description": f"{profile.get('name', 'This company')} is a company in the {profile.get('finnhubIndustry', 'N/A')} sector, headquartered in {profile.get('country', 'an unknown location')}.",
            "currentPrice": quote.get("c", None),
            "previousClose": quote.get("pc", None),
            "trailingPE": None,
            "epsTrailingTwelveMonths": None
        }

        if ticker_symbol not in st.session_state.ticker_data_cache:
            st.session_state.ticker_data_cache[ticker_symbol] = {}

        st.session_state.ticker_data_cache[ticker_symbol]['info'] = info
        return info
    except Exception as e:
        return {"error": str(e)}

# Fetch and cache financial statements
@st.cache_data(ttl=3600)
def get_financials_with_fallback(ticker_symbol):
    ticker_symbol = ticker_symbol.upper()
    if ticker_symbol in st.session_state.ticker_data_cache and 'financials' in st.session_state.ticker_data_cache[ticker_symbol]:
        return st.session_state.ticker_data_cache[ticker_symbol]['financials']

    try:
        # Annual financials
        inc_stmt = finnhub_client.financials(symbol=ticker_symbol, statement='ic', freq='annual')
        bal_stmt = finnhub_client.financials(symbol=ticker_symbol, statement='bs', freq='annual')
        cf_stmt = finnhub_client.financials(symbol=ticker_symbol, statement='cf', freq='annual')

        def convert_to_df(data):
            df = pd.DataFrame(data.get("financials", []))
            if not df.empty:
                df = df.set_index("year").T
                df.columns = pd.to_datetime(df.columns, format='%Y')
                df = df.apply(pd.to_numeric, errors='coerce')
            return df

        income_df = convert_to_df(inc_stmt)
        balance_df = convert_to_df(bal_stmt)
        cashflow_df = convert_to_df(cf_stmt)
        history_df = pd.DataFrame()

        result = (income_df, balance_df, cashflow_df, history_df)

        if ticker_symbol not in st.session_state.ticker_data_cache:
            st.session_state.ticker_data_cache[ticker_symbol] = {}

        st.session_state.ticker_data_cache[ticker_symbol]['financials'] = result
        return result

    except Exception as e:
        return (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

# Main App Interface
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
    st.session_state.ticker = st.text_input("Enter a Stock Ticker (e.g., AAPL):", value=st.session_state.ticker)

    if st.session_state.ticker:
        if 'info' not in st.session_state.ticker_data_cache.get(st.session_state.ticker, {}):
            st.session_state.ticker_data_cache[st.session_state.ticker] = st.session_state.ticker_data_cache.get(st.session_state.ticker, {})
            st.session_state.ticker_data_cache[st.session_state.ticker]['info'] = get_ticker_info(st.session_state.ticker)
        info = st.session_state.ticker_data_cache[st.session_state.ticker]['info']
        if "error" in info:
            st.error(f"Error: {info['error']}")
            st.stop()

        st.success(f"Company: {info['longName']}")
        st.write("Sector:", info["industry"])
        st.write("📘 Description:", info["description"])

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
        if st.button("📈 Growth Overview"):
            set_page('growth')
        if st.button("⚡ Leverage Overview"):
            set_page('leverage')
        if st.button("💧 Liquidity & Dividend Overview"):
            set_page('liquidity')
        if st.button("📉 Stock Price & Volatility"):
            set_page('volatility')
        if st.button("🔮 Predict Next Year EPS"):
            set_page('eps_prediction')
        if st.button("🧹 Fresh Start"):
            fresh_start()

elif st.session_state.page == 'fresh':
    st.title("🧹 Fresh Start")
    st.success("You have refreshed the app! 🔄")
    st.button("🏠 Go to Home", on_click=go_home)

elif st.session_state.page == 'description':
    st.title("📝 Company Description")
    info = st.session_state.ticker_data_cache[st.session_state.ticker]['info']
    
    if "error" in info:
        st.error("⚠️ Unable to fetch company description. Rate limit or error occurred.")
        st.stop()
    description = info.get('description', 'N/A')
    st.write(description)
    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == 'price':
    st.subheader("💰 Current Price")
    info = st.session_state.ticker_data_cache[st.session_state.ticker]['info']

    if info['currentPrice'] is not None and info['previousClose'] is not None:
        change = info['currentPrice'] - info['previousClose']
        pct = (change / info['previousClose']) * 100 if info['previousClose'] != 0 else 0
        st.metric("Current Price (USD)", f"${info['currentPrice']:.2f}", f"{pct:+.2f}%")
    else:
        st.warning("⚠️ Price data unavailable.")

    st.button("⬅️ Back", on_click=go_app)
    
elif st.session_state.page == 'profitability':
    st.subheader("📘 Profitability Ratios Overview")

    income, balance, _, _ = get_financials_with_fallback(st.session_state.ticker)
    income = income.rename(index=lambda x: x.lower())
    balance = balance.rename(index=lambda x: x.lower())

    required_income = ["revenue", "grossprofit", "ebitda", "ebit", "netincome"]
    required_balance = ["totalassets", "totalequity", "totalliabilities"]

    # Filter and align
    income = income.loc[[col for col in income.index if col in required_income]]
    balance = balance.loc[[col for col in balance.index if col in required_balance]]

    income = income.T
    balance = balance.T

    df = pd.DataFrame()
    df['Net Income'] = income.loc['netIncome']
    df['Gross Profit'] = income.loc['grossProfit']
    df['Total Revenue'] = income.loc['revenue']
    df['EBITDA'] = income.loc['ebitda']
    df['EBIT'] = income.loc['ebit']
    df['Shareholders Equity'] = balance.loc['totalequity']
    df['Total Assets'] = balance.loc['totalassets']
    df['Total Liabilities'] = balance.loc['totalliabilities']

    df = df.dropna().apply(pd.to_numeric, errors='coerce').dropna()
    df.index = df.index.year

    # Ratio calculations
    df['ROE (%)'] = (df['Net Income'] / df['Shareholders Equity']) * 100
    df['Gross Profit Margin (%)'] = (df['Gross Profit'] / df['Total Revenue']) * 100
    df['Asset Turnover'] = df['Total Revenue'] / df['Total Assets']
    df['Financial Leverage'] = df['Total Assets'] / df['Shareholders Equity']
    df['Net Profit Margin (%)'] = (df['Net Income'] / df['Total Revenue']) * 100

    st.subheader("📈 Interactive Financial Visuals")
    st.plotly_chart(px.line(df, x=df.index, y="ROE (%)", markers=True, title="Return on Equity (%)", template="plotly_dark"), use_container_width=True)
    st.plotly_chart(px.bar(df, x=df.index, y="Gross Profit Margin (%)", title="Gross Profit Margin (%)", template="plotly_dark"), use_container_width=True)
    st.plotly_chart(px.area(df, x=df.index, y="Asset Turnover", title="Asset Turnover", template="plotly_dark"), use_container_width=True)
    st.plotly_chart(px.scatter(df, x=df.index, y="Financial Leverage", size="Financial Leverage", title="Financial Leverage", template="plotly_dark"), use_container_width=True)
    st.plotly_chart(px.bar(df, x=df.index.astype(str), y="Net Profit Margin (%)", title="Net Profit Margin (%)", template="plotly_dark"), use_container_width=True)
    st.plotly_chart(px.line(df, x=df.index, y=["EBITDA", "EBIT"], markers=True, title="EBITDA vs EBIT", template="plotly_dark"), use_container_width=True)

    # Summary
    latest_year = df.index.max()
    summary_text = ""

    if df.loc[latest_year, 'ROE (%)'] > 15:
        summary_text += f"✅ Strong ROE of {df.loc[latest_year, 'ROE (%)']:.2f}% indicates efficient use of equity.\n\n"
    else:
        summary_text += f"⚠️ ROE of {df.loc[latest_year, 'ROE (%)']:.2f}% is below ideal.\n\n"

    if df.loc[latest_year, 'Gross Profit Margin (%)'] > 40:
        summary_text += f"✅ Excellent Gross Margin ({df.loc[latest_year, 'Gross Profit Margin (%)']:.2f}%).\n\n"
    elif df.loc[latest_year, 'Gross Profit Margin (%)'] > 20:
        summary_text += f"✅ Moderate Gross Margin ({df.loc[latest_year, 'Gross Profit Margin (%)']:.2f}%).\n\n"
    else:
        summary_text += f"⚠️ Weak Gross Margin ({df.loc[latest_year, 'Gross Profit Margin (%)']:.2f}%).\n\n"

    if df.loc[latest_year, 'Net Profit Margin (%)'] > 10:
        summary_text += f"✅ Healthy Net Profit Margin ({df.loc[latest_year, 'Net Profit Margin (%)']:.2f}%).\n\n"
    else:
        summary_text += f"⚠️ Thin Net Profit Margin ({df.loc[latest_year, 'Net Profit Margin (%)']:.2f}%).\n\n"

    if df.loc[latest_year, 'Asset Turnover'] > 1:
        summary_text += f"✅ High Asset Turnover ({df.loc[latest_year, 'Asset Turnover']:.2f}).\n\n"
    else:
        summary_text += f"⚠️ Low Asset Turnover ({df.loc[latest_year, 'Asset Turnover']:.2f}).\n\n"

    st.subheader("🔍 FinVAR Summary: Profitability Overview")
    st.info(summary_text)
    st.button("⬅️ Back", on_click=go_app)

