# telecom-netadds-pipeline
Automated data pipeline for extracting, cleaning, and visualizing quarterly net adds and subscriber counts from U.S. telecom carriers (AT&amp;T, Verizon, T-Mobile).

## Features
- Pulls filings (10-Q, 10-K) from SEC EDGAR
- Extracts subscriber metrics like net adds and total subscribers
- Normalizes into a clean schema
- Stores results for dashboards (AWS Athena, QuickSight, Power BI)

## Tech Stack
- Python (requests, pandas, BeautifulSoup, lxml, PyPDF2)
- AWS (S3, Lambda, Athena, QuickSight)
- GitHub for version control

## Setup

Clone the repository and set up your environment:

```bash
git clone https://github.com/usmanrehans/telecom-netadds-pipeline.git
cd telecom-netadds-pipeline
python3 -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
