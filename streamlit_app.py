import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats
import pickle, re
from pathlib import Path
from collections import Counter
from datetime import datetime

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Job Market Intelligence | J. Charan Reddy",
    page_icon="📊", layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSV Tracking Setup ───────────────────────────────────────────────────────
TRACK_DIR = Path(__file__).parent / "data" / "tracking"
TRACK_DIR.mkdir(parents=True, exist_ok=True)

ACTIVITY_CSV    = TRACK_DIR / "activity_log.csv"
PREDICTIONS_CSV = TRACK_DIR / "salary_predictions.csv"
FILTERS_CSV     = TRACK_DIR / "filter_selections.csv"

def _append_csv(filepath, row: dict):
    df_new = pd.DataFrame([row])
    if filepath.exists():
        df_new.to_csv(filepath, mode="a", header=False, index=False)
    else:
        df_new.to_csv(filepath, index=False)

def log_activity(page, action, detail=""):
    _append_csv(ACTIVITY_CSV, {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "page": page, "action": action, "detail": str(detail)
    })

def log_prediction(role, city, state, emp_type, is_remote, predicted, market_avg):
    _append_csv(PREDICTIONS_CSV, {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "role": role, "city": city, "state": state,
        "employment_type": emp_type, "is_remote": is_remote,
        "predicted_salary": round(predicted, 0),
        "market_avg": round(market_avg, 0),
        "diff_pct": round((predicted - market_avg) / market_avg * 100, 1) if market_avg > 0 else 0
    })

def log_filter(page, filter_type, value):
    _append_csv(FILTERS_CSV, {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "page": page, "filter_type": filter_type, "value": str(value)
    })

def read_csv_safe(filepath):
    return pd.read_csv(filepath) if filepath.exists() else pd.DataFrame()

