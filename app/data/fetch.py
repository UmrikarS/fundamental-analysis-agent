"""
Step [1] Data Fetch Layer
Pulls financial statements and key stats for a given ticker using the
Alpha Vantage API - genuinely free tier (no card required), 25 requests/day.

Get a free key at https://www.alphavantage.co/support/#api-key
"""

import os
import time
import requests

BASE_URL = "https://www.alphavantage.co/query"

def _get(params: dict, max_retries: int = 3) -> dict:
    api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not api_key:
        raise ValueError(
            "Missing ALPHAVANTAGE_API_KEY. Get a free key at "
            "alphavantage.co/support/#api-key and add it to your .env file."
        )

    query = {**params, "apikey": api_key}

    for attempt in range(max_retries):
        response = requests.get(BASE_URL, params=query, timeout=15)
        response.raise_for_status()
        data = response.json()

        if "Information" in data and "per second" in data["Information"].lower():
            # Per-second burst limit, not the daily cap - safe to wait and retry
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            raise ValueError(
                "Alpha Vantage burst rate limit hit repeatedly. Wait a few "
                "seconds and try again."
            )
        if "Note" in data:
            raise ValueError(
                "Alpha Vantage rate limit reached (free tier: 25 requests/day, "
                "5 requests/min). Wait a bit and try again."
            )
        if "Error Message" in data:
            raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
        if "Information" in data:
            raise ValueError(f"Alpha Vantage: {data['Information']}")

        return data

    return {}


def _to_float(value):
    """Alpha Vantage returns numbers as strings; 'None' is used for missing data."""
    if value is None or value == "None":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def fetch_company_data(ticker: str) -> dict:
    """
    Fetch raw financial data for a ticker.
    Returns a dict with income statement, balance sheet, cash flow (each a
    list of yearly dicts, most recent first) and key stats.
    """
    ticker = ticker.upper()

    overview = _get({"function": "OVERVIEW", "symbol": ticker})
    time.sleep(1.1)
    income_data = _get({"function": "INCOME_STATEMENT", "symbol": ticker})
    time.sleep(1.1)
    balance_data = _get({"function": "BALANCE_SHEET", "symbol": ticker})
    time.sleep(1.1)
    cashflow_data = _get({"function": "CASH_FLOW", "symbol": ticker})

    income_reports = income_data.get("annualReports", [])
    if not income_reports:
        raise ValueError(
            f"No data found for ticker '{ticker}'. Check the symbol is correct."
        )

    return {
        "ticker": ticker,
        "company_name": overview.get("Name", ticker),
        "sector": overview.get("Sector", "Unknown"),
        "market_cap": _to_float(overview.get("MarketCapitalization")),
        "current_price": None,  # not in OVERVIEW; price chart covers this separately
        "trailing_pe": _to_float(overview.get("PERatio")),
        "income_stmt": income_reports[:6],          # newest first
        "balance_sheet": balance_data.get("annualReports", [])[:6],
        "cash_flow": cashflow_data.get("annualReports", [])[:6],
    }


def fetch_price_history(ticker: str, outputsize: str = "compact") -> list:
    """
    Fetch historical daily close prices for charting.
    outputsize='compact' returns the last ~100 trading days (free tier friendly).
    Returns a list of {date, close} dicts, oldest first.
    """
    ticker = ticker.upper()
    data = _get({
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "outputsize": outputsize,
    })
    series = data.get("Time Series (Daily)", {})
    history = [
        {"date": date, "close": _to_float(values.get("4. close"))}
        for date, values in series.items()
    ]
    history.sort(key=lambda x: x["date"])
    return history