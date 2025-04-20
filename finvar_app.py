import streamlit as st
import yfinance as yf

st.set_page_config(page_title="FinVAR", layout="centered")
st.title("📊 FinVAR – Your Financial Assistant Referee")

user_input = st.text_input("Enter the ticker name:")

if user_input:
    ticker = yf.Ticker(user_input)
    info = ticker.info 

    st.header("🏢 Company Overview")
    company_name = info.get('longName', 'N/A')
    st.markdown(f"<h2 style='font-size:32px; color:#FFFFFF;'>🏢 Company Name: {company_name}</h2>", unsafe_allow_html=True)
    st.write(f"**Description:** {info.get('longBusinessSummary', 'N/A')}")

    price_data = ticker.history(period="1d")
    if not price_data.empty:
        latest_close = price_data['Close'].iloc[-1]
        st.markdown(f"<h2 style='font-size:16px; color:#FFFFFF;'>💵 Latest Close: ${latest_close:.2f}</h2>", unsafe_allow_html=True)
    else:
        st.warning("Price data not available for today.")

    # Display financials
    st.subheader("📑 Income Statement")
    st.dataframe(ticker.financials)

    st.subheader("📊 Balance Sheet")
    st.dataframe(ticker.balance_sheet)

    st.subheader("💰 Cash Flow")
    st.dataframe(ticker.cashflow)
