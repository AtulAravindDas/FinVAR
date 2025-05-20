from sec_edgar_downloader import Downloader
import streamlit as st
import os
st.title("SEC EDGAR 10-K Filing Downloader")
ticker_name=st.text_input("Enter Ticker Name(eg. AAPL,MSFT):")
if st.button("Download 10-K filing"):
  if ticker_name:
    try:
      dl=Downloader("Boston University","atuladas@bu.edu")
      st.info(f"Downloading latest 10-K for {ticker_name}...")
      ticker_10K=dl.get("10-K",ticker_name,limit=1)
      base_path = os.path.join("sec-edgar-filings", ticker_name.upper(), "10-K")
      latest_filing_folder = sorted(os.listdir(base_path))[-1]
      full_path = os.path.join(base_path, latest_filing_folder, "full-submission.txt")
      with open(full_path,'r') as f:
        filing_text=f.read()
      with st.expander("View 10-K filing"):
        st.write(filing_text)
    except Exception as e:
      st.error(f"Error: {e}")
