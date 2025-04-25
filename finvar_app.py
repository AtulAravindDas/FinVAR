
import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

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
                    st.markdown(f'''
                        <div style="background-color:#1e1e1e; padding:20px; border-radius:10px;">
                            <h1 style='font-size:48px; color:white;'>${current_price:.2f} USD</h1>
                            <p style='font-size:20px; color:{color};'>
                                {change:+.2f} ({percent_change:+.2f}%) today
                            </p>
                        </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.warning("Stock price data not available.")

                hist = ticker.history(period="1y")
                if not hist.empty:
                    st.subheader("📊 Stock Price (Last 12 Months)")
                    st.line_chart(hist["Close"])
                else:
                    st.warning("No historical price data found.")

            if st.button("💧 Liquidity & Payout Ratios Overview"):
                st.subheader("💧 Liquidity and Dividend Metrics")

                balance = ticker.balance_sheet
                cashflow = ticker.cashflow
                income = ticker.financials

                ideal_balance_order_liquidity = ["Current Assets", "Current Liabilities"]
                ideal_cashflow_order = ["Operating Cash Flow", "Capital Expenditures", "Cash Dividends Paid"]
                ideal_income_order_liquidity = ["Total Revenue", "Net Income"]

                balance_liquidity = balance.loc[[item for item in ideal_balance_order_liquidity if item in balance.index]].T
                cashflow_liquidity = cashflow.loc[[item for item in ideal_cashflow_order if item in cashflow.index]].T
                income_liquidity = income.loc[[item for item in ideal_income_order_liquidity if item in income.index]].T

                df_liquidity = pd.concat([balance_liquidity, cashflow_liquidity, income_liquidity], axis=1)
                df_liquidity.index = df_liquidity.index.year
                df_liquidity = df_liquidity.apply(pd.to_numeric, errors='coerce').dropna()

                df_liquidity['Current Ratio'] = df_liquidity['Current Assets'] / df_liquidity['Current Liabilities']
                df_liquidity['Free Cash Flow (FCF)'] = df_liquidity['Operating Cash Flow'] - df_liquidity['Capital Expenditures']
                df_liquidity['Capex (Capital Expenditures)'] = df_liquidity['Capital Expenditures']
                df_liquidity['FCF to Revenue (%)'] = (df_liquidity['Free Cash Flow (FCF)'] / df_liquidity['Total Revenue']) * 100
                df_liquidity['Dividend Payout Ratio (%)'] = (df_liquidity['Cash Dividends Paid'].abs() / df_liquidity['Net Income']) * 100
                df_liquidity['Retention Rate (%)'] = 100 - df_liquidity['Dividend Payout Ratio (%)']

                st.dataframe(df_liquidity[['Current Ratio', 'Free Cash Flow (FCF)', 'Capex (Capital Expenditures)',
                                           'FCF to Revenue (%)', 'Dividend Payout Ratio (%)', 'Retention Rate (%)']])

                st.subheader("📊 Liquidity and Dividend Visualizations")

                fig12 = px.line(df_liquidity, x=df_liquidity.index, y="Current Ratio", markers=True,
                                title="Current Ratio Over Time", template="plotly_dark")
                st.plotly_chart(fig12, use_container_width=True)

                fig13 = px.bar(df_liquidity, x=df_liquidity.index, y="Free Cash Flow (FCF)",
                               title="Free Cash Flow Over Time", template="plotly_dark")
                st.plotly_chart(fig13, use_container_width=True)

                fig14 = px.area(df_liquidity, x=df_liquidity.index, y="Capex (Capital Expenditures)",
                                title="Capex Over Time", template="plotly_dark")
                st.plotly_chart(fig14, use_container_width=True)

                fig15 = px.scatter(df_liquidity, x=df_liquidity.index, y="FCF to Revenue (%)", size="FCF to Revenue (%)",
                                   title="Free Cash Flow to Revenue (%)", template="plotly_dark")
                st.plotly_chart(fig15, use_container_width=True)

                fig16 = px.line(df_liquidity, x=df_liquidity.index, y="Dividend Payout Ratio (%)", markers=True,
                                title="Dividend Payout Ratio (%) Over Time", template="plotly_dark")
                st.plotly_chart(fig16, use_container_width=True)

                fig17 = px.bar(df_liquidity, x=df_liquidity.index, y="Retention Rate (%)",
                               title="Retention Rate (%) Over Time", template="plotly_dark")
                st.plotly_chart(fig17, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Error fetching data: {e}")
