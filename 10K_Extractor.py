from sec_edgar_downloader import Downloader
import streamlit as st
import os

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
                    
                    html_match = re.search(r'<html>.*?</html>', filing_text, re.DOTALL)
                    if html_match:
                        html_content = html_match.group(0)
                        with st.expander("📄 View 10-K Filing"):
                            st.components.v1.html(html_content, height=600)
                    else:
                        soup = BeautifulSoup(filing_text, 'html.parser')
                        if soup.find('body'):
                            with st.expander("📄 View 10-K Filing"):
                                st.components.v1.html(str(soup), height=600)
                        else:
                            with st.expander("📄 View 10-K Filing (Raw Format)"):
                                st.text_area("Full 10-K Filing", filing_text, height=600)
                else:
                    st.warning("full-submission.txt not found inside filing folder.")

        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter a valid ticker symbol.")
