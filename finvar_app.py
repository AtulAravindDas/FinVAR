import yfinance as yf
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="FinVAR", layout="centered")
st.title("📊 FinVAR – Your Financial Assistant Referee")

user_input = st.text_input("Enter the ticker name (e.g., AAPL):")

# ✅ Initialize session state keys
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
            company_name = info.get('longName', 'N/A')
            st.subheader("🏢 Company Name")
            st.write(company_name)

            if st.button("Show/Hide Description"):
                st.session_state["show_description"] = not st.session_state["show_description"]

            if st.session_state["show_description"]:
                st.subheader("📝 Company Description")
                description = info.get('longBusinessSummary', 'N/A')
                st.write(description)

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

                hist = ticker.history(period="1y")
                if not hist.empty:
                    st.subheader("📊 Stock Price (Last 12 Months)")
                    st.line_chart(hist["Close"])
                else:
                    st.warning("No historical price data found.")

            if st.button("📘 Profitability Ratios"):
                st.subheader("📈 Profitability Ratios Overview")

                # Internal use only — reorder key financials
                income = ticker.financials
                balance = ticker.balance_sheet

                ideal_income_order = [
                    "Total Revenue", "Gross Profit", "EBITDA", "EBIT", "Net Income"
                ]
                ideal_balance_order = [
                    "Total Assets", "Common Stock Equity", "Total Liabilities Net Minority Interest"
                ]

                income = income.loc[[item for item in ideal_income_order if item in income.index]]
                balance = balance.loc[[item for item in ideal_balance_order if item in balance.index]]

                income = income.T
                balance = balance.T

                df = pd.DataFrame()
                df['Net Income'] = income['Net Income']
                df['Gross Profit'] = income['Gross Profit']
                df['Total Revenue'] = income['Total Revenue']
                df['EBITDA'] = income['EBITDA']
                df['EBIT'] = income['EBIT']
                df['Shareholders Equity'] = balance['Common Stock Equity']
                df['Total Assets'] = balance['Total Assets']
                df['Total Liabilities'] = balance['Total Liabilities Net Minority Interest']

                # Clean and convert to numeric
                df = df.dropna()
                df = df.apply(pd.to_numeric, errors='coerce')
                df = df.dropna()
                df.index = df.index.year

                # Ratios
                df['ROE (%)'] = (df['Net Income'] / df['Shareholders Equity']) * 100
                df['Gross Profit Margin (%)'] = (df['Gross Profit'] / df['Total Revenue']) * 100
                df['Asset Turnover'] = df['Total Revenue'] / df['Total Assets']
                df['Financial Leverage'] = df['Total Assets'] / df['Shareholders Equity']
                df['Net Profit Margin (%)'] = (df['Net Income'] / df['Total Revenue']) * 100

                # Show Ratio Table
                st.dataframe(df)

                st.subheader("📊 Visual Insights")
                fig, axs = plt.subplots(3, 2, figsize=(15, 12))
                fig.suptitle('Key Financial Ratios', fontsize=18, fontweight='bold')
                x = df.index

                axs[0, 0].plot(x, df['ROE (%)'], marker='o', color='purple')
                axs[0, 0].set_title("Return on Equity (%)")
                axs[0, 0].grid(True)

                axs[0, 1].bar(x, df['Gross Profit Margin (%)'], color='teal')
                axs[0, 1].set_title("Gross Profit Margin (%)")

                axs[1, 0].plot(x, df['Asset Turnover'], marker='s', color='darkorange')
                axs[1, 0].set_title("Asset Turnover")
                axs[1, 0].grid(True)

                axs[1, 1].fill_between(x, df['Financial Leverage'], color='skyblue', alpha=0.5)
                axs[1, 1].set_title("Financial Leverage")

                axs[2, 0].barh(x.astype(str), df['Net Profit Margin (%)'], color='darkgreen')
                axs[2, 0].set_title("Net Profit Margin (%)")

                axs[2, 1].plot(x, df['EBITDA'], marker='D', label="EBITDA", linestyle='--')
                axs[2, 1].plot(x, df['EBIT'], marker='x', label="EBIT", linestyle='-')
                axs[2, 1].set_title("EBITDA vs EBIT")
                axs[2, 1].legend()
                axs[2, 1].grid(True)

                plt.tight_layout(rect=[0, 0.03, 1, 0.95])
                st.pyplot(fig)

    except Exception as e:
        st.error(f"⚠️ Error fetching data: {e}")
