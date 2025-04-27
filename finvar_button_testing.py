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
st.title("\ud83d\udcca FinVAR – Your Financial Assistant Referee")

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
            st.error("\u274c No company information found. Please enter a valid ticker.")
        else:
            nice_divider()
            styled_header("\ud83c\udfe2 Company Details")
            company_name = info.get('longName', 'N/A')
            st.write(company_name)

            nice_divider()
            styled_header("\ud83d\udcdd Company Overview")
            if st.button("Show/Hide Description"):
                st.session_state["show_description"] = not st.session_state["show_description"]

            if st.session_state["show_description"]:
                st.subheader("\ud83d\udcdc Company Description")
                description = info.get('longBusinessSummary', 'N/A')
                st.write(description)

            nice_divider()
            styled_header("\ud83d\udcb0 Stock Price Information")
            if st.button("Display Current Price \ud83d\udcb0"):
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
            styled_header("\ud83d\udcd8 Profitability Analysis")
            if st.button("\ud83d\udcd8 Profitability Ratios"):
                # Your Profitability Ratios code block
                pass

            nice_divider()
            styled_header("\ud83d\udcc8 Growth Metrics")
            if st.button("\ud83d\udcc8 Growth Overview"):
                # Your Growth Overview code block
                pass

            nice_divider()
            styled_header("\u26a1 Leverage Insights")
            if st.button("\u26a1 Leverage Overview"):
                # Your Leverage Overview code block
                pass

            nice_divider()
            styled_header("\ud83d\udca7 Liquidity & Dividend Strength")
            if st.button("\ud83d\udca7 Liquidity & Dividend Overview"):
                # Your Liquidity Overview code block
                pass

            nice_divider()
            styled_header("\ud83d\udcc8 Volatility Trends")
            if st.button("\ud83d\udcc8 Stock Price & Volatility"):
                # Your Volatility Overview code block
                pass

    except Exception as e:
        st.error(f"\u26a0\ufe0f Error fetching data: {e}")
