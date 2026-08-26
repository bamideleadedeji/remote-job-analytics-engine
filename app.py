import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Global & Africa Remote Job Search Engine",
    page_icon="🌍",
    layout="wide",
)


# --- 1. Remotive API ---
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


# --- 2. Jobicy API ---
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


# --- 3. Arbeitnow API ---
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


# --- 4. Google Jobs via SerpAPI (Regional Targeted Search) ---
@st.cache_data(ttl=1800)
def fetch_serpapi_jobs(api_key, query="remote data analyst lagos"):
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
                        "location": j.get("location", "Lagos / Remote"),
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
            "data analyst",
            "data analytics",
            "data engineer",
            "data scientist",
            "sql analyst",
            "analytics engineer",
        ]
    ):
        return "Data Analytics & Engineering"
    elif any(
        k in t
        for k in [
            "business intelligence",
            "bi analyst",
            "tableau",
            "power bi",
            "looker",
            "bi developer",
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
        for k in ["finance", "financial", "accounting", "auditor", "accountant"]
    ):
        return "Finance & Accounting"
    return "Other Roles"


# --- Data Pipeline Execution ---
st.sidebar.title("⚙️ Engine Configurations")
serpapi_key = st.sidebar.text_input(
    "SerpAPI Key (Optional for Google Jobs):", type="password"
)

# Load feeds
df_remotive = fetch_remotive()
df_jobicy = fetch_jobicy()
df_arbeitnow = fetch_arbeitnow()
df_serpapi = fetch_serpapi_jobs(
    serpapi_key, query="remote data analyst cybersecurity Lagos Nigeria"
)

raw_df = pd.concat(
    [df_remotive, df_jobicy, df_arbeitnow, df_serpapi], ignore_index=True
)

if not raw_df.empty:
    raw_df["date"] = pd.to_datetime(raw_df["date"], errors="coerce")
    raw_df["posted_date"] = raw_df["date"].dt.date
    raw_df["location"] = raw_df["location"].fillna("Worldwide")
    raw_df = raw_df.drop_duplicates(subset=["title", "company"]).reset_index(
        drop=True
    )

    raw_df["Domain"] = raw_df["title"].apply(classify_role)
    raw_df["Region Tier"] = raw_df["location"].apply(categorize_region)

    target_df = raw_df[raw_df["Domain"] != "Other Roles"].copy()

    # --- Sidebar Filters ---
    st.sidebar.markdown("---")
    st.sidebar.title("🔍 Job Filters")

    # Region Filter
    regions = [
        "All Regions",
        "Lagos / Nigeria",
        "Africa / EMEA",
        "Worldwide (Open to All)",
    ]
    selected_region = st.sidebar.selectbox("Geographic Focus:", options=regions)

    # Domain Filter
    domains = sorted(target_df["Domain"].unique().tolist())
    selected_domains = st.sidebar.multiselect(
        "Target Domains:", options=domains, default=domains
    )

    # Keyword Search
    search_keyword = st.sidebar.text_input(
        "Keyword Search (Title/Company/City):", ""
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
    st.title("🌍 Global & Regional Remote Tech Engine")
    st.caption(
        "Aggregating Remote & Hybrid Opportunities across Data, BI, Cybersecurity, and Finance with dedicated focus on Nigeria & Africa"
    )
    st.markdown("---")

    # Key Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active Matching Roles", len(filtered_df))
    m2.metric(
        "Lagos & Nigeria Openings",
        len(raw_df[raw_df["Region Tier"] == "Lagos / Nigeria"]),
    )
    m3.metric(
        "Africa / EMEA Roles",
        len(raw_df[raw_df["Region Tier"] == "Africa / EMEA"]),
    )
    m4.metric(
        "Worldwide Roles",
        len(raw_df[raw_df["Region Tier"] == "Worldwide (Open to All)"]),
    )

    st.markdown("---")

    # Analytics Dashboard
    st.subheader("📊 Market Intelligence Breakdown")
    c1, c2 = st.columns(2)

    with c1:
        reg_counts = (
            filtered_df["Region Tier"].value_counts().reset_index()
        )
        reg_counts.columns = ["Region", "Count"]
        fig_region = px.pie(
            reg_counts,
            values="Count",
            names="Region",
            title="Geographic Availability",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(fig_region, use_container_width=True)

    with c2:
        top_comp = (
            filtered_df["company"].value_counts().head(10).reset_index()
        )
        top_comp.columns = ["Company", "Openings"]
        fig_comp = px.bar(
            top_comp,
            x="Openings",
            y="Company",
            orientation="h",
            title="Top Hiring Companies",
            color="Openings",
            color_continuous_scale="Purples",
        )
        fig_comp.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_comp, use_container_width=True)

    st.markdown("---")

    # Table Grid & Export
    st.subheader("📋 Filtered Remote Openings Grid")

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

    st.download_button(
        label="📥 Export Filtered Search to CSV",
        data=export_df.to_csv(index=False).encode("utf-8"),
        file_name="remote_jobs_africa_global.csv",
        mime="text/csv",
    )

    # Configured Dataframe Grid with Direct Apply Link Buttons
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
else:
    st.warning("Unable to fetch job listings at this moment.")
