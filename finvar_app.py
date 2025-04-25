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

            # 📘 Profitability Ratios Section
            if st.button("📘 Profitability Ratios"):
                st.subheader("📈 Profitability Ratios Overview")

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
                df = df.apply(pd.to_numeric, errors='coerce')
                df = df.dropna()
                df.index = df.index.year

                # Ratios
                df['ROE (%)'] = (df['Net Income'] / df['Shareholders Equity']) * 100
                df['Gross Profit Margin (%)'] = (df['Gross Profit'] / df['Total Revenue']) * 100
                df['Asset Turnover'] = df['Total Revenue'] / df['Total Assets']
                df['Financial Leverage'] = df['Total Assets'] / df['Shareholders Equity']
                df['Net Profit Margin (%)'] = (df['Net Income'] / df['Total Revenue']) * 100

                st.dataframe(df)

                st.subheader("📊 Interactive Financial Visuals")

                # Different visualization styles
                fig1 = px.line(df, x=df.index, y="ROE (%)", markers=True, title="Return on Equity (%)", template="plotly_dark")
                st.plotly_chart(fig1, use_container_width=True)

                fig2 = px.bar(df, x=df.index, y="Gross Profit Margin (%)", title="Gross Profit Margin (%)", template="plotly_dark")
                st.plotly_chart(fig2, use_container_width=True)

                fig3 = px.area(df, x=df.index, y="Asset Turnover", title="Asset Turnover", template="plotly_dark")
                st.plotly_chart(fig3, use_container_width=True)

                fig4 = px.scatter(df, x=df.index, y="Financial Leverage", size="Financial Leverage", title="Financial Leverage", template="plotly_dark")
                st.plotly_chart(fig4, use_container_width=True)

                fig5 = px.bar(df, x=df.index.astype(str), y="Net Profit Margin (%)", title="Net Profit Margin (%)", template="plotly_dark")
                st.plotly_chart(fig5, use_container_width=True)

                fig6 = px.line(df, x=df.index, y=["EBITDA", "EBIT"], markers=True, title="EBITDA vs EBIT", template="plotly_dark")
                st.plotly_chart(fig6, use_container_width=True)

            # 📈 Growth Overview Section
            if st.button("📈 Growth Overview"):
                st.subheader("📈 Revenue and EBITDA Growth Rates")

                income = ticker.financials
                ideal_income_order_growth = ["Total Revenue", "EBITDA"]
                income_growth = income.loc[[item for item in ideal_income_order_growth if item in income.index]]
                income_growth = income_growth.T
                income_growth.index = income_growth.index.year
                income_growth = income_growth.apply(pd.to_numeric, errors='coerce').dropna()

                # Calculate YoY Growth Rates
                income_growth['Revenue Growth (%)'] = income_growth['Total Revenue'].pct_change() * 100
                income_growth['EBITDA Growth (%)'] = income_growth['EBITDA'].pct_change() * 100

                st.dataframe(income_growth[['Revenue Growth (%)', 'EBITDA Growth (%)']].dropna())

                st.subheader("📊 Growth Visualizations")

                fig7 = px.line(income_growth, x=income_growth.index, y="Revenue Growth (%)", markers=True, title="Revenue Growth (%) YoY", template="plotly_dark")
                st.plotly_chart(fig7, use_container_width=True)

                fig8 = px.bar(income_growth, x=income_growth.index, y="EBITDA Growth (%)", title="EBITDA Growth (%) YoY", template="plotly_dark")
                st.plotly_chart(fig8, use_container_width=True)

            # ⚡ Leverage Overview Section
            if st.button("⚡ Leverage Overview"):
                st.subheader("⚡ Leverage Ratios Overview")

                balance = ticker.balance_sheet
                ideal_balance_order_leverage = ["Total Assets", "Common Stock Equity", "Total Liabilities Net Minority Interest"]
                balance_leverage = balance.loc[[item for item in ideal_balance_order_leverage if item in balance.index]]
                balance_leverage = balance_leverage.T
                balance_leverage.index = balance_leverage.index.year
                balance_leverage = balance_leverage.apply(pd.to_numeric, errors='coerce').dropna()

                balance_leverage['Debt-to-Equity Ratio'] = balance_leverage['Total Liabilities Net Minority Interest'] / balance_leverage['Common Stock Equity']
                balance_leverage['Debt-to-Assets Ratio'] = balance_leverage['Total Liabilities Net Minority Interest'] / balance_leverage['Total Assets']
                balance_leverage['Financial Leverage'] = balance_leverage['Total Assets'] / balance_leverage['Common Stock Equity']

                st.dataframe(balance_leverage[['Debt-to-Equity Ratio', 'Debt-to-Assets Ratio', 'Financial Leverage']])

                st.subheader("📊 Leverage Visualizations")

                fig9 = px.line(balance_leverage, x=balance_leverage.index, y="Debt-to-Equity Ratio", markers=True,
                               title="Debt-to-Equity Ratio Over Time", template="plotly_dark")
                st.plotly_chart(fig9, use_container_width=True)

                fig10 = px.bar(balance_leverage, x=balance_leverage.index, y="Debt-to-Assets Ratio",
                               title="Debt-to-Assets Ratio Over Time", template="plotly_dark")
                st.plotly_chart(fig10, use_container_width=True)

                fig11 = px.area(balance_leverage, x=balance_leverage.index, y="Financial Leverage",
                                title="Financial Leverage Over Time", template="plotly_dark")
                st.plotly_chart(fig11, use_container_width=True)
                        # 💧 Liquidity and Dividend Overview Section
            
            if st.button("💧 Liquidity & Payout Ratios Overview"):
                st.subheader("💧 Liquidity and Dividend Metrics")

                balance = ticker.balance_sheet
                cashflow = ticker.cashflow
                income = ticker.financials

                ideal_balance_order_liquidity = ["Current Assets", "Current Liabilities"]
                ideal_cashflow_order = ["Operating Cash Flow", "Capital Expenditure", "Cash Dividends Paid"]
                ideal_income_order_liquidity = ["Total Revenue", "Net Income"]

                # Extract and process
                balance_liquidity = balance.loc[[item for item in ideal_balance_order_liquidity if item in balance.index]].T
                cashflow_liquidity = cashflow.loc[[item for item in ideal_cashflow_order if item in cashflow.index]].T
                income_liquidity = income.loc[[item for item in ideal_income_order_liquidity if item in income.index]].T

                # Combine all into one DataFrame
                df_liquidity = pd.concat([balance_liquidity, cashflow_liquidity, income_liquidity], axis=1)

                df_liquidity.index = df_liquidity.index.year
                df_liquidity = df_liquidity.apply(pd.to_numeric, errors='coerce').dropna()

                # Calculations
                df_liquidity['Current Ratio'] = df_liquidity['Current Assets'] / df_liquidity['Current Liabilities']
                df_liquidity['Free Cash Flow (FCF)'] = df_liquidity['Operating Cash Flow'] - df_liquidity['Capital Expenditure']
                df_liquidity['Capex (Capital Expenditures)'] = df_liquidity['Capital Expenditure']
                df_liquidity['FCF to Revenue (%)'] = (df_liquidity['Free Cash Flow (FCF)'] / df_liquidity['Total Revenue']) * 100
                df_liquidity['Dividend Payout Ratio (%)'] = (df_liquidity['Cash Dividends Paid'].abs() / df_liquidity['Net Income']) * 100
                df_liquidity['Retention Rate (%)'] = 100 - df_liquidity['Dividend Payout Ratio (%)']

                st.dataframe(df_liquidity[['Current Ratio', 'Free Cash Flow (FCF)', 'Capex (Capital Expenditures)', 
                                           'FCF to Revenue (%)', 'Dividend Payout Ratio (%)', 'Retention Rate (%)']])

                st.subheader("📊 Liquidity and Dividend Visualizations")

                # Different Visualizations
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
