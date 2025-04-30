import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import joblib
import sklearn
import requests

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

@st.cache_data(ttl=3600)
def get_info_safe(ticker):
    try:
        info = ticker.info
        if not info or 'longName' not in info:
            return {"error": "invalid_or_empty"}
        return info
    except Exception as e:
        if "429" in str(e):
            return {"error": "rate_limit"}
        return {"error": str(e)}

@st.cache_resource
def load_ticker(ticker_symbol):
    return yf.Ticker(ticker_symbol)

        
if st.session_state.page == 'home':
    st.image("FinVAR.png",width=300)
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
    - **EPS Prediction Engine:** Trained ML model forecasts future EPS based on real-time financials.
    ---
    Click the button below to start!""")
    
   
    st.button("🚀 Enter FinVAR App", on_click=go_app)
elif st.session_state.page == 'app':
    st.title("🔍 FinVAR – Start Analysis")
    st.session_state.ticker = st.text_input("Enter a Stock Ticker (e.g., AAPL, MSFT):", value=st.session_state.ticker)

    if st.session_state.ticker:
        info = get_ticker_info(st.session_state.ticker)
        if "error" in info:
            error_msg = info["error"]
            if "rate_limit" in error_msg:
                st.error("⚠️ Yahoo Finance rate limit reached. Please wait a few minutes and try again.")
            elif "invalid_or_empty" in error_msg:
                st.error("❌ Invalid or empty ticker. Please try another.")
            else:
                st.error(f"⚠️ Unexpected error: {error_msg}")
            st.stop()

        
        company_name = info.get('longName', 'N/A')
        st.success(f"Company: {company_name}")

        st.subheader("📂 Select an Analysis Section:")

        if st.button("📝 Show Description"):
            set_page('description')
        if st.button("💰 Current Price"):
            set_page('price')
        if st.button("📘 Profitability Ratios"):
            set_page('profitability')
        if st.button("📈 Growth Overview"):
            set_page('growth')
        if st.button("⚡ Leverage Overview"):
            set_page('leverage')
        if st.button("💧 Liquidity & Dividend Overview"):
            set_page('liquidity')
        if st.button("📉 Stock Price & Volatility"):
            set_page('volatility')
        if st.button("🔮 Predict Next Year EPS"):
            set_page('eps_prediction')
        if st.button("🧹 Fresh Start"):
            fresh_start()


elif st.session_state.page == 'fresh':
    st.title("🧹 Fresh Start")
    st.success("You have refreshed the app! 🔄")
    st.button("🏠 Go to Home", on_click=go_home)

elif st.session_state.page == 'description':
    st.title("📝 Company Description")
    info = get_ticker_info(st.session_state.ticker)
    if "error" in info:
        st.error("⚠️ Unable to fetch company description. Rate limit or error occurred.")
        st.stop()
    description = info.get('longBusinessSummary', 'N/A')
    st.write(description)
    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == 'price':
    st.subheader("💰 Current Price (Fast Info)")

    ticker = load_ticker(st.session_state.ticker)
    fast_info = ticker.fast_info

    price = fast_info.get('last_price', None)
    prev_close = fast_info.get('previous_close', None)

    if price is not None and prev_close is not None:
        change = price - prev_close
        pct_change = (change / prev_close) * 100
        st.metric("Current Price (USD)", f"${price:.2f}", f"{pct_change:+.2f}%")
    else:
        st.warning("⚠️ Price data unavailable or rate-limited.")

    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == 'profitability':
    st.subheader("📘 Profitability Ratios Overview")
    ticker = load_ticker(st.session_state.ticker)
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
    ticker = load_ticker(st.session_state.ticker)
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
    ticker = load_ticker(st.session_state.ticker)
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
    
elif st.session_state.page=="liquidity":
    st.subheader("💧 Liquidity and Dividend Overview")
    ticker = load_ticker(st.session_state.ticker)
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

    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page=="volatility":
    st.subheader("📈 Stock Price & Volatility Overview")
    ticker = load_ticker(st.session_state.ticker)
    hist = ticker.history(period="1y")
    if not hist.empty:
        hist['Daily Return'] = hist['Close'].pct_change()
        volatility = hist['Daily Return'].std() * np.sqrt(252)
        st.line_chart(hist['Close'])
        st.subheader(f"Annualized Volatility: {volatility:.2%}")
    else:
        st.warning("No historical data available.")

    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page=="eps_prediction":
    st.subheader("🔮 EPS Prediction for 2025")
    ticker = load_ticker(st.session_state.ticker)
    try:
        income = ticker.financials
        balance = ticker.balance_sheet
        cashflow = ticker.cashflow
        info = get_info_safe(ticker)
        if "error" in info:
            st.error(f"❌ EPS prediction failed: {info['error']}")
            st.button("⬅️ Back", on_click=go_app)
            st.stop()

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

        
        previous_revenue = income.loc[income.index[-2], 'Total Revenue'] if len(income.index) > 1 else np.nan
        previous_eps = info.get('epsTrailingTwelveMonths', np.nan) # fallback if past EPS not available

        revenue_growth = ((revenue - previous_revenue) / previous_revenue) if previous_revenue else 0
        eps_growth = 0  
        
        roa_to_revenue = roa / revenue if revenue != 0 else 0
        roe_to_roa = roe / roa if roa != 0 else 0
        debt_to_income = de_ratio / revenue if revenue != 0 else 0
        intcov_per_curr = intcov_ratio / curr_ratio if curr_ratio != 0 else 0
        opmad_to_npm = opmad / npm if npm != 0 else 0

        eps_3yr_avg = eps  
        revenue_3yr_avg = revenue  

        features = np.array([[ eps, eps_3yr_avg, roe, npm, opmad_to_npm,revenue_3yr_avg, intcov_per_curr, revenue_growth,roa_to_revenue, intcov_ratio]])


        features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)

        predicted_eps = model.predict(features)[0]

        st.success(f"🧠 Predicted EPS for 2025: **{predicted_eps:.2f} USD**")

        st.button("⬅️ Back", on_click=go_app)
    except Exception as e:
        st.error(f"Error in prediction:{e}")
        
