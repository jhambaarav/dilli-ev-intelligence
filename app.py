"""
DEA Market Intelligence Agent — Streamlit App
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import ollama
import json
import warnings
warnings.filterwarnings('ignore')

# ── Config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="DEA Market Intelligence Agent",
    page_icon="🛺",
    layout="centered"
)

MONTH_ORDER = ['JAN','FEB','MAR','APR','MAY','JUN',
               'JUL','AUG','SEP','OCT','NOV','DEC']
MODEL = 'llama3.1'

# ── Load Data (cached) ────────────────────────────────────────
@st.cache_data
def load_data():
    # Update this path to your local path
    df = pd.read_csv('/Users/admin/Desktop/TO DO /Project dea/data/market_clean.csv')
    df['Month'] = pd.Categorical(df['Month'], categories=MONTH_ORDER, ordered=True)
    return df

df = load_data()

# ── Tool Functions ────────────────────────────────────────────
def get_market_share(maker_group=None) -> dict:
    # Cast to string safely
    if maker_group is not None:
        maker_group = str(maker_group).strip() if maker_group else None
    total = df['Registerations'].sum()
    share = (df.groupby('Maker_Group')['Registerations']
               .sum().sort_values(ascending=False).reset_index())
    share['market_share_pct'] = (share['Registerations'] / total * 100).round(2)
    if maker_group:
        row = share[share['Maker_Group'].str.lower() == maker_group.lower()]
        if len(row) == 0:
            return {"error": f"'{maker_group}' not found"}
        return row.to_dict('records')[0]
    return share.to_dict('records')


def get_state_opportunities(min_market_size=0, max_dea_share=100) -> dict:
    # Cast to correct types — llama3.1 sometimes passes strings
    min_market_size = int(float(min_market_size)) if min_market_size else 0
    max_dea_share   = float(max_dea_share) if max_dea_share else 100.0
    state_total = df.groupby('State')['Registerations'].sum()
    dea_state   = (df[df['Maker_Group']=='Dilli Electric Auto']
                   .groupby('State')['Registerations'].sum())
    dea_share   = (dea_state / state_total * 100).round(2)
    result = pd.DataFrame({
        'state'        : state_total.index,
        'market_size'  : state_total.values.astype(int),
        'dea_units'    : [int(dea_state.get(s, 0)) for s in state_total.index],
        'dea_share_pct': [float(dea_share.get(s, 0)) for s in state_total.index]
    })
    result = result[
        (result['market_size'] >= min_market_size) &
        (result['dea_share_pct'] <= max_dea_share)
    ].sort_values('market_size', ascending=False)
    return result.to_dict('records')


def compare_competitors(makers=None) -> dict:
    # Cast makers list elements to string safely
    if makers:
        makers = [str(m) for m in makers]
        data = df[df['Maker'].isin(makers)]
    else:
        top  = df.groupby('Maker')['Registerations'].sum().sort_values(ascending=False).head(10)
        data = df[df['Maker'].isin(top.index)]
    result = (data.groupby('Maker')['Registerations']
                  .sum().sort_values(ascending=False).reset_index())
    total  = df['Registerations'].sum()
    result['market_share_pct'] = (result['Registerations'] / total * 100).round(2)
    return result.to_dict('records')


def get_monthly_trend(maker_group='Dilli Electric Auto') -> dict:
    # Cast to string safely
    maker_group = str(maker_group).strip() if maker_group else 'Dilli Electric Auto'
    data = df[df['Maker_Group'] == maker_group]
    if len(data) == 0:
        return {"error": f"No data for '{maker_group}'"}
    monthly = data.groupby('Month')['Registerations'].sum().reindex(MONTH_ORDER)
    mom     = monthly.pct_change().mul(100).round(1)
    q4      = int(monthly[['OCT','NOV','DEC']].sum())
    q1      = int(monthly[['JAN','FEB','MAR']].sum())
    return {
        "maker_group"   : maker_group,
        "monthly_units" : {str(k): int(v) for k, v in monthly.items()},
        "mom_growth_pct": {str(k): float(v) for k, v in mom.dropna().items()},
        "best_month"    : str(monthly.idxmax()),
        "worst_month"   : str(monthly.idxmin()),
        "q4_units": q4, "q1_units": q1,
        "q4_vs_q1_ratio": round(q4/q1, 2) if q1 > 0 else None,
        "total_annual"  : int(monthly.sum())
    }


def get_dea_state_performance(state=None) -> dict:
    # Cast to string safely
    if state is not None:
        state = str(state).strip() if state else None
    dea       = df[df['Maker_Group'] == 'Dilli Electric Auto']
    state_mkt = df.groupby('State')['Registerations'].sum()
    if state:
        dea_s   = dea[dea['State'] == state]
        if len(dea_s) == 0:
            return {"error": f"No DEA data for '{state}'"}
        monthly = dea_s.groupby('Month')['Registerations'].sum().reindex(MONTH_ORDER)
        mkt_sz  = int(state_mkt.get(state, 0))
        dea_tot = int(monthly.sum())
        return {
            "state": state, "dea_total": dea_tot, "market_size": mkt_sz,
            "dea_share_pct": round(dea_tot/mkt_sz*100, 2) if mkt_sz > 0 else 0,
            "best_month": str(monthly.idxmax()),
            "monthly_units": {str(k): int(v) for k, v in monthly.items()}
        }
    result = []
    for s in dea['State'].unique():
        dea_s = dea[dea['State']==s]['Registerations'].sum()
        mkt_s = state_mkt.get(s, 0)
        result.append({
            "state": s, "dea_units": int(dea_s), "market_size": int(mkt_s),
            "dea_share_pct": round(dea_s/mkt_s*100, 2) if mkt_s > 0 else 0
        })
    return sorted(result, key=lambda x: x['dea_units'], reverse=True)


TOOL_MAP = {
    "get_market_share"          : get_market_share,
    "get_state_opportunities"   : get_state_opportunities,
    "compare_competitors"       : compare_competitors,
    "get_monthly_trend"         : get_monthly_trend,
    "get_dea_state_performance" : get_dea_state_performance,
}

TOOLS = [
    {"type": "function", "function": {
        "name": "get_market_share",
        "description": "Get market share for EV 3-wheeler brand groups. Use for questions about who leads the market or DEA's overall share.",
        "parameters": {"type": "object", "properties": {
            "maker_group": {"type": "string", "description": "Optional brand group name."}
        }}
    }},
    {"type": "function", "function": {
        "name": "get_state_opportunities",
        "description": "Find states with large EV market but low DEA share — expansion opportunities.",
        "parameters": {"type": "object", "properties": {
            "min_market_size": {"type": "integer", "description": "Min state market size. Default 0."},
            "max_dea_share"  : {"type": "number",  "description": "Max DEA share %. Default 100."}
        }}
    }},
    {"type": "function", "function": {
        "name": "compare_competitors",
        "description": "Compare top EV competitors by sales volume. Use for rivalry, threat, or competitive questions.",
        "parameters": {"type": "object", "properties": {
            "makers": {"type": "array", "items": {"type": "string"}, "description": "Optional maker names. Empty = top 10."}
        }}
    }},
    {"type": "function", "function": {
        "name": "get_monthly_trend",
        "description": "Get monthly trend and MoM growth for a brand. Use for seasonality or growth questions.",
        "parameters": {"type": "object", "properties": {
            "maker_group": {"type": "string", "description": "Brand group. Default: 'Dilli Electric Auto'"}
        }}
    }},
    {"type": "function", "function": {
        "name": "get_dea_state_performance",
        "description": "Get DEA registrations broken down by state. Use for state-level performance questions.",
        "parameters": {"type": "object", "properties": {
            "state": {"type": "string", "description": "Optional state name e.g. 'UP', 'Bihar'. Empty = all states."}
        }}
    }}
]

SYSTEM_PROMPT = """You are a senior market intelligence analyst for Dilli Electric Auto (DEA),
an e-rickshaw and loader manufacturer in India.
You have tools that query real 2025 VAHAN registration data.
Always use a tool to get real data before answering. Never guess numbers.
Give clear, direct business answers using actual numbers from the data."""


def run_agent(question: str):
    """Generator that yields (type, content) tuples for streaming UI updates"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": question}
    ]

    while True:
        response = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
        msg = response.message

        if msg.tool_calls:
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": msg.tool_calls
            })
            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                args = dict(tool_call.function.arguments) if tool_call.function.arguments else {}
                yield ("tool", f"🔧 Querying: `{name}({json.dumps(args)})`")
                result = TOOL_MAP[name](**args) if name in TOOL_MAP else {"error": "unknown tool"}
                messages.append({"role": "tool", "content": json.dumps(result)})
        else:
            yield ("answer", msg.content)
            break


