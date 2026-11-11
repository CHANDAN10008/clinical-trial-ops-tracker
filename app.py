"""TrialOps Monitor — simulated multi-site recruitment operations dashboard."""

import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from clinical_ops.analytics import build_site_performance
from clinical_ops.storage import load_demo_bundle, load_postgres_bundle

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="TrialOps Monitor", page_icon="🧪", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.7rem; padding-bottom: 2rem; max-width: 1500px;}
.eyebrow {color:#73d0bd; font-size:.76rem; letter-spacing:.18em; font-weight:700;}
[data-testid="stMetric"] {background:#101c2a; border:1px solid #233c50; padding:15px; border-radius:12px;}
[data-testid="stPlotlyChart"] {border:1px solid #233c50; border-radius:12px; padding:7px; background:#0b1520;}
.notice {border-left:3px solid #f3b553; padding:.65rem .85rem; background:#111b25; border-radius:5px;}
</style>
""", unsafe_allow_html=True)


def database_url_from_secrets() -> str:
    try:
        return str(st.secrets.get("DATABASE_URL", "")).strip() or os.getenv("DATABASE_URL", "").strip()
    except Exception:
        return os.getenv("DATABASE_URL", "").strip()


@st.cache_data(ttl=600, show_spinner="Loading synthetic trial operations data…")
def load_bundle(use_database: bool, database_url: str) -> dict:
    if use_database:
        return load_postgres_bundle(database_url)
    return load_demo_bundle(ROOT)


st.markdown("<div class='eyebrow'>CLINICAL TRIAL OPERATIONS · SIMULATED DEMO</div>", unsafe_allow_html=True)
st.title("TrialOps Monitor")
st.write("A multi-site view of patient recruitment flow, enrollment targets, and data-quality exceptions.")
st.markdown("<div class='notice'><b>Demo data only.</b> Every site, trial, and screening record is synthetic. No real participant information is collected or displayed.</div>", unsafe_allow_html=True)

database_url = database_url_from_secrets()
use_database = bool(database_url)
try:
    bundle = load_bundle(use_database, database_url)
except Exception as exc:
    st.error("Could not load the configured PostgreSQL dataset. Check the DATABASE_URL secret and the schema in sql/schema.sql.")
    st.exception(exc)
    st.stop()

trials = bundle["trials"]
sites = bundle["sites"]
assignments = bundle["assignments"]
screenings = bundle["screenings"]
targets = bundle["targets"]
quality_issues = bundle["quality_issues"]
quality_report = bundle["quality_report"]

for column in ["screening_date", "consent_date", "randomization_date", "withdrawal_date"]:
    screenings[column] = pd.to_datetime(screenings[column], errors="coerce")
targets["month"] = pd.to_datetime(targets["month"], errors="coerce")
assignments["activation_date"] = pd.to_datetime(assignments["activation_date"], errors="coerce")
trials["start_date"] = pd.to_datetime(trials["start_date"], errors="coerce")

with st.sidebar:
    st.header("Explore the study network")
    st.caption("Source: PostgreSQL secret" if use_database else "Source: deterministic synthetic CSV demo")
    study_options = trials["trial_id"].dropna().astype(str).tolist()
    selected_trials = st.multiselect("Studies", study_options, default=study_options)
    region_options = sorted(sites["region"].dropna().astype(str).unique().tolist())
    selected_regions = st.multiselect("Site regions", region_options, default=region_options)
    status_options = sorted(assignments["site_status"].dropna().astype(str).unique().tolist())
    selected_status = st.multiselect("Site status", status_options, default=status_options)
    minimum_date = screenings["screening_date"].min().date()
    maximum_date = screenings["screening_date"].max().date()
    date_range = st.date_input("Screening cohort dates", value=(minimum_date, maximum_date), min_value=minimum_date, max_value=maximum_date)
    if st.button("Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

selected_assignments = assignments.merge(sites[["site_id", "region", "site_name", "country"]], on="site_id", how="left")
selected_assignments = selected_assignments.loc[
    selected_assignments["trial_id"].isin(selected_trials)
    & selected_assignments["region"].isin(selected_regions)
    & selected_assignments["site_status"].isin(selected_status)
].copy()
selected_sites = sites.loc[sites["site_id"].isin(selected_assignments["site_id"].unique())].copy()
selected_trial_rows = trials.loc[trials["trial_id"].isin(selected_trials)].copy()
selected_ids = set(selected_assignments["assignment_id"])
selected_targets = targets.loc[targets["assignment_id"].isin(selected_ids)].copy()
selected_screenings = screenings.loc[screenings["assignment_id"].isin(selected_ids)].copy()

if not selected_assignments.empty:
    performance, monthly, cohort = build_site_performance(
        selected_trial_rows, selected_sites, selected_assignments.drop(columns=["region", "site_name", "country"]),
        selected_screenings, selected_targets, start_date, end_date,
    )
else:
    performance, monthly, cohort = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

if not cohort.empty:
    screened_count = int(cohort["screening_id"].nunique())
    eligible_count = int((cohort["eligibility_status"] == "Eligible").sum())
    consented_count = int(cohort["consent_date"].notna().sum())
    randomized_count = int(cohort["randomization_date"].notna().sum())
    withdrawn_count = int(cohort["withdrawal_date"].notna().sum())
else:
    screened_count = eligible_count = consented_count = randomized_count = withdrawn_count = 0
total_target = int(performance["target_enrollments"].sum()) if not performance.empty else 0
randomized_in_period_count = int(monthly["actual_enrollments"].sum()) if not monthly.empty else 0
attainment = (randomized_in_period_count / total_target * 100) if total_target else 0.0
at_risk_sites = int(performance.loc[performance["at_risk"], "site_id"].nunique()) if not performance.empty else 0
unique_sites = int(selected_assignments["site_id"].nunique())
screen_failure = ((screened_count - eligible_count) / screened_count * 100) if screened_count else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Sites in view", f"{unique_sites}")
k2.metric("Screened", f"{screened_count:,}")
k3.metric("Randomized (cohort)", f"{randomized_count:,}")
k4.metric("Target attainment", f"{attainment:.1f}%")
k5.metric("Sites with flags", f"{at_risk_sites}")

overview_tab, sites_tab, quality_tab, backlog_tab, sql_tab = st.tabs([
    "Recruitment overview", "Site performance", "Data quality", "Delivery backlog", "SQL workbench"
])

with overview_tab:
    funnel_data = pd.DataFrame({
        "Stage": ["Screened", "Eligible", "Consented", "Randomized", "Retained"],
        "Participants": [screened_count, eligible_count, consented_count, randomized_count, max(0, randomized_count - withdrawn_count)],
    })
    left, right = st.columns([1.0, 1.3])
    with left:
        fig = px.funnel(funnel_data, x="Participants", y="Stage", title="Recruitment conversion funnel",
                        color="Stage", color_discrete_sequence=["#6ed0c1", "#65b6ce", "#609ad0", "#778ce0", "#b78be0"])
        fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=55, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Screen-failure rate: {screen_failure:.1f}% · Consent conversion among eligible: {consented_count / eligible_count * 100 if eligible_count else 0:.1f}%")
    with right:
        if not monthly.empty:
            monthly_total = monthly.groupby("month", as_index=False)[["target_enrollments", "actual_enrollments"]].sum()
            fig = go.Figure()
            fig.add_trace(go.Bar(x=monthly_total["month"], y=monthly_total["target_enrollments"], name="Target", marker_color="#44677c"))
            fig.add_trace(go.Bar(x=monthly_total["month"], y=monthly_total["actual_enrollments"], name="Randomized", marker_color="#57c5ad"))
            fig.update_layout(title="Monthly enrollment: target vs actual", barmode="group", xaxis_title="Month", yaxis_title="Participants", margin=dict(l=10, r=10, t=55, b=10), legend=dict(orientation="h", y=1.12))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No monthly enrollment data matches the selected filters.")
    if not performance.empty:
        reason_counts = performance.loc[performance["bottleneck"] != "On track", "bottleneck"].str.split("; ").explode().value_counts().rename_axis("Bottleneck rule").reset_index(name="Assignment count")
        if not reason_counts.empty:
            st.subheader("Why sites are flagged")
            fig = px.bar(reason_counts, x="Assignment count", y="Bottleneck rule", orientation="h", color="Assignment count", color_continuous_scale="Teal")
            fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=20, b=10), yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

with sites_tab:
    st.subheader("Recruitment performance by site and study")
    st.caption("Rule flags are transparent review cues: attainment below 60%, screen-failure rate above 55%, median consent lag above 14 days, or zero randomizations despite an assigned target.")
    if performance.empty:
        st.info("Select at least one study, region, and site status.")
    else:
        view = performance[["trial_id", "protocol_title", "site_id", "site_name", "region", "site_status", "target_enrollments", "screened", "eligible", "consented", "randomized", "randomized_in_period", "withdrawn", "attainment_pct", "screen_failure_pct", "median_days_to_consent", "bottleneck"]].copy()
        st.dataframe(
            view.style.format({"attainment_pct": "{:.1f}%", "screen_failure_pct": "{:.1f}%", "median_days_to_consent": "{:.1f}"}, na_rep="—"),
            use_container_width=True, hide_index=True,
            column_config={
                "protocol_title": st.column_config.TextColumn("Protocol", width="large"),
                "randomized": st.column_config.NumberColumn("Randomized in screening cohort"),
                "randomized_in_period": st.column_config.NumberColumn("Randomized in target months"),
                "target_enrollments": st.column_config.NumberColumn("Target in selected months"),
                "bottleneck": st.column_config.TextColumn("Review flag", width="large"),
            },
        )
        st.download_button("Download filtered site report", view.to_csv(index=False), "trialops_site_performance.csv", "text/csv")
        fig = px.scatter(view, x="target_enrollments", y="randomized_in_period", color="bottleneck", size="screened", hover_name="site_name", hover_data=["trial_id", "region", "attainment_pct"], title="Randomizations in selected period vs assigned target", color_discrete_sequence=px.colors.qualitative.Safe)
        fig.update_layout(xaxis_title="Target in selected months", yaxis_title="Randomized in selected months", margin=dict(l=10, r=10, t=55, b=10))
        st.plotly_chart(fig, use_container_width=True)

with quality_tab:
    st.subheader("Source checks and repair log")
    q1, q2, q3 = st.columns(3)
    q1.metric("Source screening rows", f"{quality_report.get('source_screening_rows', quality_report.get('screening_rows', 0)):,}")
    q2.metric("Clean screening rows", f"{quality_report.get('clean_screening_rows', len(screenings)):,}")
    q3.metric("Logged quality issues", f"{quality_report.get('quality_issue_count', len(quality_issues)):,}")
    st.json(quality_report)
    st.write("Detected examples")
    st.dataframe(quality_issues.head(100), use_container_width=True, hide_index=True)
    if not quality_issues.empty and "issue_type" in quality_issues:
        issue_summary = quality_issues["issue_type"].value_counts().rename_axis("Issue type").reset_index(name="Rows")
        st.bar_chart(issue_summary, x="Issue type", y="Rows", color="#e4a95a")
    st.download_button("Download quality issue log", quality_issues.to_csv(index=False), "trialops_data_quality_issues.csv", "text/csv")

with backlog_tab:
    st.subheader("Prioritized vertical-slice backlog")
    st.caption("Stories are scoped for a simulated portfolio demo. Status refers to the capabilities represented in this demo; it does not imply work at a real sponsor or site.")
    backlog = pd.read_csv(ROOT / "docs" / "user_stories.csv")
    sprint_filter = st.multiselect("Sprint", sorted(backlog["sprint"].unique()), default=sorted(backlog["sprint"].unique()))
    priority_filter = st.multiselect("Priority", sorted(backlog["priority"].unique()), default=sorted(backlog["priority"].unique()))
    selected_backlog = backlog[backlog["sprint"].isin(sprint_filter) & backlog["priority"].isin(priority_filter)]
    st.dataframe(selected_backlog[["story_id", "sprint", "priority", "status", "story", "acceptance_criteria"]], use_container_width=True, hide_index=True,
                 column_config={"acceptance_criteria": st.column_config.TextColumn("Acceptance criteria", width="large"), "story": st.column_config.TextColumn("User story", width="large")})
    st.caption("A downloadable CSV and full story notes are included in the repository docs. This demo provides a reviewed backlog artifact; it does not create or claim a live GitHub Projects board.")

with sql_tab:
    st.subheader("PostgreSQL schema and stakeholder queries")
    st.caption("The public demo runs on synthetic CSV data by default. Add a PostgreSQL DATABASE_URL in Streamlit Secrets to read the documented trialops tables.")
    query_files = [("Schema", ROOT / "sql" / "schema.sql"), ("Stakeholder reporting", ROOT / "sql" / "queries.sql"), ("QA checks", ROOT / "sql" / "qa_checks.sql")]
    for label, path in query_files:
        with st.expander(label):
            st.code(path.read_text(encoding="utf-8"), language="sql")
    st.info("SQL assets include CTEs, date grouping, filtered aggregates, RANK, LAG, and cumulative window frames. PostgreSQL integration is optional; no participant or database credentials are required for the public demo.")

st.divider()
st.caption(f"Data source: {bundle['source_mode']} · {int(trials['trial_id'].nunique())} simulated studies · {int(sites['site_id'].nunique())} sites · Synthetic participant references only")
