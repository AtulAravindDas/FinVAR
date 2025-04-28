import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import joblib
import sklearn

st.set_page_config(page_title="FinVAR", layout="centered")
model=joblib.load("final_eps_predictor.pkl")

if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'ticker' not in st.session_state:
    st.session_state.ticker = ''

def go_home():
    st.session_state.page = 'home'
def go_app():
    st.session_state.page = 'app'
def set_page(name):
    st.session_state.page = name
def fresh_start():
    st.session_state.ticker = ''
    st.session_state.page = 'fresh'

if st.session_state.page == 'home':
    st.title("📊 FinVAR – Financial Assistant Referee")
    st.markdown("""
    Your financial assistant referee – reviewing every ticker, flagging every risk.

    🧠 **Understand the market.**  
    🚨 **Flag the risks.**  
    💼 **Make smarter investment moves.**
    ---
    ## 🚀 What is FinVAR?
    FinVAR is a financial visualization and analysis tool that not only presents key profitability, growth, leverage, and liquidity metrics, but also uses Machine Learning to predict the future Earnings Per Share (EPS) of companies — helping investors and analysts make better-informed decisions.

    ---
    ## 📈 Key Features
    - **Company Insights:** Real-time company descriptions and financials.
    - **Profitability Overview:** ROE, Gross Margin, Net Margin, Asset Turnover, Financial Leverage.
    - **Growth Overview:** Revenue Growth and EBITDA Growth visualization.
    - **Leverage and Liquidity Overview:** Debt Ratios and Free Cash Flow.
    - **Stock Price and Volatility Analysis:** 1-year trend analysis and volatility.
    - **EPS Prediction Engine:** Trained ML model forecasts future EPS based on real-time financials.""")

   
    st.button("🚀 Enter FinVAR App", on_click=go_app)
elif st.session_state.page == 'app':
    st.title("🔍 FinVAR – Start Analysis")
    st.session_state.ticker = st.text_input("Enter a Stock Ticker (e.g., AAPL, MSFT):", value=st.session_state.ticker)

    if st.session_state.ticker:
        ticker = yf.Ticker(st.session_state.ticker)
        info = ticker.info

        if not info or 'longName' not in info:
            st.error("❌ Invalid ticker. Please try again.")
        else:
            company_name = info.get('longName', 'N/A')
            st.success(f"Company: {company_name}")

            st.subheader("📂 Select an Analysis Section:")
            st.button("📝 Show Description", on_click=lambda: set_page('description'))
            st.button("💰 Current Price", on_click=lambda: set_page('price'))
            st.button("📘 Profitability Ratios", on_click=lambda: set_page('profitability'))
            st.button("📈 Growth Overview", on_click=lambda: set_page('growth'))
            st.button("⚡ Leverage Overview", on_click=lambda: set_page('leverage'))
            st.button("💧 Liquidity & Dividend Overview", on_click=lambda: set_page('liquidity'))
            st.button("📉 Stock Price & Volatility", on_click=lambda: set_page('volatility'))
            st.button("🔮 Predict Next Year EPS", on_click=lambda: set_page('eps_prediction'))
            st.button("🧹 Fresh Start", on_click=fresh_start)

elif st.session_state.page == 'fresh':
    st.title("🧹 Fresh Start")
    st.success("You have refreshed the app! 🔄")
    st.button("🏠 Go to Home", on_click=go_home)