# ─── Styles ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #0a0a0f; color: #e2e8f0; }
section[data-testid="stSidebar"] { background: #0f0f1a; border-right: 1px solid #1e1e2e; }
.hero-container {
    background: linear-gradient(135deg, #0f0f1a 0%, #1a0a2e 50%, #0a1628 100%);
    border: 1px solid #2d2d4e; border-radius: 16px; padding: 48px;
    margin-bottom: 32px; position: relative; overflow: hidden;
}
.hero-container::before {
    content: ''; position: absolute; top: -50%; right: -20%;
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
}
.hero-title {
    font-family: 'Space Mono', monospace; font-size: 2.8rem; font-weight: 700;
    background: linear-gradient(135deg, #818cf8, #38bdf8, #34d399);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0 0 8px 0; line-height: 1.2;
}
.hero-subtitle { color: #94a3b8; font-size: 1.1rem; font-weight: 300; margin: 0 0 24px 0; }
.author-badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.3);
    border-radius: 100px; padding: 8px 20px;
    font-family: 'Space Mono', monospace; font-size: 0.85rem;
    color: #818cf8; letter-spacing: 0.05em;
}
.metric-card {
    background: #0f0f1a; border: 1px solid #1e1e2e; border-radius: 12px;
    padding: 24px; text-align: center;
}
.metric-card:hover { border-color: #6366f1; }
.metric-value { font-family: 'Space Mono', monospace; font-size: 2rem; font-weight: 700; color: #818cf8; }
.metric-label { font-size: 0.8rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px; }
.section-header {
    font-family: 'Space Mono', monospace; font-size: 1.1rem; color: #38bdf8;
    border-left: 3px solid #38bdf8; padding-left: 12px; margin: 32px 0 16px 0;
}
.insight-box {
    background: rgba(56,189,248,0.05); border: 1px solid rgba(56,189,248,0.2);
    border-radius: 8px; padding: 16px 20px; margin: 8px 0;
    font-size: 0.9rem; color: #94a3b8;
}
.insight-box strong { color: #38bdf8; }
.stat-pill {
    display: inline-block; background: rgba(52,211,153,0.1);
    border: 1px solid rgba(52,211,153,0.3); border-radius: 100px;
    padding: 4px 12px; font-size: 0.8rem; color: #34d399; margin: 2px;
}
.recommendation-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(56,189,248,0.05));
    border: 1px solid rgba(99,102,241,0.25); border-radius: 10px;
    padding: 16px 20px; margin: 8px 0;
}
.prediction-result {
    background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(56,189,248,0.1));
    border: 1px solid rgba(99,102,241,0.4); border-radius: 12px;
    padding: 32px; text-align: center;
}
.predicted-salary {
    font-family: 'Space Mono', monospace; font-size: 3rem; font-weight: 700;
    background: linear-gradient(135deg, #818cf8, #38bdf8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
footer { display: none; }
#MainMenu { display: none; }
</style>
""", unsafe_allow_html=True)

# ─── Plotly Theme ─────────────────────────────────────────────────────────────
T = dict(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
         plot_bgcolor="rgba(0,0,0,0)", font=dict(family="DM Sans", color="#94a3b8"),
         margin=dict(t=48, b=32, l=16, r=16))

# ─── Helpers ─────────────────────────────────────────────────────────────────
SKILLS = ["python","sql","tableau","power bi","excel","machine learning","deep learning",
          "spark","aws","azure","gcp","docker","kubernetes","tensorflow","pytorch",
          "scikit-learn","pandas","numpy","r","scala","kafka","airflow","dbt",
          "looker","snowflake","databricks","nlp","statistics","visualization","communication"]
clean = lambda t: re.sub(r"[^a-zA-Z\s]","",str(t).lower())

def rec_card(title, desc, color="#818cf8"):
    st.markdown(f"""
    <div class='recommendation-card'>
        <div style='color:{color}; font-size:0.8rem; text-transform:uppercase;
                    letter-spacing:0.1em; margin-bottom:6px; font-family:Space Mono,monospace;'>{title}</div>
        <div style='color:#94a3b8; font-size:0.88rem; line-height:1.6;'>{desc}</div>
    </div>""", unsafe_allow_html=True)

# ─── Data & Model ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent

@st.cache_data
def load_data():
    data_path = Path("data/jobs_cleaned.csv")
    df = pd.read_csv(data_path)
    df["Job Is Remote"] = df["Job Is Remote"].astype(bool)
    return df

@st.cache_resource
def load_model():
    try:
        return (pickle.load(open(BASE_DIR / "models" / "salary_model.pkl","rb")),
                pickle.load(open(BASE_DIR / "models" / "encoders.pkl","rb")))
    except:
        return None, None
df = load_data()
model, encoders = load_model()

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:20px 0 8px 0;'>
        <div style='font-family:Space Mono,monospace; font-size:0.7rem; color:#4b5563;
                    text-transform:uppercase; letter-spacing:0.15em;'>Navigation</div>
    </div>""", unsafe_allow_html=True)

    page = st.radio("", [
        "Overview", "Market Analysis", "NLP — Skill Intelligence",
        "Statistical Testing", "Salary Predictor",
        "Raw Data Explorer", "User Activity & Extracts", "About This Project"
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown(f"""
    <div style='font-size:0.75rem; color:#4b5563; line-height:1.8;'>
        <div style='font-family:Space Mono,monospace; color:#6366f1; margin-bottom:8px;'>Dataset</div>
        Total Records: <span style='color:#e2e8f0;'>{len(df)}</span><br>
        Roles Covered: <span style='color:#e2e8f0;'>6</span><br>
        With Salary: <span style='color:#e2e8f0;'>{(df["Avg Salary"]>0).sum()}</span><br>
        Source: <span style='color:#e2e8f0;'>JSearch API</span>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.7rem; color:#374151; text-align:center; font-family:Space Mono,monospace;'>
        Built by J. CHARAN REDDY<br>March 2026
    </div>""", unsafe_allow_html=True)

# ─── Log page visit ───────────────────────────────────────────────────────────
log_activity(page, "Page Visit")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "Overview":
    st.markdown("""
    <div class='hero-container'>
        <div class='hero-title'>Job Market<br>Intelligence Platform</div>
        <div class='hero-subtitle'>Real-time analysis of 929 live job listings across 6 data roles — US Market 2026</div>
        <div class='author-badge'>&#9632; Built by J. CHARAN REDDY &nbsp;|&nbsp; March 2026</div>
    </div>""", unsafe_allow_html=True)

    df_sal = df[df["Avg Salary"]>0]
    for col,(v,l) in zip(st.columns(5), [
        (f"{len(df):,}","Total Jobs"), ("6","Roles Covered"),
        (f"${df_sal['Avg Salary'].mean():,.0f}","Avg Salary"),
        (f"{df['Job Is Remote'].sum()}","Remote Jobs"),
        (f"{df['Employer Name'].nunique()}","Companies"),
    ]):
        col.markdown(f"""<div class='metric-card'>
            <div class='metric-value'>{v}</div>
            <div class='metric-label'>{l}</div></div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Role Distribution</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([3,2])
    with c1:
        rc = df["Role"].value_counts().reset_index()
        rc.columns = ["Role","Count"]
        rc["Pct"] = (rc["Count"]/rc["Count"].sum()*100).round(1)
        fig = px.bar(rc, x="Count", y="Role", orientation="h", color="Count",
                     color_continuous_scale="viridis", text=rc["Pct"].apply(lambda x: f"{x}%"))
        fig.update_traces(textposition="outside", textfont=dict(color="#94a3b8", size=11))
        fig.update_layout(**T, title="Jobs by Role", showlegend=False,
                          yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("<div class='section-header'>Key Findings</div>", unsafe_allow_html=True)
        for key,val in [
            ("ML Engineer","highest avg salary at $69K"),
            ("97.4%","of jobs are onsite — remote is rare"),
            ("Washington DC","top hiring city with 83 listings"),
            ("Capital One","most active recruiter — 28 listings"),
            ("Machine Learning","most demanded skill phrase"),
        ]:
            st.markdown(f"<div class='insight-box'><strong>{key}</strong> — {val}</div>",
                        unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Salary Distribution by Role</div>", unsafe_allow_html=True)
    fig = px.box(df_sal, x="Role", y="Avg Salary", color="Role",
                 color_discrete_sequence=px.colors.qualitative.Bold)
    fig.update_layout(**T, showlegend=False, xaxis_tickangle=-15)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-header'>Role Summary Table</div>", unsafe_allow_html=True)
    summary = df.groupby("Role").agg(
        Total_Jobs=("Role","count"),
        Remote_Jobs=("Job Is Remote","sum"),
        Avg_Salary=("Avg Salary", lambda x: f"${x[x>0].mean():,.0f}" if (x>0).any() else "N/A"),
        Top_City=("Job City", lambda x: x.mode()[0]),
        Top_Company=("Employer Name", lambda x: x.mode()[0])
    ).reset_index()
    st.dataframe(summary, use_container_width=True, hide_index=True)
    st.download_button("Download Role Summary", summary.to_csv(index=False).encode(),
                       "role_summary.csv","text/csv")

    st.markdown("<div class='section-header'>Market Recommendations</div>", unsafe_allow_html=True)
    best_sal_role = df_sal.groupby("Role")["Avg Salary"].mean().idxmax()
    most_jobs_role = df["Role"].value_counts().idxmax()
    rec_card("Highest Paying Role", f"<strong>{best_sal_role}</strong> offers the highest average salary — prioritize if you have the skills.")
    rec_card("Highest Demand Role", f"<strong>{most_jobs_role}</strong> has the most listings — highest chance of landing interviews quickly.")
    rec_card("Remote Job Reality", f"Only <strong>{df['Job Is Remote'].mean()*100:.1f}%</strong> of all data jobs are remote in 2026. Build a strong onsite strategy.")
    rec_card("Geographic Strategy", "Washington DC, New York and McLean dominate hiring. Targeting these cities significantly increases your chances.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — MARKET ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Market Analysis":
    st.markdown("<h2 style='color:#818cf8; font-family:Space Mono,monospace;'>Market Analysis</h2>",
                unsafe_allow_html=True)

    with st.expander("Filters", expanded=True):
        c1, c2, c3 = st.columns(3)
        roles = c1.multiselect("Role", df["Role"].unique(), default=df["Role"].unique())
        states = c2.multiselect("State", sorted(df[df["Job State"]!="Unknown"]["Job State"].unique()))
        remote = c3.selectbox("Work Type", ["All","Remote Only","Onsite Only"])

    log_filter("Market Analysis","roles_selected", roles)
    if states: log_filter("Market Analysis","states_selected", states)
    log_filter("Market Analysis","work_type", remote)

    fdf = df[df["Role"].isin(roles)]
    if states: fdf = fdf[fdf["Job State"].isin(states)]
    if remote == "Remote Only": fdf = fdf[fdf["Job Is Remote"]==True]
    elif remote == "Onsite Only": fdf = fdf[fdf["Job Is Remote"]==False]

    st.markdown(f"<div class='stat-pill'>{len(fdf)} jobs match current filters</div>",
                unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(fdf.groupby("Employer Name").size().reset_index(name="count").nlargest(10,"count"),
                     x="count", y="Employer Name", orientation="h", color="count",
                     color_continuous_scale="plasma", title="Top 10 Hiring Companies")
        fig.update_layout(**T, showlegend=False, yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(fdf[fdf["Job City"]!="Unknown"].groupby("Job City").size()
                     .reset_index(name="count").nlargest(10,"count"),
                     x="count", y="Job City", orientation="h", color="count",
                     color_continuous_scale="viridis", title="Top 10 Cities")
        fig.update_layout(**T, showlegend=False, yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        rc = fdf["Job Is Remote"].map({True:"Remote",False:"Onsite"}).value_counts().reset_index()
        rc.columns = ["Type","Count"]
        fig = px.pie(rc, names="Type", values="Count", hole=0.5,
                     color_discrete_sequence=["#6366f1","#38bdf8"], title="Remote vs Onsite")
        fig.update_layout(**T)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        ec = fdf["Job Employment Type"].value_counts().reset_index()
        ec.columns = ["Type","Count"]
        fig = px.pie(ec, names="Type", values="Count", hole=0.5,
                     color_discrete_sequence=px.colors.qualitative.Bold, title="Employment Type")
        fig.update_layout(**T)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-header'>Salary by Employment Type</div>", unsafe_allow_html=True)
    fig = px.box(fdf[fdf["Avg Salary"]>0], x="Job Employment Type", y="Avg Salary",
                 color="Job Employment Type", title="Salary by Employment Type")
    fig.update_layout(**T, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-header'>State-Level Heatmap</div>", unsafe_allow_html=True)
    pivot = fdf[fdf["Job State"]!="Unknown"].groupby(["Job State","Role"]).size().unstack(fill_value=0)
    fig = px.imshow(pivot, color_continuous_scale="viridis", title="Job Density by Role & State", aspect="auto")
    fig.update_layout(**T)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-header'>Market Insights & Recommendations</div>",unsafe_allow_html=True)
    top_role = fdf["Role"].value_counts().idxmax()
    top_city = fdf[fdf["Job City"]!="Unknown"]["Job City"].value_counts().idxmax()
    top_co   = fdf["Employer Name"].value_counts().idxmax()
    remote_pct = fdf["Job Is Remote"].mean()*100
    rec_card("Highest Demand Role", f"<strong>{top_role}</strong> has the most listings in your filtered view — prioritize this role.")
    rec_card("Best City to Target", f"<strong>{top_city}</strong> has the highest job concentration — consider targeting companies here.")
    rec_card("Top Recruiter to Follow", f"<strong>{top_co}</strong> is the most active hiring company — follow their careers page directly.")
    rec_card("Remote Availability", f"Only <strong>{remote_pct:.1f}%</strong> of filtered jobs are remote. {'Apply broadly onsite.' if remote_pct<5 else 'Some remote options exist.'}")

    st.markdown("<div class='section-header'>Full Market Data Table</div>", unsafe_allow_html=True)
    mkt_table = fdf.groupby(["Role","Job City","Job State"]).agg(
        Jobs=("Role","count"),
        Avg_Salary=("Avg Salary", lambda x: f"${x[x>0].mean():,.0f}" if (x>0).any() else "N/A"),
        Remote_Count=("Job Is Remote","sum")
    ).reset_index().sort_values("Jobs", ascending=False).head(25)
    st.dataframe(mkt_table, use_container_width=True, hide_index=True)
    st.download_button("Download Market Table", mkt_table.to_csv(index=False).encode(),
                       "market_table.csv","text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — NLP
# ══════════════════════════════════════════════════════════════════════════════
elif page == "NLP — Skill Intelligence":
    st.markdown("<h2 style='color:#818cf8; font-family:Space Mono,monospace;'>NLP — Skill Intelligence</h2>",
                unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b;'>Extracted from 929 real job descriptions using spaCy & NLTK VADER</p>",
                unsafe_allow_html=True)

    role_f = st.selectbox("Select Role", ["All Roles"] + sorted(df["Role"].unique()))
    log_filter("NLP","role_selected", role_f)
    fdf = df if role_f=="All Roles" else df[df["Role"]==role_f]

    skill_counts = Counter(s for d in fdf["Job Description"].dropna() for s in SKILLS if s in clean(d))
    skills_df = pd.DataFrame(skill_counts.most_common(20), columns=["Skill","Count"])

    c1, c2 = st.columns([3,2])
    with c1:
        fig = px.bar(skills_df, x="Count", y="Skill", orientation="h", color="Count",
                     color_continuous_scale="viridis", title=f"Top 20 Skills — {role_f}")
        fig.update_layout(**T, showlegend=False, yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("<div class='section-header'>Skill Demand %</div>", unsafe_allow_html=True)
        for skill, count in skill_counts.most_common(10):
            pct = int(count/len(fdf)*100)
            st.markdown(f"""
            <div style='display:flex; justify-content:space-between; align-items:center;
                        padding:8px 0; border-bottom:1px solid #1e1e2e;'>
                <span style='color:#e2e8f0; font-size:0.9rem;'>{skill.title()}</span>
                <div style='display:flex; align-items:center; gap:8px;'>
                    <div style='width:80px; height:4px; background:#1e1e2e; border-radius:2px;'>
                        <div style='width:{min(pct,100)}%; height:100%; background:#6366f1; border-radius:2px;'></div>
                    </div>
                    <span style='color:#6366f1; font-size:0.8rem; font-family:Space Mono,monospace;'>{pct}%</span>
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Skill vs Role Heatmap</div>", unsafe_allow_html=True)
    top_skills = [s for s,_ in skill_counts.most_common(10)]
    heat_df = pd.DataFrame(
        {role: [sum(1 for d in df[df["Role"]==role]["Job Description"].dropna()
                    if s in clean(d)) for s in top_skills]
         for role in df["Role"].unique()}, index=top_skills)
    fig = px.imshow(heat_df, color_continuous_scale="viridis", aspect="auto",
                    title="Top 10 Skills vs Role", text_auto=True)
    fig.update_layout(**T)
    st.plotly_chart(fig, use_container_width=True)

    try:
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        import nltk
        nltk.download("vader_lexicon", quiet=True)
        sia = SentimentIntensityAnalyzer()
        fdf = fdf.copy()
        fdf["Sentiment"] = fdf["Job Description"].dropna().apply(lambda x: sia.polarity_scores(x)["compound"])
        fdf["Sentiment Label"] = pd.cut(fdf["Sentiment"], bins=[-1,-0.05,0.05,1],
                                        labels=["Negative","Neutral","Positive"])
        c1, c2 = st.columns(2)
        with c1:
            fig = px.histogram(fdf, x="Sentiment", color="Sentiment Label",
                               color_discrete_map={"Positive":"#34d399","Neutral":"#f59e0b","Negative":"#ef4444"},
                               title="Sentiment Distribution", nbins=40)
            fig.update_layout(**T)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.box(fdf, x="Role", y="Sentiment", color="Role", title="Sentiment by Role")
            fig.update_layout(**T, showlegend=False, xaxis_tickangle=-15)
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Sentiment unavailable: {e}")

    st.markdown("<div class='section-header'>Skills Priority Table</div>", unsafe_allow_html=True)
    skills_full = pd.DataFrame(skill_counts.most_common(15), columns=["Skill","Mentions"])
    skills_full["Demand %"] = (skills_full["Mentions"]/len(fdf)*100).round(1).astype(str)+"%"
    q70, q40 = skills_full["Mentions"].quantile(0.7), skills_full["Mentions"].quantile(0.4)
    skills_full["Priority"] = skills_full["Mentions"].apply(
        lambda x: "Must Have" if x>=q70 else "Good to Have" if x>=q40 else "Nice to Have")
    st.dataframe(skills_full, use_container_width=True, hide_index=True)
    st.download_button("Download Skills Table",
                       skills_full.to_csv(index=False).encode(),
                       f"skills_{role_f.replace(' ','_')}.csv","text/csv")

    st.markdown("<div class='section-header'>Learning Recommendations</div>", unsafe_allow_html=True)
    must = skills_full[skills_full["Priority"]=="Must Have"]["Skill"].tolist()
    good = skills_full[skills_full["Priority"]=="Good to Have"]["Skill"].tolist()
    nice = skills_full[skills_full["Priority"]=="Nice to Have"]["Skill"].tolist()
    rec_card("Must Have — Learn These First",
             f"{', '.join([s.title() for s in must])} — Master these before applying.", "#ef4444")
    rec_card("Good to Have — Learn After Basics",
             f"{', '.join([s.title() for s in good])} — Strong differentiators above average candidates.", "#f59e0b")
    rec_card("Nice to Have — Long-Term Goals",
             f"{', '.join([s.title() for s in nice])} — Opens doors to senior or niche roles.", "#34d399")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — STATISTICAL TESTING
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Statistical Testing":
    st.markdown("<h2 style='color:#818cf8; font-family:Space Mono,monospace;'>Statistical Hypothesis Testing</h2>",
                unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b;'>T-test & Mann-Whitney U test at α = 0.05</p>",
                unsafe_allow_html=True)

    df_sal = df[df["Avg Salary"]>0]
    ds = df_sal[df_sal["Role"]=="Data Scientist"]["Avg Salary"]
    da = df_sal[df_sal["Role"]=="Data Analyst"]["Avg Salary"]
    t1, p1 = stats.ttest_ind(ds, da)
    _, pm1 = stats.mannwhitneyu(ds, da, alternative="two-sided")

    st.markdown("<div class='section-header'>H1 — Data Scientist vs Data Analyst</div>",
                unsafe_allow_html=True)
    for col,(v,l) in zip(st.columns(4), [
        (f"${ds.mean():,.0f}","DS Avg"), (f"${da.mean():,.0f}","DA Avg"),
        (f"{t1:.3f}","T-Statistic"), (f"{p1:.4f}","P-Value")
    ]):
        col.metric(l, v)

    color = "#34d399" if p1<0.05 else "#ef4444"
    st.markdown(f"""<div style='border:1px solid {color}; border-radius:8px; padding:16px;
        margin:8px 0; color:{color}; font-family:Space Mono,monospace; font-size:0.85rem;'>
        {"REJECT — DS earns significantly more (p < 0.05)" if p1<0.05 else "FAIL TO REJECT"}
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.box(df_sal[df_sal["Role"].isin(["Data Scientist","Data Analyst"])],
                     x="Role", y="Avg Salary", color="Role",
                     color_discrete_sequence=["#6366f1","#38bdf8"], title=f"H1 (p={p1:.4f})")
        fig.update_layout(**T, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.histogram(df_sal[df_sal["Role"].isin(["Data Scientist","Data Analyst"])],
                           x="Avg Salary", color="Role", nbins=30, barmode="overlay",
                           color_discrete_sequence=["#6366f1","#38bdf8"], title="Distribution Overlap")
        fig.update_layout(**T)
        st.plotly_chart(fig, use_container_width=True)

    remote_sal = df_sal[df_sal["Job Is Remote"]==True]["Avg Salary"]
    onsite_sal = df_sal[df_sal["Job Is Remote"]==False]["Avg Salary"]
    t2, p2 = stats.ttest_ind(remote_sal, onsite_sal)
    _, pm2 = stats.mannwhitneyu(remote_sal, onsite_sal, alternative="two-sided")

    st.markdown("<div class='section-header'>H2 — Remote vs Onsite Salary</div>",
                unsafe_allow_html=True)
    for col,(v,l) in zip(st.columns(4), [
        (f"${remote_sal.mean():,.0f}",f"Remote (n={len(remote_sal)})"),
        (f"${onsite_sal.mean():,.0f}",f"Onsite (n={len(onsite_sal)})"),
        (f"{t2:.3f}","T-Statistic"), (f"{p2:.4f}","P-Value")
    ]):
        col.metric(l, v)

    color2 = "#34d399" if p2<0.05 else "#f59e0b"
    st.markdown(f"""<div style='border:1px solid {color2}; border-radius:8px; padding:16px;
        margin:8px 0; color:{color2}; font-family:Space Mono,monospace; font-size:0.85rem;'>
        {"REJECT — Significant difference found" if p2<0.05 else "FAIL TO REJECT — No significant difference"}
    </div>""", unsafe_allow_html=True)

    fig = px.box(df_sal.assign(Type=df_sal["Job Is Remote"].map({True:"Remote",False:"Onsite"})),
                 x="Type", y="Avg Salary", color="Type",
                 color_discrete_sequence=["#f59e0b","#6366f1"], title=f"H2 (p={p2:.4f})")
    fig.update_layout(**T, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-header'>Test Results Summary Table</div>", unsafe_allow_html=True)
    results_df = pd.DataFrame({
        "Hypothesis": ["H1: DS vs DA","H2: Remote vs Onsite"],
        "T-Statistic": [round(t1,3), round(t2,3)],
        "P-Value (t-test)": [round(p1,4), round(p2,4)],
        "P-Value (Mann-Whitney)": [round(pm1,4), round(pm2,4)],
        "Conclusion": ["Significant" if p1<0.05 else "Not Significant",
                       "Significant" if p2<0.05 else "Not Significant"]
    })
    st.dataframe(results_df, use_container_width=True, hide_index=True)
    st.download_button("Download Test Results", results_df.to_csv(index=False).encode(),
                       "hypothesis_results.csv","text/csv")

    st.markdown("<div class='section-header'>All Roles Salary Statistics Table</div>",
                unsafe_allow_html=True)
    all_stats = df_sal.groupby("Role")["Avg Salary"].agg(
        ["mean","median","min","max","std","count"]).round(0).reset_index()
    all_stats.columns = ["Role","Mean","Median","Min","Max","Std Dev","Sample Size"]
    all_stats_display = all_stats.copy()
    for c in ["Mean","Median","Min","Max","Std Dev"]:
        all_stats_display[c] = all_stats_display[c].apply(lambda x: f"${x:,.0f}")
    st.dataframe(all_stats_display, use_container_width=True, hide_index=True)
    st.download_button("Download Salary Stats", all_stats.to_csv(index=False).encode(),
                       "salary_statistics.csv","text/csv")

    st.markdown("<div class='section-header'>Interpretation & Recommendations</div>",
                unsafe_allow_html=True)
    rec_card("H1 Takeaway",
             f"With p={p1:.4f}, strong statistical evidence Data Scientists earn more. "
             "Upskilling from DA → DS can dramatically increase earning potential.")
    rec_card("H2 Takeaway",
             f"With p={p2:.4f}, remote vs onsite salary difference is not significant. "
             "Choose between remote/onsite based on role quality, not salary.")
    rec_card("Career Strategy",
             "Highest ROI move: <strong>Data Analyst → Data Scientist</strong>. "
             "Salary gap is statistically proven and skill overlap is high (Python, SQL, Statistics).")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — SALARY PREDICTOR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Salary Predictor":
    st.markdown("<h2 style='color:#818cf8; font-family:Space Mono,monospace;'>Salary Predictor</h2>",
                unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b;'>Gradient Boosting — MAE $34,885 | R² 0.429 | 929 real listings</p>",
                unsafe_allow_html=True)

    if model is None:
        st.error("Model not found. Ensure models/salary_model.pkl exists.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            role     = st.selectbox("Role", sorted(df["Role"].unique()))
            city     = st.selectbox("City", sorted(df[df["Job City"]!="Unknown"]["Job City"].unique()))
            state    = st.selectbox("State", sorted(df[df["Job State"]!="Unknown"]["Job State"].unique()))
        with c2:
            emp_type  = st.selectbox("Employment Type",
                sorted(df[df["Job Employment Type"]!="Unknown"]["Job Employment Type"].unique()))
            is_remote = st.toggle("Remote Position", value=False)
            st.markdown("<br>", unsafe_allow_html=True)
            predict_btn = st.button("Predict Salary", type="primary", use_container_width=True)

        if predict_btn:
            log_filter("Salary Predictor","role_selected", role)
            log_filter("Salary Predictor","city_selected", city)
            log_filter("Salary Predictor","state_selected", state)
            try:
                input_df = pd.DataFrame([{"Role":role,"Job City":city,"Job State":state,
                                           "Job Is Remote":is_remote,"Job Employment Type":emp_type}])
                for col in ["Role","Job City","Job State","Job Employment Type"]:
                    val = input_df[col][0]
                    if val in encoders[col].classes_:
                        input_df[col] = encoders[col].transform([val])[0]
                    else:
                        most_common = df[col].mode()[0]
                        input_df[col] = encoders[col].transform([most_common])[0] \
                                        if most_common in encoders[col].classes_ else 0

                prediction = max(0, model.predict(input_df)[0])
                market     = df[df["Role"]==role]["Avg Salary"]
                market_avg = market[market>0].mean()
                diff_pct   = (prediction-market_avg)/market_avg*100 if market_avg>0 else 0

                log_prediction(role, city, state, emp_type, is_remote, prediction, market_avg)
                log_activity("Salary Predictor","Prediction Made",
                             f"{role}|{city}|{state}|${prediction:,.0f}")

                st.markdown(f"""
                <div class='prediction-result'>
                    <div style='color:#64748b; font-size:0.85rem; text-transform:uppercase;
                                letter-spacing:0.1em; margin-bottom:8px;'>Estimated Annual Salary</div>
                    <div class='predicted-salary'>${prediction:,.0f}</div>
                    <div style='color:#64748b; font-size:0.85rem; margin-top:12px;'>
                        {role} &nbsp;·&nbsp; {city}, {state} &nbsp;·&nbsp;
                        {'Remote' if is_remote else 'Onsite'}
                    </div>
                </div>""", unsafe_allow_html=True)

                badge = "#34d399" if diff_pct>=0 else "#ef4444"
                st.markdown(f"""<div class='insight-box' style='margin-top:12px;'>
                    Market avg for <strong>{role}</strong>: <strong>${market_avg:,.0f}</strong>
                    — prediction is
                    <strong style='color:{badge};'>{"+" if diff_pct>=0 else ""}{diff_pct:.1f}%</strong>
                    vs market
                </div>""", unsafe_allow_html=True)

                role_skills  = Counter(s for d in df[df["Role"]==role]["Job Description"].dropna()
                                       for s in SKILLS if s in clean(d))
                top_r_skills = [s.title() for s,_ in role_skills.most_common(5)]
                top_cities   = df[df["Role"]==role]["Job City"].value_counts().head(3).index.tolist()

                st.markdown("<div class='section-header'>Personalized Recommendations</div>",
                            unsafe_allow_html=True)
                rec_card("Top Skills to Master",
                         f"For <strong>{role}</strong>: <strong>{', '.join(top_r_skills)}</strong> — "
                         "these appear most frequently in job descriptions for your chosen role.")
                rec_card("Best Cities for This Role",
                         f"Top cities: <strong>{', '.join(top_cities)}</strong>. "
                         f"{'You are already in a top city!' if city in top_cities else f'Consider applying in {top_cities[0]} for maximum exposure.'}")
                rec_card("Salary Negotiation Strategy",
                         f"Target <strong>${prediction*1.1:,.0f} – ${prediction*1.2:,.0f}</strong> "
                         "in negotiations (10–20% above prediction is industry standard).")
                rec_card("Remote Market Reality",
                         f"Only <strong>2.6%</strong> of {role} jobs are remote. "
                         f"{'Apply broadly to onsite roles — remote openings are rare.' if not is_remote else 'Remote is competitive — strengthen your GitHub and portfolio.'}")

                st.markdown("<div class='section-header'>Role Salary Comparison Table</div>",
                            unsafe_allow_html=True)
                role_stats = df[df["Avg Salary"]>0].groupby("Role")["Avg Salary"].agg(
                    ["mean","median","min","max","count"]).round(0).reset_index()
                role_stats.columns = ["Role","Avg","Median","Min","Max","Jobs with Salary"]
                role_stats_dl = role_stats.copy()
                for c in ["Avg","Median","Min","Max"]:
                    role_stats[c] = role_stats[c].apply(lambda x: f"${x:,.0f}")
                st.dataframe(role_stats, use_container_width=True, hide_index=True)
                st.download_button("Download Role Comparison",
                                   role_stats_dl.to_csv(index=False).encode(),
                                   "role_comparison.csv","text/csv")

                st.markdown("<div class='section-header'>Salary Distribution — Your Role vs All</div>",
                            unsafe_allow_html=True)
                fig = px.box(df[df["Avg Salary"]>0], x="Role", y="Avg Salary", color="Role",
                             color_discrete_sequence=px.colors.qualitative.Bold,
                             title=f"{role} vs All Roles")
                fig.update_layout(**T, showlegend=False, xaxis_tickangle=-15)
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("<div class='section-header'>Top Companies Hiring for This Role</div>",
                            unsafe_allow_html=True)
                role_cos = df[df["Role"]==role].groupby("Employer Name").size()\
                           .reset_index(name="Openings").nlargest(10,"Openings")
                fig = px.bar(role_cos, x="Openings", y="Employer Name", orientation="h",
                             color="Openings", color_continuous_scale="viridis",
                             title=f"Top Companies Hiring {role}")
                fig.update_layout(**T, showlegend=False,
                                  yaxis=dict(categoryorder="total ascending"))
                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Prediction error: {e}")

        st.markdown("<div class='section-header'>Model Performance</div>", unsafe_allow_html=True)
        for col,(label,val) in zip(st.columns(4), [
            ("Algorithm","Gradient Boosting"),("MAE","$34,885"),("RMSE","$48,953"),("R²","0.429")
        ]):
            col.markdown(f"""<div class='metric-card'>
                <div class='metric-value' style='font-size:1.3rem;'>{val}</div>
                <div class='metric-label'>{label}</div></div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — RAW DATA EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Raw Data Explorer":
    st.markdown("<h2 style='color:#818cf8; font-family:Space Mono,monospace;'>Raw Data Explorer</h2>",
                unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    role_f  = c1.multiselect("Role", df["Role"].unique(), default=df["Role"].unique())
    state_f = c2.multiselect("State", sorted(df[df["Job State"]!="Unknown"]["Job State"].unique()))
    sal_f   = c3.slider("Min Salary ($)", 0, int(df["Avg Salary"].max()), 0, step=5000)

    log_filter("Raw Data","roles_selected", role_f)
    log_filter("Raw Data","min_salary", sal_f)

    fdf = df[df["Role"].isin(role_f) & (df["Avg Salary"]>=sal_f)]
    if state_f: fdf = fdf[fdf["Job State"].isin(state_f)]

    st.markdown(f"<div class='stat-pill'>{len(fdf)} records</div>", unsafe_allow_html=True)
    st.dataframe(fdf.drop(columns=["Job Description"]).reset_index(drop=True),
                 use_container_width=True, height=400)

    c1, c2 = st.columns(2)
    with c1:
        st.download_button("Download Filtered Data",
                           fdf.to_csv(index=False).encode(),
                           "filtered_jobs.csv","text/csv", use_container_width=True)
    with c2:
        st.download_button("Download Full Dataset",
                           df.to_csv(index=False).encode(),
                           "all_jobs.csv","text/csv", use_container_width=True)

    st.markdown("<div class='section-header'>Summary Statistics</div>", unsafe_allow_html=True)
    st.dataframe(fdf[["Avg Salary"]].describe().round(2), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(fdf[fdf["Avg Salary"]>0], x="Avg Salary", color="Role",
                           nbins=30, title="Salary Distribution")
        fig.update_layout(**T)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        rc = fdf["Role"].value_counts().reset_index()
        rc.columns = ["Role","count"]
        fig = px.bar(rc, x="Role", y="count", color="count",
                     color_continuous_scale="viridis", title="Jobs by Role")
        fig.update_layout(**T, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 7 — USER ACTIVITY & EXTRACTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "User Activity & Extracts":
    st.markdown("<h2 style='color:#818cf8; font-family:Space Mono,monospace;'>User Activity & Extracts</h2>",
                unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b;'>All user interactions automatically saved to CSV — extract any dataset below</p>",
                unsafe_allow_html=True)

    activity_df    = read_csv_safe(ACTIVITY_CSV)
    predictions_df = read_csv_safe(PREDICTIONS_CSV)
    filters_df     = read_csv_safe(FILTERS_CSV)

    # ── Metrics ──
    for col,(v,l) in zip(st.columns(3), [
        (len(activity_df),"Total Page Visits"),
        (len(predictions_df),"Salary Predictions Made"),
        (len(filters_df),"Filter Selections"),
    ]):
        col.markdown(f"""<div class='metric-card'>
            <div class='metric-value'>{v}</div>
            <div class='metric-label'>{l}</div></div>""", unsafe_allow_html=True)

    # ── Activity Log ──
    st.markdown("<div class='section-header'>Activity Log</div>", unsafe_allow_html=True)
    if len(activity_df) > 0:
        st.dataframe(activity_df.sort_values("timestamp", ascending=False).head(50),
                     use_container_width=True, hide_index=True)
        st.download_button("Download Activity Log",
                           activity_df.to_csv(index=False).encode(),
                           "activity_log.csv","text/csv")

        c1, c2 = st.columns(2)
        with c1:
            pv = activity_df[activity_df["action"]=="Page Visit"]["page"].value_counts().reset_index()
            pv.columns = ["Page","Visits"]
            fig = px.bar(pv, x="Visits", y="Page", orientation="h",
                         color="Visits", color_continuous_scale="viridis", title="Page Visit Counts")
            fig.update_layout(**T, showlegend=False, yaxis=dict(categoryorder="total ascending"))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            actions = activity_df["action"].value_counts().reset_index()
            actions.columns = ["Action","Count"]
            fig = px.pie(actions, names="Action", values="Count", hole=0.5,
                         title="Action Types", color_discrete_sequence=px.colors.qualitative.Bold)
            fig.update_layout(**T)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No activity recorded yet.")

    # ── Salary Predictions ──
    st.markdown("<div class='section-header'>All Salary Predictions</div>", unsafe_allow_html=True)
    if len(predictions_df) > 0:
        st.dataframe(predictions_df.sort_values("timestamp", ascending=False),
                     use_container_width=True, hide_index=True)
        st.download_button("Download Predictions Data",
                           predictions_df.to_csv(index=False).encode(),
                           "salary_predictions.csv","text/csv")

        c1, c2 = st.columns(2)
        with c1:
            fig = px.histogram(predictions_df, x="predicted_salary", color="role",
                               nbins=20, title="Predicted Salary Distribution")
            fig.update_layout(**T)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            rp = predictions_df.groupby("role")["predicted_salary"].mean().reset_index()
            fig = px.bar(rp, x="role", y="predicted_salary", color="predicted_salary",
                         color_continuous_scale="viridis", title="Avg Predicted Salary by Role")
            fig.update_layout(**T, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No predictions made yet.")

    # ── Filter Selections ──
    st.markdown("<div class='section-header'>Filter Selections</div>", unsafe_allow_html=True)
    if len(filters_df) > 0:
        st.dataframe(filters_df.sort_values("timestamp", ascending=False).head(50),
                     use_container_width=True, hide_index=True)
        st.download_button("Download Filter Data",
                           filters_df.to_csv(index=False).encode(),
                           "filter_selections.csv","text/csv")
    else:
        st.info("No filter interactions recorded yet.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 8 — ABOUT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "About This Project":
    st.markdown("""
    <div class='hero-container'>
        <div class='hero-title'>About This Project</div>
        <div class='hero-subtitle'>End-to-End Job Market Intelligence Platform — Built from scratch</div>
        <div class='author-badge'>&#9632; J. CHARAN REDDY &nbsp;|&nbsp; Data Analyst & Data Scientist Portfolio</div>
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='section-header'>Project Methodology</div>", unsafe_allow_html=True)
        for i,(title,desc) in enumerate([
            ("Data Collection","929 live jobs via JSearch REST API across 6 roles"),
            ("Data Engineering","Pandas method chaining + SQLAlchemy → MySQL"),
            ("SQL Analysis","13 advanced queries — window functions & CTEs"),
            ("EDA","8+ interactive Plotly visualizations"),
            ("NLP Pipeline","spaCy + NLTK VADER — skills & sentiment"),
            ("Statistical Testing","T-test & Mann-Whitney at α=0.05"),
            ("Machine Learning","Gradient Boosting tuned via GridSearchCV — R²=0.429"),
            ("Deployment","Streamlit Cloud — public URL with user tracking"),
        ]):
            st.markdown(f"""
            <div style='display:flex; gap:16px; padding:12px 0; border-bottom:1px solid #1e1e2e;'>
                <div style='font-family:Space Mono,monospace; color:#6366f1; font-size:0.8rem;
                            min-width:24px;'>0{i+1}</div>
                <div>
                    <div style='color:#e2e8f0; font-weight:500; font-size:0.9rem;'>{title}</div>
                    <div style='color:#64748b; font-size:0.82rem; margin-top:2px;'>{desc}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='section-header'>Tech Stack</div>", unsafe_allow_html=True)
        for category, tools in {
            "Data Collection": ["Python","JSearch API","RapidAPI"],
            "Storage & SQL": ["MySQL","SQLAlchemy","CSV Tracking"],
            "Processing": ["Pandas","NumPy","Pathlib"],
            "NLP": ["spaCy","NLTK VADER","regex"],
            "Statistics": ["SciPy","Mann-Whitney","T-test"],
            "Machine Learning": ["Scikit-learn","XGBoost","GridSearchCV"],
            "Visualization": ["Plotly","Matplotlib","Seaborn"],
            "Deployment": ["Streamlit","Streamlit Cloud","GitHub"],
        }.items():
            st.markdown(f"""
            <div style='padding:10px 0; border-bottom:1px solid #1e1e2e;'>
                <div style='color:#64748b; font-size:0.75rem; text-transform:uppercase;
                            letter-spacing:0.1em; margin-bottom:6px;'>{category}</div>
                <div>{''.join(f"<span class='stat-pill'>{t}</span>" for t in tools)}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Key Findings</div>", unsafe_allow_html=True)
    for f in [
        "ML Engineers command the highest salaries — max $675K observed",
        "Only 2.6% of data jobs are remote in 2026",
        "Data Scientists earn significantly more than Analysts (p=0.0000)",
        "Role & City are the top salary predictors per feature importance",
        "Machine Learning is the #1 bigram in 929 job descriptions",
        "Washington DC dominates hiring with 83 listings",
        "Capital One is the most active recruiter — 28 postings",
        "Job descriptions are overwhelmingly positive in sentiment (>0.9)",
    ]:
        st.markdown(f"""<div style='padding:8px 0 8px 16px; border-left:2px solid #6366f1;
            margin:6px 0; color:#94a3b8; font-size:0.88rem;'>{f}</div>""",
            unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Resume Bullets</div>", unsafe_allow_html=True)
    for b in [
        "Built a Job Market Intelligence Platform fetching 929+ live listings via REST API",
        "Applied NLP (spaCy, NLTK) to extract in-demand skills from 929 job descriptions",
        "Conducted hypothesis testing (t-test, Mann-Whitney) proving DS earns more than DA",
        "Trained Gradient Boosting salary predictor — R²=0.429, MAE=$34,885",
        "Deployed full-stack data product on Streamlit Cloud with automatic user tracking",
    ]:
        st.markdown(f"""<div class='recommendation-card' style='margin:6px 0;'>
            <div style='color:#94a3b8; font-size:0.88rem;'>&#8226; &nbsp;{b}</div>
        </div>""", unsafe_allow_html=True)
