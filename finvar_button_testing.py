import yfinance as yf
import streamlit as st

st.set_page_config(page_title="FinVAR", layout="centered")
st.title("📊 FinVAR – Your Financial Assistant Referee")

# ✅ Use Streamlit text_input instead of Python input()
user_input = st.text_input("Enter the ticker name (e.g., AAPL):")

if user_input:
    try:
        ticker = yf.Ticker(user_input)
        info = ticker.info

        # Company Name
        st.subheader("🏢 Company Name")
        st.write(info.get('longName', 'N/A'))

        # ✅ Button to show current price
        if st.button("Display Current Price 💰"):
            st.subheader("💰 Current Price")
            st.write(info.get('currentPrice', 'N/A'))

    except Exception as e:
        st.error(f"Error fetching data: {e}")
