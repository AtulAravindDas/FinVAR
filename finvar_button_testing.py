from yahooquery import Ticker
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import joblib
import sklearn

st.set_page_config(page_title="FinVAR", layout="centered")
model = joblib.load("final_eps_predictor.pkl")

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

@st.cache_data
def load_ticker_data(ticker_symbol):
    return Ticker(ticker_symbol)

@st.cache_data
def get_ticker_info(ticker_symbol):
    try:
        t = Ticker(ticker_symbol, timeout=5)
        return {
            "profile": t.asset_profile.get(ticker_symbol, {}),
            "summary": t.summary_detail.get(ticker_symbol, {}),
            "stats": t.key_stats.get(ticker_symbol, {}),
            "financials": t.financial_data.get(ticker_symbol, {}),
            "income": t.income_statement(frequency="a").get(ticker_symbol, {}).get('incomeStatementHistory', []),
            "balance": t.balance_sheet(frequency="a").get(ticker_symbol, {}).get('balanceSheetHistory', []),
            "cashflow": t.cash_flow(frequency="a").get(ticker_symbol, {}).get('cashflowStatementHistory', []),
            "history": t.history(period="1y")
        }
    except Exception as e:
        return {"error": str(e)}

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
        profile = info["profile"]

        if not profile:
            st.error("❌ Invalid ticker. Please try again.")
        else:
            company_name = profile.get('longBusinessSummary', 'N/A')
            st.success(f"Company: {company_name[:300]}...")
            st.subheader("📂 Select an Analysis Section:")

            st.button("📝 Show Description", on_click=lambda: set_page('description'))
            st.button("💰 Current Price", on_click=lambda: set_page('price'))
            st.button("📘 Profitability Ratios", on_click=lambda: set_page('profitability'))
            st.button("📈 Growth Overview", on_click=lambda: set_page('growth'))
            st.button("⚡ Leverage Overview", on_click=lambda: set_page('leverage'))
            st.button("💧 Liquidity & Dividend Overview", on_click=lambda: set_page('liquidity'))
            st.button("📉 Stock Price & Volatility", on_click=lambda: set_page('volatility'))
            st.button("🔮 Predict Next Year EPS", on_click=lambda: set_page('eps_prediction'))
            st.button("🧹 Fresh Start", on_click=fresh_start)

elif st.session_state.page == 'fresh':
    st.title("🧹 Fresh Start")
    st.success("You have refreshed the app! 🔄")
    st.button("🏠 Go to Home", on_click=go_home)

elif st.session_state.page == 'description':
    st.title("📝 Company Description")
    info = get_ticker_info(st.session_state.ticker)
    profile = info.get("profile", {})
    st.write(profile.get('longBusinessSummary', 'Description not available.'))
    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == 'price':
    st.title("💰 Current Price")
    info = get_ticker_info(st.session_state.ticker)
    summary = info.get("summary", {})
    price = summary.get("previousClose", 'N/A')
    market_cap = summary.get("marketCap", 'N/A')
    st.metric("Previous Close", f"${price}")
    st.metric("Market Cap", f"${market_cap}")
    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == 'profitability':
    st.title("📘 Profitability Ratios")
    info = get_ticker_info(st.session_state.ticker)
    financials = info.get("financials", {})
    roe = financials.get("returnOnEquity", 'N/A')
    roa = financials.get("returnOnAssets", 'N/A')
    margin = financials.get("profitMargins", 'N/A')
    st.write(f"**ROE:** {roe}")
    st.write(f"**ROA:** {roa}")
    st.write(f"**Profit Margin:** {margin}")
    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == 'growth':
    st.title("📈 Growth Overview")
    info = get_ticker_info(st.session_state.ticker)
    financials = info.get("financials", {})
    revenue = financials.get("totalRevenue", 'N/A')
    ebitda = financials.get("ebitda", 'N/A')
    st.write(f"**Revenue:** {revenue}")
    st.write(f"**EBITDA:** {ebitda}")
    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == 'leverage':
    st.title("⚡ Leverage Overview")
    info = get_ticker_info(st.session_state.ticker)
    financials = info.get("financials", {})
    debt_equity = financials.get("debtToEquity", 'N/A')
    st.write(f"**Debt to Equity:** {debt_equity}")
    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == 'liquidity':
    st.title("💧 Liquidity & Dividend Overview")
    info = get_ticker_info(st.session_state.ticker)
    financials = info.get("financials", {})
    current_ratio = financials.get("currentRatio", 'N/A')
    free_cash_flow = financials.get("freeCashflow", 'N/A')
    st.write(f"**Current Ratio:** {current_ratio}")
    st.write(f"**Free Cash Flow:** {free_cash_flow}")
    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == 'volatility':
    st.title("📉 Stock Price & Volatility")
    info = get_ticker_info(st.session_state.ticker)
    hist = info.get("history", pd.DataFrame())
    if not hist.empty:
        hist['Daily Return'] = hist['close'].pct_change()
        volatility = hist['Daily Return'].std() * np.sqrt(252)
        st.line_chart(hist['close'])
        st.subheader(f"Annualized Volatility: {volatility:.2%}")
    else:
        st.warning("No historical data available.")
    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == 'eps_prediction':
    st.title("🔮 Predict Next Year EPS")
    info = get_ticker_info(st.session_state.ticker)
    stats = info.get("stats", {})
    financials = info.get("financials", {})
    eps = stats.get("trailingEps", np.nan)
    roe = financials.get("returnOnEquity", np.nan)
    margin = financials.get("profitMargins", np.nan)
    debt_equity = financials.get("debtToEquity", np.nan)
    current_ratio = financials.get("currentRatio", np.nan)
    features = np.array([[eps, roe, margin, debt_equity, current_ratio]])
    features = np.nan_to_num(features)
    prediction = model.predict(features)[0]
    st.success(f"Predicted EPS: ${prediction:.2f}")
    st.button("⬅️ Back", on_click=go_app)
