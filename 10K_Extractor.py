from sec_edgar_downloader import Downloader
import streamlit as st
import os
import re
from bs4 import BeautifulSoup

st.title("📄 SEC EDGAR 10-K Filing Viewer")

ticker_name = st.text_input("Enter Ticker Symbol (e.g., AAPL, MSFT):")

if st.button("Download & Display 10-K Filing"):
    if ticker_name:
        try:
            dl = Downloader("Boston University", "atuladas@bu.edu")
            dl.get("10-K", ticker_name.upper(), limit=1)

            base_path = os.path.join("sec-edgar-filings", ticker_name.upper(), "10-K")
            if not os.path.exists(base_path):
                st.error("Filing directory not found.")
            else:
                latest_filing_folder = sorted(os.listdir(base_path))[-1]
                full_path = os.path.join(base_path, latest_filing_folder, "full-submission.txt")

                if os.path.exists(full_path):
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        filing_text = f.read()
                        types=re.findall(r'<TYPE>(.*?)\n',filing_text)
                        st.subheader("📂 Document Types Found in Filing")
                        for t in types:
                            st.write(f"-{t.strip()}")
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter a valid ticker symbol.")
