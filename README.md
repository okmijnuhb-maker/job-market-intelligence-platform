# Job Market Intelligence Platform

I built this project because I wanted to understand what the data job market actually looks like in 2026 — not from a Kaggle dataset that's 2 years old, but from real live job listings pulled directly from the internet.

The end result is a full web app where you can explore the market, check which skills are in demand, test salary hypotheses, and predict what you'd earn based on your role and location.

---

## What This Project Does

It collects live job data from the JSearch API, stores it in MySQL, runs NLP on the job descriptions, does statistical testing to validate salary assumptions, trains a machine learning model to predict salaries, and serves everything through an interactive Streamlit dashboard.

Everything from raw API call to deployed web app — no shortcuts.

---

## Live App

[Open the App](https://job-market-charan.streamlit.app/)

---

## What I Found

A few things surprised me when I actually looked at the data:

- **97.4% of data jobs are onsite.** Everyone talks about remote work like it's the norm. It's not — at least not in data roles in 2026.
- **Washington DC has more data job listings than New York or San Francisco.** Government contracts drive a huge amount of hiring.
- **Data Scientists earn significantly more than Data Analysts** — the p-value came out at 0.0000. That's not close.
- **Communication is the most mentioned skill** across all 6 roles. More than Python. More than SQL.
- **Role and City together explain 66% of salary variance** according to the feature importance from the Gradient Boosting model.

---

## Project Structure

```
job-market-intelligence-platform/
│
├── streamlit_app.py          # Main application file
├── requirements.txt          # Python dependencies
│
├── data/
│   ├── cleaned/
│   │   └── jobs_cleaned.csv  # 929 cleaned job listings
│   └── raw/                  # Raw JSON files from API
│
├── models/
│   ├── salary_model.pkl      # Trained Gradient Boosting model
│   └── encoders.pkl          # Label encoders for categorical features
│
├── notebooks/
│   ├── 01_api_fetch.ipynb    # Data collection notebook
│   ├── 02_eda_nlp.ipynb      # EDA and NLP notebook
│   └── 03_statistical_testing.ipynb  # Stats and ML notebook
│
└── SQL Script.sql            # 13 advanced SQL queries
```

---

## How I Built It — Week by Week

**Week 1 — Data Collection & Storage**

I used the JSearch API on RapidAPI to pull 20 pages of results for each of 6 roles. That gave me 982 raw records. After cleaning — removing duplicates, fixing null values, standardizing role names — I ended up with 929 records across 13 columns. All of it went into a MySQL database.

I then wrote 13 SQL queries to explore the data, using window functions like RANK() OVER PARTITION BY, CTEs, NTILE for salary deciles, and CASE WHEN for salary band classification.

**Week 2 — EDA and NLP**

Built 8 Plotly visualizations to understand the market — salary distributions, top companies, city heatmaps, employment type breakdowns. Then ran NLP on all 929 job descriptions using spaCy to extract skills and NLTK VADER for sentiment analysis.

The sentiment finding was interesting — over 86% of job descriptions scored above 0.9 compound sentiment. Employers really do write in an aggressively positive tone.

**Week 3 — Statistics and Machine Learning**

Ran two hypothesis tests at α = 0.05:
- H1: Do Data Scientists earn more than Data Analysts? → Yes, significantly (p = 0.0000)
- H2: Do remote jobs pay more than onsite? → No significant difference (p = 0.3618)

For the ML model, I compared Random Forest, Gradient Boosting, and XGBoost. Gradient Boosting won on both MAE and R². After GridSearchCV tuning across 80 fits, the final model achieved MAE of $34,885 and R² of 0.429 on the test set.

**Week 4 — Streamlit App and Deployment**

Built an 8-page interactive app with filters, charts, a salary predictor, and automatic CSV logging of user activity. Deployed on Streamlit Cloud via GitHub.

---

## App Pages

| Page | What's on it |
|------|-------------|
| Overview | KPI cards, role distribution, key findings, market recommendations |
| Market Analysis | Filters by role/state/work type, charts, market data table |
| NLP — Skill Intelligence | Skill demand charts, heatmap, sentiment analysis, priority table |
| Statistical Testing | H1 and H2 results, salary stats by role, career recommendations |
| Salary Predictor | Input your role and location, get a predicted salary and personalized advice |
| Raw Data Explorer | Browse and download the full dataset |
| User Activity & Extracts | All user interactions logged and downloadable |
| About | Project methodology, tech stack, resume bullets |

---

## Tech Stack

- **Data Collection** — Python, requests, JSearch API (RapidAPI)
- **Storage** — MySQL, SQLAlchemy
- **Processing** — Pandas, NumPy
- **NLP** — spaCy, NLTK VADER
- **Statistics** — SciPy
- **Machine Learning** — Scikit-learn, XGBoost
- **Visualization** — Plotly Express
- **App** — Streamlit
- **Deployment** — Streamlit Cloud, GitHub

---

## How to Run Locally

```bash
git clone https://github.com/okmijnuhb-maker/job-market-intelligence-platform.git
cd job-market-intelligence-platform
pip install -r requirements.txt
streamlit run streamlit_app.py
```

You'll need the `data/jobs_cleaned.csv` and `models/` files which are included in the repo.

---

## Dataset

- **929 job listings** collected via live API in March 2026
- **6 roles:** Data Analyst, Data Scientist, Business Analyst, Data Engineer, ML Engineer, BI Analyst
- **Coverage:** United States
- **Source:** JSearch API (aggregates LinkedIn, Indeed, Glassdoor and others)
- **324 records** have salary data for ML training

---

## Author

**J. Charan Reddy**

Built this as a portfolio project to demonstrate end-to-end data science skills — not just analysis, but engineering, statistics, machine learning, and deployment together in one project.

---

*If you find this useful or have suggestions, feel free to open an issue or connect on LinkedIn.*
