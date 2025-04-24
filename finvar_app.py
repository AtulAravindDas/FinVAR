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
if "show_financials" not in st.session_state:
    st.session_state["show_financials"] = False

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

            if st.button("Show Financial Statements 📈"):
                st.session_state["show_financials"] = not st.session_state["show_financials"]

            if st.session_state["show_financials"]:
                st.subheader("📑 Income Statement (Standard Order)")
                income_statement = ticker.financials
                ideal_income_order = [
                    "Operating Revenue", "Total Revenue", "Cost Of Revenue", "Reconciled Cost Of Revenue",
                    "Gross Profit", "Selling General And Administration", "Research And Development",
                    "Operating Expense", "Reconciled Depreciation", "EBITDA", "EBIT", "Operating Income",
                    "Total Operating Income As Reported", "Other Income Expense", "Other Non Operating Income Expenses",
                    "Interest Income", "Interest Income Non Operating", "Interest Expense", "Interest Expense Non Operating",
                    "Net Interest Income", "Net Non Operating Interest Income Expense", "Pretax Income", "Tax Provision",
                    "Tax Effect Of Unusual Items", "Tax Rate For Calcs", "Net Income From Continuing Operation Net Minority Interest",
                    "Net Income Continuous Operations", "Net Income From Continuing And Discontinued Operation",
                    "Net Income Including Noncontrolling Interests", "Net Income Common Stockholders", "Net Income",
                    "Normalized Income", "Normalized EBITDA", "Diluted NI Availto Com Stockholders",
                    "Diluted EPS", "Basic EPS", "Diluted Average Shares", "Basic Average Shares", "Total Expenses"
                ]

                ordered_income = income_statement.loc[
                    [item for item in ideal_income_order if item in income_statement.index]
                ]
                ordered_income = ordered_income[ordered_income.columns[::-1]]
                st.write(ordered_income)

                st.subheader("📊 Balance Sheet")
                st.write(ticker.balance_sheet)

                st.subheader("💵 Cash Flow Statement (Standard Order)")
                cash_flow = ticker.cashflow

                ideal_cashflow_order = [
                    # Operating
                    "Net Income From Continuing Operations", "Depreciation And Amortization", "Depreciation Amortization Depletion",
                    "Deferred Tax", "Deferred Income Tax", "Stock Based Compensation", "Other Non Cash Items",
                    "Change In Receivables", "Changes In Account Receivables", "Change In Inventory",
                    "Change In Account Payable", "Change In Payable", "Change In Payables And Accrued Expense",
                    "Change In Other Current Assets", "Change In Other Current Liabilities",
                    "Change In Other Working Capital", "Change In Working Capital",
                    "Cash Flow From Continuing Operating Activities", "Operating Cash Flow",

                    # Investing
                    "Purchase Of PPE", "Net PPE Purchase And Sale", "Purchase Of Business", "Net Business Purchase And Sale",
                    "Purchase Of Investment", "Sale Of Investment", "Net Investment Purchase And Sale",
                    "Net Other Investing Changes", "Cash Flow From Continuing Investing Activities", "Investing Cash Flow",

                    # Financing
                    "Long Term Debt Issuance", "Long Term Debt Payments", "Net Long Term Debt Issuance",
                    "Net Short Term Debt Issuance", "Net Issuance Payments Of Debt",
                    "Common Stock Issuance", "Common Stock Payments", "Net Common Stock Issuance",
                    "Common Stock Dividend Paid", "Cash Dividends Paid", "Net Other Financing Charges",
                    "Cash Flow From Continuing Financing Activities", "Financing Cash Flow",
                    "Issuance Of Capital Stock", "Issuance Of Debt", "Repayment Of Debt", "Repurchase Of Capital Stock",

                    # Summary
                    "Changes In Cash", "Beginning Cash Position", "End Cash Position",
                    "Income Tax Paid Supplemental Data", "Interest Paid Supplemental Data",
                    "Capital Expenditure", "Free Cash Flow"
                ]

                ordered_cf = cash_flow.loc[
                    [item for item in ideal_cashflow_order if item in cash_flow.index]
                ]
                ordered_cf = ordered_cf[ordered_cf.columns[::-1]]
                st.write(ordered_cf)

                st.success("✅ Company data loaded successfully!")

            if st.button("📘 Profitability Ratios"):
                st.subheader("📈 Profitability Trends")
                income = ticker.financials.T
                balance = ticker.balance_sheet.T

                df = pd.DataFrame()
                df['Net Income'] = income['Net Income']
                df['Gross Profit'] = income['Gross Profit']
                df['Total Revenue'] = income['Total Revenue']
                df['EBITDA'] = income['EBITDA']
                df['EBIT'] = income['EBIT']
                df['Shareholders Equity'] = balance['Common Stock Equity']
                df['Total Assets'] = balance['Total Assets']
                df['Total Liabilities'] = balance['Total Liab']

                df = df.dropna()
                df.index = df.index.year

                df['ROE (%)'] = (df['Net Income'] / df['Shareholders Equity']) * 100
                df['Gross Profit Margin (%)'] = (df['Gross Profit'] / df['Total Revenue']) * 100
                df['Asset Turnover'] = df['Total Revenue'] / df['Total Assets']
                df['Financial Leverage'] = df['Total Assets'] / df['Shareholders Equity']
                df['Net Profit Margin (%)'] = (df['Net Income'] / df['Total Revenue']) * 100

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
