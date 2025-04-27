import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Divider and Styled Header functions
def nice_divider():
    st.markdown("""---""")

def styled_header(title):
    st.markdown(f"<h2 style='color:#4CAF50;'>{title}</h2>", unsafe_allow_html=True)

st.set_page_config(page_title="FinVAR", layout="centered")
st.title("📊 FinVAR – Your Financial Assistant Referee")

user_input = st.text_input("Enter the ticker name (e.g., AAPL):")

# Initialize session state keys
if "show_description" not in st.session_state:
    st.session_state["show_description"] = False
if "show_price" not in st.session_state:
    st.session_state["show_price"] = False

if user_input:
    try:
        ticker = yf.Ticker(user_input)
        info = ticker.info

        if not info or 'longName' not in info:
            st.error("❌ No company information found. Please enter a valid ticker.")
        else:
            nice_divider()
            styled_header("🏢 Company Details")
            company_name = info.get('longName', 'N/A')
            st.write(company_name)

            nice_divider()
            styled_header("📝 Company Overview")
            if st.button("Show/Hide Description"):
                st.session_state["show_description"] = not st.session_state["show_description"]

            if st.session_state["show_description"]:
                st.subheader("📝 Company Description")
                description = info.get('longBusinessSummary', 'N/A')
                st.write(description)

            nice_divider()
            styled_header("💰 Stock Price Information")
            if st.button("Display Current Price 💰"):
                st.session_state["show_price"] = not st.session_state["show_price"]

            if st.session_state["show_price"]:
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

            nice_divider()
            styled_header("📘 Profitability Analysis")
            if st.button("📘 Profitability Ratios"):
                # Your Profitability Ratios code block
                pass

            nice_divider()
            styled_header("📈 Growth Metrics")
            if st.button("📈 Growth Overview"):
                # Your Growth Overview code block
                pass

            nice_divider()
            styled_header("⚡ Leverage Insights")
            if st.button("⚡ Leverage Overview"):
                # Your Leverage Overview code block
                pass

            nice_divider()
            styled_header("💧 Liquidity & Dividend Strength")
            if st.button("💧 Liquidity & Dividend Overview"):
                # Your Liquidity Overview code block
                pass

            nice_divider()
            styled_header("📈 Volatility Trends")
            if st.button("📈 Stock Price & Volatility"):
                # Your Volatility Overview code block
                pass

    except Exception as e:
        st.error(f"⚠️ Error fetching data: {e}")
