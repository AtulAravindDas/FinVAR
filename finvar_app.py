import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

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

            if st.button("📘 Profitability Ratios"):
                st.subheader("📘 Profitability Ratios Overview")
                income = ticker.financials
                balance = ticker.balance_sheet
                ideal_income_order = ["Total Revenue", "Gross Profit", "EBITDA", "EBIT", "Net Income"]
                ideal_balance_order = ["Total Assets", "Common Stock Equity", "Total Liabilities Net Minority Interest"]
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
                df = df.dropna()
                df = df.apply(pd.to_numeric, errors='coerce').dropna()
                df.index = df.index.year
                df['ROE (%)'] = (df['Net Income'] / df['Shareholders Equity']) * 100
                df['Gross Profit Margin (%)'] = (df['Gross Profit'] / df['Total Revenue']) * 100
                df['Asset Turnover'] = df['Total Revenue'] / df['Total Assets']
                df['Financial Leverage'] = df['Total Assets'] / df['Shareholders Equity']
                df['Net Profit Margin (%)'] = (df['Net Income'] / df['Total Revenue']) * 100
                st.dataframe(df)
                st.subheader("📈 Interactive Financial Visuals")
                st.plotly_chart(px.line(df, x=df.index, y="ROE (%)", markers=True, title="Return on Equity (%)", template="plotly_dark"), use_container_width=True)
                st.plotly_chart(px.bar(df, x=df.index, y="Gross Profit Margin (%)", title="Gross Profit Margin (%)", template="plotly_dark"), use_container_width=True)
                st.plotly_chart(px.area(df, x=df.index, y="Asset Turnover", title="Asset Turnover", template="plotly_dark"), use_container_width=True)
                st.plotly_chart(px.scatter(df, x=df.index, y="Financial Leverage", size="Financial Leverage", title="Financial Leverage", template="plotly_dark"), use_container_width=True)
                st.plotly_chart(px.bar(df, x=df.index.astype(str), y="Net Profit Margin (%)", title="Net Profit Margin (%)", template="plotly_dark"), use_container_width=True)
                st.plotly_chart(px.line(df, x=df.index, y=["EBITDA", "EBIT"], markers=True, title="EBITDA vs EBIT", template="plotly_dark"), use_container_width=True)
                latest_year = df.index.max()
                roe_latest = df.loc[latest_year, 'ROE (%)']
                gross_margin_latest = df.loc[latest_year, 'Gross Profit Margin (%)']
                net_margin_latest = df.loc[latest_year, 'Net Profit Margin (%)']
                asset_turnover_latest = df.loc[latest_year, 'Asset Turnover']
                summary_text = ""
                if roe_latest > 15:
                    summary_text += f"✅ Strong ROE of {roe_latest:.2f}% indicates efficient use of equity.\n\n"
                else:
                    summary_text += f"⚠️ ROE of {roe_latest:.2f}% is below ideal; check company's return generation.\n\n"
                if gross_margin_latest > 40:
                    summary_text += f"✅ Excellent Gross Margin ({gross_margin_latest:.2f}%) suggests strong pricing power.\n\n"
                elif gross_margin_latest > 20:
                    summary_text += f"✅ Moderate Gross Margin ({gross_margin_latest:.2f}%), acceptable for most industries.\n\n"
                else:
                    summary_text += f"⚠️ Weak Gross Margin ({gross_margin_latest:.2f}%) — may face margin pressure.\n\n"
                if net_margin_latest > 10:
                    summary_text += f"✅ Net Profit Margin of {net_margin_latest:.2f}% is healthy.\n\n"
                else:
                    summary_text += f"⚠️ Thin Net Profit Margin ({net_margin_latest:.2f}%) could be a concern.\n\n"
                if asset_turnover_latest > 1:
                    summary_text += f"✅ High Asset Turnover ({asset_turnover_latest:.2f}) — efficient asset use.\n\n"
                else:
                    summary_text += f"⚠️ Low Asset Turnover ({asset_turnover_latest:.2f}) — inefficient use of assets.\n\n"
                st.subheader("🔍 FinVAR Summary: Profitability Overview")
                st.info(summary_text)

            if st.button("📈 Growth Overview"):
                st.subheader("📈 Revenue and EBITDA Growth Overview")
                income = ticker.financials
                growth_df = income.T[['Total Revenue', 'EBITDA']]
                growth_df = growth_df.pct_change() * 100
                st.dataframe(growth_df)
                st.plotly_chart(px.line(growth_df, x=growth_df.index.year, y=['Total Revenue', 'EBITDA'], markers=True, title="Revenue and EBITDA Growth YoY (%)", template="plotly_dark"), use_container_width=True)

            if st.button("⚡ Leverage Overview"):
                st.subheader("⚡ Leverage Ratios Overview")
                balance = ticker.balance_sheet.T
                leverage_df = pd.DataFrame()
                leverage_df['Debt-to-Equity'] = balance['Total Liabilities Net Minority Interest'] / balance['Common Stock Equity']
                leverage_df['Debt-to-Assets'] = balance['Total Liabilities Net Minority Interest'] / balance['Total Assets']
                leverage_df.index = leverage_df.index.year
                st.dataframe(leverage_df)
                st.plotly_chart(px.bar(leverage_df, x=leverage_df.index, y=['Debt-to-Equity', 'Debt-to-Assets'], title="Leverage Ratios", template="plotly_dark"), use_container_width=True)

            if st.button("💧 Liquidity & Dividend Overview"):
                st.subheader("💧 Liquidity and Dividend Overview")
                balance = ticker.balance_sheet.T
                cashflow = ticker.cashflow.T
                liquidity_df = pd.DataFrame()
                liquidity_df['Current Ratio'] = balance['Current Assets'] / balance['Current Liabilities']
                liquidity_df['FCF'] = cashflow['Operating Cash Flow'] - cashflow['Capital Expenditure']
                liquidity_df.index = liquidity_df.index.year
                st.dataframe(liquidity_df)
                st.plotly_chart(px.line(liquidity_df, x=liquidity_df.index, y=['Current Ratio', 'FCF'], markers=True, title="Liquidity & FCF Trends", template="plotly_dark"), use_container_width=True)

            if st.button("📈 Stock Price & Volatility"):
                st.subheader("📈 Stock Price & Volatility Overview")
                hist = ticker.history(period="1y")
                if not hist.empty:
                    hist['Daily Return'] = hist['Close'].pct_change()
                    volatility = hist['Daily Return'].std() * np.sqrt(252)
                    st.line_chart(hist['Close'])
                    st.subheader(f"Annualized Volatility: {volatility:.2%}")
                else:
                    st.warning("No historical data available.")

    except Exception as e:
        st.error(f"⚠️ Error fetching data: {e}")