elif st.session_state.page == 'description':
    st.title("📝 Company Description")
    ticker = yf.Ticker(st.session_state.ticker)
    description = ticker.info.get('longBusinessSummary', 'N/A')
    st.write(description)
    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == 'price':
    st.subheader("💰 Current Price")
    ticker = yf.Ticker(st.session_state.ticker)
    price = ticker.info.get('currentPrice', 'N/A')
    prev_close = ticker.info.get('previousClose', 'N/A')
    if price != 'N/A' and prev_close != 'N/A':
        change = price - prev_close
        pct_change = (change / prev_close) * 100
        st.metric("Current Price (USD)", f"${price:.2f}", f"{pct_change:+.2f}%")
    else:
        st.warning("Price data unavailable.")
    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == 'profitability':
    st.subheader("📘 Profitability Ratios Overview")
    ticker = yf.Ticker(st.session_state.ticker)

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
    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == "growth":
    st.subheader("📈 Expanded Growth Overview")
    ticker = yf.Ticker(st.session_state.ticker)
    income = ticker.financials
    cashflow = ticker.cashflow

    # Create Growth DataFrame
    growth_df = pd.DataFrame()
    growth_df['Total Revenue'] = income.T.get('Total Revenue')
    growth_df['EBITDA'] = income.T.get('EBITDA')
    growth_df['Net Income'] = income.T.get('Net Income')
    growth_df['Operating Cash Flow'] = cashflow.T.get('Operating Cash Flow')

    st.plotly_chart(
        px.line(
            growth_df,
            x=growth_df.index.year,
            y=growth_df.columns,
            markers=True,
            title="Raw Financial Metrics Over Time",
            template="plotly_dark"
        ),
        use_container_width=True
    )

    latest_years = growth_df.dropna().index.sort_values()[-2:]  

    if len(latest_years) == 2:
        prev_year = latest_years[0]
        latest_year = latest_years[1]

        revenue_growth = ((growth_df.loc[latest_year, 'Total Revenue'] - growth_df.loc[prev_year, 'Total Revenue']) / growth_df.loc[prev_year, 'Total Revenue']) * 100
        ebitda_growth = ((growth_df.loc[latest_year, 'EBITDA'] - growth_df.loc[prev_year, 'EBITDA']) / growth_df.loc[prev_year, 'EBITDA']) * 100
        net_income_growth = ((growth_df.loc[latest_year, 'Net Income'] - growth_df.loc[prev_year, 'Net Income']) / growth_df.loc[prev_year, 'Net Income']) * 100
        op_cashflow_growth = ((growth_df.loc[latest_year, 'Operating Cash Flow'] - growth_df.loc[prev_year, 'Operating Cash Flow']) / growth_df.loc[prev_year, 'Operating Cash Flow']) * 100
    else:
        revenue_growth = ebitda_growth = net_income_growth = op_cashflow_growth = None

    summary_text = ""

    if revenue_growth is not None:
        if revenue_growth > 10:
            summary_text += f"✅ Strong Revenue Growth: {revenue_growth:.2f}%\n\n"
        else:
            summary_text += f"⚠️ Moderate or Low Revenue Growth: {revenue_growth:.2f}%\n\n"
    else:
        summary_text += "⚠️ Revenue Growth data unavailable.\n\n"

    if ebitda_growth is not None:
        if ebitda_growth > 10:
            summary_text += f"✅ Strong EBITDA Growth: {ebitda_growth:.2f}%\n\n"
        else:
            summary_text += f"⚠️ EBITDA Growth below ideal: {ebitda_growth:.2f}%\n\n"
    else:
        summary_text += "⚠️ EBITDA Growth data unavailable.\n\n"

    if net_income_growth is not None:
        if net_income_growth > 10:
            summary_text += f"✅ Strong Net Income Growth: {net_income_growth:.2f}%\n\n"
        else:
            summary_text += f"⚠️ Weak Net Income Growth: {net_income_growth:.2f}%\n\n"
    else:
        summary_text += "⚠️ Net Income Growth data unavailable.\n\n"

    if op_cashflow_growth is not None:
        if op_cashflow_growth > 10:
            summary_text += f"✅ Strong Operating Cash Flow Growth: {op_cashflow_growth:.2f}%\n\n"
        else:
            summary_text += f"⚠️ Weak Operating Cash Flow Growth: {op_cashflow_growth:.2f}%\n\n"
    else:
        summary_text += "⚠️ Operating Cash Flow Growth data unavailable.\n\n"

    st.subheader("🔍 FinVAR Summary: Growth Overview")
    st.info(summary_text)

    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page=="leverage":
    st.subheader("⚡ Leverage Ratios Overview")
    ticker = yf.Ticker(st.session_state.ticker)
    balance = ticker.balance_sheet.T
    leverage_df = pd.DataFrame()
    leverage_df['Debt-to-Equity'] = balance['Total Liabilities Net Minority Interest'] / balance['Common Stock Equity']
    leverage_df['Debt-to-Assets'] = balance['Total Liabilities Net Minority Interest'] / balance['Total Assets']
    leverage_df.index = leverage_df.index.year
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

    st.button("⬅️ Back", on_click=go_app)

