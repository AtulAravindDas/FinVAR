import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import joblib
import sklearn
import requests
import time
import random
from functools import wraps

st.set_page_config(page_title="FinVAR", layout="centered")
model = joblib.load("final_eps_predictor.pkl")

if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'ticker' not in st.session_state:
    st.session_state.ticker = ''
if 'ticker_data_cache' not in st.session_state:
    st.session_state.ticker_data_cache = {}
if 'retry_delay' not in st.session_state:
    st.session_state.retry_delay = 1

def go_home():
    st.session_state.page = 'home'
def go_app():
    st.session_state.page = 'app'
def set_page(name):
    st.session_state.page = name
def fresh_start():
    st.session_state.ticker = ''
    st.session_state.page = 'fresh'

def retry_with_exponential_backoff(max_retries=3, initial_delay=1, exponential_base=2, jitter=True):
    """Retry decorator with exponential backoff and jitter."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use the global retry delay as a starting point
            delay = st.session_state.retry_delay
            num_retries = 0
            
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "429" in str(e) and num_retries < max_retries:
                        # Add jitter to prevent synchronized retries
                        sleep_time = delay * (exponential_base ** num_retries)
                        if jitter:
                            sleep_time = sleep_time * (1 + random.random())
                        
                        # Update global delay for future requests
                        st.session_state.retry_delay = min(sleep_time, 30)  # Cap at 30 seconds
                        
                        time.sleep(sleep_time)
                        num_retries += 1
                    else:
                        raise e
        return wrapper
    return decorator

@st.cache_resource
def load_ticker(ticker_symbol):
    """Enhanced version of load_ticker with retries."""
    # First check if we have a cached Ticker object
    if ticker_symbol in st.session_state.ticker_data_cache:
        return st.session_state.ticker_data_cache[ticker_symbol]['ticker_obj']
    
    # Try to load with retries
    for attempt in range(3):
        try:
            ticker = yf.Ticker(ticker_symbol)
            # Cache the ticker object
            if ticker_symbol not in st.session_state.ticker_data_cache:
                st.session_state.ticker_data_cache[ticker_symbol] = {}
            st.session_state.ticker_data_cache[ticker_symbol]['ticker_obj'] = ticker
            return ticker
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                # Exponential backoff
                time.sleep((2 ** attempt) + random.random())
            else:
                raise e
    
    return None  # Should not reach here if retries work

@retry_with_exponential_backoff(max_retries=3)
def fetch_ticker_info(ticker_symbol):
    """Fetch ticker info with retry mechanism."""
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    if not info or 'longName' not in info:
        return {"error": "invalid_or_empty"}
    return info

@st.cache_data(ttl=3600)
def get_ticker_info(ticker_symbol):
    """Get ticker info with caching and fallback."""
    # Check if we have cached data
    if ticker_symbol in st.session_state.ticker_data_cache and 'info' in st.session_state.ticker_data_cache[ticker_symbol]:
        return st.session_state.ticker_data_cache[ticker_symbol]['info']
    
    try:
        info = fetch_ticker_info(ticker_symbol)
        
        # Cache the successful result
        if ticker_symbol not in st.session_state.ticker_data_cache:
            st.session_state.ticker_data_cache[ticker_symbol] = {}
        st.session_state.ticker_data_cache[ticker_symbol]['info'] = info
        
        # Reset retry delay on success
        st.session_state.retry_delay = 1
        
        return info
    except Exception as e:
        if "429" in str(e):  # Rate limited
            # If we have some basic data cached, use that instead
            if ticker_symbol in st.session_state.ticker_data_cache:
                st.warning("⚠️ Using cached data due to Yahoo Finance rate limit. Some information may not be up-to-date.")
                if 'info' in st.session_state.ticker_data_cache[ticker_symbol]:
                    return st.session_state.ticker_data_cache[ticker_symbol]['info']
            
            return {"error": "rate_limit"}
        return {"error": str(e)}

@retry_with_exponential_backoff(max_retries=2)
def get_financial_data(ticker_obj, data_type):
    """
    Get financial data with retries
    data_type can be 'financials', 'balance_sheet', 'cashflow', 'history'
    """
    try:
        if data_type == 'financials':
            return ticker_obj.financials
        elif data_type == 'balance_sheet':
            return ticker_obj.balance_sheet
        elif data_type == 'cashflow':
            return ticker_obj.cashflow
        elif data_type == 'history':
            return ticker_obj.history(period="1y")
        else:
            raise ValueError(f"Unknown data_type: {data_type}")
    except Exception as e:
        # If we hit a rate limit, see if we have cached data
        if "429" in str(e) and ticker_obj.ticker in st.session_state.ticker_data_cache:
            cache_entry = st.session_state.ticker_data_cache[ticker_obj.ticker]
            if data_type in cache_entry:
                st.warning(f"⚠️ Using cached {data_type} data due to Yahoo Finance rate limit.")
                return cache_entry[data_type]
        # If no cached data or other error, re-raise
        raise

def get_financials_with_fallback(ticker_symbol, log_warning=True):
    """Get all financial data with caching and fallback"""
    ticker = load_ticker(ticker_symbol)
    cache_key = ticker_symbol
    
    # Initialize cache entry if needed
    if cache_key not in st.session_state.ticker_data_cache:
        st.session_state.ticker_data_cache[cache_key] = {}
    
    # Get all financial data with retries and caching
    try:
        financials = get_financial_data(ticker, 'financials')
        st.session_state.ticker_data_cache[cache_key]['financials'] = financials
    except Exception as e:
        if 'financials' not in st.session_state.ticker_data_cache[cache_key]:
            if log_warning:
                st.warning("⚠️ Could not retrieve financial data. Using placeholder data.")
            # Create empty DataFrame as fallback
            financials = pd.DataFrame()
        else:
            if log_warning:
                st.warning("⚠️ Using cached financial data due to API limitations.")
            financials = st.session_state.ticker_data_cache[cache_key]['financials']
    
    try:
        balance_sheet = get_financial_data(ticker, 'balance_sheet')
        st.session_state.ticker_data_cache[cache_key]['balance_sheet'] = balance_sheet
    except Exception as e:
        if 'balance_sheet' not in st.session_state.ticker_data_cache[cache_key]:
            if log_warning:
                st.warning("⚠️ Could not retrieve balance sheet data. Using placeholder data.")
            balance_sheet = pd.DataFrame()
        else:
            if log_warning:
                st.warning("⚠️ Using cached balance sheet data due to API limitations.")
            balance_sheet = st.session_state.ticker_data_cache[cache_key]['balance_sheet']
    
    try:
        cashflow = get_financial_data(ticker, 'cashflow')
        st.session_state.ticker_data_cache[cache_key]['cashflow'] = cashflow
    except Exception as e:
        if 'cashflow' not in st.session_state.ticker_data_cache[cache_key]:
            if log_warning:
                st.warning("⚠️ Could not retrieve cash flow data. Using placeholder data.")
            cashflow = pd.DataFrame()
        else:
            if log_warning:
                st.warning("⚠️ Using cached cash flow data due to API limitations.")
            cashflow = st.session_state.ticker_data_cache[cache_key]['cashflow']
    
    try:
        history = get_financial_data(ticker, 'history')
        st.session_state.ticker_data_cache[cache_key]['history'] = history
    except Exception as e:
        if 'history' not in st.session_state.ticker_data_cache[cache_key]:
            if log_warning:
                st.warning("⚠️ Could not retrieve historical data. Using placeholder data.")
            history = pd.DataFrame()
        else:
            if log_warning:
                st.warning("⚠️ Using cached historical data due to API limitations.")
            history = st.session_state.ticker_data_cache[cache_key]['history']
    
    return financials, balance_sheet, cashflow, history

# App interface starts here
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
                st.error("⚠️ Yahoo Finance rate limit reached. The app will automatically retry with increasing delays. Please wait a moment and try again, or try a different ticker.")
                # Prefetch data in the background to use later
                try:
                    get_financials_with_fallback(st.session_state.ticker, log_warning=False)
                except:
                    pass
            elif "invalid_or_empty" in error_msg:
                st.error("❌ Invalid or empty ticker. Please try another.")
            else:
                st.error(f"⚠️ Unexpected error: {error_msg}")
            st.stop()

        company_name = info.get('longName', 'N/A')
        st.success(f"Company: {company_name}")

        # Prefetch data in the background to use later
        try:
            get_financials_with_fallback(st.session_state.ticker, log_warning=False)
        except:
            pass

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
    st.subheader("💰 Current Price")
    info = get_ticker_info(st.session_state.ticker)
    if "error" in info:
        st.error("⚠️ Unable to fetch company description. Rate limit or error occurred.")
        st.stop()
    price = info.get('currentPrice', 'N/A')
    prev_close = info.get('previousClose', 'N/A')
    if price != 'N/A' and prev_close != 'N/A':
        change = price - prev_close
        pct_change = (change / prev_close) * 100
        st.metric("Current Price (USD)", f"${price:.2f}", f"{pct_change:+.2f}%")
    else:
        st.warning("Price data unavailable.")
    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == 'profitability':
    st.subheader("📘 Profitability Ratios Overview")
    
    try:
        income, balance, cashflow, _ = get_financials_with_fallback(st.session_state.ticker)
        
        if income.empty or balance.empty:
            st.error("⚠️ Insufficient financial data available for this ticker.")
            st.button("⬅️ Back", on_click=go_app)
            st.stop()
            
        ideal_income_order = ["Total Revenue", "Gross Profit", "EBITDA", "EBIT", "Net Income"]
        ideal_balance_order = ["Total Assets", "Common Stock Equity", "Total Liabilities Net Minority Interest"]
        
        # Make sure the required columns exist
        if not all(item in income.index for item in ideal_income_order) or not all(item in balance.index for item in ideal_balance_order):
            st.warning("⚠️ Some financial data is missing. Analysis may be incomplete.")
            # Filter to only use available columns
            income_available = [item for item in ideal_income_order if item in income.index]
            balance_available = [item for item in ideal_balance_order if item in balance.index]
            income = income.loc[income_available]
            balance = balance.loc[balance_available]
        else:
            income = income.loc[ideal_income_order]
            balance = balance.loc[ideal_balance_order]
        
        income = income.T
        balance = balance.T
        
        df = pd.DataFrame()
        
        # Safely add columns with error handling
        try:
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
            
            # Calculate ratios with safeguards
            df['ROE (%)'] = (df['Net Income'] / df['Shareholders Equity']) * 100
            df['Gross Profit Margin (%)'] = (df['Gross Profit'] / df['Total Revenue']) * 100
            df['Asset Turnover'] = df['Total Revenue'] / df['Total Assets']
            df['Financial Leverage'] = df['Total Assets'] / df['Shareholders Equity']
            df['Net Profit Margin (%)'] = (df['Net Income'] / df['Total Revenue']) * 100
            
            # Display charts with error handling
            st.subheader("📈 Interactive Financial Visuals")
            
            try:
                st.plotly_chart(px.line(df, x=df.index, y="ROE (%)", markers=True, title="Return on Equity (%)", template="plotly_dark"), use_container_width=True)
                st.plotly_chart(px.bar(df, x=df.index, y="Gross Profit Margin (%)", title="Gross Profit Margin (%)", template="plotly_dark"), use_container_width=True)
                st.plotly_chart(px.area(df, x=df.index, y="Asset Turnover", title="Asset Turnover", template="plotly_dark"), use_container_width=True)
                st.plotly_chart(px.scatter(df, x=df.index, y="Financial Leverage", size="Financial Leverage", title="Financial Leverage", template="plotly_dark"), use_container_width=True)
                st.plotly_chart(px.bar(df, x=df.index.astype(str), y="Net Profit Margin (%)", title="Net Profit Margin (%)", template="plotly_dark"), use_container_width=True)
                st.plotly_chart(px.line(df, x=df.index, y=["EBITDA", "EBIT"], markers=True, title="EBITDA vs EBIT", template="plotly_dark"), use_container_width=True)
            
                # Create FinVAR summary
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
                
            except Exception as e:
                st.error(f"⚠️ Error creating visualizations: {e}")
                
        except Exception as e:
            st.error(f"⚠️ Error processing financial data: {e}")
    
    except Exception as e:
        st.error(f"⚠️ Error retrieving financial data: {e}")
    
    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == "growth":
    st.subheader("📈 Expanded Growth Overview")
    
    try:
        income, balance, cashflow, _ = get_financials_with_fallback(st.session_state.ticker)
        
        if income.empty or cashflow.empty:
            st.error("⚠️ Insufficient financial data available for this ticker.")
            st.button("⬅️ Back", on_click=go_app)
            st.stop()

        # Create Growth DataFrame with error handling
        growth_df = pd.DataFrame()
        
        if 'Total Revenue' in income.index:
            growth_df['Total Revenue'] = income.T.get('Total Revenue')
        if 'EBITDA' in income.index:
            growth_df['EBITDA'] = income.T.get('EBITDA')
        if 'Net Income' in income.index:
            growth_df['Net Income'] = income.T.get('Net Income')
        if 'Operating Cash Flow' in cashflow.index:
            growth_df['Operating Cash Flow'] = cashflow.T.get('Operating Cash Flow')
        
        if growth_df.empty:
            st.error("⚠️ Required financial metrics not available.")
            st.button("⬅️ Back", on_click=go_app)
            st.stop()
        
        try:
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
            
            latest_years = growth_df.dropna().index.sort_values()[-2:] if len(growth_df.dropna()) >= 2 else []

            # Initialize these variables
            revenue_growth = ebitda_growth = net_income_growth = op_cashflow_growth = None
            
            if len(latest_years) == 2:
                prev_year = latest_years[0]
                latest_year = latest_years[1]

                # Calculate growth rates with error handling
                try:
                    if 'Total Revenue' in growth_df.columns:
                        revenue_growth = ((growth_df.loc[latest_year, 'Total Revenue'] - growth_df.loc[prev_year, 'Total Revenue']) / 
                                        growth_df.loc[prev_year, 'Total Revenue']) * 100
                except:
                    revenue_growth = None
                
                try:
                    if 'EBITDA' in growth_df.columns:
                        ebitda_growth = ((growth_df.loc[latest_year, 'EBITDA'] - growth_df.loc[prev_year, 'EBITDA']) / 
                                        growth_df.loc[prev_year, 'EBITDA']) * 100
                except:
                    ebitda_growth = None
                
                try:
                    if 'Net Income' in growth_df.columns:
                        net_income_growth = ((growth_df.loc[latest_year, 'Net Income'] - growth_df.loc[prev_year, 'Net Income']) / 
                                            growth_df.loc[prev_year, 'Net Income']) * 100
                except:
                    net_income_growth = None
                
                try:
                    if 'Operating Cash Flow' in growth_df.columns:
                        op_cashflow_growth = ((growth_df.loc[latest_year, 'Operating Cash Flow'] - growth_df.loc[prev_year, 'Operating Cash Flow']) / 
                                            growth_df.loc[prev_year, 'Operating Cash Flow']) * 100
                except:
                    op_cashflow_growth = None

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
            
        except Exception as e:
            st.error(f"⚠️ Error creating visualizations: {e}")
    
    except Exception as e:
        st.error(f"⚠️ Error retrieving financial data: {e}")

    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == "leverage":
    st.subheader("⚡ Leverage Ratios Overview")
    
    try:
        _, balance, _, _ = get_financials_with_fallback(st.session_state.ticker)
        
        if balance.empty:
            st.error("⚠️ Insufficient balance sheet data available for this ticker.")
            st.button("⬅️ Back", on_click=go_app)
            st.stop()
        
        balance = balance.T
        leverage_df = pd.DataFrame()
        
        # Check if required columns exist
        if 'Total Liabilities Net Minority Interest' in balance.columns and 'Common Stock Equity' in balance.columns and 'Total Assets' in balance.columns:
            leverage_df['Debt-to-Equity'] = balance['Total Liabilities Net Minority Interest'] / balance['Common Stock Equity']
            leverage_df['Debt-to-Assets'] = balance['Total Liabilities Net Minority Interest'] / balance['Total Assets']
            leverage_df.index = leverage_df.index.year
            
            st.plotly_chart(px.bar(leverage_df, x=leverage_df.index, y=['Debt-to-Equity', 'Debt-to-Assets'], 
                                   title="Leverage Ratios", template="plotly_dark"), use_container_width=True)

            try:
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
            except Exception as e:
                st.error(f"⚠️ Error creating leverage summary: {e}")
        else:
            st.error("⚠️ Required balance sheet data not available for leverage analysis.")
    except Exception as e:
        st.error(f"⚠️ Error retrieving balance sheet data: {e}")

    st.button("⬅️ Back", on_click=go_app)
    
elif st.session_state.page == "liquidity":
    st.subheader("💧 Liquidity and Dividend Overview")
    
    try:
        _, balance, cashflow, _ = get_financials_with_fallback(st.session_state.ticker)
        
        if balance.empty or cashflow.empty:
            st.error("⚠️ Insufficient financial data available for this ticker.")
            st.button("⬅️ Back", on_click=go_app)
            st.stop()
            
        balance = balance.T
        cashflow = cashflow.T
        
        liquidity_df = pd.DataFrame()
        
        # Check if required columns exist
        has_current_data = 'Current Assets' in balance.columns and 'Current Liabilities' in balance.columns
        has_cashflow_data = 'Operating Cash Flow' in cashflow.columns and 'Capital Expenditure' in cashflow.columns
        
        if has_current_data:
            liquidity_df['Current Ratio'] = balance['Current Assets'] / balance['Current Liabilities']
        
        if has_cashflow_data:
            liquidity_df['FCF'] = cashflow['Operating Cash Flow'] - cashflow['Capital Expenditure']
        
        if liquidity_df.empty:
            st.error("⚠️ Required liquidity data not available.")
            st.button("⬅️ Back", on_click=go_app)
            st.stop()
            
        liquidity_df.index = liquidity_df.index.year
        st.dataframe(liquidity_df)
        
        try:
            st.plotly_chart(px.line(liquidity_df, x=liquidity_df.index, y=liquidity_df.columns.tolist(), 
                                   markers=True, title="Liquidity & FCF Trends", template="plotly_dark"), 
                          use_container_width=True)
            
            if not liquidity_df.empty:
                latest_year = liquidity_df.index.max()
                summary_text = ""
                
                if 'Current Ratio' in liquidity_df.columns:
                    current_ratio = liquidity_df.loc[latest_year, 'Current Ratio']
                    if current_ratio >= 1.5:
                        summary_text += f"✅ Strong Current Ratio: {current_ratio:.2f}\n\n"
                    else:
                        summary_text += f"⚠️ Low Current Ratio: {current_ratio:.2f}\n\n"
                else:
                    summary_text += "⚠️ Current Ratio data unavailable.\n\n"
                
                if 'FCF' in liquidity_df.columns:
                    fcf = liquidity_df.loc[latest_year, 'FCF']
                    if fcf > 0:
                        summary_text += f"✅ Positive Free Cash Flow (FCF): {fcf/1e6:.2f}M\n\n"
                    else:
                        summary_text += f"⚠️ Negative Free Cash Flow (FCF): {fcf/1e6:.2f}M\n\n"
                else:
                    summary_text += "⚠️ Free Cash Flow data unavailable.\n\n"
                
                st.subheader("🔍 FinVAR Summary: Liquidity & Dividend Overview")
                st.info(summary_text)
            else:
                st.warning("⚠️ Not enough data to generate liquidity summary.")
        except Exception as e:
            st.error(f"⚠️ Error creating liquidity visualizations: {e}")
    except Exception as e:
        st.error(f"⚠️ Error retrieving financial data: {e}")

    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == "volatility":
    st.subheader("📈 Stock Price & Volatility Overview")
    
    try:
        _, _, _, hist = get_financials_with_fallback(st.session_state.ticker)
        
        if hist.empty:
            st.error("⚠️ Insufficient historical price data available for this ticker.")
            st.button("⬅️ Back", on_click=go_app)
            st.stop()
            
        if 'Close' in hist.columns:
            hist['Daily Return'] = hist['Close'].pct_change()
            volatility = hist['Daily Return'].std() * np.sqrt(252)
            
            st.line_chart(hist['Close'])
            st.subheader(f"Annualized Volatility: {volatility:.2%}")
        else:
            st.warning("Close price data not available in historical data.")
    except Exception as e:
        st.error(f"⚠️ Error retrieving or processing historical data: {e}")

    st.button("⬅️ Back", on_click=go_app)

elif st.session_state.page == "eps_prediction":
    st.subheader("🔮 EPS Prediction for 2025")
    
    try:
        income, balance, cashflow, _ = get_financials_with_fallback(st.session_state.ticker)
        info = get_ticker_info(st.session_state.ticker)
        
        if "error" in info or income.empty or balance.empty or cashflow.empty:
            st.error("⚠️ Insufficient data available for EPS prediction.")
            st.button("⬅️ Back", on_click=go_app)
            st.stop()
            
        try:
            income = income.T
            balance = balance.T
            cashflow = cashflow.T
            
            # Ensure we have the latest data
            latest_year = income.index.max()
            
            # Get all required metrics with error handling
            required_fields = {
                'income': ['Net Income', 'Operating Income', 'Total Revenue', 'EBIT', 'Interest Expense'],
                'balance': ['Total Assets', 'Common Stock Equity', 'Total Liabilities Net Minority Interest', 
                           'Current Assets', 'Current Liabilities'],
                'info': ['trailingPE', 'epsTrailingTwelveMonths']
            }
            
            # Check if all required fields are available
            missing_fields = []
            
            for df_name, fields in required_fields.items():
                if df_name == 'income':
                    for field in fields:
                        if field not in income.columns:
                            missing_fields.append(f"{field} (Income Statement)")
                elif df_name == 'balance':
                    for field in fields:
                        if field not in balance.columns:
                            missing_fields.append(f"{field} (Balance Sheet)")
                elif df_name == 'info':
                    for field in fields:
                        if field not in info:
                            missing_fields.append(f"{field} (Company Info)")
            
            if missing_fields:
                st.warning(f"⚠️ The following data is missing and will be estimated: {', '.join(missing_fields)}")
            
            # Initialize variables with safe defaults
            pe_exi = info.get('trailingPE', np.nan)
            eps = info.get('epsTrailingTwelveMonths', np.nan)
            
            # Get financial metrics with safe fallbacks
            try:
                npm = income.loc[income.index[-1], 'Net Income'] / income.loc[income.index[-1], 'Total Revenue']
            except:
                npm = 0.05  # Fallback to 5% net profit margin
                st.warning("⚠️ Net Profit Margin data missing - using estimate.")
                
            try:
                opmad = income.loc[income.index[-1], 'Operating Income'] / income.loc[income.index[-1], 'Total Revenue']
            except:
                opmad = 0.1  # Fallback to 10% operating margin
                st.warning("⚠️ Operating Margin data missing - using estimate.")
                
            try:
                roa = income.loc[income.index[-1], 'Net Income'] / balance.loc[balance.index[-1], 'Total Assets']
            except:
                roa = 0.03  # Fallback to 3% ROA
                st.warning("⚠️ Return on Assets data missing - using estimate.")
                
            try:
                roe = income.loc[income.index[-1], 'Net Income'] / balance.loc[balance.index[-1], 'Common Stock Equity']
            except:
                roe = 0.08  # Fallback to 8% ROE
                st.warning("⚠️ Return on Equity data missing - using estimate.")
                
            try:
                de_ratio = balance.loc[balance.index[-1], 'Total Liabilities Net Minority Interest'] / balance.loc[balance.index[-1], 'Common Stock Equity']
            except:
                de_ratio = 1.0  # Fallback to a DE ratio of 1.0
                st.warning("⚠️ Debt-to-Equity data missing - using estimate.")
                
            try:
                intcov_ratio = income.loc[income.index[-1], 'EBIT'] / income.loc[income.index[-1], 'Interest Expense']
            except:
                intcov_ratio = 5.0  # Fallback to interest coverage of 5.0
                st.warning("⚠️ Interest Coverage Ratio data missing - using estimate.")
                
            try:
                curr_ratio = balance.loc[balance.index[-1], 'Current Assets'] / balance.loc[balance.index[-1], 'Current Liabilities']
            except:
                curr_ratio = 1.5  # Fallback to current ratio of 1.5
                st.warning("⚠️ Current Ratio data missing - using estimate.")
                
            try:
                revenue = income.loc[income.index[-1], 'Total Revenue']
            except:
                if len(income) > 0 and 'Total Revenue' in income.columns:
                    # Take the average of available revenue data
                    revenue = income['Total Revenue'].mean()
                else:
                    # Fallback to a reasonable value based on EPS and market average PE
                    revenue = eps * 20 * 1e7 if not np.isnan(eps) else 1e9
                st.warning("⚠️ Revenue data missing - using estimate.")
            
            # Get previous data for growth calculations
            try:
                previous_revenue = income.loc[income.index[-2], 'Total Revenue'] if len(income.index) > 1 else np.nan
                revenue_growth = ((revenue - previous_revenue) / previous_revenue) if not np.isnan(previous_revenue) and previous_revenue != 0 else 0.05
            except:
                revenue_growth = 0.05  # Fallback to 5% growth
                st.warning("⚠️ Revenue Growth data missing - using estimate.")
            
            # Fallback for missing EPS
            if np.isnan(eps):
                # Try to estimate from net income and shares outstanding
                try:
                    net_income = income.loc[income.index[-1], 'Net Income']
                    shares = info.get('sharesOutstanding', 1e8)  # Default to 100M shares
                    eps = net_income / shares
                except:
                    eps = 1.0  # Complete fallback
                st.warning("⚠️ EPS data missing - using estimate.")
            
            # Compute derived metrics for model
            eps_growth = 0  # Conservative default
            
            try:
                roa_to_revenue = roa / revenue if revenue != 0 else 0
            except:
                roa_to_revenue = 0.00000003  # Fallback
            
            try:
                roe_to_roa = roe / roa if roa != 0 else 0
            except:
                roe_to_roa = 2.5  # Fallback, typically ROE > ROA
            
            try:
                debt_to_income = de_ratio / revenue if revenue != 0 else 0
            except:
                debt_to_income = 0.000001  # Fallback
            
            try:
                intcov_per_curr = intcov_ratio / curr_ratio if curr_ratio != 0 else 0
            except:
                intcov_per_curr = 3.0  # Fallback
            
            try:
                opmad_to_npm = opmad / npm if npm != 0 else 0
            except:
                opmad_to_npm = 2.0  # Fallback, typically Operating Margin > Net Margin
            
            eps_3yr_avg = eps  # Fallback if we don't have 3 years of data
            revenue_3yr_avg = revenue  # Fallback if we don't have 3 years of data
            
            features = np.array([[
                eps, eps_3yr_avg, roe, npm, opmad_to_npm,
                revenue_3yr_avg, intcov_per_curr, revenue_growth,
                roa_to_revenue, intcov_ratio
            ]])
            
            # Replace any NaN, inf, -inf with 0 to avoid model errors
            features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
            
            # Make prediction with exception handling
            try:
                predicted_eps = model.predict(features)[0]
                
                # Validate prediction and show warning if unrealistic
                if predicted_eps < 0 and eps > 0:
                    st.warning("⚠️ The model predicted a negative EPS which seems unrealistic given current positive EPS. Consider this prediction with caution.")
                elif predicted_eps > eps * 3 and eps > 0:
                    st.warning("⚠️ The model predicted an unusually high EPS increase. Consider this prediction with caution.")
                
                st.success(f"🧠 Predicted EPS for 2025: **{predicted_eps:.2f} USD**")
                
                # Add more context about confidence
                if len(missing_fields) > 3:
                    st.warning("⚠️ Due to missing data, this prediction has lower confidence.")
                elif len(missing_fields) > 0:
                    st.info("ℹ️ This prediction is based on some estimated values, use with appropriate caution.")
                else:
                    st.info("✅ This prediction is based on complete financial data.")
                
            except Exception as e:
                st.error(f"⚠️ Error in prediction model: {e}")
                st.warning("The model couldn't make a reliable prediction with the available data.")
        except Exception as e:
            st.error(f"⚠️ Error processing financial data for prediction: {e}")
    except Exception as e:
        st.error(f"⚠️ Error retrieving data for EPS prediction: {e}")

    st.button("⬅️ Back", on_click=go_app)
