import streamlit as st
import yfinance as yf

st.set_page_config(page_title="FinVAR", layout="centered")
st.title("📊 FinVAR – Your Financial Assistant Referee")

user_input = st.text_input("Enter the ticker name (e.g., AAPL)")

if st.button("Fetch Data") and user_input:
    with st.spinner("Loading stock data..."):
        try:
            ticker = yf.Ticker(user_input)
            price = ticker.fast_info.get("lastPrice", "N/A")
            st.success("Data loaded successfully! ✅")
            st.subheader(f"💰 Current Price: ${price}")

        except Exception as e:
            st.error(f"Error loading data: {e}")
