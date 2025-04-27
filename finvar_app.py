import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import joblib

st.set_page_config(page_title="FinVAR", layout="centered")
st.title("📊 FinVAR – Your Financial Assistant Referee")

user_input = st.text_input("Enter the ticker name (e.g., AAPL):")

model=joblib.load(final_eps_predictor.pkl)

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

                latest_year = growth_df.index.max()
                revenue_growth = growth_df.loc[latest_year, 'Total Revenue']
                ebitda_growth = growth_df.loc[latest_year, 'EBITDA']


                summary_text = ""
                if revenue_growth > 10:
                    summary_text += f"✅ Strong Revenue Growth: {revenue_growth:.2f}%\n\n"
                else:
                    summary_text += f"⚠️ Moderate or Low Revenue Growth: {revenue_growth:.2f}%\n\n"

                if ebitda_growth > 10:
                    summary_text += f"✅ Strong EBITDA Growth: {ebitda_growth:.2f}%\n\n"
                else:
                    summary_text += f"⚠️ EBITDA Growth below ideal: {ebitda_growth:.2f}%\n\n"

                st.subheader("🔍 FinVAR Summary: Growth Overview")
                st.info(summary_text)


            if st.button("⚡ Leverage Overview"):
                st.subheader("⚡ Leverage Ratios Overview")
                balance = ticker.balance_sheet.T
                leverage_df = pd.DataFrame()
                leverage_df['Debt-to-Equity'] = balance['Total Liabilities Net Minority Interest'] / balance['Common Stock Equity']
                leverage_df['Debt-to-Assets'] = balance['Total Liabilities Net Minority Interest'] / balance['Total Assets']
                leverage_df.index = leverage_df.index.year
                st.dataframe(leverage_df)
                st.plotly_chart(px.bar(leverage_df, x=leverage_df.index, y=['Debt-to-Equity', 'Debt-to-Assets'], title="Leverage Ratios", template="plotly_dark"), use_container_width=True)

                latest_year = leverage_df.index.max()
                debt_equity = leverage_df.loc[latest_year, 'Debt-to-Equity']
                debt_assets = leverage_df.loc[latest_year, 'Debt-to-Assets']
                
                summary_text = ""
                if debt_equity < 1:
                    summary_text += f"✅ Healthy Debt-to-Equity Ratio: {debt_equity:.2f}\n\n"
                else:
                    summary_text += f"⚠️ High Debt-to-Equity Ratio: {debt_equity:.2f}\n\n"

                if debt_assets < 0.5:
                    summary_text += f"✅ Low Debt-to-Assets Ratio: {debt_assets:.2f}\n\n"
                else:
                    summary_text += f"⚠️ Higher Debt reliance: {debt_assets:.2f}\n\n"

                st.subheader("🔍 FinVAR Summary: Leverage Overview")
                st.info(summary_text)

            
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

                latest_year = liquidity_df.index.max()
                current_ratio = liquidity_df.loc[latest_year, 'Current Ratio']
                fcf = liquidity_df.loc[latest_year, 'FCF']

                summary_text = ""
                if current_ratio >= 1.5:
                    summary_text += f"✅ Strong Current Ratio: {current_ratio:.2f}\n\n"
                else:
                    summary_text += f"⚠️ Low Current Ratio: {current_ratio:.2f}\n\n"

                if fcf > 0:
                    summary_text += f"✅ Positive Free Cash Flow (FCF): {fcf/1e6:.2f}M\n\n"
                else:
                    summary_text += f"⚠️ Negative Free Cash Flow (FCF): {fcf/1e6:.2f}M\n\n"

                st.subheader("🔍 FinVAR Summary: Liquidity & Dividend Overview")
                st.info(summary_text)


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
            
            if st.button("🔮 Predict Next Year EPS (2025)"):
                st.subheader("🔮 EPS Prediction for 2025")
                try:
                    income = ticker.financials
                    balance = ticker.balance_sheet
                    cashflow = ticker.cashflow
                    info = ticker.info

                    income = income.T
                    balance = balance.T
                    cashflow = cashflow.T

                    latest_year = income.index.max().year

        
                    pe_exi = info.get('trailingPE', np.nan)
                    npm = income.loc[income.index[-1], 'Net Income'] / income.loc[income.index[-1], 'Total Revenue']
                    opmad = income.loc[income.index[-1], 'Operating Income'] / income.loc[income.index[-1], 'Total Revenue']
                    roa = income.loc[income.index[-1], 'Net Income'] / balance.loc[balance.index[-1], 'Total Assets']
                    roe = income.loc[income.index[-1], 'Net Income'] / balance.loc[balance.index[-1], 'Common Stock Equity']
                    de_ratio = balance.loc[balance.index[-1], 'Total Liabilities Net Minority Interest'] / balance.loc[balance.index[-1], 'Common Stock Equity']
                    intcov_ratio = income.loc[income.index[-1], 'EBIT'] / income.loc[income.index[-1], 'Interest Expense']
                    curr_ratio = balance.loc[balance.index[-1], 'Current Assets'] / balance.loc[balance.index[-1], 'Current Liabilities']
                    revenue = income.loc[income.index[-1], 'Total Revenue']
                    eps = info.get('epsTrailingTwelveMonths', np.nan)
            
                    # Calculate engineered features
                    previous_revenue = income.loc[income.index[-2], 'Total Revenue'] if len(income.index) > 1 else np.nan
                    previous_eps = info.get('epsTrailingTwelveMonths', np.nan) # fallback if past EPS not available
            
                    revenue_growth = ((revenue - previous_revenue) / previous_revenue) if previous_revenue else 0
                    eps_growth = 0  # fallback
                    
                    roa_to_revenue = roa / revenue if revenue != 0 else 0
                    roe_to_roa = roe / roa if roa != 0 else 0
                    debt_to_income = de_ratio / revenue if revenue != 0 else 0
                    intcov_per_curr = intcov_ratio / curr_ratio if curr_ratio != 0 else 0
                    opmad_to_npm = opmad / npm if npm != 0 else 0
            
                    eps_3yr_avg = eps  # fallback
                    revenue_3yr_avg = revenue  # fallback
            
                    # Build feature array
                    features = np.array([[ 
                        pe_exi, npm, opmad, roa, roe, de_ratio, intcov_ratio, curr_ratio,
                        revenue_growth, eps_growth, roa_to_revenue, roe_to_roa,
                        debt_to_income, intcov_per_curr, opmad_to_npm, eps_3yr_avg, revenue_3yr_avg
                    ]])
            
                    # Predict
                    predicted_eps = model.predict(features)[0]
            
                    st.success(f"🧠 Predicted EPS for 2025: **{predicted_eps:.2f} USD**")
                
    except Exception as e:
        st.error(f"⚠️ Error fetching data: {e}")
