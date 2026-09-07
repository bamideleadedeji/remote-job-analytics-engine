import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import xml.etree.ElementTree as ET

# Page Configuration
st.set_page_config(
    page_title="Global & Africa Remote Job Search Engine",
    page_icon="🌍",
    layout="wide",
)


# --- 1. We Work Remotely (WWR) RSS Feeds ---
@st.cache_data(ttl=1800)
def fetch_weworkremotely():
    # WWR RSS feeds for Data, Programming, and DevOps
    urls = [
        "https://weworkremotely.com/categories/remote-data-science-jobs.rss",
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    ]
    parsed = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                for item in root.findall("./channel/item"):
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    pub_date = item.findtext("pubDate", "")
                    
                    # WWR titles are formatted as "Company: Title"
                    company = "We Work Remotely"
                    job_title = title
                    if ":" in title:
                        parts = title.split(":", 1)
                        company = parts[0].strip()
                        job_title = parts[1].strip()

                    parsed.append(
                        {
                            "title": job_title,
                            "company": company,
                            "location": "Worldwide / Remote",
                            "date": pub_date,
                            "url": link,
                            "source": "We Work Remotely",
                        }
                    )
        except Exception:
            continue
    return pd.DataFrame(parsed)


# --- 2. Remotive API ---
@st.cache_data(ttl=1800)
def fetch_remotive():
    url = "https://remotive.com/api/remote-jobs"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            jobs = res.json().get("jobs", [])
            parsed = []
            for j in jobs:
                parsed.append(
                    {
                        "title": j.get("title"),
                        "company": j.get("company_name"),
                        "location": j.get(
                            "candidate_required_location", "Worldwide"
                        ),
                        "date": j.get("publication_date"),
                        "url": j.get("url"),
                        "source": "Remotive",
                    }
                )
            return pd.DataFrame(parsed)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


# --- 3. Jobicy API ---
@st.cache_data(ttl=1800)
def fetch_jobicy():
    url = "https://jobicy.com/api/v2/remote-jobs"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            jobs = res.json().get("jobs", [])
            parsed = []
            for j in jobs:
                parsed.append(
                    {
                        "title": j.get("jobTitle"),
                        "company": j.get("companyName"),
                        "location": j.get("jobGeo", "Worldwide"),
                        "date": j.get("pubDate"),
                        "url": j.get("url"),
                        "source": "Jobicy",
                    }
                )
            return pd.DataFrame(parsed)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


# --- 4. Arbeitnow API ---
@st.cache_data(ttl=1800)
def fetch_arbeitnow():
    url = "https://www.arbeitnow.com/api/job-board-api"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            jobs = res.json().get("data", [])
            parsed = []
            for j in jobs:
                loc = (
                    "Worldwide"
                    if j.get("remote")
                    else f"{j.get('location')} (Hybrid)"
                )
                parsed.append(
                    {
                        "title": j.get("title"),
                        "company": j.get("company_name"),
                        "location": loc,
                        "date": j.get("created_at"),
                        "url": j.get("url"),
                        "source": "Arbeitnow",
                    }
                )
            return pd.DataFrame(parsed)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


# --- 5. Google Jobs via SerpAPI ---
@st.cache_data(ttl=1800)
def fetch_serpapi_jobs(api_key, query="remote analytics engineer global"):
    if not api_key:
        return pd.DataFrame()
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_jobs",
        "q": query,
        "hl": "en",
        "api_key": api_key,
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            jobs = res.json().get("jobs_results", [])
            parsed = []
            for j in jobs:
                detected_extensions = j.get("detected_extensions", {})
                parsed.append(
                    {
                        "title": j.get("title"),
                        "company": j.get("company_name"),
                        "location": j.get("location", "Worldwide / Remote"),
                        "date": detected_extensions.get(
                            "posted_at", "Recently"
                        ),
                        "url": (
                            j.get("related_links", [{}])[0].get("link")
                            or j.get("share_link")
                        ),
                        "source": "Google Jobs (SerpAPI)",
                    }
                )
            return pd.DataFrame(parsed)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


