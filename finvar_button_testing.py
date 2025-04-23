import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="FinVAR", layout="centered")
st.title("📊 FinVAR – Your Financial Assistant Referee")

user_input = st.text_input("Enter the ticker name (e.g., AAPL):")

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
                st.subheader("📝 Company Description")
                description = info.get('longBusinessSummary', 'N/A')
                st.write(description)

            if st.button("Display Current Price 💰"):
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
                    st.subheader("📈 Stock Price (Last 12 Months)")
                    st.line_chart(hist["Close"])
                else:
                    st.warning("No historical price data found.")

            st.success("✅ Company data loaded successfully!")

            # 🔁 LOAD FINANCIAL STATEMENTS ONCE
            income_statement = ticker.financials
            balance_sheet = ticker.balance_sheet
            cash_flow_statement = ticker.cashflow
            years = income_statement.columns[::-1]

            if st.button("Profitability Ratios"):
                st.subheader("📊 Profitability Ratios (2021–2024)")

                data = {
                    "Year": [],
                    "ROE": [],
                    "Gross Profit Margin": [],
                    "Asset Turnover": [],
                    "Financial Leverage": [],
                    "Net Profit Margin": [],
                    "EBITDA ($M)": [],
                    "EBIT ($M)": [],
                }

                for year in years:
                    try:
                        revenue = income_statement.loc["Total Revenue", year]
                        cogs = income_statement.loc["Cost Of Revenue", year]
                        net_income = income_statement.loc["Net Income", year]
                        ebit = income_statement.loc["Operating Income", year]
                        interest = income_statement.loc.get("Interest Expense", {}).get(year, 0)
                        tax = income_statement.loc.get("Income Tax Expense", {}).get(year, 0)
                        depreciation = cash_flow_statement.loc.get("Depreciation", {}).get(year, 0)
                        amortization = cash_flow_statement.loc.get("Amortization", {}).get(year, 0)
                        da = depreciation + amortization

                        total_assets = balance_sheet.loc["Total Assets", year]
                        equity = balance_sheet.loc["Total Stockholder Equity", year]

                        idx = list(years).index(year)
                        if idx < len(years) - 1:
                            prev_year = years[idx + 1]
                            prev_assets = balance_sheet.loc["Total Assets", prev_year]
                            prev_equity = balance_sheet.loc["Total Stockholder Equity", prev_year]
                            avg_assets = (total_assets + prev_assets) / 2
                            avg_equity = (equity + prev_equity) / 2
                        else:
                            avg_assets = total_assets
                            avg_equity = equity

                        gross_profit = revenue - cogs
                        roe = net_income / avg_equity if avg_equity else None
                        gross_margin = gross_profit / revenue if revenue else None
                        asset_turnover = revenue / avg_assets if avg_assets else None
                        leverage = total_assets / equity if equity else None
                        net_margin = net_income / revenue if revenue else None
                        ebitda = (net_income + interest + tax + da) / 1e6
                        ebit_m = ebit / 1e6

                        data["Year"].append(str(year.year))
                        data["ROE"].append(round(roe, 4))
                        data["Gross Profit Margin"].append(round(gross_margin, 4))
                        data["Asset Turnover"].append(round(asset_turnover, 4))
                        data["Financial Leverage"].append(round(leverage, 4))
                        data["Net Profit Margin"].append(round(net_margin, 4))
                        data["EBITDA ($M)"].append(round(ebitda, 2))
                        data["EBIT ($M)"].append(round(ebit_m, 2))

                    except Exception:
                        continue

                df_ratios = pd.DataFrame(data)
                st.dataframe(df_ratios)

                st.subheader("📈 Interactive Visualizations")

                years = df_ratios["Year"]
                tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                    "ROE", "Gross Margin", "Asset Turnover", "Leverage", "Net Margin", "EBITDA", "EBIT"
                ])

                with tab1:
                    fig = go.Figure(data=go.Scatter(x=years, y=df_ratios["ROE"], mode='lines+markers'))
                    fig.update_layout(title="Return on Equity (ROE)", yaxis_title="ROE", xaxis_title="Year")
                    st.plotly_chart(fig, use_container_width=True)

                with tab2:
                    fig = go.Figure(data=go.Bar(x=years, y=df_ratios["Gross Profit Margin"]))
                    fig.update_layout(title="Gross Profit Margin", yaxis_title="Margin", xaxis_title="Year")
                    st.plotly_chart(fig, use_container_width=True)

                with tab3:
                    fig = go.Figure(data=go.Scatter(x=years, y=df_ratios["Asset Turnover"], mode='lines+markers'))
                    fig.update_layout(title="Asset Turnover", yaxis_title="Ratio", xaxis_title="Year")
                    st.plotly_chart(fig, use_container_width=True)

                with tab4:
                    fig = go.Figure(data=go.Bar(x=years, y=df_ratios["_
