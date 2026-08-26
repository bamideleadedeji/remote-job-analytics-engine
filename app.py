import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Global Remote Job Search & Analytics Engine",
    page_icon="💼",
    layout="wide",
)


# --- 1. Remotive API Ingestion ---
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


# --- 2. Jobicy API Ingestion ---
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


# --- 3. Arbeitnow API Ingestion ---
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


# --- Aggregation & Normalization Pipeline ---
@st.cache_data(ttl=1800)
def load_all_remote_jobs():
    df_remotive = fetch_remotive()
    df_jobicy = fetch_jobicy()
    df_arbeitnow = fetch_arbeitnow()

    df = pd.concat(
        [df_remotive, df_jobicy, df_arbeitnow], ignore_index=True
    )

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["posted_date"] = df["date"].dt.date
        df["location"] = df["location"].fillna("Worldwide")
        df = df.drop_duplicates(subset=["title", "company"]).reset_index(
            drop=True
        )
    return df


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
            "compliance analyst",
        ]
    ):
        return "Cybersecurity"
    elif any(
        k in t
        for k in ["finance", "financial", "accounting", "auditor", "accountant"]
    ):
        return "Finance & Accounting"
    return "Other Roles"


# Master Pipeline Execution
raw_df = load_all_remote_jobs()

if not raw_df.empty:
    raw_df["Domain"] = raw_df["title"].apply(classify_role)

    # Filter out unclassified roles by default for focused results
    target_df = raw_df[raw_df["Domain"] != "Other Roles"].copy()

    # --- Sidebar Controls ---
    st.sidebar.title("🔍 Job Search Filters")

    # Domain Filter
    domains = sorted(target_df["Domain"].unique().tolist())
    selected_domains = st.sidebar.multiselect(
        "Target Domains:", options=domains, default=domains
    )

    # Source API Filter
    sources = ["All API Sources"] + sorted(
        target_df["source"].unique().tolist()
    )
    selected_source = st.sidebar.selectbox("API Data Source:", options=sources)

    # Search Keyword
    search_keyword = st.sidebar.text_input(
        "Keyword Search (Title or Company):", ""
    )

    # Filter Logic
    filtered_df = target_df[target_df["Domain"].isin(selected_domains)]

    if selected_source != "All API Sources":
        filtered_df = filtered_df[filtered_df["source"] == selected_source]

    if search_keyword:
        filtered_df = filtered_df[
            filtered_df["title"].str.contains(
                search_keyword, case=False, na=False
            )
            | filtered_df["company"].str.contains(
                search_keyword, case=False, na=False
            )
        ]

    # --- Header Section ---
    st.title("💼 Multi-Source Remote Tech Job Engine")
    st.caption(
        "Aggregating Live Opportunities across Data Analytics, BI, Cybersecurity, and Finance from Remotive, Jobicy, and Arbeitnow"
    )
    st.markdown("---")

    # KPI Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active Matching Roles", len(filtered_df))
    m2.metric("Aggregated Sources", raw_df["source"].nunique())
    m3.metric(
        "Worldwide Openings",
        len(
            filtered_df[
                filtered_df["location"].str.contains("Worldwide", case=False)
            ]
        ),
    )
    m4.metric(
        "Unique Employers",
        (
            filtered_df["company"].nunique()
            if not filtered_df.empty
            else 0
        ),
    )

    st.markdown("---")

    # Analytics Section
    st.subheader("📊 Market Intelligence Breakdown")
    col1, col2 = st.columns(2)

    with col1:
        domain_counts = (
            filtered_df["Domain"].value_counts().reset_index()
        )
        domain_counts.columns = ["Domain", "Count"]
        fig_pie = px.pie(
            domain_counts,
            values="Count",
            names="Domain",
            title="Role Distribution",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        top_companies = (
            filtered_df["company"].value_counts().head(10).reset_index()
        )
        top_companies.columns = ["Company", "Openings"]
        fig_bar = px.bar(
            top_companies,
            x="Openings",
            y="Company",
            orientation="h",
            title="Top Hiring Companies",
            color="Openings",
            color_continuous_scale="Viridis",
        )
        fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # Output Grid & Download
    st.subheader("📋 Active Openings Grid")

    export_df = filtered_df[
        ["title", "company", "Domain", "location", "posted_date", "source", "url"]
    ].rename(
        columns={
            "title": "Role Title",
            "company": "Company",
            "location": "Location Constraint",
            "posted_date": "Date Posted",
            "source": "Source Feed",
            "url": "Application Link",
        }
    )

    csv_data = export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Search Results to CSV",
        data=csv_data,
        file_name="remote_jobs_aggregated.csv",
        mime="text/csv",
    )

    st.dataframe(
        export_df,
        column_config={
            "Application Link": st.column_config.LinkColumn(
                "Apply", display_text="Apply Now ↗"
            ),
            "Date Posted": st.column_config.DateColumn("Posted Date"),
        },
        use_container_width=True,
        hide_index=True,
    )
else:
    st.warning("No job feed data returned. Please try refreshing the app.")
