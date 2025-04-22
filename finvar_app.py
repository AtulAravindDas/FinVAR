import yfinance as yf
import streamlit as st

# Page configuration
st.set_page_config(page_title="FinVAR", layout="centered")
st.title("📊 FinVAR – Your Financial Assistant Referee")

# User input
user_input = st.text_input("Enter the ticker name (e.g., AAPL):")

# Initialize ticker and display information
if user_input:
    try:
        ticker = yf.Ticker(user_input)
        info = ticker.info
        company_name = info.get('longName', 'N/A')

        # Display company name
        st.subheader("🏢 Company Name")
        st.write(company_name)

        st.subheader("📝 Company Description")
        description = info.get('longBusinessSummary', 'N/A')
        st.write(description)

        
        # Current price section
        
        current_price = info.get("currentPrice", "N/A")
        prev_close = info.get("previousClose", "N/A")

        if current_price != "N/A" and prev_close != "N/A":
            change = current_price - prev_close
            percent_change = (change / prev_close) * 100
            color = "#00FF00" if change >= 0 else "#FF4C4C"
            st.markdown(f"""<div style="background-color:#1e1e1e; padding:20px; border-radius:10px;"><h1 style='font-size:48px; color:white;'>${current_price:.2f} USD</h1><p style='font-size:20px; color:{color};'>{change:+.2f} ({percent_change:+.2f}%) today</p>
                    </div>""", unsafe_allow_html=True)
        else:
                st.warning("Stock price data not available.")
            
        hist = ticker.history(period="1y")  # you can also use "12mo"

        if not hist.empty:
            st.subheader("📊 Stock Price (Last 12 Months)")
            st.line_chart(hist["Close"])  # only closing prices
        else:
            st.warning("No data found for the given ticker.")


    except Exception as e:
        st.error(f"Error fetching data: {e}")