# --- Helper Categorization ---
def categorize_region(location_str):
    loc = str(location_str).lower()
    if any(
        k in loc
        for k in ["lagos", "nigeria", "abuja", "ibadan", "port harcourt"]
    ):
        return "Lagos / Nigeria"
    elif any(
        k in loc
        for k in [
            "africa",
            "emea",
            "kenya",
            "nairobi",
            "south africa",
            "ghana",
            "accra",
            "egypt",
        ]
    ):
        return "Africa / EMEA"
    elif any(
        k in loc for k in ["worldwide", "anywhere", "global", "remote work"]
    ):
        return "Worldwide (Open to All)"
    elif any(k in loc for k in ["us", "usa", "united states", "uk", "europe", "eu", "canada"]):
        return "US / EU / Specific Region"
    return "Worldwide (Open to All)"


def classify_role(title):
    t = str(title).lower()
    if any(
        k in t
        for k in [
            "analytics engineer",
            "dbt",
            "data engineer",
            "data analyst",
            "data analytics",
            "data scientist",
            "sql analyst",
            "data platform",
        ]
    ):
        return "Analytics & Data Engineering"
    elif any(
        k in t
        for k in [
            "business intelligence",
            "bi analyst",
            "tableau",
            "power bi",
            "looker",
            "bi developer",
            "omni",
        ]
    ):
        return "Business Intelligence"
    elif any(
        k in t
        for k in [
            "cybersecurity",
            "cyber security",
            "infosec",
            "security analyst",
            "soc",
            "information security",
            "compliance",
        ]
    ):
        return "Cybersecurity"
    elif any(
        k in t
        for k in ["finance", "financial", "accounting", "auditor", "accountant", "ledger"]
    ):
        return "Finance & Accounting"
    return "Other Tech Roles"


# --- Data Pipeline Execution ---
st.sidebar.title("⚙️ Engine Configurations")
serpapi_key = st.sidebar.text_input(
    "SerpAPI Key (Optional for Google Jobs):", type="password"
)

# Load feeds
df_wwr = fetch_weworkremotely()
df_remotive = fetch_remotive()
df_jobicy = fetch_jobicy()
df_arbeitnow = fetch_arbeitnow()
df_serpapi = fetch_serpapi_jobs(
    serpapi_key, query="remote analytics engineer dbt global"
)

raw_df = pd.concat(
    [df_wwr, df_remotive, df_jobicy, df_arbeitnow, df_serpapi], ignore_index=True
)

