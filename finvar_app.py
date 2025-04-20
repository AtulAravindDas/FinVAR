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

    current_price = info.get("currentPrice", "N/A")
    prev_close = info.get("previousClose", "N/A")

    if current_price != "N/A" and prev_close != "N/A":
        change = current_price - prev_close
        percent_change = (change / prev_close) * 100
        color = "#00FF00" if change >= 0 else "#FF4C4C"
        sign = "+" if change >= 0 else "-"
        st.markdown(f"""
            <div style="background-color:#1e1e1e; padding:20px; border-radius:10px;">
                <h1 style='font-size:48px; color:white;'>${current_price:.2f} USD</h1>
                <p style='font-size:20px; color:{color};'>
                    {change:+.2f} ({percent_change:+.2f}%) today
                </p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Stock price data not available.")

    
    '''st.subheader("📑 Income Statement")
    st.dataframe(ticker.financials)

    st.subheader("📊 Balance Sheet")
    st.dataframe(ticker.balance_sheet)

    st.subheader("💰 Cash Flow")
    st.dataframe(ticker.cashflow)'''
