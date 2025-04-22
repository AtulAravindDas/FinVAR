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

        if not info:
            st.error("❌ No company information found. Please enter a valid ticker.")
        else:
            # Display company name
            company_name = info.get('longName', 'N/A')
            st.subheader("🏢 Company Name")
            st.write(company_name)

            # Company description
            st.subheader("📝 Company Description")
            description = info.get('longBusinessSummary', 'N/A')
            st.write(description)

            # Current price
            current_price = info.get("currentPrice")
            prev_close = info.get("previousClose")

            if current_price is not None and prev_close is not None:
                change = current_price - prev_close
                percent_change = (change / prev_close) * 100
                color = "#00FF00" if change >= 0 else "#FF4C4C"
                st.markdown(f"""<div style="background-color:#1e1e1e; padding:20px; border-radius:10px;">
                    <h1 style='font-size:48px; color:white;'>${current_price:.2f} USD</h1>
                    <p style='font-size:20px; color:{color};'>{change:+.2f} ({percent_change:+.2f}%) today</p>
                    </div>""", unsafe_allow_html=True)
            else:
                st.warning("💡 Stock price data not available.")

            # Price history
            hist = ticker.history(period="1y")
            if not hist.empty:
                st.subheader("📊 Stock Price (Last 12 Months)")
                st.line_chart(hist["Close"])
            else:
                st.warning("No historical price data found.")

    except Exception as e:
        st.error(f"🚨 Error fetching data: {e}")
