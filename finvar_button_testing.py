import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import joblib
import requests

API_KEY = st.secrets["FMP_API_KEY"]
BASE_URL = "https://financialmodelingprep.com/api/v3"
model = joblib.load("final_eps_predictor.pkl")

if 'ticker_data_cache' not in st.session_state:
    st.session_state.ticker_data_cache = {}

@st.cache_data(ttl=3600)
def get_all_ticker_data(ticker_symbol):
    ticker_symbol = ticker_symbol.upper()
    if ticker_symbol in st.session_state.ticker_data_cache and 'complete_data' in st.session_state.ticker_data_cache[ticker_symbol]:
        return st.session_state.ticker_data_cache[ticker_symbol]['complete_data']

    try:
        # Use a session to make a single connection for all requests
        with requests.Session() as session:
            # Make all API calls at once
            profile_url = f"{BASE_URL}/profile/{ticker_symbol}?apikey={API_KEY}"
            quote_url = f"{BASE_URL}/quote/{ticker_symbol}?apikey={API_KEY}"
            income_url = f"{BASE_URL}/income-statement/{ticker_symbol}?limit=5&apikey={API_KEY}"
            balance_url = f"{BASE_URL}/balance-sheet-statement/{ticker_symbol}?limit=5&apikey={API_KEY}"
            cashflow_url = f"{BASE_URL}/cash-flow-statement/{ticker_symbol}?limit=5&apikey={API_KEY}"
            # Add historical price data endpoint
            historical_url = f"{BASE_URL}/historical-price-full/{ticker_symbol}?apikey={API_KEY}"
            
            # Execute all requests
            profile_data = session.get(profile_url).json()
            quote_data = session.get(quote_url).json()
            income_data = session.get(income_url).json()
            balance_data = session.get(balance_url).json()
            cashflow_data = session.get(cashflow_url).json()
            historical_data = session.get(historical_url).json()

        if not profile_data or not quote_data:
            raise ValueError("Invalid data returned from FMP API.")

        profile = profile_data[0]
        quote = quote_data[0]

        # Company info
        info = {
            "longName": profile.get("companyName", "N/A"),
            "industry": profile.get("industry", "N/A"),
            "description": profile.get("description", "N/A"),
            "currentPrice": quote.get("price", None),
            "previousClose": quote.get("previousClose", None),
            "trailingPE": profile.get("pe", None),
            "epsTrailingTwelveMonths": profile.get("eps", None)
        }
        
        # Financial statements
        income_df = pd.DataFrame(income_data).set_index("date").T if income_data else pd.DataFrame()
        balance_df = pd.DataFrame(balance_data).set_index("date").T if balance_data else pd.DataFrame()
        cashflow_df = pd.DataFrame(cashflow_data).set_index("date").T if cashflow_data else pd.DataFrame()
        
        # Historical price data
        history_df = pd.DataFrame(historical_data.get('historical', [])) if 'historical' in historical_data else pd.DataFrame()
        if not history_df.empty:
            history_df['date'] = pd.to_datetime(history_df['date'])
            history_df.set_index('date', inplace=True)
            history_df = history_df.sort_index()
        
        # Process dataframes
        for df in [income_df, balance_df, cashflow_df]:
            if not df.empty:
                df.columns = pd.to_datetime(df.columns)
                df = df.apply(pd.to_numeric, errors='coerce')
        
        # Store complete data
        complete_data = {
            'info': info,
            'financials': (income_df, balance_df, cashflow_df, history_df)
        }
        
        # Cache the results
        st.session_state.ticker_data_cache[ticker_symbol] = {'complete_data': complete_data}
        return complete_data
        
    except Exception as e:
        return {
            'info': {"error": str(e)},
            'financials': (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
        }

st.set_page_config(page_title="FinVAR", layout="centered")

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
    # Force rerun to update the UI immediately

def fresh_start():
    st.session_state.ticker = ''
    st.session_state.page = 'fresh'

if st.session_state.page == 'home':
    st.image("FinVAR.png", width=300)
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
    if st.button("🚀 Enter FinVAR App", key="enter_app"):
        go_app()

elif st.session_state.page == 'app':
    st.title("🔍 FinVAR – Start Analysis")
    st.session_state.ticker = st.text_input("Enter a Stock Ticker (e.g., AAPL, MSFT):", value=st.session_state.ticker)

    if st.session_state.ticker:
        # Get all data at once
        all_data = get_all_ticker_data(st.session_state.ticker)
        info = all_data['info']

        if 'error' in info:
            st.error(f"Error fetching data: {info['error']}")
        else:
            st.success(f"Company: {info['longName']}")
            
            if info['currentPrice'] is not None and info['previousClose'] is not None:
                change = info['currentPrice'] - info['previousClose']
                pct = (change / info['previousClose']) * 100 if info['previousClose'] != 0 else 0
                st.metric("Price", f"${info['currentPrice']:.2f}", f"{pct:+.2f}%")
            else:
                st.warning("Price data unavailable.")

            st.subheader("📂 Select an Analysis Section:")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📝 Show Description", key="btn_description", use_container_width=True):
                    set_page('description')
                if st.button("📘 Profitability Ratios", key="btn_profit", use_container_width=True):
                    set_page('profitability')
                if st.button("⚡ Leverage Overview", key="btn_leverage", use_container_width=True):
                    set_page('leverage')
                if st.button("📉 Stock Price & Volatility", key="btn_volatility", use_container_width=True):
                    set_page('volatility')
            with col2:
                if st.button("💰 Current Price", key="btn_price", use_container_width=True):
                    set_page('price')
                if st.button("📈 Growth Overview", key="btn_growth", use_container_width=True):
                    set_page('growth')
                if st.button("💧 Liquidity & Dividend", key="btn_liquidity", use_container_width=True):
                    set_page('liquidity')
                if st.button("🔮 Predict Next Year EPS", key="btn_eps", use_container_width=True):
                    set_page('eps_prediction')
            
            if st.button("🧹 Fresh Start", key="btn_fresh", use_container_width=True):
                fresh_start()

elif st.session_state.page == 'description':
    st.title("📝 Company Description")
    all_data = get_all_ticker_data(st.session_state.ticker)
    info = all_data['info']
    if 'error' in info:
        st.error("⚠️ Unable to fetch company description. API issue.")
    else:
        st.markdown(f"**{info['description']}**")
    st.write("")
    st.write("")
    if st.button("⬅️ Back to Main Menu", key="desc_back", use_container_width=True):
        go_app()
  
elif st.session_state.page == 'price':
    st.title("💰 Current Stock Price")
    all_data = get_all_ticker_data(st.session_state.ticker)
    info = all_data['info']
    if 'error' in info:
        st.error("⚠️ Unable to fetch price data. API issue.")
    elif info['currentPrice'] is not None and info['previousClose'] is not None:
        change = info['currentPrice'] - info['previousClose']
        pct_change = (change / info['previousClose']) * 100
        st.metric("Current Price (USD)", f"${info['currentPrice']:.2f}", f"{pct_change:+.2f}%")
    else:
        st.warning("Price data not available.")
    st.write("")
    st.write("")
    if st.button("⬅️ Back to Main Menu", key="price_back", use_container_width=True):
        go_app()

elif st.session_state.page == 'profitability':
    st.title("📘 Profitability Ratios Overview")
    all_data = get_all_ticker_data(st.session_state.ticker)
    income_df, balance_df, _, _ = all_data['financials']

    if income_df.empty or balance_df.empty:
        st.warning("⚠️ Financial data not available for this ticker.")
        if st.button("⬅️ Back to Main Menu", key="profit_back_empty", use_container_width=True):
            go_app()
    else:
        df = pd.DataFrame()
        df['Net Income'] = income_df.loc['netIncome']
        df['Gross Profit'] = income_df.loc['grossProfit']
        df['Revenue'] = income_df.loc['revenue']
        df['EBITDA'] = income_df.loc['ebitda']
        df['EBIT'] = income_df.loc['operatingIncome']
        df['Equity'] = balance_df.loc['totalStockholdersEquity']
        df['Assets'] = balance_df.loc['totalAssets']
        df['Liabilities'] = balance_df.loc['totalLiabilities']

        df = df.dropna().T
        df.columns = df.columns.year
        df = df.T
        df = df.apply(pd.to_numeric, errors='coerce')

        df['ROE (%)'] = (df['Net Income'] / df['Equity']) * 100
        df['Gross Margin (%)'] = (df['Gross Profit'] / df['Revenue']) * 100
        df['Net Margin (%)'] = (df['Net Income'] / df['Revenue']) * 100
        df['Asset Turnover'] = df['Revenue'] / df['Assets']
        df['Financial Leverage'] = df['Assets'] / df['Equity']

        st.plotly_chart(px.line(df, x=df.index, y='ROE (%)', title='Return on Equity (%)', markers=True, template='plotly_dark'), use_container_width=True)
        st.plotly_chart(px.bar(df, x=df.index, y='Gross Margin (%)', title='Gross Profit Margin (%)', template='plotly_dark'), use_container_width=True)
        st.plotly_chart(px.line(df, x=df.index, y='Net Margin (%)', title='Net Profit Margin (%)', markers=True, template='plotly_dark'), use_container_width=True)
        st.plotly_chart(px.area(df, x=df.index, y='Asset Turnover', title='Asset Turnover', template='plotly_dark'), use_container_width=True)
        st.plotly_chart(px.scatter(df, x=df.index, y='Financial Leverage', title='Financial Leverage', size='Financial Leverage', template='plotly_dark'), use_container_width=True)

        latest_year = df.index.max()
        roe_latest = df.loc[latest_year, 'ROE (%)']
        gross_margin_latest = df.loc[latest_year, 'Gross Margin (%)']
        net_margin_latest = df.loc[latest_year, 'Net Margin (%)']
        asset_turnover_latest = df.loc[latest_year, 'Asset Turnover']
        summary_text = ""
        if roe_latest > 15:
            summary_text += f"✅ Strong ROE of {roe_latest:.2f}% indicates efficient use of equity.\n"
        else:
            summary_text += f"⚠️ ROE of {roe_latest:.2f}% is below ideal; check company's return generation.\n"

        if gross_margin_latest > 40:
            summary_text += f"✅ Excellent Gross Margin ({gross_margin_latest:.2f}%) suggests strong pricing power.\n"
        elif gross_margin_latest > 20:
            summary_text += f"✅ Moderate Gross Margin ({gross_margin_latest:.2f}%), acceptable for most industries.\n"
        else:
            summary_text += f"⚠️ Weak Gross Margin ({gross_margin_latest:.2f}%) — may face margin pressure.\n"

        if net_margin_latest > 10:
            summary_text += f"✅ Net Profit Margin of {net_margin_latest:.2f}% is healthy.\n"
        else:
            summary_text += f"⚠️ Thin Net Profit Margin ({net_margin_latest:.2f}%) could be a concern.\n"

        if asset_turnover_latest > 1:
            summary_text += f"✅ High Asset Turnover ({asset_turnover_latest:.2f}) — efficient asset use.\n"
        else:
            summary_text += f"⚠️ Low Asset Turnover ({asset_turnover_latest:.2f}) — inefficient use of assets.\n"

        st.subheader("🔍 FinVAR Summary: Profitability Overview")
        st.info(summary_text)

        st.write("")
        st.write("")
        if st.button("⬅️ Back to Main Menu", key="profit_back", use_container_width=True):
            go_app()
            
elif st.session_state.page == "growth":
    st.subheader("📈 Expanded Growth Overview")
    all_data = get_all_ticker_data(st.session_state.ticker)
    income_df, _, cashflow_df, _ = all_data['financials']
    
    # Create Growth DataFrame
    growth_df = pd.DataFrame()
    growth_df['Total Revenue'] = income_df.loc['revenue'] if 'revenue' in income_df.index else None
    growth_df['EBITDA'] = income_df.loc['ebitda'] if 'ebitda' in income_df.index else None
    growth_df['Net Income'] = income_df.loc['netIncome'] if 'netIncome' in income_df.index else None
    growth_df['Operating Cash Flow'] = cashflow_df.loc['operatingCashFlow'] if 'operatingCashFlow' in cashflow_df.index else None

    st.plotly_chart(
        px.line(
            growth_df,
            x=growth_df.index,
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

        revenue_growth = ((growth_df.loc[latest_year, 'Total Revenue'] - growth_df.loc[prev_year, 'Total Revenue']) / growth_df.loc[prev_year, 'Total Revenue']) * 100 if 'Total Revenue' in growth_df.columns else None
        ebitda_growth = ((growth_df.loc[latest_year, 'EBITDA'] - growth_df.loc[prev_year, 'EBITDA']) / growth_df.loc[prev_year, 'EBITDA']) * 100 if 'EBITDA' in growth_df.columns else None
        net_income_growth = ((growth_df.loc[latest_year, 'Net Income'] - growth_df.loc[prev_year, 'Net Income']) / growth_df.loc[prev_year, 'Net Income']) * 100 if 'Net Income' in growth_df.columns else None
        op_cashflow_growth = ((growth_df.loc[latest_year, 'Operating Cash Flow'] - growth_df.loc[prev_year, 'Operating Cash Flow']) / growth_df.loc[prev_year, 'Operating Cash Flow']) * 100 if 'Operating Cash Flow' in growth_df.columns else None
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

    st.write("")
    st.write("")
    if st.button("⬅️ Back to Main Menu", key="growth_back", use_container_width=True):
        go_app()

elif st.session_state.page == "leverage":
    st.subheader("⚡ Leverage Ratios Overview")
    all_data = get_all_ticker_data(st.session_state.ticker)
    balance_df = all_data['financials'][1]
    
    leverage_df = pd.DataFrame()
    leverage_df['Debt-to-Equity'] = balance_df.loc['totalLiabilities'] / balance_df.loc['totalStockholdersEquity'] if ('totalLiabilities' in balance_df.index and 'totalStockholdersEquity' in balance_df.index) else None
    leverage_df['Debt-to-Assets'] = balance_df.loc['totalLiabilities'] / balance_df.loc['totalAssets'] if ('totalLiabilities' in balance_df.index and 'totalAssets' in balance_df.index) else None
    
    st.plotly_chart(px.bar(leverage_df, x=leverage_df.index, y=['Debt-to-Equity', 'Debt-to-Assets'], title="Leverage Ratios", template="plotly_dark"), use_container_width=True)

    if not leverage_df.empty and not leverage_df['Debt-to-Equity'].isna().all() and not leverage_df['Debt-to-Assets'].isna().all():
        latest_year = leverage_df.dropna().index.max()
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
    else:
        st.warning("⚠️ Leverage data not available for this ticker.")

    st.write("")
    st.write("")
    if st.button("⬅️ Back to Main Menu", key="leverage_back", use_container_width=True):
        go_app()

elif st.session_state.page == "liquidity":
    st.subheader("💧 Liquidity and Dividend Overview")
    all_data = get_all_ticker_data(st.session_state.ticker)
    balance_df, cashflow_df = all_data['financials'][1], all_data['financials'][2]
    
    liquidity_df = pd.DataFrame()
    liquidity_df['Current Ratio'] = balance_df.loc['totalCurrentAssets'] / balance_df.loc['totalCurrentLiabilities'] if ('totalCurrentAssets' in balance_df.index and 'totalCurrentLiabilities' in balance_df.index) else None
    liquidity_df['FCF'] = cashflow_df.loc['operatingCashFlow'] - cashflow_df.loc['capitalExpenditure'] if ('operatingCashFlow' in cashflow_df.index and 'capitalExpenditure' in cashflow_df.index) else None
    
    st.dataframe(liquidity_df)
    st.plotly_chart(px.line(liquidity_df, x=liquidity_df.index, y=['Current Ratio', 'FCF'], markers=True, title="Liquidity & FCF Trends", template="plotly_dark"), use_container_width=True)

    if not liquidity_df.empty and not liquidity_df['Current Ratio'].isna().all() and not liquidity_df['FCF'].isna().all():
        latest_year = liquidity_df.dropna().index.max()
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
    else:
        st.warning("⚠️ Liquidity data not available for this ticker.")

    st.write("")
    st.write("")
    if st.button("⬅️ Back to Main Menu", key="liquidity_back", use_container_width=True):
        go_app()

elif st.session_state.page == "volatility":
    st.subheader("📈 Stock Price & Volatility Overview")
    all_data = get_all_ticker_data(st.session_state.ticker)
    history_df = all_data['financials'][3]
    
    if history_df.empty:
        st.warning("⚠️ Historical price data not available for this ticker.")
    else:
        # Calculate daily returns
        history_df['Daily Return'] = history_df['close'].pct_change()
        
        # Calculate annualized volatility (252 trading days per year)
        volatility = history_df['Daily Return'].std() * np.sqrt(252)
        
        # Display stock price chart
        st.subheader("Price History")
        fig = px.line(
            history_df, 
            y='close',
            title=f"{st.session_state.ticker} Price History",
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Display volatility metrics
        st.subheader(f"Annualized Volatility: {volatility:.2%}")
        
        # Show additional metrics in columns
        col1, col2, col3 = st.columns(3)
        with col1:
            recent_close = history_df['close'].iloc[-1]
            st.metric("Latest Close", f"${recent_close:.2f}")
        with col2:
            year_high = history_df['high'].max()
            st.metric("52-Week High", f"${year_high:.2f}")
        with col3:
            year_low = history_df['low'].min()
            st.metric("52-Week Low", f"${year_low:.2f}")
            
        # Add daily returns histogram
        st.subheader("Daily Returns Distribution")
        fig_hist = px.histogram(
            history_df, 
            x='Daily Return',
            nbins=50,
            title="Distribution of Daily Returns",
            template="plotly_dark"
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Summary text
        summary_text = ""
        if volatility > 0.4:
            summary_text += f"⚠️ High volatility ({volatility:.2%}): This stock shows significant price swings, indicating higher risk.\n\n"
        elif volatility > 0.2:
            summary_text += f"⚠️ Moderate volatility ({volatility:.2%}): This stock shows average market volatility.\n\n"
        else:
            summary_text += f"✅ Low volatility ({volatility:.2%}): This stock shows relatively stable price action.\n\n"
            
        # Add price trend information
        returns_30d = (history_df['close'].iloc[-1] / history_df['close'].iloc[-min(30, len(history_df))]) - 1
        if returns_30d > 0.05:
            summary_text += f"✅ Strong recent uptrend: {returns_30d:.2%} over the last month.\n\n"
        elif returns_30d < -0.05:
            summary_text += f"⚠️ Significant recent downtrend: {returns_30d:.2%} over the last month.\n\n"
        else:
            summary_text += f"⚠️ Sideways price action: {returns_30d:.2%} over the last month.\n\n"
        
        st.subheader("🔍 FinVAR Summary: Volatility Analysis")
        st.info(summary_text)

    st.write("")
    st.write("")
    if st.button("⬅️ Back to Main Menu", key="volatility_back", use_container_width=True):
        go_app()

elif st.session_state.page == "eps_prediction":
    st.subheader("🔮 EPS Prediction for 2025")
    all_data = get_all_ticker_data(st.session_state.ticker)
    info = all_data['info']
    income_df, balance_df, cashflow_df, _ = all_data['financials']
    
    try:
        # Ensure we have all required data
        if income_df.empty or balance_df.empty or cashflow_df.empty:
            raise ValueError("Financial data not available for this ticker")
            
        # Get the latest year data
        latest_year = income_df.columns.max()
        prev_year = income_df.columns[-2] if len(income_df.columns) > 1 else None
        
        # Extract necessary metrics with better error handling
        try:
            pe_exi = info.get('trailingPE', 0)
        except:
            pe_exi = 0
            
        try:
            npm = income_df.loc['netIncome', latest_year] / income_df.loc['revenue', latest_year] if 'netIncome' in income_df.index and 'revenue' in income_df.index else 0
        except:
            npm = 0
            
        try:
            opmad = income_df.loc['operatingIncome', latest_year] / income_df.loc['revenue', latest_year] if 'operatingIncome' in income_df.index and 'revenue' in income_df.index else 0
        except:
            opmad = 0
            
        try:
            roa = income_df.loc['netIncome', latest_year] / balance_df.loc['totalAssets', latest_year] if 'netIncome' in income_df.index and 'totalAssets' in balance_df.index else 0
        except:
            roa = 0
            
        try:
            roe = income_df.loc['netIncome', latest_year] / balance_df.loc['totalStockholdersEquity', latest_year] if 'netIncome' in income_df.index and 'totalStockholdersEquity' in balance_df.index else 0
        except:
            roe = 0
            
        try:
            de_ratio = balance_df.loc['totalLiabilities', latest_year] / balance_df.loc['totalStockholdersEquity', latest_year] if 'totalLiabilities' in balance_df.index and 'totalStockholdersEquity' in balance_df.index else 0
        except:
            de_ratio = 0
            
        try:
            intcov_ratio = income_df.loc['operatingIncome', latest_year] / income_df.loc['interestExpense', latest_year] if 'operatingIncome' in income_df.index and 'interestExpense' in income_df.index and income_df.loc['interestExpense', latest_year] != 0 else 0
        except:
            intcov_ratio = 0
            
        try:
            curr_ratio = balance_df.loc['totalCurrentAssets', latest_year] / balance_df.loc['totalCurrentLiabilities', latest_year] if 'totalCurrentAssets' in balance_df.index and 'totalCurrentLiabilities' in balance_df.index else 0
        except:
            curr_ratio = 0
            
        try:
            revenue = income_df.loc['revenue', latest_year] if 'revenue' in income_df.index else 0
        except:
            revenue = 0
            
        try:
            eps = info.get('epsTrailingTwelveMonths', 0)
        except:
            eps = 0
        
        # Calculate growth with error handling
        try:
            previous_revenue = income_df.loc['revenue', prev_year] if prev_year and 'revenue' in income_df.index else 0
            revenue_growth = ((revenue - previous_revenue) / previous_revenue) if previous_revenue != 0 else 0
        except:
            revenue_growth = 0
        
        # Calculate derived metrics with error handling
        try:
            roa_to_revenue = roa / revenue if revenue != 0 else 0
        except:
            roa_to_revenue = 0
            
        try:
            opmad_to_npm = opmad / npm if npm != 0 else 0
        except:
            opmad_to_npm = 0
            
        try:
            intcov_per_curr = intcov_ratio / curr_ratio if curr_ratio != 0 else 0
        except:
            intcov_per_curr = 0
        
        # Use simple averages
        eps_3yr_avg = eps
        revenue_3yr_avg = revenue
        
        # Prepare features for model, replacing NaN with 0
        features = np.array([[
            eps, eps_3yr_avg, roe, npm, opmad_to_npm,
            revenue_3yr_avg, intcov_per_curr, revenue_growth,
            roa_to_revenue, intcov_ratio
        ]])
        
        # Handle any NaN values explicitly
        features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Log the features for debugging
        st.write("Feature names:", ["eps", "eps_3yr_avg", "roe", "npm", "opmad_to_npm", 
                                  "revenue_3yr_avg", "intcov_per_curr", "revenue_growth", 
                                  "roa_to_revenue", "intcov_ratio"])
        st.write("Feature values (after NaN handling):", features[0])
        
        # Make prediction
        predicted_eps = model.predict(features)[0]
        
        # Display prediction
        st.success(f"🧠 Predicted EPS for 2025: **${predicted_eps:.2f}**")
        
        # Show comparison if current EPS is available
        if eps > 0:
            eps_growth_pct = ((predicted_eps - eps) / eps) * 100
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Current EPS", f"${eps:.2f}")
            with col2:
                st.metric("Projected Growth", f"{eps_growth_pct:+.2f}%")
            
            # Simple bar chart
            eps_data = pd.DataFrame({
                'Year': ['Current', '2025 (Predicted)'],
                'EPS': [eps, predicted_eps]
            })
            
            fig = px.bar(
                eps_data, 
                x='Year', 
                y='EPS', 
                title="EPS Comparison",
                template="plotly_dark",
                color='Year'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Prediction confidence
            st.info("""
            **Prediction Notes**:
            - This prediction is based on current financial metrics and historical patterns
            - Actual results may vary due to market conditions and company performance
            - The model performs best with complete financial data
            """)
        
    except Exception as e:
        st.error(f"Error in prediction: {str(e)}")
        st.info("""
        **Prediction Not Available**
        
        The EPS prediction requires complete financial data to make accurate forecasts.
        This could be due to:
        - Missing or incomplete financial data from the API
        - Division by zero in financial ratio calculations
        - Incompatible data format for the prediction model
        
        Try a different stock ticker with more complete financial data.
        """)
    
    st.write("")
    st.write("")
    if st.button("⬅️ Back to Main Menu", key="eps_back", use_container_width=True):
        go_app()
