import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Remote Job Market Analytics Engine",
    page_icon="📊",
    layout="wide",
)


# Data Ingestion Layer with Caching
@st.cache_data(ttl=3600)
def load_job_data():
    url = "https://remotive.com/api/remote-jobs"
    try:
        res = requests.get(url, timeout=12)
        if res.status_code == 200:
            data = res.json().get("jobs", [])
            df = pd.DataFrame(data)
            df["publication_date"] = pd.to_datetime(df["publication_date"])
            df["posted_date"] = df["publication_date"].dt.date
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching API feed: {e}")
        return pd.DataFrame()


def categorize_domain(title):
    t = str(title).lower()
    if any(k in t for k in ["data analyst", "data analytics", "data engineer"]):
        return "Data Analytics"
    elif any(
        k in t
        for k in ["business intelligence", "bi analyst", "tableau", "power bi"]
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
        ]
    ):
        return "Cybersecurity"
    return "Other"


# Data Processing
raw_df = load_job_data()

if not raw_df.empty:
    raw_df["Domain"] = raw_df["title"].apply(categorize_domain)
    target_df = raw_df[raw_df["Domain"] != "Other"].copy()

    # --- Sidebar Controls ---
    st.sidebar.title("⚙️ Engine Controls")
    selected_domains = st.sidebar.multiselect(
        "Select Target Domains:",
        options=["Data Analytics", "Business Intelligence", "Cybersecurity"],
        default=[
            "Data Analytics",
            "Business Intelligence",
            "Cybersecurity",
        ],
    )

    search_term = st.sidebar.text_input("Search Title or Company:", "")

    # Filter Logic
    filtered_df = target_df[target_df["Domain"].isin(selected_domains)]
    if search_term:
        filtered_df = filtered_df[
            filtered_df["title"].str.contains(search_term, case=False, na=False)
            | filtered_df["company_name"].str.contains(
                search_term, case=False, na=False
            )
        ]

    # --- Header Section ---
    st.title("📊 Remote Tech Job Market Intelligence Engine")
    st.caption(
        "Live Market Data Engine & Visual Analytics for Data Analytics, BI, and Cybersecurity Roles"
    )
    st.markdown("---")

    # --- High-Level Metrics ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Relevant Roles", len(filtered_df))
    m2.metric(
        "Data Analytics",
        len(filtered_df[filtered_df["Domain"] == "Data Analytics"]),
    )
    m3.metric(
        "Business Intelligence",
        len(filtered_df[filtered_df["Domain"] == "Business Intelligence"]),
    )
    m4.metric(
        "Cybersecurity",
        len(filtered_df[filtered_df["Domain"] == "Cybersecurity"]),
    )

    st.markdown("---")

    # --- Visual Market Analytics ---
    st.subheader("📈 Interactive Market Analytics")

    col1, col2 = st.columns(2)

    with col1:
        # Domain Share Chart
        domain_counts = (
            filtered_df["Domain"].value_counts().reset_index()
        )
        domain_counts.columns = ["Domain", "Count"]

        fig_pie = px.pie(
            domain_counts,
            values="Count",
            names="Domain",
            title="Role Distribution by Domain",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_pie.update_layout(margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Top Hiring Companies
        top_companies = (
            filtered_df["company_name"]
            .value_counts()
            .head(10)
            .reset_index()
        )
        top_companies.columns = ["Company", "Open Positions"]

        fig_bar = px.bar(
            top_companies,
            x="Open Positions",
            y="Company",
            orientation="h",
            title="Top Hiring Companies in Target Domains",
            color="Open Positions",
            color_continuous_scale="Blues",
        )
        fig_bar.update_layout(
            yaxis={"categoryorder": "total ascending"},
            margin=dict(t=40, b=20, l=20, r=20),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Time-Series Posting Volume Chart
    st.subheader("📅 Posting Velocity Over Time")
    trend_df = (
        filtered_df.groupby(["posted_date", "Domain"])
        .size()
        .reset_index(name="Postings")
    )

    fig_line = px.line(
        trend_df,
        x="posted_date",
        y="Postings",
        color="Domain",
        title="Daily Job Posting Velocity by Domain",
        markers=True,
    )
    fig_line.update_xaxes(title_text="Publication Date")
    fig_line.update_yaxes(title_text="Number of Positions")
    st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("---")

    # --- Data Grid View ---
    st.subheader("📋 Active Openings Grid")

    table_df = filtered_df[
        [
            "title",
            "company_name",
            "Domain",
            "candidate_required_location",
            "publication_date",
            "url",
        ]
    ].rename(
        columns={
            "title": "Role Title",
            "company_name": "Company",
            "candidate_required_location": "Location",
            "publication_date": "Posted Date",
            "url": "Application Link",
        }
    )

    st.dataframe(
        table_df,
        column_config={
            "Application Link": st.column_config.LinkColumn(
                "Apply", display_text="Apply Now ↗"
            ),
            "Posted Date": st.column_config.DateColumn("Date Posted"),
        },
        use_container_width=True,
        hide_index=True,
    )
else:
    st.warning("No live market data available. Please verify connection status.")