if not raw_df.empty:
    raw_df["date"] = pd.to_datetime(raw_df["date"], errors="coerce")
    raw_df["posted_date"] = raw_df["date"].dt.date
    raw_df["location"] = raw_df["location"].fillna("Worldwide / Remote")
    raw_df = raw_df.drop_duplicates(subset=["title", "company"]).reset_index(
        drop=True
    )

    raw_df["Domain"] = raw_df["title"].apply(classify_role)
    raw_df["Region Tier"] = raw_df["location"].apply(categorize_region)

    target_df = raw_df[raw_df["Domain"] != "Other Tech Roles"].copy()

    # --- Sidebar Filters ---
    st.sidebar.markdown("---")
    st.sidebar.title("🔍 Job Filters")

    # Region Filter
    regions = [
        "All Regions",
        "Worldwide (Open to All)",
        "Africa / EMEA",
        "Lagos / Nigeria",
    ]
    selected_region = st.sidebar.selectbox("Geographic Focus:", options=regions)

    # Domain Filter
    domains = sorted(target_df["Domain"].unique().tolist())
    selected_domains = st.sidebar.multiselect(
        "Target Domains:", options=domains, default=domains
    )

    # Keyword Search
    search_keyword = st.sidebar.text_input(
        "Keyword Search (Title / Company / Tech Stack):", ""
    )

    # Filter Applications
    filtered_df = target_df[target_df["Domain"].isin(selected_domains)]

    if selected_region != "All Regions":
        filtered_df = filtered_df[
            filtered_df["Region Tier"] == selected_region
        ]

    if search_keyword:
        filtered_df = filtered_df[
            filtered_df["title"].str.contains(
                search_keyword, case=False, na=False
            )
            | filtered_df["company"].str.contains(
                search_keyword, case=False, na=False
            )
            | filtered_df["location"].str.contains(
                search_keyword, case=False, na=False
            )
        ]

    # --- UI Layout ---
    st.title("🌍 Global Remote Tech & Analytics Engine")
    st.caption(
        "Aggregating Worldwide & Regional Remote Opportunities across Analytics Engineering, Data, BI, Cybersecurity, and Finance"
    )
    st.markdown("---")

    # Key Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active Matching Roles", len(filtered_df))
    m2.metric(
        "Worldwide Roles",
        len(raw_df[raw_df["Region Tier"] == "Worldwide (Open to All)"]),
    )
    m3.metric(
        "Africa / EMEA Roles",
        len(raw_df[raw_df["Region Tier"] == "Africa / EMEA"]),
    )
    m4.metric(
        "Lagos & Nigeria Openings",
        len(raw_df[raw_df["Region Tier"] == "Lagos / Nigeria"]),
    )

    st.markdown("---")

    # Navigation Tabs
    tab_cards, tab_grid, tab_directory = st.tabs(
        ["🚀 One-Click Apply Cards", "📊 Data Grid View", "🌐 Global Remote Companies & Boards"]
    )

    export_df = filtered_df[
        [
            "title",
            "company",
            "Domain",
            "location",
            "Region Tier",
            "source",
            "url",
        ]
    ].rename(
        columns={
            "title": "Role Title",
            "company": "Company",
            "location": "Location Details",
            "Region Tier": "Region",
            "source": "Feed Source",
            "url": "Application Link",
        }
    )

    with tab_cards:
        st.download_button(
            label="📥 Export Filtered Search to CSV",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name="remote_jobs_global.csv",
            mime="text/csv",
        )
        st.write("")
        if filtered_df.empty:
            st.info("No matching job listings found for the current filters.")
        else:
            for idx, row in filtered_df.reset_index(drop=True).iterrows():
                with st.container(border=True):
                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.markdown(f"### **{row['title']}**")
                        st.markdown(
                            f"🏢 **{row['company']}** | 🎯 **{row['Domain']}** | 📍 **{row['location']}** ({row['Region Tier']}) | 📌 Source: *{row['source']}*"
                        )
                    with col_btn:
                        st.write("")
                        st.link_button(
                            "⚡ Direct Apply",
                            row["url"],
                            use_container_width=True,
                            help="Open application portal directly in a new tab",
                        )

    with tab_grid:
        st.dataframe(
            export_df,
            column_config={
                "Application Link": st.column_config.LinkColumn(
                    "Quick Apply",
                    help="Click to open direct application portal in a new tab",
                    display_text="Apply Now ↗",
                    validate="^https?://",
                ),
                "Role Title": st.column_config.TextColumn("Role Title", width="medium"),
                "Company": st.column_config.TextColumn("Company", width="small"),
                "Location Details": st.column_config.TextColumn("Location Details", width="medium"),
                "Region": st.column_config.TextColumn("Region", width="small"),
                "Feed Source": st.column_config.TextColumn("Feed Source", width="small"),
            },
            column_order=[
                "Role Title",
                "Company",
                "Domain",
                "Location Details",
                "Region",
                "Feed Source",
                "Application Link",
            ],
            use_container_width=True,
            hide_index=True,
        )

    with tab_directory:
        st.subheader(" Curated Global Remote Companies & Job Platforms")
        st.write(
            "These platforms and companies actively hire global employees and contractors using Employer of Record (EOR) services like Deel and Remote.com."
        )

        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("####  Premier Global Remote Platforms")
            st.markdown("- **[Otta / Handshake](https://otta.com):** Search 'Analytics Engineer' with Location: *Anywhere / Remote*.")
            st.markdown("- **[Wellfound](https://wellfound.com):** Filter by *Analytics Engineer*, *Worldwide Remote*, and *Hiring International Candidates*.")
            st.markdown("- **[We Work Remotely](https://weworkremotely.com):** Explore top worldwide data, engineering, and DevOps roles.")
            st.markdown("- **[Remotive](https://remotive.com):** Filter 'Data' category by *Worldwide* remote access.")

        with col_right:
            st.markdown("####  100% Distributed Remote-First Companies")
            st.markdown("- **[GitLab Careers](https://about.gitlab.com/jobs):** Fully remote company with global hiring infrastructure for data & BI.")
            st.markdown("- **[Canonical Careers](https://canonical.com/careers):** Distributed workforce hiring remote Data Engineers & Analytics Engineers globally.")
            st.markdown("- **[Automattic Careers](https://automattic.com/work-with-us):** Creators of WordPress; 100% remote global engineering team.")
            st.markdown("- **[Zapier Careers](https://zapier.com/jobs):** Distributed global analytics, data platform, and telemetry teams.")

else:
    st.warning("Unable to fetch job listings at this moment.")
