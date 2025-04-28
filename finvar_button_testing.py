import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import joblib
import sklearn

st.set_page_config(page_title="FinVAR", layout="centered")
model=joblib.load("final_eps_predictor.pkl")

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
    - **EPS Prediction Engine:** Trained ML model forecasts future EPS based on real-time financials.""")

   
    st.button("🚀 Enter FinVAR App", on_click=go_app)
elif st.session_state.page == 'app':
    st.title("🔍 FinVAR – Start Analysis")
    st.session_state.ticker = st.text_input("Enter a Stock Ticker (e.g., AAPL, MSFT):", value=st.session_state.ticker)

    if st.session_state.ticker:
        ticker = yf.Ticker(st.session_state.ticker)
        info = ticker.info

        if not info or 'longName' not in info:
            st.error("❌ Invalid ticker. Please try again.")
        else:
            company_name = info.get('longName', 'N/A')
            st.success(f"Company: {company_name}")

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
    ticker = yf.Ticker(st.session_state.ticker)
    description = ticker.info.get('longBusinessSummary', 'N/A')
    st.write(description)
    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == 'price':
    st.title("💰 Current Price")
    ticker = yf.Ticker(st.session_state.ticker)
    price = ticker.info.get('currentPrice', 'N/A')
    prev_close = ticker.info.get('previousClose', 'N/A')
    if price != 'N/A' and prev_close != 'N/A':
        change = price - prev_close
        pct_change = (change / prev_close) * 100
        st.metric("Current Price (USD)", f"${price:.2f}", f"{pct_change:+.2f}%")
    else:
        st.warning("Price data unavailable.")
    st.button("⬅️ Back", on_click=go_app)

    
