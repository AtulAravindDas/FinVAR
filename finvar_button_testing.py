import finnhub
import streamlit as st
import pandas as pd
import numpy as np

# Initialize Finnhub client with secure API key
finnhub_client = finnhub.Client(api_key=st.secrets["finnhub_api_key"])

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
            "longBusinessSummary": profile.get("finnhubIndustry", "N/A"),
            "currentPrice": quote.get("c", None),
            "previousClose": quote.get("pc", None),
            "trailingPE": None,  # Optional: use additional API for fundamentals
            "epsTrailingTwelveMonths": None  # Optional: fetch from earnings endpoint
        }

        if ticker_symbol not in st.session_state.ticker_data_cache:
            st.session_state.ticker_data_cache[ticker_symbol] = {}

        st.session_state.ticker_data_cache[ticker_symbol]['info'] = info
        return info
    except Exception as e:
        return {"error": str(e)}

# Example usage inside Streamlit
st.title("FinVAR Finnhub Test")
ticker = st.text_input("Enter a Stock Ticker (e.g., AAPL):")

if ticker:
    info = get_ticker_info(ticker)
    if "error" in info:
        st.error(f"Error: {info['error']}")
    else:
        st.success(f"Company: {info['longName']}")
        st.write("Sector/Industry:", info["longBusinessSummary"])
        if info['currentPrice'] is not None and info['previousClose'] is not None:
            change = info['currentPrice'] - info['previousClose']
            pct = (change / info['previousClose']) * 100 if info['previousClose'] != 0 else 0
            st.metric("Price", f"${info['currentPrice']:.2f}", f"{pct:+.2f}%")
        else:
            st.warning("Price data unavailable.")
