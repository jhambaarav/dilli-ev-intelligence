# 🛺 Dilli Electric Auto — EV Market Intelligence Tool

This project presents a full-scale market intelligence system for **Dilli Electric Auto (DEA)**, an e-rickshaw and electric loader manufacturer operating across North and East India. Built using real 2025 VAHAN (Government of India) registration data across 11 states and 611 makers, it combines data cleaning, SQL analysis, machine learning, and a Gen AI agent to map the competitive EV 3-wheeler landscape and surface actionable business insights.

## 🧠 Objective

- Analyze DEA's competitive position across 11 Indian states using real government registration data
- Identify high-opportunity markets where DEA is under-penetrated relative to market size
- Predict monthly EV demand using a Random Forest model to support inventory and dealer planning
- Build an AI agent that autonomously answers business questions by querying live data

## 📈 Methodology

1. **Data Collection & Cleaning**
   - Downloaded EV 3-wheeler registration data from VAHAN dashboard (2025) for 11 states
   - Unpivoted and transformed raw state-wise Excel files using Power Query into a unified long-format CSV
   - Applied Python (Pandas) cleaning: column type fixes, ordered month categories, feature engineering (Month_Num, Is_DEA flag, Annual_Total)

2. **SQL Analysis**
   - Loaded clean data into SQLite and wrote 10 business queries covering market share, competitor comparison, MoM growth, seasonal demand, Pareto analysis, and state opportunity flagging
   - Techniques used: CTEs, window functions (LAG, RANK, SUM OVER, AVG with ROWS BETWEEN), CASE WHEN, NULLIF, COALESCE, LEFT JOIN

3. **Exploratory Data Analysis**
   - Built 6 visualizations: market share pie chart, top 10 makers bar chart, DEA vs Bajaj vs YC monthly trend, state-wise opportunity chart, DEA state × month heatmap, Pareto 80/20 chart
   - Key finding: DEA holds 2.31% national market share (20,065 units); UP is strongest state; December is peak month; only 55 makers drive 80% of the 869,751-unit market

4. **Machine Learning — Random Forest Demand Prediction**
   - Built a Random Forest Regressor to predict monthly EV registrations by maker, state, and month
   - Features: state encoding, maker group, month number, Q4 flag, annual total, state market share
   - Model performance: R² = 0.98, MAE = 3.4 units — explains 98.3% of variance in registrations
   - Used to predict DEA's expected demand by state for inventory and dealer planning

5. **Gen AI Agent — Agentic Tool Use**
   - Built an AI agent using Ollama (Llama 3.1) with 5 tools that query live data autonomously
   - Agent decides which tool to call based on the question, executes it on the real dataset, and returns a written business answer
   - Deployed as an interactive Streamlit web app with suggested questions and real-time tool call visibility

---

## 📂 Files Included

| File | Description |
|------|-------------|
| `01_data_cleaning.py` | Loads raw CSV, cleans types, engineers features, saves market_clean.csv |
| `02_analysis_queries.sql` | 10 SQL business queries with window functions and CTEs |
| `03_eda.ipynb` | Exploratory Data Analysis with 6 visualizations |
| `04_sql_analysis.ipynb` | All 10 SQL queries executed with results embedded |
| `05_ml_model.ipynb` | Random Forest demand prediction model with evaluation and scenario predictions |
| `06_genai_agent.ipynb` | Agentic AI with tool use — answers business questions from live data |
| `app.py` | Streamlit web app — interactive chat interface for the AI agent |
| `data/market_master.csv` | Raw VAHAN data (11 states, 2025) |
| `data/market_clean.csv` | Cleaned and feature-engineered dataset |

## 🧮 Key Findings

| Metric | Value |
|--------|-------|
| Total Market Registrations (2025) | 8,69,751 |
| DEA Total Registrations | 20,065 |
| DEA National Market Share | 2.31% |
| DEA Rank (individual makers) | 7th nationally |
| DEA Best State | Uttar Pradesh |
| DEA Peak Month | December |
| Biggest Competitor | Bajaj Auto (2,24,736 units — 11.2x DEA) |
| Closest Direct Rival | YC Electric (36,871 units) |
| States Covered | 11 |
| Unique Makers in Dataset | 611 |

## 🛠 Tools & Skills Used

- **Languages:** Python, SQL
- **Libraries:** Pandas, NumPy, Matplotlib, Seaborn, Scikit-learn, Streamlit, Ollama
- **ML Model:** Random Forest Regressor (R² = 0.98)
- **AI / Gen AI:** Ollama (Llama 3.1), Tool Use, Agentic Loop
- **Database:** SQLite (in-memory, via Python)
- **Data Source:** VAHAN Dashboard — parivahan.gov.in
- **Other:** Power Query (Excel unpivot), Jupyter Notebook, GitHub

## 💡 Business Insights & Recommendations

- **Bihar and West Bengal** are HIGH opportunity states — large markets (50,000+ units) where DEA holds under 3% share
- **Q4 (Oct–Dec) drives disproportionate demand** — DEA should ensure maximum inventory by September every year
- **YC Electric is DEA's closest rival** — outsells DEA by 1.84x in overlapping geographies and states
- **Only 55 out of 611 makers drive 80% of the market** — DEA is already in this top group; the challenge is moving up within it
- **UP distribution should be protected** — it is DEA's highest-volume state and anchor for expansion strategy

## ℹ️ About

**Data Source:** All registration data sourced from VAHAN Dashboard (Government of India) — [vahan.parivahan.gov.in](https://vahan.parivahan.gov.in/vahan4dashboard)

**Context:** Dilli Electric Auto is a real business. This project was built to combine portfolio-grade data analysis with genuine business utility — the AI agent is deployed internally for market intelligence queries.
