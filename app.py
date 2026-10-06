from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parent
LIVE_DATA = ROOT / "data" / "processed" / "jobs.csv"
SAMPLE_DATA = ROOT / "data" / "sample_jobs.csv"
SKILL_ORDER = [
    "SQL", "Power BI", "Excel", "Python", "Tableau", "Microsoft Fabric",
    "Azure", "DAX", "Power Query", "Stakeholder communication",
]
REGION_ORDER = [
    "London", "South East", "East of England", "South West", "East Midlands",
    "West Midlands", "Yorkshire and the Humber", "North West", "North East",
    "Scotland", "Wales", "Northern Ireland", "Unclassified",
]
COLOURS = {
    "ink": "#e8edf4", "muted": "#91a0b2", "panel": "#111b29",
    "line": "#243447", "teal": "#67e2c0", "blue": "#7eafff",
    "amber": "#ffc577", "rose": "#ff8e9e",
}

st.set_page_config(
    page_title="UK Data Careers Observatory",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&display=swap');
      html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif; }}
      .stApp {{ background: #0a111b; color: {COLOURS['ink']}; }}
      [data-testid="stHeader"] {{ background: rgba(10,17,27,.94); }}
      [data-testid="stSidebar"] {{ background: #0d1723; border-right: 1px solid #243447; }}
      [data-testid="stMetric"] {{ background: #111b29; border: 1px solid #243447;
        border-radius: 12px; padding: 18px 20px; }}
      [data-testid="stMetricLabel"] {{ color: #91a0b2; }}
      [data-testid="stMetricValue"] {{ color: #e8edf4; }}
      h1, h2, h3 {{ letter-spacing: -.035em; }}
      .eyebrow {{ color: #67e2c0; font: 500 11px 'DM Mono', monospace;
        letter-spacing: .14em; text-transform: uppercase; }}
      .lede {{ color: #91a0b2; font-size: 1.04rem; max-width: 760px; }}
      .source-note {{ color: #91a0b2; font: 11px 'DM Mono', monospace; }}
      .stAlert {{ border-radius: 10px; }}
      div[data-testid="stPlotlyChart"] {{ border: 1px solid #243447;
        border-radius: 12px; background: #111b29; padding: 8px; }}
      footer {{ visibility: hidden; }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_data(path: str, modified: float) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["posted_date"] = pd.to_datetime(frame["posted_date"], errors="coerce")
    frame["retrieved_on"] = pd.to_datetime(frame["retrieved_on"], errors="coerce")
    frame["salary_min"] = pd.to_numeric(frame["salary_min"], errors="coerce")
    frame["salary_max"] = pd.to_numeric(frame["salary_max"], errors="coerce")
    frame["is_synthetic"] = frame["is_synthetic"].astype(str).str.casefold().isin(["true", "1"])
    frame["salary_is_predicted"] = frame["salary_is_predicted"].astype(str).str.casefold().isin(["true", "1"])
    return frame


def chart_layout(fig, height: int = 330):
    fig.update_layout(
        height=height,
        margin=dict(l=18, r=18, t=24, b=14),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color=COLOURS["muted"], size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor=COLOURS["line"], zerolinecolor=COLOURS["line"], title=None),
        yaxis=dict(gridcolor=COLOURS["line"], zerolinecolor=COLOURS["line"], title=None),
        hoverlabel=dict(bgcolor="#172536", bordercolor=COLOURS["line"], font_color=COLOURS["ink"]),
    )
    return fig


data_path = LIVE_DATA if LIVE_DATA.exists() else SAMPLE_DATA
data = load_data(str(data_path), data_path.stat().st_mtime)
if data.empty:
    st.error("The selected data file contains no adverts. Collect a new sample or switch back to the synthetic preview.")
    st.stop()
synthetic = bool(data["is_synthetic"].all())
source_label = "Synthetic preview" if synthetic else "Adzuna sample"

st.markdown("<div class='eyebrow'>LABOUR MARKET · UNITED KINGDOM</div>", unsafe_allow_html=True)
st.title("UK Data Careers Observatory")
st.markdown(
    "<p class='lede'>A closer look at advertised demand for Data Analyst, BI Analyst and MI Analyst roles: "
    "where listings appear, which skills they mention, and when salary is disclosed.</p>",
    unsafe_allow_html=True,
)

if synthetic:
    st.warning(
        "Preview uses fictional sample records to demonstrate the dashboard. "
        "These figures do not describe the UK job market.",
        icon="ⓘ",
    )
else:
    latest_extract = data["retrieved_on"].max()
    extract_date = latest_extract.strftime("%d %b %Y") if pd.notna(latest_extract) else "date unavailable"
    st.info(
        f"Adzuna extract retrieved {extract_date}. Search coverage and missing fields limit what this sample represents.",
        icon="↗",
    )

with st.sidebar:
    st.markdown("<div class='eyebrow'>EXPLORE THE SAMPLE</div>", unsafe_allow_html=True)
    st.caption(f"Current source · {source_label}")
    role_options = sorted(data["role_family"].dropna().unique())
    selected_roles = st.multiselect("Role family", role_options, default=role_options)
    region_options = [r for r in REGION_ORDER if r in set(data["region"].dropna())]
    region_options += sorted(set(data["region"].dropna()) - set(region_options))
    selected_regions = st.multiselect("Location region", region_options, default=region_options)

    dates = data["posted_date"].dropna()
    if not dates.empty:
        min_date, max_date = dates.min().date(), dates.max().date()
        date_range = st.date_input(
            "Advertised date",
            value=(max(min_date, max_date - pd.Timedelta(days=90)), max_date),
            min_value=min_date,
            max_value=max_date,
        )
    else:
        date_range = ()
    st.divider()
    st.markdown("**How to read this**")
    st.caption("Pay charts include complete annual ranges not marked as predicted by the source. Skill rates use a small keyword list and the returned advert text.")
    st.caption("An advert is counted once per unique source ID in the current extract.")

filtered = data[data["role_family"].isin(selected_roles) & data["region"].isin(selected_regions)].copy()
if len(date_range) == 2:
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    filtered = filtered[filtered["posted_date"].between(start_date, end_date)]

if filtered.empty:
    st.info("No adverts match those filters. Widen your location or date selection.")
    st.stop()

salary_rows = filtered[
    (filtered["salary_period"] == "annual")
    & filtered["salary_min"].notna()
    & filtered["salary_max"].notna()
    & ~filtered["salary_is_predicted"]
].copy()
salary_rows["salary_midpoint"] = (salary_rows["salary_min"] + salary_rows["salary_max"]) / 2
salary_share = len(salary_rows) / len(filtered) * 100
salary_median = salary_rows["salary_midpoint"].median() if not salary_rows.empty else None
salary_display = f"£{salary_median:,.0f}" if pd.notna(salary_median) else "—"
region_share = (filtered["region"] != "Unclassified").mean() * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("Adverts in view", f"{len(filtered):,}", help="Unique posting IDs in the selected extract and filters.")
c2.metric("Source-reported annual ranges", f"{salary_share:.0f}%", help="Complete annual salary ranges not marked as predicted by the source.")
c3.metric("Median reported midpoint", salary_display, help="Median midpoint for complete annual ranges not marked as predicted by the source.")
c4.metric("Locations classified", f"{region_share:.0f}%", help="Share assigned a UK region. Unclassified locations remain visible in the location chart.")

left, right = st.columns([1.45, 1])
with left:
    st.subheader("When were these adverts posted?")
    monthly = (
        filtered.dropna(subset=["posted_date"])
        .assign(month=lambda df: df["posted_date"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)
        .size()
        .rename(columns={"size": "adverts"})
    )
    fig = px.area(monthly, x="month", y="adverts", markers=True)
    fig.update_traces(line_color=COLOURS["teal"], fillcolor="rgba(103,226,192,.12)", marker_color=COLOURS["teal"])
    fig.update_xaxes(tickformat="%b %y")
    st.plotly_chart(chart_layout(fig), use_container_width=True, config={"displayModeBar": False})
with right:
    st.subheader("Where are roles listed?")
    locations = filtered.groupby("region", as_index=False).size().rename(columns={"size": "adverts"})
    locations["region"] = pd.Categorical(locations["region"], categories=REGION_ORDER, ordered=True)
    locations = locations.sort_values("adverts", ascending=True)
    fig = px.bar(locations, x="adverts", y="region", orientation="h", text="adverts")
    fig.update_traces(marker_color=COLOURS["blue"], textposition="outside", cliponaxis=False)
    st.plotly_chart(chart_layout(fig), use_container_width=True, config={"displayModeBar": False})

left, right = st.columns([1, 1.45])
with left:
    st.subheader("What annual pay did employers report?")
    if salary_rows.empty:
        st.caption("No complete, employer-reported annual ranges match these filters. Values marked as predicted are excluded.")
        predicted_count = int(filtered["salary_is_predicted"].sum())
        if predicted_count:
            st.markdown(
                f"""
                <div style="display:flex;align-items:center;gap:9px;margin-top:14px">
                  <a href="https://www.adzuna.co.uk/jobs/salary-predictor.html"
                     title="Salary estimate powered by Adzuna Jobsworth">
                    <svg width="24" height="24" viewBox="0 0 24 24" role="img" aria-label="Salary estimate icon">
                      <circle cx="12" cy="12" r="11" fill="#67e2c0"/>
                      <text x="12" y="17" text-anchor="middle" font-size="15" font-family="sans-serif" fill="#0a111b">£</text>
                    </svg>
                  </a>
                  <a href="https://www.adzuna.co.uk/jobs/salary-predictor.html"
                     title="Salary estimate powered by Adzuna Jobsworth">Adzuna Jobsworth</a>
                  <span style="color:#91a0b2">· {predicted_count} source estimates excluded from the pay chart</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        fig = px.box(
            salary_rows, x="role_family", y="salary_midpoint", color="role_family",
            points="all", hover_data=["title", "region", "salary_is_predicted"],
            color_discrete_sequence=[COLOURS["teal"], COLOURS["blue"], COLOURS["amber"]],
        )
        fig.update_yaxes(tickprefix="£", tickformat=",.0f")
        fig.update_layout(showlegend=False)
        st.plotly_chart(chart_layout(fig, 360), use_container_width=True, config={"displayModeBar": False})
with right:
    st.subheader("Which skills appear in the text?")
    skill_records = []
    for skill in SKILL_ORDER:
        mentioned = filtered["skills"].fillna("").str.split("|").apply(lambda tags: skill in tags)
        count = int(mentioned.sum())
        skill_records.append({"skill": skill, "mention_rate": count / len(filtered) * 100, "mentions": count})
    skills = pd.DataFrame(skill_records).sort_values("mention_rate", ascending=True)
    fig = px.bar(skills, x="mention_rate", y="skill", orientation="h", text="mention_rate")
    fig.update_traces(marker_color=COLOURS["amber"], texttemplate="%{text:.0f}%", textposition="outside", cliponaxis=False)
    fig.update_xaxes(ticksuffix="%", range=[0, min(100, max(12, skills["mention_rate"].max() * 1.2))])
    st.plotly_chart(chart_layout(fig, 360), use_container_width=True, config={"displayModeBar": False})

with st.expander("Check sample coverage"):
    coverage = pd.DataFrame(
        {
            "Field": ["Advertised date", "Region classified", "Salary bounds returned", "Source-reported annual ranges", "Salary marked predicted", "Skill tags"],
            "Records present": [
                filtered["posted_date"].notna().sum(),
                (filtered["region"] != "Unclassified").sum(),
                (filtered["salary_min"].notna() & filtered["salary_max"].notna()).sum(),
                (filtered["salary_period"].eq("annual") & ~filtered["salary_is_predicted"]).sum(),
                filtered["salary_is_predicted"].sum(),
                filtered["skills"].fillna("").ne("").sum(),
            ],
            "Share": [
                filtered["posted_date"].notna().mean(),
                (filtered["region"] != "Unclassified").mean(),
                (filtered["salary_min"].notna() & filtered["salary_max"].notna()).mean(),
                (filtered["salary_period"].eq("annual") & ~filtered["salary_is_predicted"]).mean(),
                filtered["salary_is_predicted"].mean(),
                filtered["skills"].fillna("").ne("").mean(),
            ],
        }
    )
    coverage["Share"] = coverage["Share"].map(lambda value: f"{value:.0%}")
    st.dataframe(coverage, hide_index=True, use_container_width=True)
    st.caption("Low coverage can make a comparison misleading. Salary shares use annual-period detection from title and returned text.")

st.divider()
attribution = (
    "SYNTHETIC PREVIEW DATA"
    if synthetic
    else "<a href='https://www.adzuna.co.uk/'>The Adzuna API</a>"
)
st.markdown(
    f"<div class='source-note'>SOURCE: {attribution} · {len(data):,} UNIQUE RECORDS · "
    "SKILLS: KEYWORD MATCH · SALARY: SOURCE-REPORTED ANNUAL RANGES ONLY</div>",
    unsafe_allow_html=True,
)
