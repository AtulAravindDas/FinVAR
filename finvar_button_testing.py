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

        if not info or 'longName' not in info:
            st.error("❌ No company information found. Please enter a valid ticker.")
        else:
            # Company Name
            company_name = info.get('longName', 'N/A')
            st.subheader("🏢 Company Name")
            st.write(company_name)

            # Toggle Description
            if "show_description" not in st.session_state:
                st.session_state.show_description = False

            if st.button("Show/Hide Description"):
                st.session_state.show_description = not st.session_state.show_description

            if st.session_state.show_description:
                st.subheader("📝 Company Description")
                description = info.get('longBusinessSummary', 'N/A')
                st.write(description)

            # Stock Price Section
            if st.button("Display Current Price 💰"):
                current_price = info.get("currentPrice", "N/A")
                prev_close = info.get("previousClose", "N/A")

                if current_price != "N/A" and prev_close != "N/A":
                    change = current_price - prev_close
                    percent_change = (change / prev_close) * 100
                    color = "#00FF00" if change >= 0 else "#FF4C4C"
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

                # Stock history chart
                hist = ticker.history(period="1y")
                if not hist.empty:
                    st.subheader("📊 Stock Price (Last 12 Months)")
                    st.line_chart(hist["Close"])
                else:
                    st.warning("No historical price data found.")

            # Financial Statements
            income_statement = ticker.financials
            balance_sheet = ticker.balance_sheet
            cash_flow_statement = ticker.cashflow

            if not income_statement.empty:
                st.success("✅ Company financial data loaded successfully!")
                st.subheader("📄 Income Statement")
                st.dataframe(income_statement)
            else:
                st.warning("Income statement data not available.")

            # Buttons for Ratios
            if st.button("📈 Show Profitability Ratios"):
                st.info("Calculating Profitability Ratios... (coming soon)")

            if st.button("📊 Show Growth Ratios"):
                st.info("Calculating Growth Ratios... (coming soon)")

    except
