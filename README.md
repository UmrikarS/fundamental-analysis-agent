# Fundamental Analysis Agent

A small project combining fundamental/accounting analysis with an AI agent
pipeline. Pulls company financials via Yahoo Finance, computes standard
fundamental ratios, and runs a 3-step agent pipeline to produce an
analyst-style written summary.

## Why this project exists

Built to demonstrate:
- Accounting/fundamental analysis knowledge (ratio engine, in plain Python — no AI involved)
- Data pipeline skills (Alpha Vantage API → structured ratios → dashboard)
- Practical AI agent design: a multi-step pipeline (Interpreter → Anomaly Detector → Synthesizer),
  each with a narrow task and structured input/output, rather than one big prompt

## Architecture

```
User enters ticker
      │
      ▼
[1] Data Fetch (app/data/fetch.py)        — Alpha Vantage API: statements, price history
      │
      ▼
[2] Ratio Engine (app/utils/ratios.py)    — ROE, ROA, margins, D/E, FCF, YoY growth
      │
      ▼
[3] Agent Pipeline (app/agents/agents.py)
      A. Interpreter   — plain-English financial health summary
      B. Anomaly        — flags unusual YoY changes, explains why
      C. Synthesis      — combines A + B into Strengths / Risks / Summary
      │
      ▼
[4] Streamlit UI (app/main.py)            — charts, ratio table, agent output tabs
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and add:
#   GEMINI_API_KEY        (free at https://aistudio.google.com)
#   ALPHAVANTAGE_API_KEY  (free at https://www.alphavantage.co/support/#api-key)
```

## Run

```bash
streamlit run app/main.py
```

Then open the local URL Streamlit prints (usually http://localhost:8501) and
enter a ticker (e.g. `AAPL`, `MSFT`, `NVDA`).

## Notes / Disclaimers

- Output is analytical and educational only — the agents are explicitly
  instructed not to give buy/sell/hold recommendations.
- Alpha Vantage's free tier allows 25 requests/day and 5 requests/minute,
  with no credit card required. Each ticker analysis uses ~5 requests
  (overview, income statement, balance sheet, cash flow, price history),
  so plan for roughly 5 analyses/day on the free tier. Results are cached
  for 1 hour in the app to avoid burning through the limit on repeated reruns.

## Possible next steps

- Peer/sector comparison mode (loop the pipeline across multiple tickers)
- Natural-language query box ("show me Apple's debt trend") mapped to chart generation
- Cache agent outputs (e.g. SQLite) so repeat lookups don't re-call the API
- Earnings call / 10-K sentiment analysis using NLP (extends to text-based filings)
