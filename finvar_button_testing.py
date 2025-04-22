import yfinance as yf
import streamlit as st

st.set_page_config(page_title="FinVAR", layout="centered")
st.title("📊 FinVAR – Your Financial Assistant Referee")


user_input = st.text_input("Enter the ticker name (e.g., AAPL):")

if user_input:
    try:
        ticker = yf.Ticker(user_input)
        info = ticker.info  
        company_name = info.get('longName', 'N/A')

        st.subheader("🏢 Company Name")
        st.write(company_name)

        
        if st.button("Display Current Price 💰"):
            fast_price = ticker.fast_info.get('lastPrice', 'N/A')
            st.subheader("💰 Current Price")
            st.write(f"${fast_price}")

    except Exception as e:
        st.error(f"Error fetching data: {e}")
