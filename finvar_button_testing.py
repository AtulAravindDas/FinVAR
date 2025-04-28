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
    