# ── UI ────────────────────────────────────────────────────────
st.markdown("""
<h1 style='text-align:center'>🛺 DEA Market Intelligence Agent</h1>
<p style='text-align:center; color:gray'>Ask any business question about the EV 3-wheeler market in India (2025 VAHAN Data)</p>
""", unsafe_allow_html=True)

st.divider()

# Stats row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Market",  "8,69,751")
col2.metric("DEA Units",     "20,065")
col3.metric("DEA Share",     "2.31%")
col4.metric("States",        "11")

st.divider()

# Suggested questions
st.markdown("**💡 Try asking:**")
suggestions = [
    "Which state should DEA expand to next?",
    "Who is DEA's biggest competitive threat?",
    "When should DEA push maximum inventory?",
    "Compare DEA's performance in UP vs Bihar",
]
cols = st.columns(2)
for i, s in enumerate(suggestions):
    if cols[i % 2].button(s, use_container_width=True):
        st.session_state['question'] = s

st.divider()

# Input
question = st.text_input(
    "Ask a business question:",
    value=st.session_state.get('question', ''),
    placeholder="e.g. What is DEA's market share compared to YC Electric?",
    key="input"
)

if st.button("Ask Agent ▶", type="primary", use_container_width=True):
    if question.strip():
        st.markdown("---")
        with st.spinner("Agent thinking..."):
            tool_container = st.container()
            answer_container = st.container()

            tools_used = []
            final_answer = ""

            for event_type, content in run_agent(question):
                if event_type == "tool":
                    tools_used.append(content)
                    with tool_container:
                        for t in tools_used:
                            st.info(t)
                elif event_type == "answer":
                    final_answer = content

            with answer_container:
                st.markdown("### 📊 Answer")
                st.markdown(final_answer)
    else:
        st.warning("Please enter a question.")

# Footer
st.divider()
st.caption("Built by Aarav | Data: VAHAN 2025 | Model: Llama 3.1 (Ollama) | Project: Dilli Electric Auto")
