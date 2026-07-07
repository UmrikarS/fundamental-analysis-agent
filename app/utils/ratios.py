"""
Step [2] Ratio Engine
Your accounting logic lives here - this is the most "show your expertise"
part of the project, independent of any AI.

Takes raw statements from fetch.py (Alpha Vantage format: list of yearly
dicts, newest first, all numeric values as strings) and computes standard
fundamental ratios and YoY trends.
"""


def _num(value):
    """Alpha Vantage returns numbers as strings; 'None' marks missing data."""
    if value is None or value == "None":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def compute_ratios(company_data: dict) -> dict:
    """
    Compute key fundamental ratios across all available years.
    Returns a dict of {year: {ratio_name: value}} plus a flat trends summary.
    """
    income_list = company_data["income_stmt"]
    balance_list = company_data["balance_sheet"]
    cashflow_list = company_data["cash_flow"]

    balance_by_date = {b["fiscalDateEnding"]: b for b in balance_list}
    cashflow_by_date = {c["fiscalDateEnding"]: c for c in cashflow_list}

    ratios_by_year = {}

    for income in income_list:
        date = income.get("fiscalDateEnding")
        year_label = date[:4] if date else "Unknown"

        balance = balance_by_date.get(date, {})
        cashflow = cashflow_by_date.get(date, {})

        revenue = _num(income.get("totalRevenue"))
        net_income = _num(income.get("netIncome"))

        total_assets = _num(balance.get("totalAssets"))
        total_equity = _num(balance.get("totalShareholderEquity"))
        total_debt = _num(balance.get("shortLongTermDebtTotal"))
        current_assets = _num(balance.get("totalCurrentAssets"))
        current_liab = _num(balance.get("totalCurrentLiabilities"))

        op_cash_flow = _num(cashflow.get("operatingCashflow"))
        capex = _num(cashflow.get("capitalExpenditures"))  # positive = cash spent
        free_cash_flow = None
        if op_cash_flow is not None and capex is not None:
            free_cash_flow = op_cash_flow - capex

        def pct(a, b):
            if a is None or b in (None, 0):
                return None
            return round((a / b) * 100, 2)

        ratios_by_year[year_label] = {
            "revenue": revenue,
            "net_income": net_income,
            "net_margin_pct": pct(net_income, revenue),
            "roe_pct": pct(net_income, total_equity),
            "roa_pct": pct(net_income, total_assets),
            "debt_to_equity": round(total_debt / total_equity, 2) if total_debt and total_equity else None,
            "current_ratio": round(current_assets / current_liab, 2) if current_assets and current_liab else None,
            "free_cash_flow": free_cash_flow,
            "fcf_margin_pct": pct(free_cash_flow, revenue),
        }

    # YoY revenue/net income growth, most-recent vs prior year
    sorted_years = sorted(ratios_by_year.keys(), reverse=True)
    trends = {}
    if len(sorted_years) >= 2:
        latest, prior = sorted_years[0], sorted_years[1]
        rev_latest = ratios_by_year[latest]["revenue"]
        rev_prior = ratios_by_year[prior]["revenue"]
        ni_latest = ratios_by_year[latest]["net_income"]
        ni_prior = ratios_by_year[prior]["net_income"]

        trends["revenue_growth_pct"] = (
            round((rev_latest - rev_prior) / abs(rev_prior) * 100, 2)
            if rev_latest is not None and rev_prior else None
        )
        trends["net_income_growth_pct"] = (
            round((ni_latest - ni_prior) / abs(ni_prior) * 100, 2)
            if ni_latest is not None and ni_prior else None
        )

    return {
        "ticker": company_data["ticker"],
        "company_name": company_data["company_name"],
        "sector": company_data["sector"],
        "valuation": {
            "trailing_pe": company_data.get("trailing_pe"),
            "market_cap": company_data.get("market_cap"),
        },
        "ratios_by_year": ratios_by_year,
        "trends": trends,
    }
