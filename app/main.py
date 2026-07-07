"""
Main Streamlit app — light professional theme, 3-dashboard layout.

Run with:
    streamlit run app/main.py
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv

from app.data.fetch import fetch_company_data, fetch_price_history
from app.utils.ratios import compute_ratios
from app.agents.agents import run_pipeline, run_chat_agent

load_dotenv()  # local development

# Streamlit Cloud secrets override (used when deployed)
import streamlit as _st
try:
    if "GEMINI_API_KEY" in _st.secrets:
        os.environ["GEMINI_API_KEY"] = _st.secrets["GEMINI_API_KEY"]
    if "ALPHAVANTAGE_API_KEY" in _st.secrets:
        os.environ["ALPHAVANTAGE_API_KEY"] = _st.secrets["ALPHAVANTAGE_API_KEY"]
except Exception:
    pass  # secrets not available locally — .env is used instead

fetch_company_data = st.cache_data(ttl=3600)(fetch_company_data)
fetch_price_history = st.cache_data(ttl=3600)(fetch_price_history)

st.set_page_config(
    page_title="FinSight — Fundamental Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #f0f4f8 !important;
    color: #1e293b !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding: 0 2rem 4rem 2rem !important; max-width: 1200px; }

/* NAV */
.navbar {
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 0.9rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 0 -2rem 0 -2rem;
    position: sticky;
    top: 0;
    z-index: 100;
}
.nav-logo { font-family: 'Space Mono', monospace; font-size: 1.1rem; font-weight: 700; color: #1e3a8a; letter-spacing: -0.02em; }
.nav-logo span { color: #2563eb; }
.nav-right { display: flex; align-items: center; gap: 1.5rem; font-size: 0.78rem; color: #64748b; font-weight: 500; }
.nav-right a { color: #64748b; text-decoration: none; }
.nav-right a:hover { color: #2563eb; }
.nav-badge { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; border-radius: 20px; padding: 3px 10px; font-size: 0.7rem; font-weight: 600; font-family: 'Space Mono', monospace; }

/* HERO */
.hero {
    background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 50%, #0ea5e9 100%);
    margin: 0 -2rem;
    padding: 3rem 2rem 2.5rem;
    color: white;
}
.hero-eyebrow { font-size: 0.7rem; letter-spacing: 0.2em; text-transform: uppercase; color: #93c5fd; font-weight: 600; margin-bottom: 0.8rem; }
.hero-title { font-size: 2.4rem; font-weight: 700; line-height: 1.15; margin-bottom: 0.6rem; letter-spacing: -0.025em; }
.hero-title em { color: #fde68a; font-style: normal; }
.hero-sub { font-size: 0.92rem; color: #bfdbfe; max-width: 500px; line-height: 1.7; margin-bottom: 0; font-weight: 400; }

/* INPUT AREA */
.input-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 1.4rem;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 4px 16px rgba(0,0,0,0.04);
    margin-bottom: 1.5rem;
}
.input-label { font-size: 0.7rem; letter-spacing: 0.12em; text-transform: uppercase; color: #2563eb; font-weight: 600; margin-bottom: 0.4rem; font-family: 'Space Mono', monospace; }

[data-testid="stTextInput"] input {
    background: #f8fafc !important;
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 8px !important;
    color: #1e3a8a !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    padding: 0.65rem 1rem !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
[data-testid="stTextInput"] input:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
}
[data-testid="stTextInput"] label { display: none !important; }

[data-testid="stButton"] > button {
    background: #1d4ed8 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.68rem 1.8rem !important;
    width: 100%;
    transition: background 0.15s;
}
[data-testid="stButton"] > button:hover { background: #1e40af !important; }

/* COMPANY HEADER STRIP */
.company-strip {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.cs-left { display: flex; align-items: center; gap: 1rem; }
.cs-avatar {
    width: 46px; height: 46px; border-radius: 10px;
    background: linear-gradient(135deg, #1e3a8a, #2563eb);
    display: flex; align-items: center; justify-content: center;
    font-family: 'Space Mono', monospace; font-size: 0.7rem;
    font-weight: 700; color: white; letter-spacing: 0.05em;
}
.cs-ticker { font-family: 'Space Mono', monospace; font-size: 0.72rem; color: #2563eb; letter-spacing: 0.2em; text-transform: uppercase; font-weight: 700; }
.cs-name { font-size: 1.15rem; font-weight: 700; color: #0f172a; letter-spacing: -0.015em; }
.cs-sector { font-size: 0.78rem; color: #64748b; margin-top: 1px; }
.cs-right { text-align: right; }
.cs-price { font-size: 1.4rem; font-weight: 700; color: #0f172a; font-family: 'Space Mono', monospace; }
.cs-sub { font-size: 0.72rem; color: #64748b; }

/* METRIC CARDS */
.metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 1rem 1.1rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.metric-label { font-size: 0.68rem; letter-spacing: 0.12em; text-transform: uppercase; color: #64748b; font-weight: 600; margin-bottom: 0.4rem; }
.metric-value { font-size: 1.5rem; font-weight: 700; color: #1e3a8a; font-family: 'Space Mono', monospace; letter-spacing: -0.01em; }
.metric-sub { font-size: 0.7rem; color: #94a3b8; margin-top: 0.2rem; }
.metric-card.accent .metric-value { color: #2563eb; }
.metric-card.green .metric-value { color: #059669; }
.metric-card.amber .metric-value { color: #d97706; }

/* SECTION HEADING */
.sec-heading {
    font-size: 0.68rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #2563eb;
    font-weight: 700;
    font-family: 'Space Mono', monospace;
    margin-bottom: 0.8rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #eff6ff;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.sec-heading .dot { width: 6px; height: 6px; border-radius: 50%; background: #2563eb; display: inline-block; }

/* DASHBOARD TABS */
[data-testid="stTabs"] [role="tablist"] {
    background: #ffffff !important;
    border-radius: 10px 10px 0 0 !important;
    border: 1px solid #e2e8f0 !important;
    border-bottom: none !important;
    gap: 0 !important;
    padding: 0 1rem !important;
}
[data-testid="stTabs"] button[role="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    color: #64748b !important;
    padding: 0.75rem 1.2rem !important;
    border-bottom: 3px solid transparent !important;
    background: transparent !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #1d4ed8 !important;
    border-bottom-color: #1d4ed8 !important;
    font-weight: 600 !important;
}
[data-testid="stTabContent"] {
    background: #ffffff !important;
    border-radius: 0 0 10px 10px !important;
    border: 1px solid #e2e8f0 !important;
    border-top: none !important;
    padding: 1.5rem !important;
}

/* CHART PANEL */
.chart-panel {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 1.2rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    margin-bottom: 1rem;
}

/* TABLE */
[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    overflow: hidden !important;
    border: 1px solid #e2e8f0 !important;
}
[data-testid="stDataFrame"] th {
    background: #f8fafc !important;
    color: #374151 !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
}
[data-testid="stDataFrame"] td { font-size: 0.82rem !important; }

/* AI AGENT CARDS */
.agent-step {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #2563eb;
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
}
.agent-step.green { border-left-color: #059669; }
.agent-step.amber { border-left-color: #d97706; }
.agent-label { font-size: 0.67rem; letter-spacing: 0.15em; text-transform: uppercase; font-weight: 700; color: #2563eb; font-family: 'Space Mono', monospace; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.4rem; }
.agent-step.green .agent-label { color: #059669; }
.agent-step.amber .agent-label { color: #d97706; }

/* SYNTHESIS CARD */
.synthesis-card {
    background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%);
    border: 1px solid #bfdbfe;
    border-radius: 10px;
    padding: 1.4rem;
    margin-bottom: 1rem;
}
.synthesis-title { font-size: 0.7rem; letter-spacing: 0.15em; text-transform: uppercase; color: #1d4ed8; font-weight: 700; font-family: 'Space Mono', monospace; margin-bottom: 0.8rem; }

/* PIPELINE FLOW */
.pipeline-flow { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1.2rem; flex-wrap: wrap; }
.pipe-step { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 4px 10px; font-size: 0.68rem; font-weight: 600; color: #1d4ed8; font-family: 'Space Mono', monospace; }
.pipe-arrow { color: #94a3b8; font-size: 0.8rem; }

/* FOOTER */
.footer { text-align: center; padding: 2rem 0 0.5rem; font-size: 0.72rem; color: #94a3b8; }
.footer a { color: #2563eb; text-decoration: none; }
.footer strong { color: #475569; }

/* DISCLAIMER */
.disclaimer { background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 0.6rem 1rem; font-size: 0.75rem; color: #92400e; margin-top: 1rem; }

/* Spinner */
[data-testid="stSpinner"] > div { color: #2563eb !important; }
</style>
""", unsafe_allow_html=True)

