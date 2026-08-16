# remote-job-analytics-engine
An interactive Streamlit dashboard and data engine that aggregates live remote job listings across Data Analytics, Business Intelligence, and Cybersecurity via REST APIs. Features automated data cleaning, real-time KPI metrics, interactive Plotly market analytics, and role-based filtering deployed continuous-integration on Streamlit Cloud
#  Remote Job Market Analytics Engine

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An end-to-end data pipeline and interactive analytics dashboard that ingests, cleans, categorizes, and visualizes live remote job openings across **Data Analytics**, **Business Intelligence (BI)**, **Cybersecurity**, and **Finance & Accounting**.

Built with **Python**, **Pandas**, **Plotly**, and **Streamlit**, this application queries public REST APIs in real time to evaluate remote market dynamics, employer demand, and hiring trends without fragile web-scraping dependencies.

---

##  Key Features

* **Automated Data Ingestion:** Fetches real-time remote position listings via non-blocking REST APIs.
* **Intelligent Domain Taxonomy:** Normalizes and categorizes raw job postings into key technical and financial tracks using keyword pattern matching.
* **Interactive Market Analytics:**
  * **Role Distribution:** Visualizes domain market share using interactive Plotly charts.
  * **Top Hiring Entities:** Identifies top companies hiring across target domains.
  * **Posting Velocity:** Tracks daily listing frequency over time.
* **Dynamic Search & Export:** Filter live opportunities by domain, location, or keyword, and download search results as CSV.
* **Performance Caching:** Integrated `@st.cache_data` decorators reduce latency and prevent API rate-limiting.

---

##  Technical Architecture

```text
┌─────────────────────────┐
│     Live REST API       │  (Remotive Job Feed API)
└───────────┬─────────────┘
            │ HTTP GET (JSON)
┌───────────▼─────────────┐
│  Data Processing Layer  │  (Pandas / Python 3.10+)
│  - Field Isolation      │  - Schema Normalization
│  - Keyword Taxonomy     │  - Date Parsing & Deduplication
└───────────┬─────────────┘
            │ In-Memory DataFrames
┌───────────▼─────────────┐
│ Visual Analytics Layer  │  (Plotly Express & Streamlit Components)
│  - Metric Cards (KPIs)  │  - Market Share & Top Employers
│  - Posting Trends       │  - Interactive Data Grid & CSV Export
└───────────┬─────────────┘
            │ Continuous Integration
┌───────────▼─────────────┐
│  Streamlit Cloud App    │  (Hosted from GitHub master branch)
└─────────────────────────┘
