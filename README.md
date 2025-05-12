# 📊 FinVAR – Financial Assistant Referee

**By: Atul Aravind Das & Dhinesh Mahalingam**

---
Your financial assistant referee – reviewing every ticker, flagging every risk.
---

🧠**Understand the market.**  
🚨**Flag the risks.**  
💼**Make smarter investment moves.**

---

## 🚀 What is FinVAR?

**FinVAR** is a financial visualization and analysis tool that not only presents key profitability, growth, leverage, and liquidity metrics, but also uses **Machine Learning** to predict the **future Earnings Per Share (EPS)** of companies — helping investors and analysts make better-informed decisions.

---

## 📈 Key Features

- **Company Insights**  
  - Fetch and display real-time company descriptions and financials via Yahoo Finance API.

- **Profitability Overview**  
  - ROE, Gross Profit Margin, Net Profit Margin, Asset Turnover, Financial Leverage.

- **Growth Overview**  
  - Revenue Growth and EBITDA Growth visualized interactively.

- **Leverage and Liquidity Overview**  
  - Debt-to-Equity, Debt-to-Assets, Current Ratio, Free Cash Flow (FCF) Analysis.

- **Stock Price and Volatility Analysis**  
  - 1-year historical price trends and volatility computations.

- **📈 EPS Prediction Engine**  
  - Trained using Gradient Boosting on historical financial ratios.
  - Auto-fetches latest ratios and predicts **future EPS** without manual data entry.
- **🔢 Beneish-M-Score**
  - Leverages forensic accounting ratios to flag potential earnings manipulation.
  - Helps investors sniff out financial red flags before the market reacts.
---

## 🛠️ Tech Stack

- Python
- Streamlit
- Scikit-learn
- Plotly
- Yahoo Finance API (via `yfinance`)

---

## 📦 Files in this Repository

| File | Description |
|:---|:---|
| `finvar_app.py` | Main Streamlit Application |
| `finvar_button_testing.py` | Tests and error handling for the main Streamlit Application |
| `final_eps_predictor.pkl` | Trained Machine Learning model (Gradient Boosting) |
| `final_top_features.json` | Feature set used for EPS prediction |
| `requirements.txt` | All required Python libraries |
| `README.md` | This documentation file |

---

## 💻 How to Run it

Use the link given here: https://finvar-vx73xpw7zpwvqnryawbcen.streamlit.app/