# ── NAVBAR ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="navbar">
  <div class="nav-logo">Fin<span>Sight</span></div>
  <div class="nav-right">
    <span>Fundamental Analysis</span>
    <span>·</span>
    <a href="https://github.com/UmrikarS" target="_blank">GitHub</a>
    <span class="nav-badge">Free Preview</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">⬡ AI-Powered Equity Research Platform</div>
  <h1 class="hero-title">Fundamental Analysis,<br><em>Intelligently Automated</em></h1>
  <p class="hero-sub">
    Enter any listed stock ticker to get financial health metrics, ratio trends,
    technical charts, and a 3-step AI analyst report — all in one place.
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── INPUT ─────────────────────────────────────────────────────────────────────
with st.container():
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    st.markdown('<div class="input-label">↳ Enter Stock Ticker Symbol</div>', unsafe_allow_html=True)
    col_inp, col_btn = st.columns([4, 1])
    with col_inp:
        ticker = st.text_input("ticker", value="AAPL", label_visibility="collapsed").strip().upper()
    with col_btn:
        run_button = st.button("Analyse →", use_container_width=True)
    st.markdown("<div style='font-size:0.72rem;color:#94a3b8;margin-top:0.3rem'>Examples: AAPL · MSFT · NVDA · TSLA · AMZN · GOOGL</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── ANALYSIS ──────────────────────────────────────────────────────────────────

# Step 1: fetch data when Analyse is clicked, store in session state
if run_button and ticker:
    with st.spinner(f"Fetching data for {ticker} — this takes ~5 seconds due to API rate pacing…"):
        try:
            company_data  = fetch_company_data(ticker)
            price_history = fetch_price_history(ticker)
            ratios        = compute_ratios(company_data)
            st.session_state["current_ratios"]        = ratios
            st.session_state["current_price_history"] = price_history
            st.session_state["current_company_data"]  = company_data
        except ValueError as e:
            st.error(str(e))
            st.stop()
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            st.stop()

# Step 2: display whenever data exists in session state (covers initial load + chat reruns)
if "current_ratios" in st.session_state:
    ratios        = st.session_state["current_ratios"]
    price_history = st.session_state["current_price_history"]
    company_data  = st.session_state["current_company_data"]

    # Prepare shared data
    ratio_df     = pd.DataFrame(ratios["ratios_by_year"]).T.sort_index()
    sorted_years = sorted(ratios["ratios_by_year"].keys(), reverse=True)
    latest_year  = sorted_years[0] if sorted_years else None
    ly           = ratios["ratios_by_year"].get(latest_year, {})

    latest_close = price_history[-1]["close"] if price_history else None
    pe           = ratios["valuation"]["trailing_pe"]
    market_cap   = ratios["valuation"]["market_cap"]

    def fmt_cap(v):
        if v is None: return "N/A"
        if v >= 1e12: return f"${v/1e12:.2f}T"
        if v >= 1e9:  return f"${v/1e9:.2f}B"
        if v >= 1e6:  return f"${v/1e6:.2f}M"
        return f"${v:,.0f}"

    def fmt_pct(v): return f"{v:.1f}%" if v is not None else "N/A"
    def fmt_ratio(v): return f"{v:.2f}x" if v is not None else "N/A"

    # COMPANY HEADER STRIP
    ticker_abbr = ticker[:3]
    st.markdown(f"""
    <div class="company-strip">
      <div class="cs-left">
        <div class="cs-avatar">{ticker_abbr}</div>
        <div>
          <div class="cs-ticker">{ratios['ticker']}</div>
          <div class="cs-name">{ratios['company_name']}</div>
          <div class="cs-sector">{ratios['sector']}</div>
        </div>
      </div>
      <div class="cs-right">
        <div class="cs-price">{f"${latest_close:,.2f}" if latest_close else "—"}</div>
        <div class="cs-sub">Latest close · Data via Alpha Vantage</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── FOUR DASHBOARD TABS ───────────────────────────────────────────────────
    tab_fund, tab_tech, tab_ai = st.tabs([
        "📊  Fundamental Analysis",
        "📈  Technical Analysis",
        "🤖  AI Agent Analysis",
    ])

    # ── TAB 1: FUNDAMENTAL ───────────────────────────────────────────────────
    with tab_fund:

        # KPI cards row 1
        st.markdown('<div class="sec-heading"><span class="dot"></span>Valuation & Profitability</div>', unsafe_allow_html=True)
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        kpi_cards = [
            (c1, "Trailing P/E", f"{pe:.1f}x" if pe else "N/A", "Price / earnings", "accent"),
            (c2, "Market Cap",   fmt_cap(market_cap),             "Total market value", ""),
            (c3, "Net Margin",   fmt_pct(ly.get("net_margin_pct")), f"FY{latest_year}", "green"),
            (c4, "ROE",          fmt_pct(ly.get("roe_pct")),      f"FY{latest_year}", "green"),
            (c5, "ROA",          fmt_pct(ly.get("roa_pct")),      f"FY{latest_year}", "accent"),
            (c6, "D/E Ratio",    fmt_ratio(ly.get("debt_to_equity")), f"FY{latest_year}", "amber"),
        ]
        for col, label, value, sub, cls in kpi_cards:
            with col:
                st.markdown(f"""
                <div class="metric-card {cls}">
                  <div class="metric-label">{label}</div>
                  <div class="metric-value">{value}</div>
                  <div class="metric-sub">{sub}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        # KPI cards row 2
        st.markdown('<div class="sec-heading"><span class="dot"></span>Liquidity & Cash Flow</div>', unsafe_allow_html=True)
        d1, d2, d3, d4 = st.columns(4)
        kpi2 = [
            (d1, "Current Ratio", fmt_ratio(ly.get("current_ratio")),   f"FY{latest_year}", "green"),
            (d2, "Free Cash Flow", f"${ly.get('free_cash_flow')/1e9:.1f}B" if ly.get("free_cash_flow") else "N/A", f"FY{latest_year}", "green"),
            (d3, "FCF Margin",     fmt_pct(ly.get("fcf_margin_pct")),   f"FY{latest_year}", "accent"),
            (d4, "Revenue Growth", fmt_pct(ratios["trends"].get("revenue_growth_pct")), "YoY", "amber"),
        ]
        for col, label, value, sub, cls in kpi2:
            with col:
                st.markdown(f"""
                <div class="metric-card {cls}">
                  <div class="metric-label">{label}</div>
                  <div class="metric-value">{value}</div>
                  <div class="metric-sub">{sub}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

        # Profitability + Leverage charts
        ch1, ch2 = st.columns(2)
        CHART_STYLE = dict(
            paper_bgcolor="#ffffff", plot_bgcolor="#f8fafc",
            font=dict(family="Inter, sans-serif", color="#64748b", size=11),
            margin=dict(l=10, r=10, t=10, b=20),
            xaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0", tickfont=dict(size=10)),
            yaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0", tickfont=dict(size=10)),
            legend=dict(
                bgcolor="rgba(255,255,255,0.9)",
                orientation="h",
                yanchor="bottom", y=-0.28,
                xanchor="left", x=0,
                font=dict(size=10),
            ),
        )

        with ch1:
            st.markdown('<div class="sec-heading"><span class="dot"></span>Profitability Trends</div>', unsafe_allow_html=True)
            fig = go.Figure()
            if "net_margin_pct" in ratio_df.columns:
                fig.add_trace(go.Bar(x=ratio_df.index, y=ratio_df["net_margin_pct"].astype(float),
                    name="Net Margin %", marker_color="#bfdbfe",
                    hovertemplate="%{y:.1f}%<extra>Net Margin</extra>"))
            if "roe_pct" in ratio_df.columns:
                fig.add_trace(go.Scatter(x=ratio_df.index, y=ratio_df["roe_pct"].astype(float),
                    name="ROE %", line=dict(color="#1d4ed8", width=2.5),
                    mode="lines+markers", marker=dict(size=7, color="#1d4ed8"),
                    hovertemplate="%{y:.1f}%<extra>ROE</extra>", yaxis="y2"))
            fig.update_layout(**CHART_STYLE, height=300,
                yaxis2=dict(overlaying="y", side="right", gridcolor="rgba(0,0,0,0)",
                            tickfont=dict(size=10), linecolor="#e2e8f0"))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        with ch2:
            st.markdown('<div class="sec-heading"><span class="dot"></span>Leverage & Liquidity</div>', unsafe_allow_html=True)
            fig2 = go.Figure()
            if "debt_to_equity" in ratio_df.columns:
                fig2.add_trace(go.Bar(x=ratio_df.index, y=ratio_df["debt_to_equity"].astype(float),
                    name="Debt / Equity", marker_color="#fde68a",
                    hovertemplate="%{y:.2f}x<extra>D/E</extra>"))
            if "current_ratio" in ratio_df.columns:
                fig2.add_trace(go.Scatter(x=ratio_df.index, y=ratio_df["current_ratio"].astype(float),
                    name="Current Ratio", line=dict(color="#059669", width=2.5),
                    mode="lines+markers", marker=dict(size=7, color="#059669"),
                    hovertemplate="%{y:.2f}x<extra>Current Ratio</extra>", yaxis="y2"))
            fig2.update_layout(**CHART_STYLE, height=300,
                yaxis2=dict(overlaying="y", side="right", gridcolor="rgba(0,0,0,0)",
                            tickfont=dict(size=10), linecolor="#e2e8f0"))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        # Revenue & Net Income chart
        st.markdown('<div class="sec-heading"><span class="dot"></span>Revenue & Net Income</div>', unsafe_allow_html=True)
        fig3 = go.Figure()
        if "revenue" in ratio_df.columns:
            rev = ratio_df["revenue"].astype(float) / 1e9
            fig3.add_trace(go.Bar(x=ratio_df.index, y=rev, name="Revenue ($B)",
                marker_color="#c7d2fe", hovertemplate="$%{y:.1f}B<extra>Revenue</extra>"))
        if "net_income" in ratio_df.columns:
            ni = ratio_df["net_income"].astype(float) / 1e9
            fig3.add_trace(go.Bar(x=ratio_df.index, y=ni, name="Net Income ($B)",
                marker_color="#1d4ed8", hovertemplate="$%{y:.1f}B<extra>Net Income</extra>"))
        fig3.update_layout(**CHART_STYLE, height=270, barmode="group")
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

        # FREE CASH FLOW chart
        st.markdown('<div class="sec-heading"><span class="dot"></span>Free Cash Flow Trend</div>', unsafe_allow_html=True)
        if "free_cash_flow" in ratio_df.columns:
            fcf = ratio_df["free_cash_flow"].astype(float) / 1e9
            colors = ["#059669" if v >= 0 else "#ef4444" for v in fcf]
            fig4 = go.Figure()
            fig4.add_trace(go.Bar(x=ratio_df.index, y=fcf, name="FCF ($B)",
                marker_color=colors,
                hovertemplate="$%{y:.1f}B<extra>Free Cash Flow</extra>"))
            fig4.update_layout(**CHART_STYLE, height=240,
                showlegend=False)
            st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

        # RATIO TABLE
        st.markdown('<div class="sec-heading"><span class="dot"></span>Key Ratios by Year — Full Detail</div>', unsafe_allow_html=True)
        display_df = ratio_df.copy()

        # Compute trend arrows from oldest → newest available value for each column
        def trend_arrow(series):
            """Compare most recent vs prior year; return arrow + emoji."""
            vals = pd.to_numeric(series, errors="coerce").dropna()
            if len(vals) < 2:
                return "→"
            latest, prior = vals.iloc[-1], vals.iloc[-2]
            if prior == 0:
                return "→"
            pct_change = (latest - prior) / abs(prior) * 100
            if pct_change > 3:
                return "↑"
            elif pct_change < -3:
                return "↓"
            else:
                return "→"

        # Compute arrows before formatting (while values are still numeric)
        arrows = {col: trend_arrow(display_df[col]) for col in display_df.columns}

        # Format revenue and net income as $B
        for col in ["revenue", "net_income", "free_cash_flow"]:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(
                    lambda x: f"${float(x)/1e9:.1f}B" if x not in (None, "None", "") and str(x) != "nan" else "—"
                )
        for col in ["net_margin_pct", "roe_pct", "roa_pct", "fcf_margin_pct"]:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(
                    lambda x: f"{float(x):.1f}%" if x not in (None, "None", "") and str(x) != "nan" else "—"
                )
        for col in ["debt_to_equity", "current_ratio"]:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(
                    lambda x: f"{float(x):.2f}x" if x not in (None, "None", "") and str(x) != "nan" else "—"
                )

        # Rename columns: human label + trend arrow
        def col_label(c):
            name = c.replace("_pct", " %").replace("_", " ").title()
            arrow = arrows.get(c, "→")
            return f"{name}  {arrow}"

        display_df.columns = [col_label(c) for c in display_df.columns]
        display_df.index.name = "Year"
        st.dataframe(display_df, use_container_width=True)

        # Arrow legend
        st.markdown("""
        <div style="font-size:0.72rem;color:#64748b;margin-top:0.4rem">
          ↑ trending up &nbsp;·&nbsp; ↓ trending down &nbsp;·&nbsp; → broadly flat
          &nbsp;·&nbsp; <em>Trend compares most recent year vs prior year (threshold ±3%)</em>
        </div>
        """, unsafe_allow_html=True)

    # ── TAB 2: TECHNICAL ─────────────────────────────────────────────────────
    with tab_tech:

        if not price_history:
            st.info("No price history available for this ticker.")
        else:
            price_df = pd.DataFrame(price_history)
            price_df["date"]  = pd.to_datetime(price_df["date"])
            price_df["close"] = pd.to_numeric(price_df["close"], errors="coerce")
            price_df = price_df.sort_values("date").dropna(subset=["close"])

            # Compute simple technicals
            price_df["MA20"]  = price_df["close"].rolling(20).mean()
            price_df["MA50"]  = price_df["close"].rolling(50).mean()
            price_df["daily_return"] = price_df["close"].pct_change() * 100

            high_52w   = price_df["close"].max()
            low_52w    = price_df["close"].min()
            avg_close  = price_df["close"].mean()
            volatility = price_df["daily_return"].std()
            pct_from_high = ((latest_close - high_52w) / high_52w * 100) if latest_close else None

            # Tech metric cards
            st.markdown('<div class="sec-heading"><span class="dot"></span>Price Summary</div>', unsafe_allow_html=True)
            t1, t2, t3, t4, t5 = st.columns(5)
            tech_kpis = [
                (t1, "Latest Close",     f"${latest_close:,.2f}" if latest_close else "N/A", "Most recent", "accent"),
                (t2, "Period High",      f"${high_52w:,.2f}",  "100-day range", ""),
                (t3, "Period Low",       f"${low_52w:,.2f}",   "100-day range", ""),
                (t4, "Avg Close",        f"${avg_close:,.2f}", "100-day avg", ""),
                (t5, "Daily Volatility", f"{volatility:.2f}%", "Std dev of returns", "amber"),
            ]
            for col, label, value, sub, cls in tech_kpis:
                with col:
                    st.markdown(f"""
                    <div class="metric-card {cls}">
                      <div class="metric-label">{label}</div>
                      <div class="metric-value">{value}</div>
                      <div class="metric-sub">{sub}</div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

            # Price + MAs chart
            st.markdown('<div class="sec-heading"><span class="dot"></span>Price History with Moving Averages</div>', unsafe_allow_html=True)
            fig_p = go.Figure()
            fig_p.add_trace(go.Scatter(x=price_df["date"], y=price_df["close"],
                name="Close Price", line=dict(color="#1d4ed8", width=1.8),
                fill="tozeroy", fillcolor="rgba(29,78,216,0.06)",
                hovertemplate="$%{y:.2f}<extra>Close</extra>"))
            if "MA20" in price_df.columns:
                fig_p.add_trace(go.Scatter(x=price_df["date"], y=price_df["MA20"],
                    name="MA 20", line=dict(color="#f59e0b", width=1.5, dash="dot"),
                    hovertemplate="$%{y:.2f}<extra>MA20</extra>"))
            if "MA50" in price_df.columns:
                fig_p.add_trace(go.Scatter(x=price_df["date"], y=price_df["MA50"],
                    name="MA 50", line=dict(color="#ef4444", width=1.5, dash="dash"),
                    hovertemplate="$%{y:.2f}<extra>MA50</extra>"))
            fig_p.update_layout(**{**CHART_STYLE, "height": 360,
                "legend": dict(bgcolor="rgba(255,255,255,0.9)", orientation="h",
                               yanchor="bottom", y=-0.22, xanchor="left", x=0, font=dict(size=10))})
            st.plotly_chart(fig_p, use_container_width=True, config={"displayModeBar": False})

            # Daily returns chart
            ch_r1, ch_r2 = st.columns(2)
            with ch_r1:
                st.markdown('<div class="sec-heading"><span class="dot"></span>Daily Returns (%)</div>', unsafe_allow_html=True)
                fig_r = go.Figure()
                colors_r = ["#059669" if v >= 0 else "#ef4444" for v in price_df["daily_return"].fillna(0)]
                fig_r.add_trace(go.Bar(x=price_df["date"], y=price_df["daily_return"],
                    name="Daily Return %", marker_color=colors_r,
                    hovertemplate="%{y:.2f}%<extra>Return</extra>"))
                fig_r.update_layout(**{**CHART_STYLE, "height": 270}, showlegend=False)
                st.plotly_chart(fig_r, use_container_width=True, config={"displayModeBar": False})

            with ch_r2:
                st.markdown('<div class="sec-heading"><span class="dot"></span>Return Distribution</div>', unsafe_allow_html=True)
                fig_h = go.Figure()
                fig_h.add_trace(go.Histogram(x=price_df["daily_return"].dropna(),
                    nbinsx=30, name="Return %",
                    marker_color="#1d4ed8", opacity=0.75,
                    hovertemplate="%{x:.2f}%<extra></extra>"))
                fig_h.update_layout(**{**CHART_STYLE, "height": 270}, showlegend=False)
                st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})

            # Price data table
            st.markdown('<div class="sec-heading"><span class="dot"></span>Price History — Full Data</div>', unsafe_allow_html=True)
            price_table = price_df[["date", "close", "MA20", "MA50", "daily_return"]].copy()
            price_table.columns = ["Date", "Close ($)", "MA 20", "MA 50", "Daily Return (%)"]
            price_table = price_table.sort_values("Date", ascending=False).head(60)
            for col in ["Close ($)", "MA 20", "MA 50"]:
                price_table[col] = price_table[col].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "—")
            price_table["Daily Return (%)"] = price_table["Daily Return (%)"].apply(
                lambda x: f"{x:+.2f}%" if pd.notna(x) else "—")
            price_table["Date"] = price_table["Date"].dt.strftime("%d %b %Y")
            st.dataframe(price_table, use_container_width=True, hide_index=True)

    # ── TAB 3: AI AGENT ───────────────────────────────────────────────────────
    with tab_ai:

        if not os.environ.get("GEMINI_API_KEY"):
            st.warning("Add GEMINI_API_KEY to your .env file to enable the AI agent pipeline.")
            st.stop()

        # ── Run pipeline once per ticker, cache in session state ──────────────
        cache_key = f"pipeline_{ratios['ticker']}"
        if cache_key not in st.session_state:
            with st.spinner("Running 3-step agent pipeline — this takes 10-15 seconds…"):
                st.session_state[cache_key] = run_pipeline(ratios)
        results = st.session_state[cache_key]

        # ── Pipeline flow indicator ───────────────────────────────────────────
        st.markdown("""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;
             padding:1rem 1.2rem;margin-bottom:1.2rem;">
          <div style="font-size:0.68rem;letter-spacing:0.15em;text-transform:uppercase;
               color:#64748b;font-weight:600;margin-bottom:0.7rem;font-family:monospace">
            Agent Pipeline Flow
          </div>
          <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap">
            <div style="background:#dbeafe;border:1px solid #93c5fd;border-radius:6px;
                 padding:5px 12px;font-size:0.75rem;font-weight:600;color:#1d4ed8;font-family:monospace">
              📥 Raw Financial Data
            </div>
            <span style="color:#94a3b8;font-size:1rem">→</span>
            <div style="background:#dcfce7;border:1px solid #86efac;border-radius:6px;
                 padding:5px 12px;font-size:0.75rem;font-weight:600;color:#166534;font-family:monospace">
              🔍 Agent A · Interpreter
            </div>
            <span style="color:#94a3b8;font-size:1rem">→</span>
            <div style="background:#fef9c3;border:1px solid #fde047;border-radius:6px;
                 padding:5px 12px;font-size:0.75rem;font-weight:600;color:#854d0e;font-family:monospace">
              ⚠️ Agent B · Anomaly Detector
            </div>
            <span style="color:#94a3b8;font-size:1rem">→</span>
            <div style="background:#ede9fe;border:1px solid #c4b5fd;border-radius:6px;
                 padding:5px 12px;font-size:0.75rem;font-weight:600;color:#5b21b6;font-family:monospace">
              📋 Agent C · Synthesizer
            </div>
            <span style="color:#94a3b8;font-size:1rem">→</span>
            <div style="background:#fce7f3;border:1px solid #f9a8d4;border-radius:6px;
                 padding:5px 12px;font-size:0.75rem;font-weight:600;color:#831843;font-family:monospace">
              💬 Chat Agent
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── STEP A — Interpreter ──────────────────────────────────────────────
        st.markdown(
            "<div style='font-size:0.68rem;letter-spacing:0.18em;text-transform:uppercase;"
            "color:#166534;font-weight:700;font-family:monospace;padding:0.5rem 0 0.4rem;"
            "border-bottom:2px solid #dcfce7;margin-bottom:0.8rem'>"
            "🔍 Agent A — Financial Health Interpreter</div>",
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.markdown(results["interpreter"])

        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

        # ── STEP B — Anomaly Detector ─────────────────────────────────────────
        st.markdown(
            "<div style='font-size:0.68rem;letter-spacing:0.18em;text-transform:uppercase;"
            "color:#854d0e;font-weight:700;font-family:monospace;padding:0.5rem 0 0.4rem;"
            "border-bottom:2px solid #fef9c3;margin-bottom:0.8rem'>"
            "⚠️ Agent B — Anomaly Detector</div>",
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.markdown(results["anomaly"])

        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

        # ── STEP C — Synthesis ────────────────────────────────────────────────
        st.markdown(
            "<div style='font-size:0.68rem;letter-spacing:0.18em;text-transform:uppercase;"
            "color:#5b21b6;font-weight:700;font-family:monospace;padding:0.5rem 0 0.4rem;"
            "border-bottom:2px solid #ede9fe;margin-bottom:0.8rem'>"
            "📋 Agent C — Senior Analyst Synthesis</div>",
            unsafe_allow_html=True,
        )

        synthesis_text = results["synthesis"]

        # Parse sections — look for the three labels anywhere in the text
        def extract_section(text, label, next_labels):
            upper = text.upper()
            start = upper.find(label)
            if start == -1:
                return ""
            start = start + len(label)
            # Find where this section ends (start of next section or end of string)
            end = len(text)
            for nl in next_labels:
                pos = upper.find(nl, start)
                if pos != -1 and pos < end:
                    end = pos
            return text[start:end].strip()

        strengths  = extract_section(synthesis_text, "STRENGTHS",
                                     ["RISKS AND WATCH ITEMS", "SUMMARY"])
        risks      = extract_section(synthesis_text, "RISKS AND WATCH ITEMS", ["SUMMARY"])
        summary    = extract_section(synthesis_text, "SUMMARY", [])

        if strengths or risks or summary:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.success("**✅ Strengths**")
                st.write(strengths or "—")
            with c2:
                st.warning("**⚠️ Risks & Watch Items**")
                st.write(risks or "—")
            with c3:
                st.info("**📋 Summary**")
                st.write(summary or "—")
        else:
            with st.container(border=True):
                st.write(synthesis_text)

        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

        # ── CHAT AGENT ────────────────────────────────────────────────────────
        st.markdown(
            "<div style='font-size:0.68rem;letter-spacing:0.18em;text-transform:uppercase;"
            "color:#831843;font-weight:700;font-family:monospace;padding:0.5rem 0 0.4rem;"
            "border-bottom:2px solid #fce7f3;margin-bottom:0.8rem'>"
            "💬 Ask the AI Analyst</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='font-size:0.82rem;color:#64748b;margin-bottom:1rem'>"
            f"Ask anything about <strong>{ratios['company_name']}</strong> — "
            "the agent has full access to the financial data and the analysis above.</div>",
            unsafe_allow_html=True,
        )

        # ── CHAT AGENT ────────────────────────────────────────────────────────
        st.markdown(
            "<div style='font-size:0.68rem;letter-spacing:0.18em;text-transform:uppercase;"
            "color:#831843;font-weight:700;font-family:monospace;padding:0.5rem 0 0.4rem;"
            "border-bottom:2px solid #fce7f3;margin-bottom:0.8rem'>"
            "💬 Ask the AI Analyst</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='font-size:0.82rem;color:#64748b;margin-bottom:1rem'>"
            f"Ask anything about <strong>{ratios['company_name']}</strong> — "
            "the agent has full access to the financial data and the analysis above.</div>",
            unsafe_allow_html=True,
        )

        # Initialise chat history first
        chat_key = f"chat_{ratios['ticker']}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []

        def _submit_question(question: str):
            """Add question, call agent, store answer."""
            st.session_state[chat_key].append({"role": "user", "content": question})
            answer = run_chat_agent(
                question, ratios, results, st.session_state[chat_key]
            )
            st.session_state[chat_key].append({"role": "assistant", "content": answer})

        # Suggested question buttons
        suggestions = [
            f"What is the biggest financial risk for {ratios['company_name']}?",
            "How has free cash flow changed over the years?",
            "Is the debt level a concern?",
            "What does the ROE trend tell us?",
        ]
        st.markdown(
            "<div style='font-size:0.72rem;color:#94a3b8;margin-bottom:0.5rem'>Suggested questions:</div>",
            unsafe_allow_html=True,
        )
        q_cols = st.columns(len(suggestions))
        for i, (col, q) in enumerate(zip(q_cols, suggestions)):
            with col:
                if st.button(q, key=f"sugg_{i}", use_container_width=True):
                    with st.spinner("Thinking…"):
                        _submit_question(q)

        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

        # Text input + Send button (works reliably inside tabs unlike st.chat_input)
        inp_col, btn_col = st.columns([5, 1])
        with inp_col:
            user_question = st.text_input(
                "Your question",
                placeholder=f"e.g. How profitable is {ratios['company_name']} compared to its history?",
                label_visibility="collapsed",
                key="chat_input_box",
            )
        with btn_col:
            send = st.button("Send →", use_container_width=True, type="primary")

        if send and user_question.strip():
            with st.spinner("Thinking…"):
                _submit_question(user_question.strip())

        # Display conversation history
        if st.session_state[chat_key]:
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            for msg in st.session_state[chat_key]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            if st.button("🗑 Clear chat history", type="secondary"):
                st.session_state[chat_key] = []
                st.rerun()

        st.markdown("""
        <div class="disclaimer" style="margin-top:1.5rem">
          ⚠️ AI outputs are generated for educational and informational purposes only.
          Nothing here constitutes financial advice or a recommendation to buy or sell any security.
        </div>
        """, unsafe_allow_html=True)

    # FOOTER
    st.markdown(f"""
    <div class="footer">
      Built by <strong>Sneha Umrikar</strong> — Data & AI Specialist ·
      <a href="https://github.com/UmrikarS" target="_blank">GitHub</a> ·
      <a href="https://linkedin.com/in/sneha-umrikar-3376a9337" target="_blank">LinkedIn</a>
      <br><br>
      <span style="font-size:0.68rem">Data: Alpha Vantage · AI: Gemini API · Built with Streamlit · For portfolio demonstration only</span>
    </div>
    """, unsafe_allow_html=True)

else:
    # Empty state — no data yet
    st.markdown("""
    <div style="text-align:center; padding:5rem 0 3rem; color:#94a3b8;">
      <div style="font-size:3.5rem; margin-bottom:1rem;">📊</div>
      <div style="font-size:0.85rem; font-weight:500; color:#475569; margin-bottom:0.5rem;">Ready to analyse</div>
      <div style="font-size:0.78rem;">Enter a ticker symbol above and click Analyse →</div>
    </div>
    """, unsafe_allow_html=True)