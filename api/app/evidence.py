"""Financial evidence for the Council: what the source reported, what we computed from it, and
exactly what is missing where a measure cannot be computed.

Three kinds of statement are kept apart, because a seat that cannot tell them apart will argue
from the wrong one:

  reported   a figure the source published. It travels with the period it covers (FY, TTM or a
             single quarter), the date that period ends, the currency, the unit, and the rule
             that aggregated it.
  derived    a figure computed here, with its formula, its operands, the window the operands
             share, and a check that proves it — or no figure at all and a `missing` list naming
             the inputs, when the reported figures do not support one.
  opinion    a rule-based vote. Not in this module: the council's seats are their own dataset
             (`get_council`) and say on their face that they are rules, not measurements.

Nothing here estimates, annualises or back-fills. A measure whose inputs are absent comes back
with `missing`, never with a number.

Two schemas are supported on purpose. The repaired pipeline records `period`, `period_end` and
`source_json` per line item and keeps the single quarters in `fundamentals_lineitems_quarterly`;
a database parsed before that repair has none of those. Everything here degrades to what the
database actually holds, so the API can ship before the pipeline is repaired and gains the
period-aware answers the moment it is — which is also what lets the two be deployed in either
order. `period_aware` says which schema is in front of us.
"""

from __future__ import annotations

import json
import sqlite3
from calendar import monthrange
from datetime import date
from typing import Any

from pydantic import BaseModel

FLOW_SECTIONS = ("Income Statement", "Cash Flow Statement")

# Label groups, read off the live database on 2026-10-29 with a count of the tickers carrying each
# alias - not from what a statement "should" be called. Within a group the first entry that matches
# wins, so the more specific label comes first.
#
# Two things make a group work across the Gulf. Labels are compared after `_norm`: whitespace
# collapsed, English case folded, and the alef and ya forms unified, because the source is not
# consistent about them ("إجمالي حقوق المساهمين" and "إجمالى حقوق المساهمين" are the same line on
# 101 tickers between them). And an entry beginning with "~" matches any label that STARTS with
# the rest, which is how one entry covers a per-share line whose unit is written into its name -
# (فلس), (درهم), (ريال قطري), (بيسة) - without listing every currency in the region.
PREFIX = "~"
# Alef and ya forms only. The taa marbuta is deliberately left alone: folding ة into ه would make
# two different words equal as often as it would unify one.
_FORMS = str.maketrans({"\u0623": "\u0627", "\u0625": "\u0627", "\u0622": "\u0627", "\u0649": "\u064a"})


def _norm(label: str) -> str:
    return " ".join((label or "").translate(_FORMS).split()).casefold()


def matches(label: str, entry: str) -> bool:
    """Does this row's label answer to this group entry?"""
    if entry.startswith(PREFIX):
        return _norm(label).startswith(_norm(entry[len(PREFIX):]))
    return _norm(label) == _norm(entry)


NET_INCOME = ("Net Income", "\u0635\u0627\u0641\u064a \u0627\u0644\u062f\u062e\u0644", "\u0627\u0644\u0631\u0628\u062d \u0627\u0644\u0635\u0627\u0641\u064a")
NET_INCOME_BEFORE_UNUSUAL = ("Net Profit Before Unusual Items",
                             PREFIX + "\u0635\u0627\u0641\u064a \u0627\u0644\u062f\u062e\u0644 \u0642\u0628\u0644 \u0627\u0644\u0628\u0646\u0648\u062f \u0627\u0644\u0627\u0633\u062a\u062b\u0646\u0627\u0626\u064a\u0629")
EXTRAORDINARY = ("Extraordinary income/expense", "\u0628\u0646\u062f \u0627\u0633\u062a\u062b\u0646\u0627\u0626\u064a")
# The unit is inside the label on every Arabic grid, so these two are prefixes. "ربح السهم قبل"
# does not begin with "ربح السهم (", so the bracket is what keeps the two apart.
EPS_REPORTED = ("Earning Per Share (Riyal)", "Earnings Per Share (Riyal)",
                PREFIX + "\u0631\u0628\u062d \u0627\u0644\u0633\u0647\u0645 (")
EPS_BEFORE_UNUSUAL = ("Earnings Per Share before unusual items (Riyal)",
                      PREFIX + "\u0631\u0628\u062d \u0627\u0644\u0633\u0647\u0645 \u0642\u0628\u0644 \u0627\u0644\u0628\u0646\u0648\u062f \u0627\u0644\u0627\u0633\u062a\u062b\u0646\u0627\u0626\u064a\u0629 (")
SHARES = ("Shares Outstanding (Million)", "Number of Ordinary Shares (Millions)")
# 408 tickers carry an average-share row, in the balance sheet of the Arabic grids. Before this
# was measured the mean rule had no live example and was only exercised against the function.
AVERAGE_SHARES = ("Average number of shares (Million)", "Weighted average number of shares",
                  PREFIX + "\u0645\u062a\u0648\u0633\u0637 \u0639\u062f\u062f \u0627\u0644\u0627\u0633\u0647\u0645")
EQUITY_COMMON = ("Total Shareholders' Equity", "Total Shareholders Equity",
                 "\u0645\u062c\u0645\u0648\u0639 \u062d\u0642\u0648\u0642 \u0627\u0644\u0645\u0633\u0627\u0647\u0645\u064a\u0646",
                 "\u0625\u062c\u0645\u0627\u0644\u064a \u062d\u0642\u0648\u0642 \u0627\u0644\u0645\u0633\u0627\u0647\u0645\u064a\u0646")
# "Total Common Equity" is NOT common equity, whatever it is called: on 1180 it is 203,827.25,
# exactly shareholders' equity plus minority interest plus equity sukuk, and the same holds on
# 1010. Reading it as the common-equity denominator would understate every conventional Saudi
# bank's return on equity by about a tenth. Checking the arithmetic caught what the name hid.
EQUITY_ALL = ("Total Owners Equity", "Total Owners' Equity", "Total Common Equity",
              "\u0645\u062c\u0645\u0648\u0639 \u062d\u0642\u0648\u0642 \u0627\u0644\u0645\u0644\u0643\u064a\u0629")
REVENUE = ("Sales", "Total Revenue", "Net Sales", "\u0627\u0644\u0627\u064a\u0631\u0627\u062f\u0627\u062a", "\u0627\u0644\u0645\u0628\u064a\u0639\u0627\u062a")
GROSS_INCOME = ("Gross Income",)
OPERATING_INCOME = ("Operating Income", "\u0627\u062c\u0645\u0627\u0644\u064a \u062f\u062e\u0644 \u0627\u0644\u0639\u0645\u0644\u064a\u0627\u062a", "\u0627\u0644\u0631\u0628\u062d \u0627\u0644\u062a\u0634\u063a\u064a\u0644\u064a")
TOTAL_ASSETS = ("Total Assets", "\u0645\u062c\u0645\u0648\u0639 \u0627\u0644\u0645\u0648\u062c\u0648\u062f\u0627\u062a",
                "\u0625\u062c\u0645\u0627\u0644\u064a \u0627\u0644\u0645\u0648\u062c\u0648\u062f\u0627\u062a", "\u0625\u062c\u0645\u0627\u0644\u064a \u0627\u0644\u0623\u0635\u0648\u0644",
                "\u0645\u062c\u0645\u0648\u0639 \u0627\u0644\u0623\u0635\u0648\u0644")
TCA = ("Total Current Assets", "\u0645\u062c\u0645\u0648\u0639 \u0627\u0644\u0645\u0648\u062c\u0648\u062f\u0627\u062a \u0627\u0644\u0645\u062a\u062f\u0627\u0648\u0644\u0629")

# Bank templates. A bank's top line is `Operating Income`, not `Sales`, and these lines have no
# analogue outside a bank - which is why a bank gets its own measures instead of being pushed
# through a price-to-sales ratio. Three templates are in the data: the Islamic one (financing
# investments), the conventional Saudi one (loans and advances), and the Arabic one, which carries
# net loans and deposits but NO performing/non-performing split and no provision stock - so asset
# quality is genuinely absent there rather than merely unlabelled, and comes back `missing`.
BANK_NET_FINANCING_INCOME = ("Net income from investments and financing activities",
                             "Net Financing Income",
                             "\u0635\u0627\u0641\u064a \u062f\u062e\u0644 \u0627\u0644\u0639\u0645\u0648\u0644\u0627\u062a \u0627\u0644\u062e\u0627\u0635\u0629")
BANK_OPERATING_EXPENSES = ("Operating Expenses", "\u0627\u062c\u0645\u0627\u0644\u064a \u0645\u0635\u0627\u0631\u064a\u0641 \u0627\u0644\u0639\u0645\u0644\u064a\u0627\u062a")
BANK_PROVISIONS = ("Debt Provisions", "\u0645\u062e\u0635\u0635\u0627\u062a \u0627\u0644\u062f\u064a\u0648\u0646")
BANK_FINANCING = ("Net Financing Investments", "Net Loans & Advances",
                  "\u0635\u0627\u0641\u064a \u0627\u0644\u0642\u0631\u0648\u0636 \u0648 \u0627\u0644\u0633\u0644\u0641")
BANK_PERFORMING = ("Performing Financing Investments", "Performing Loans & Advances")
BANK_NPL = ("Non-performing Financing Investments", "Non-Performing Loans & Advances (NPLs)")
BANK_LOSS_PROVISION = ("Financing Investments Loss Provision", "Provision for Credit Losses (PCL)")
BANK_DEPOSITS = ("Customer Deposits", "Customers' Deposits", "\u0648\u062f\u0627\u0626\u0639 \u0627\u0644\u0639\u0645\u0644\u0627\u0621")
BANK_INVESTMENTS = ("Investments", "\u0625\u0633\u062a\u062b\u0645\u0627\u0631\u0627\u062a", "\u0627\u0633\u062a\u062b\u0645\u0627\u0631\u0627\u062a")
BANK_DUE_FROM_BANKS = ("Due from Banks", "Due from Banks & Other FI's",
                       "\u0623\u0631\u0635\u062f\u0629 \u0644\u062f\u0649 \u0627\u0644\u0628\u0646\u0648\u0643 \u0648 \u0627\u0644\u0645\u0624\u0633\u0633\u0627\u062a \u0627\u0644\u0645\u0627\u0644\u064a\u0629 \u0627\u0644\u0623\u062e\u0631\u0649")

# What the fundamentals strip shows, and what each number actually is. The pipeline computes some
# of these from statements and publishes others from the data source; a reader cannot recover a
# formula from a name, so the formula travels with the number.
DEFINITIONS: dict[str, dict[str, str]] = {
    "pe": {
        "formula": "price / earnings per share over the trailing twelve months",
        "source": "published by the data source",
        "denominator": "the source does not disclose the share count behind its EPS",
    },
    "pb": {
        "formula": "price / book value per share",
        "source": "computed from statements where available, else published by the data source",
        "denominator": "book value per share as reported on the balance sheet",
    },
    "ev_ebitda": {
        "formula": "(market capitalisation + total debt - cash) / EBITDA",
        "source": "computed from statements",
        "denominator": "EBITDA as reported, or operating income plus depreciation where the"
                       " statement carries no EBITDA line",
    },
    "ps": {
        "formula": "market capitalisation / revenue",
        "source": "computed from statements",
        "denominator": "revenue over the income statement's own window",
    },
    "roe": {
        "formula": "net income / shareholders' equity x 100",
        "source": "published by the data source",
        # The requirement this answers: say which equity, every time. The published figure cannot
        # say, and that is itself the finding.
        "denominator": "NOT DISCLOSED by the source: neither the equity date nor whether it is"
                       " period-end or average equity is stated, so this figure cannot be"
                       " reproduced or checked. The derived `roe_on_period_end_common_equity`"
                       " names its denominator and can be.",
    },
    "roa": {
        "formula": "net income / total assets x 100",
        "source": "published by the data source",
        "denominator": "NOT DISCLOSED by the source (period-end or average assets)",
    },
    "roic": {
        "formula": "operating income after tax / (total debt + equity - cash) x 100",
        "source": "computed from statements",
        "denominator": "invested capital at the balance-sheet date",
    },
    "net_margin": {
        "formula": "net income / revenue x 100",
        "source": "computed from statements",
        "denominator": "revenue over the same window as the earnings",
    },
    "gross_margin": {
        "formula": "gross income / revenue x 100",
        "source": "computed from statements",
        "denominator": "revenue over the same window as the gross income",
    },
    "debt_equity": {
        "formula": "total debt / total equity",
        "source": "computed from statements",
        "denominator": "equity at the balance-sheet date",
    },
    "current_ratio": {
        "formula": "total current assets / total current liabilities",
        "source": "computed from statements",
        "denominator": "current liabilities at the balance-sheet date",
    },
    "interest_coverage": {
        "formula": "operating income / financing expense",
        "source": "computed from statements",
        "denominator": "financing expense over the same window as the operating income",
    },
    "fcf_yield": {
        "formula": "free cash flow / market capitalisation x 100",
        "source": "computed from statements",
        "denominator": "market capitalisation at the quote's date",
    },
    "div_yield": {
        "formula": "dividends per share over twelve months / price x 100",
        "source": "published by the data source",
        "denominator": "the source does not state which twelve months",
    },
    "payout": {
        "formula": "dividends / net income x 100",
        "source": "computed from statements and the dividend history",
        "denominator": "net income over the window the dividends are matched to",
    },
}

# Generic ratios that are not meaningful for a bank, and why. The pipeline already marks some of
# these `na_sector`; the rest come back `missing_inputs`, because the label they look for is not
# in a bank's statement. "Missing" reads as a gap to be filled, which invites exactly the wrong
# fix — mapping a bank's `Operating Income` into the revenue slot, so that a price-to-sales ratio
# and a margin on financing income appear beside industrial companies' and get compared with
# them. The measures a bank is actually read on are in `_bank_measures`.
BANK_UNSUITABLE: dict[str, str] = {
    "ps": "a bank has no sales line; price to revenue is not a measure banks are valued on",
    "net_margin": "margin on revenue has no bank analogue; net financing margin is the measure",
    "gross_margin": "a bank reports no cost of sales, so there is no gross margin",
    "current_ratio": "a bank's balance sheet is not split into current and non-current",
    "interest_coverage": "interest is a bank's raw material, not a financing cost to cover",
    "roic": "invested capital is not defined for a deposit-funded balance sheet",
    "ev_ebitda": "enterprise value is not meaningful where debt is the operating input",
    "fcf_yield": "operating cash flow follows deposit and financing flows, not operations",
}


class Cell(BaseModel):
    """One reported figure, with everything needed to say what it is."""

    label: str
    section: str
    fiscal_year: int
    item_index: int = 0
    value: float | None = None
    period: str | None = None
    period_end: str | None = None
    rule: str | None = None
    # The source columns behind the figure: the quarter ends that were added together, where it
    # was reconstructed from a quarterly grid. This is the reference that makes a reconstructed
    # annual figure checkable against the page it came from.
    window: list[str] = []


class Calculation(BaseModel):
    """A derived figure, or the reason there is none. Never both.

    `operands` is `[label, value, where]` per operand, the same compact shape the statements use
    for their rows: a seat reads every operand of every calculation inside one prompt, and an
    object with six keys per operand spends the budget on key names instead of figures.
    """

    metric: str
    formula: str
    value: float | None = None
    unit: str | None = None
    window: str | None = None
    denominator: str | None = None
    operands: list[list[Any]] = []
    checks: list[str] = []
    missing: list[str] = []


class Period(BaseModel):
    period: str | None  # FY | TTM | Q
    period_end: str | None  # "2026-06"
    aggregation: str | None  # the rule behind the figures, e.g. sum_quarters
    # The source columns the figures were built from, where they were reconstructed.
    source_columns: list[str] = []


# --- reading the statements ------------------------------------------------------------------


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def columns_of(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def period_aware(conn: sqlite3.Connection) -> bool:
    """True once the parser records a reporting mode per line item."""
    return {"period", "period_end"} <= columns_of(conn, "fundamentals_lineitems")


class Items:
    """One ticker's line items for the years asked for, with lookup by label group."""

    def __init__(self, rows: list[Cell], quarterly: list[Cell]):
        self.rows = rows
        self.quarterly = quarterly
        self.years = sorted({r.fiscal_year for r in rows}, reverse=True)
        self.latest = self.years[0] if self.years else None

    def find(self, labels: tuple[str, ...], section: str | None = None, year: int | None = None) -> Cell | None:
        """The first row answering to the earliest entry of this group. Entry order is priority:
        a group's more specific label comes first, so a row matching it wins over one matching a
        later entry even where the later one appears earlier in the statement."""
        year = self.latest if year is None else year
        for entry in labels:
            for r in self.rows:
                if (
                    r.fiscal_year == year
                    and r.value is not None
                    and (section is None or r.section == section)
                    and matches(r.label, entry)
                ):
                    return r
        return None

    def section_of(self, section: str, year: int | None = None) -> list[Cell]:
        year = self.latest if year is None else year
        return [r for r in self.rows if r.section == section and r.fiscal_year == year]

    def sections(self) -> list[str]:
        order = ["Income Statement", "Balance Sheet", "Cash Flow Statement"]
        present = {r.section for r in self.rows}
        return [s for s in order if s in present] + sorted(present - set(order))

    def period(self, section: str, year: int | None = None) -> Period:
        """The window this section's figures cover in this year. One window per section is an
        invariant of the repaired parser; where rows disagree the commonest one is reported."""
        cells = self.section_of(section, year)
        if not cells:
            return Period(period=None, period_end=None, aggregation=None)
        counts: dict[tuple, int] = {}
        rules: dict[str, int] = {}
        for c in cells:
            counts[(c.period, c.period_end)] = counts.get((c.period, c.period_end), 0) + 1
            if c.rule:
                rules[c.rule] = rules.get(c.rule, 0) + 1
        (period, end), _n = max(counts.items(), key=lambda kv: kv[1])
        columns: list[str] = []
        for c in cells:
            if c.period == period and c.period_end == end and len(c.window) > len(columns):
                columns = c.window
        return Period(
            period=period, period_end=end,
            aggregation=max(rules.items(), key=lambda kv: kv[1])[0] if rules else None,
            source_columns=columns,
        )

    def quarters(self, section: str = "Income Statement") -> list[str]:
        return sorted({q.period_end for q in self.quarterly if q.section == section and q.period_end})

    def quarter_series(self, labels: tuple[str, ...], section: str = "Income Statement") -> list[Cell]:
        for entry in labels:
            got = [q for q in self.quarterly if q.section == section and matches(q.label, entry)]
            if got:
                return sorted(got, key=lambda q: q.period_end or "")
        return []


def load_items(conn: sqlite3.Connection, ticker_key: str, years: int = 2) -> Items:
    aware = period_aware(conn)
    extra = ", period, period_end, source_json" if aware else ""
    yrs = [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT fiscal_year FROM fundamentals_lineitems WHERE ticker_key = ?"
            " ORDER BY fiscal_year DESC LIMIT ?",
            (ticker_key, max(1, years)),
        )
    ]
    rows: list[Cell] = []
    if yrs:
        marks = ",".join("?" for _ in yrs)
        for r in conn.execute(
            f"SELECT section, fiscal_year, item_index, line_item_label, value{extra}"
            f" FROM fundamentals_lineitems WHERE ticker_key = ? AND fiscal_year IN ({marks})"
            " ORDER BY section, item_index",
            (ticker_key, *yrs),
        ):
            rows.append(_cell(r, aware))

    quarterly: list[Cell] = []
    if table_exists(conn, "fundamentals_lineitems_quarterly"):
        for r in conn.execute(
            "SELECT section, fiscal_year, item_index, line_item_label, value, period, period_end,"
            " source_json FROM fundamentals_lineitems_quarterly WHERE ticker_key = ? AND period = 'Q'"
            " ORDER BY section, item_index, period_end",
            (ticker_key,),
        ):
            quarterly.append(_cell(r, True))
    return Items(rows, quarterly)


def _cell(r: sqlite3.Row, aware: bool) -> Cell:
    rule, window = None, []
    if aware and r["source_json"]:
        try:
            src = json.loads(r["source_json"])
            rule = src.get("rule")
            got = src.get("window") or ([src["quarter"]] if src.get("quarter") else [])
            window = [str(w) for w in got] if isinstance(got, list) else []
        except (ValueError, TypeError):
            rule, window = None, []
    return Cell(
        label=r["line_item_label"],
        section=r["section"] or "Other",
        fiscal_year=r["fiscal_year"],
        item_index=r["item_index"],
        value=r["value"],
        period=r["period"] if aware else None,
        period_end=r["period_end"] if aware else None,
        rule=rule,
        window=window,
    )


# --- windows ----------------------------------------------------------------------------------


def window_of(period: str | None, period_end: str | None, fiscal_year: int | None = None) -> tuple[str, str] | None:
    """The calendar window a reporting mode covers, as ISO dates. A dividend or any other event
    is matched to earnings through this, never by its fiscal-year label: a trailing-twelve-month
    window ending in June is not the fiscal year it is filed under."""
    if period_end and len(period_end) >= 7:
        year, month = int(period_end[:4]), int(period_end[5:7])
    elif fiscal_year:
        year, month = fiscal_year, 12
    else:
        return None
    end = date(year, month, monthrange(year, month)[1])
    months = {"FY": 12, "TTM": 12, "Q": 3}.get(period or "FY", 12)
    start_month, start_year = month - months + 1, year
    while start_month <= 0:
        start_month += 12
        start_year -= 1
    return (date(start_year, start_month, 1).isoformat(), end.isoformat())


def window_label(p: Period) -> str | None:
    if not p.period:
        return None
    if p.period == "FY":
        return f"fiscal year to {p.period_end}" if p.period_end else "fiscal year"
    if p.period == "TTM":
        return f"twelve months to {p.period_end}"
    return f"the quarter to {p.period_end}"


# --- sector -----------------------------------------------------------------------------------


def sector_of(items: Items, gauge_inputs: dict[str, dict]) -> str:
    """Which kind of company this is, for deciding which measures mean anything.

    The pipeline records its own verdict on every gauge row and that is taken first. But the test
    behind it - no gross income line and no current-asset split - is an ABSENCE, and an absence
    is a weak thing to build on: the Arabic statement templates carry neither line for ordinary
    companies either. Measured on the live database on 2026-10-29, the pipeline calls 204 tickers
    banks, of which only 53 are in the Banks sector the site shows; the rest are 27 insurers, 20
    real-estate companies, 13 industrials, 17 consumer companies and 4 energy companies.

    So a bank claim, from wherever it comes, must be corroborated by something a bank positively
    has: a customer-deposit line or a lending balance. On the same data that leaves 64 - all 53 of
    the site's banks, 10 financing companies and one unlabelled - and drops all 140 others. Not one
    company the site calls a bank is dropped by it.

    A bank claim the balance sheet does not corroborate yields `unknown`, which suppresses nothing:
    we know from the statements that this is not a bank, and the absence of two labels does not say
    what it is instead."""
    recorded = next(
        (str(i["sector"]) for i in gauge_inputs.values() if isinstance(i, dict) and i.get("sector")),
        None,
    )
    sector = recorded or _detected(items)
    if sector != "bank":
        return sector
    lends = items.find(BANK_FINANCING, "Balance Sheet") is not None
    deposits = items.find(BANK_DEPOSITS, "Balance Sheet") is not None
    return "bank" if (lends or deposits) else "unknown"


def _detected(items: Items) -> str:
    """The pipeline's own test, for a database whose gauges do not carry a sector.

    "bank" is a positive finding and never a default. With no statements at all - or with no
    balance sheet for the absence to be an absence in - every company would pass it, and the
    generic ratios a bank is not read on would be withheld from the companies that are read on
    exactly those."""
    if not items.rows or "Balance Sheet" not in {r.section for r in items.rows if r.fiscal_year == items.latest}:
        return "unknown"
    if items.find(GROSS_INCOME) is None and items.find(TCA) is None:
        return "bank"
    return "non_bank"


# --- staleness --------------------------------------------------------------------------------


def stale_reason(inputs: dict[str, Any], items: Items) -> str | None:
    """Why a gauge must not be shown beside these statements, or None.

    The gauge stage reads one fiscal year per ticker and stamps the row with it. If the
    statements have moved on and the gauges have not, the number on the screen was computed from
    figures that are no longer the ones beside it — the exact accident a refreshed statement
    invites. A gauge from a database with no stamp cannot be dated, and is left alone rather than
    called stale on a guess."""
    if not isinstance(inputs, dict) or items.latest is None:
        return None
    year = inputs.get("fiscal_year")
    if not isinstance(year, int):
        return None
    if year < items.latest:
        return (
            f"computed from fiscal year {year} while the statements now carry {items.latest}:"
            " the gauge stage has not run since the statements were refreshed"
        )
    stamped = inputs.get("period_end")
    if stamped:
        current = items.period("Income Statement", items.latest).period_end
        if current and stamped != current:
            return (f"computed from the window ending {stamped} while the income statement now"
                    f" ends {current}")
    return None


# --- the calculations -------------------------------------------------------------------------


def _where(c: Cell) -> str:
    bits = [c.section]
    if c.period and c.period_end:
        bits.append(f"{c.period}@{c.period_end}")
    elif c.period_end:
        bits.append(c.period_end)
    else:
        bits.append(str(c.fiscal_year))
    if c.rule:
        bits.append(c.rule)
    return " ".join(bits)


def _op(c: Cell | None) -> list[Any] | None:
    return None if c is None else [c.label, c.value, _where(c)]


def _ops(*cells: Cell | None) -> list[list[Any]]:
    return [o for o in (_op(c) for c in cells) if o]


def _pct(n: float, d: float) -> float:
    return round(n / d * 100.0, 4)


def _window_text(items: Items, *cells: Cell | None) -> str | None:
    """The window a calculation is struck over, read off its own operands rather than assumed:
    a ratio of two balance-sheet lines is a position at one date, and a flow over a position
    spans both."""
    flow, position = items.period("Income Statement"), items.period("Balance Sheet")
    sections = {c.section for c in cells if c is not None}
    if sections == {"Balance Sheet"}:
        return f"position at {position.period_end}" if position.period_end else None
    if "Balance Sheet" in sections and sections - {"Balance Sheet"}:
        flow_text = window_label(flow) or "the reported window"
        return (f"{flow_text} over the position at {position.period_end}"
                if position.period_end else flow_text)
    return window_label(flow)


def calculations(
    items: Items,
    *,
    sector: str,
    dividends: list[dict] | None = None,
    price: float | None = None,
    currency: str | None = None,
) -> list[Calculation]:
    """Every measure this company's reported figures support, and every one they do not."""
    out: list[Calculation] = []
    out.extend(_earnings_quality(items))
    out.extend(_per_share(items))
    out.extend(_returns(items, sector))
    if sector == "bank":
        out.extend(_bank_measures(items))
    out.extend(_dividend_measures(items, dividends or [], price))
    return out


def _earnings_quality(items: Items) -> list[Calculation]:
    """Reported earnings against earnings before unusual items. In a loss year this is the
    difference between a cyclical result and a one-off charge, and the statement carries both."""
    ni = items.find(NET_INCOME, "Income Statement")
    before = items.find(NET_INCOME_BEFORE_UNUSUAL, "Income Statement")
    extra = items.find(EXTRAORDINARY, "Income Statement")
    eps = items.find(EPS_REPORTED, "Income Statement")
    eps_before = items.find(EPS_BEFORE_UNUSUAL, "Income Statement")
    formula = "(net income - net profit before unusual items) / |net income| x 100"
    base = {"metric": "extraordinary_share_of_earnings", "formula": formula,
            "window": _window_text(items, ni, before)}
    if ni is None:
        return [Calculation(**base, missing=["no net income line in the income statement"])]
    if before is None:
        return [Calculation(**base, operands=_ops(ni), missing=[
            "no 'Net Profit Before Unusual Items' line, so reported earnings cannot be split into"
            " an underlying result and a one-off"])]
    gap = (ni.value or 0.0) - (before.value or 0.0)
    checks = []
    if extra is not None and extra.value is not None:
        agrees = abs(gap - extra.value) <= max(0.01, abs(extra.value) * 0.005)
        checks.append(
            f"reported minus before-unusual is {gap:,.2f} and the statement's extraordinary line"
            f" is {extra.value:,.2f}: " + ("they agree, so the split is the statement's own"
                                           if agrees else "they DISAGREE, so do not rely on it"))
    if eps is not None and eps_before is not None:
        checks.append(f"per share the same split is {eps.value} reported against"
                      f" {eps_before.value} before unusual items")
    ops = _ops(ni, before, extra)
    if not ni.value:
        return [Calculation(**base, operands=ops, checks=checks,
                            missing=["reported net income is zero, so a share of it is undefined"])]
    return [Calculation(
        **base, value=_pct(gap, abs(ni.value)), unit="%", operands=ops, checks=checks,
        denominator="the absolute value of reported net income, so the share reads the same for a"
                    " profit and a loss",
    )]


def _per_share(items: Items) -> list[Calculation]:
    """Earnings per share derived from the statements, and the unit check that makes the reported
    per-share figure usable.

    The denominator is the whole question. A share count is a position, so a window's figure is
    the count at its end; an average-share row is a mean over the window. The two differ exactly
    when the count moved, and the difference is invisible in the result. Where only an
    end-of-period position is available AND the count moved inside the window, this derivation is
    withheld: there is no supported denominator, and a plausible wrong number is worse than a gap.
    """
    out: list[Calculation] = []
    ni = items.find(NET_INCOME, "Income Statement")
    eps = items.find(EPS_REPORTED, "Income Statement")
    avg = items.find(AVERAGE_SHARES, "Income Statement")
    shares = items.find(SHARES, "Income Statement") or items.find(SHARES, "Balance Sheet")
    p = items.period("Income Statement")

    denominator: Cell | None = None
    basis: str | None = None
    missing: list[str] = []
    if avg is not None:
        denominator = avg
        basis = (f"'{avg.label}', the mean share count over the window — the denominator a"
                 " per-share flow requires")
    elif shares is not None:
        series = items.quarter_series(SHARES, shares.section)
        counts = [q.value for q in series if q.value is not None]
        if len(set(counts)) > 1 and p.period in ("TTM", "FY"):
            moved = ", ".join(f"{q.period_end}={q.value:,.0f}" for q in series if q.value is not None)
            missing = [
                f"the only share count is '{shares.label}', an end-of-period position, and it"
                f" moved inside the window ({moved}): a flow over a closing count is not a"
                " supported earnings per share, and there is no average-share line"
            ]
        else:
            denominator = shares
            basis = (f"'{shares.label}', a position at {shares.period_end or 'the period end'}"
                     + (", unchanged through every quarter of the window, so it equals the"
                        " window's mean" if counts and len(set(counts)) == 1 else ""))
    else:
        missing = ["no share count in either the income statement or the balance sheet"]
    if ni is None:
        missing.append("no net income line")

    window = _window_text(items, ni, denominator)
    if missing or denominator is None or ni is None or not denominator.value:
        out.append(Calculation(
            metric="eps_derived", formula="net income / share count", window=window,
            operands=_ops(ni, denominator), missing=missing or ["the share count is zero"]))
    else:
        value = round((ni.value or 0.0) / denominator.value, 4)
        checks = []
        if eps is not None and eps.value is not None:
            close = abs(value - eps.value) <= max(0.01, abs(eps.value) * 0.02)
            checks.append(
                f"the statement's own '{eps.label}' is {eps.value:,.4f} against {value:,.4f}"
                " derived: " + ("within 2%, so both are on this share count"
                                if close else "more than 2% apart, so one is on another share"
                                              " count or another unit"))
        out.append(Calculation(
            metric="eps_derived", formula="net income / share count", value=value,
            unit="currency units per share", window=window, denominator=basis,
            operands=_ops(ni, denominator), checks=checks))

    # The unit confirmation the published ratio cannot make for a loss-making company: it checks
    # EPS against a price/earnings ratio, and a company with negative earnings has none.
    if eps is not None and shares is not None and ni is not None and eps.value and shares.value:
        implied = eps.value * shares.value
        agrees = ni.value is not None and abs(implied - ni.value) <= max(1.0, abs(ni.value) * 0.02)
        out.append(Calculation(
            metric="eps_unit_confirmation",
            formula="earnings per share x share count, against reported net income",
            value=round(implied, 2), unit="millions of the reporting currency",
            window=_window_text(items, eps, ni), operands=_ops(eps, shares, ni),
            checks=[f"{eps.value:,.4f} x {shares.value:,.0f} = {implied:,.2f} against reported"
                    f" {ni.value:,.2f}: " + ("the per-share figure is in the statement's own unit"
                                             if agrees else "they do not agree, so the per-share"
                                                            " figure is on another unit and must"
                                                            " not be used")]))
    return out


def _returns(items: Items, sector: str) -> list[Calculation]:
    """Return on equity with its denominator named, which is the point of computing it here: the
    published figure cannot say which equity it divided by."""
    ni = items.find(NET_INCOME, "Income Statement")
    equity = items.find(EQUITY_COMMON, "Balance Sheet")
    equity_all = items.find(EQUITY_ALL, "Balance Sheet")
    flow, position = items.period("Income Statement"), items.period("Balance Sheet")
    base = {"metric": "roe_on_period_end_common_equity",
            "formula": "net income / total shareholders' equity x 100",
            "window": _window_text(items, ni, equity)}
    if ni is None or equity is None or not equity.value or equity.value < 0:
        # Negative equity is the case worth spelling out. A loss over negative equity comes back
        # POSITIVE and large - on one Qatari company in the live data, a loss of 125.17 over equity
        # of -18.99 gives +659%, which reads as a spectacular return and is nothing of the kind.
        # The published ratio is nulled for the same reason (ratios.RatioSources: "ROE over
        # negative equity reads as a high positive return: not meaningful"), and a figure withheld
        # with its reason is worth more here than a number no one can use.
        return [Calculation(**base, operands=_ops(ni, equity), missing=[
            "no net income line" if ni is None else
            "no total shareholders' equity line on the balance sheet" if equity is None else
            f"shareholders' equity is {equity.value:,.2f}: a return on negative equity comes back"
            " positive whatever the earnings were, so there is no meaningful figure to give"
            if equity.value < 0 else "shareholders' equity is zero"])]
    same_date = bool(equity.period_end and flow.period_end and equity.period_end == flow.period_end)
    checks = [
        f"earnings cover {window_label(flow) or 'the reported window'} and equity is struck at"
        f" {equity.period_end or position.period_end or 'the balance-sheet date'}: "
        + ("one point in time" if same_date else
           "different dates, so a trailing result sits over an older position")
    ]
    prior = items.find(EQUITY_COMMON, "Balance Sheet", items.years[1]) if len(items.years) > 1 else None
    if prior is not None and prior.value:
        average = (equity.value + prior.value) / 2.0
        checks.append(f"on average equity ({prior.period_end} and {equity.period_end}, mean"
                      f" {average:,.2f}) the same earnings give"
                      f" {_pct(ni.value or 0.0, average):,.2f}%")
    note = ""
    if equity_all is not None and equity_all.value:
        note = (f" '{equity_all.label}' ({equity_all.value:,.2f}) is NOT the denominator: it"
                " carries minority interest"
                + (" and equity sukuk" if sector == "bank" else "")
                + ", which reported net income is already net of.")
    return [Calculation(
        **base, value=_pct(ni.value or 0.0, equity.value), unit="%",
        denominator=f"'{equity.label}' at {equity.period_end or 'the balance-sheet date'}:"
                    " period-end common equity, NOT an average of opening and closing equity."
                    + note,
        operands=_ops(ni, equity), checks=checks)]


def _bank_measures(items: Items) -> list[Calculation]:
    """What a bank is actually read on. Each one is a ratio of lines a bank's statement carries,
    so none of them needs a revenue line that does not exist."""
    g = items.find
    ni, opi = g(NET_INCOME, "Income Statement"), g(OPERATING_INCOME, "Income Statement")
    nfi = g(BANK_NET_FINANCING_INCOME, "Income Statement")
    opex = g(BANK_OPERATING_EXPENSES, "Income Statement")
    prov = g(BANK_PROVISIONS, "Income Statement")
    financing = g(BANK_FINANCING, "Balance Sheet")
    performing, npl = g(BANK_PERFORMING, "Balance Sheet"), g(BANK_NPL, "Balance Sheet")
    loss, deposits = g(BANK_LOSS_PROVISION, "Balance Sheet"), g(BANK_DEPOSITS, "Balance Sheet")
    invest, due_from = g(BANK_INVESTMENTS, "Balance Sheet"), g(BANK_DUE_FROM_BANKS, "Balance Sheet")
    assets, equity = g(TOTAL_ASSETS, "Balance Sheet"), g(EQUITY_COMMON, "Balance Sheet")

    def make(metric, formula, numerator, denominator, cells, *, denom_note=None, checks=None,
             missing_note=None):
        window = _window_text(items, *cells)
        if numerator is None or not denominator:
            return Calculation(metric=metric, formula=formula, window=window,
                               operands=_ops(*cells),
                               missing=[missing_note or "an operand this measure needs is absent"])
        return Calculation(metric=metric, formula=formula,
                           value=round(numerator / denominator * 100.0, 4), unit="%",
                           window=window, denominator=denom_note, operands=_ops(*cells),
                           checks=checks or [])

    earning_assets = None
    if invest is not None and financing is not None and invest.value is not None and financing.value is not None:
        earning_assets = invest.value + financing.value

    out = [
        make("net_financing_margin", "net financing income / earning assets x 100",
             nfi.value if nfi else None, earning_assets, (nfi, invest, financing),
             denom_note="earning assets taken as investments plus net financing investments."
                        " Due from banks"
                        + (f" ({due_from.value:,.2f})" if due_from and due_from.value else "")
                        + " is excluded: it is a short-term interbank position, not an asset the"
                          " bank sets its margin on.",
             checks=[f"earning assets = {invest.value:,.2f} + {financing.value:,.2f}"]
                    if earning_assets else [],
             missing_note="net financing income or the earning-asset lines are absent"),
        make("cost_to_income", "operating expenses / operating income x 100",
             abs(opex.value) if opex and opex.value is not None else None,
             opi.value if opi else None, (opex, opi),
             denom_note="operating income, a bank's revenue analogue — the line a price-to-sales"
                        " ratio needs and does not find",
             missing_note="no operating expense or operating income line"),
        make("cost_of_risk", "credit provisions / net financing investments x 100",
             abs(prov.value) if prov and prov.value is not None else None,
             financing.value if financing else None, (prov, financing),
             denom_note="net financing investments at the balance-sheet date",
             missing_note="no provisions line or no financing-investment balance"),
        make("npl_ratio", "non-performing / (performing + non-performing) x 100",
             npl.value if npl else None,
             (performing.value + npl.value) if performing and npl and performing.value is not None
             and npl.value is not None else None, (npl, performing),
             denom_note="gross financing investments, before the loss provision",
             missing_note="the statement does not split performing from non-performing"),
        make("npl_coverage", "loss provision / non-performing financing x 100",
             abs(loss.value) if loss and loss.value is not None else None,
             npl.value if npl else None, (loss, npl),
             denom_note="non-performing financing at the balance-sheet date",
             missing_note="no loss-provision or non-performing line"),
        make("equity_to_assets", "total shareholders' equity / total assets x 100",
             equity.value if equity else None, assets.value if assets else None, (equity, assets),
             denom_note="total assets at the balance-sheet date. A leverage measure, NOT a"
                        " regulatory capital ratio: not risk-weighted, not comparable with CET1.",
             missing_note="no equity or total-asset line"),
        make("financing_to_deposits", "net financing investments / customer deposits x 100",
             financing.value if financing else None, deposits.value if deposits else None,
             (financing, deposits),
             denom_note="customer deposits only, excluding due to banks and term sukuk: the"
                        " measure is about deposit funding",
             missing_note="no financing-investment or customer-deposit line"),
    ]
    if ni is not None and opi is not None and opi.value:
        out.append(make("net_income_to_operating_income",
                        "net income / operating income x 100", ni.value, opi.value, (ni, opi),
                        denom_note="operating income, a bank's revenue analogue. Comparable with"
                                   " other banks only, never with a net margin on sales."))
    return out


def _dividend_measures(items: Items, dividends: list[dict], price: float | None) -> list[Calculation]:
    """Dividends against the earnings of the same window.

    The window is the whole difficulty. A dividend history is a list of events and the earnings
    are a window; matching them by fiscal-year label counts five quarters of dividends against
    four of earnings and reports a payout near 100%. Every dividend here is matched by its own
    date falling inside the earnings window, and the cash basis (paid) is kept apart from the
    declared basis (announced), because they answer different questions."""
    ni = items.find(NET_INCOME, "Income Statement")
    shares = items.find(SHARES, "Income Statement") or items.find(SHARES, "Balance Sheet")
    p = items.period("Income Statement")
    window = window_label(p)
    out: list[Calculation] = []
    if not items.section_of("Income Statement"):
        return [Calculation(
            metric="payout_cash",
            formula="dividends paid in the earnings window / net income over that window x 100",
            missing=["there is no income statement, so there is no earnings window to match"
                     " dividends to and no payout ratio can be computed"])]
    win = window_of(p.period, p.period_end, items.latest)
    if win is None:
        return [Calculation(
            metric="payout_cash",
            formula="dividends paid in the earnings window / net income over that window x 100",
            missing=["the income statement records no reporting period, so no dividend window"
                     " can be matched to it"])]
    start, end = win
    if not dividends:
        return [Calculation(
            metric="payout_cash",
            formula="dividends paid in the earnings window / net income over that window x 100",
            window=window, missing=[f"no dividend records between {start} and {end}"])]

    for metric, field, basis in (("payout_cash", "pay_date", "paid"),
                                 ("payout_declared", "announce_date", "declared")):
        rows = [d for d in dividends if d.get(field) and start <= str(d[field])[:10] <= end]
        formula = f"dividends {basis} in the earnings window / net income over that window x 100"
        ops: list[list[Any]] = [
            [f"dividend {basis} {str(d[field])[:10]}" + (f" ({d['note']})" if d.get("note") else ""),
             d.get("amount_mn"), "dividend history"] for d in rows
        ]
        ops += _ops(ni)
        if not rows:
            out.append(Calculation(metric=metric, formula=formula, window=window, missing=[
                f"no dividend has a {field.replace('_', ' ')} between {start} and {end}"]))
            continue
        with_amount = [d for d in rows if d.get("amount_mn") is not None]
        if len(with_amount) < len(rows):
            out.append(Calculation(metric=metric, formula=formula, window=window, operands=ops,
                                   missing=[f"{len(rows) - len(with_amount)} of {len(rows)}"
                                            " matched dividends carry no company-total amount, so"
                                            " a total would understate the payout"]))
            continue
        if ni is None or not ni.value or ni.value <= 0:
            out.append(Calculation(metric=metric, formula=formula, window=window, operands=ops,
                                   missing=["net income over the window is not positive, so a"
                                            " payout ratio is not meaningful" if ni and
                                            ni.value is not None else "no net income line"]))
            continue
        total = sum(d["amount_mn"] for d in with_amount)
        out.append(Calculation(
            metric=metric, formula=formula, value=_pct(total, ni.value), unit="%", window=window,
            denominator=f"net income over {window}, the same window the dividends are matched to",
            operands=ops,
            checks=[f"{len(rows)} dividend(s) with a {field.replace('_', ' ')} in {start}..{end}"
                    f" total {total:,.2f} against net income {ni.value:,.2f}",
                    "amounts are company totals from the dividend history, not a per-share figure"
                    " multiplied by a share count"]))

    rows = [d for d in dividends if d.get("dps") is not None and d.get("ex_date")
            and start <= str(d["ex_date"])[:10] <= end]
    ops = [[f"dividend ex {str(d['ex_date'])[:10]}", d["dps"], "dividend history"] for d in rows]
    formula = "sum of per-share dividends with an ex-date inside the earnings window"
    if not rows:
        out.append(Calculation(metric="dps_window", formula=formula, window=window,
                               missing=[f"no dividend has an ex-date between {start} and {end}"]))
        return out
    dps = sum(d["dps"] for d in rows)
    checks = [f"{len(rows)} ex-date(s) inside {start}..{end}"]
    if shares and shares.value:
        checks.append(f"against the share count the earnings use ({shares.value:,.0f}) that is"
                      f" {dps * shares.value:,.2f} in total")
    out.append(Calculation(metric="dps_window", formula=formula, value=round(dps, 6),
                           unit="currency units per share", window=window, operands=ops,
                           checks=checks))
    if price:
        out.append(Calculation(
            metric="dividend_yield_on_window",
            formula="dividends per share over the earnings window / price x 100",
            value=_pct(dps, price), unit="%", window=window,
            denominator=f"the latest close, {price:,.4f}. A yield compares a past twelve months"
                        " of dividends with today's price; it is not a forecast.",
            operands=[*ops, ["price", price, "quote"]]))
    return out


# --- the bounded dataset the Council reads ----------------------------------------------------

# A seat reads every dataset in one prompt, so this one has a budget (debate/pack.DATASET_CHARS).
# Bounding by row count in the statement's own order keeps the figures that matter and says how
# many were left out; letting the prompt truncate the JSON instead cuts a row in half and changes
# a number without saying so. Two periods: the latest and the one before, which is as far back as
# a reconstructed Tadawul grid reaches.
# P9 carries the statements themselves, so its budget is its own rather than the uniform
# per-dataset one (debate/pack.DATASET_CHARS_BY_TAG). Measured on 2026-10-29: a bank's income
# statement and balance sheet, the eight measures a bank is actually read on, five quarters of
# history and the limitations come to about 13,000 characters, and the three non-financial cases
# to between 9,000 and 11,000. Holding this dataset to 12,000 would mean dropping reported rows
# to pay for the prose that explains them, which is the wrong way round.
DATASET_BUDGET = 16_000
BOUNDED_ROWS = {"Income Statement": 30, "Balance Sheet": 34, "Cash Flow Statement": 24}
BOUNDED_QUARTER_ROWS = 8
BOUNDED_YEARS = 2

# The flow lines a quarterly series is worth carrying for: enough to see whether a result is
# turning, few enough to fit. Anything not here is still in the statements above.
QUARTERLY_INTEREST = (
    *REVENUE, *GROSS_INCOME, *OPERATING_INCOME, "Operating Expenses",
    *NET_INCOME_BEFORE_UNUSUAL, *EXTRAORDINARY, *NET_INCOME, *EPS_REPORTED,
)

# Rows the budget trim must not drop: the totals, the earnings, the share count and the per-share
# figures. Everything a measure here divides is one of these, and a trim that removed one would
# leave a calculation whose operands are nowhere in the statements beside it.
PROTECTED_GROUPS = ((
    *REVENUE, *GROSS_INCOME, *OPERATING_INCOME, *NET_INCOME, *NET_INCOME_BEFORE_UNUSUAL,
    *EXTRAORDINARY, *EPS_REPORTED, *EPS_BEFORE_UNUSUAL, *SHARES, *AVERAGE_SHARES,
    *EQUITY_COMMON, *EQUITY_ALL, *TOTAL_ASSETS, *TCA, *BANK_NET_FINANCING_INCOME,
    *BANK_PROVISIONS, *BANK_FINANCING, *BANK_PERFORMING, *BANK_NPL, *BANK_LOSS_PROVISION,
    *BANK_DEPOSITS, *BANK_INVESTMENTS,
    "Cost of Sales", "Operating Expenses", "Financing Expense", "EBITDA", "Total Liabilities",
    "Total Current liabilities", "Total Non-Current Assets", "Total Non-Current Liabilities",
    "Cash & Cash Equivalents", "Short-term Debt", "Long-Term Debt", "Total Debt",
))


def is_protected(label: str) -> bool:
    """Is this a row the budget trim must keep? Through the same matcher as every other lookup,
    so a line protected in English is protected in Arabic."""
    return any(matches(label, entry) for entry in PROTECTED_GROUPS)


class BoundedStatement(BaseModel):
    section: str
    period: str | None
    period_end: str | None
    aggregation: str | None
    source_columns: list[str] = []
    columns: list[str]  # ["label", "2026", "2025"]
    rows: list[list[Any]]
    rows_omitted: int = 0
    row_rules: dict[str, str] = {}  # label -> rule, only where it differs from `aggregation`


class QuarterSeries(BaseModel):
    section: str
    note: str
    columns: list[str]  # ["label", "2025-06", ...]
    rows: list[list[Any]]


class EvidenceDataset(BaseModel):
    """P9. Reported statements, the measures they support, and the limits of both."""

    ticker: str
    currency: str | None
    unit: str
    basis: str
    source: str
    sector: str
    statements: list[BoundedStatement]
    quarters: QuarterSeries | None
    calculations: list[Calculation]
    limitations: list[str]


def bounded_statements(items: Items) -> list[BoundedStatement]:
    out: list[BoundedStatement] = []
    years = items.years[:BOUNDED_YEARS]
    for section in items.sections():
        in_section = [r for r in items.rows if r.section == section and r.fiscal_year in years]
        if not in_section:
            continue
        cols = [y for y in years if any(r.fiscal_year == y and r.value is not None for r in in_section)]
        by_index: dict[int, dict[int, Cell]] = {}
        for r in in_section:
            by_index.setdefault(r.item_index, {})[r.fiscal_year] = r
        latest = cols[0] if cols else None

        def key(item: tuple[int, dict[int, Cell]], latest: int | None = latest) -> tuple[int, int]:
            index, per_year = item
            own = per_year.get(latest) if latest is not None else None
            return (0 if own is not None and own.value is not None else 1, index)

        ordered = sorted(by_index.items(), key=key)
        limit = BOUNDED_ROWS.get(section, 24)
        # The row cap takes the protected lines first and fills the rest in the statement's own
        # order. Taking the first N in order would drop whatever sits at the end of the section,
        # and on a Tadawul balance sheet that is the share count and the book value per share —
        # the share count being the denominator of every per-share measure here. A statement
        # that omits the figure its own calculations divide by is worse than a shorter one.
        def labelled(item: tuple[int, dict[int, Cell]]) -> str:
            cell = next((c for c in item[1].values() if c is not None), None)
            return cell.label if cell else ""

        keep = [it for it in ordered if is_protected(labelled(it))]
        rest = [it for it in ordered if not is_protected(labelled(it))]
        kept = keep[:limit] + rest[: max(0, limit - len(keep))]
        omitted = max(0, len(ordered) - len(kept))
        p = items.period(section, latest)
        rows: list[list[Any]] = []
        row_rules: dict[str, str] = {}
        for _index, per_year in sorted(kept, key=lambda kv: kv[0]):
            cell = next((c for c in per_year.values() if c is not None), None)
            if cell is None:
                continue
            rows.append([cell.label, *[(per_year[y].value if y in per_year else None) for y in cols]])
            own = per_year.get(latest) if latest is not None else None
            if own is not None and own.rule and own.rule != p.aggregation:
                row_rules[cell.label] = own.rule
        out.append(BoundedStatement(
            section=section, period=p.period, period_end=p.period_end, aggregation=p.aggregation,
            source_columns=p.source_columns, columns=["label", *[str(y) for y in cols]],
            rows=rows, rows_omitted=omitted, row_rules=row_rules))
    return out


def bounded_quarters(items: Items) -> QuarterSeries | None:
    """The single quarters behind the annual figures, for the lines worth a trend.

    These are reported facts, each one column of the source grid, and they are the only way to
    tell a result that is turning from one that is not. A standalone quarter is NOT a share of the
    annual figure: it is what the company reported for those three months."""
    ends = items.quarters("Income Statement")
    if not ends:
        return None
    rows: list[list[Any]] = []
    seen: set[str] = set()
    for label in QUARTERLY_INTEREST:
        if label in seen or len(rows) >= BOUNDED_QUARTER_ROWS:
            continue
        series = items.quarter_series((label,), "Income Statement")
        if not series:
            continue
        seen.add(label)
        by_end = {q.period_end: q.value for q in series}
        rows.append([label, *[by_end.get(e) for e in ends]])
    if not rows:
        return None
    return QuarterSeries(
        section="Income Statement",
        note="each column is one quarter as reported, standalone and not cumulative; the annual"
             " figures above are the sum of four consecutive columns of this kind",
        columns=["label", *ends], rows=rows)


def limitations_of(items: Items, sector: str) -> list[str]:
    """What this evidence cannot answer. Said plainly, because a seat that does not know a gap
    exists will argue around it."""
    out: list[str] = []
    if "Cash Flow Statement" not in set(items.sections()):
        out.append(
            "NO CASH FLOW STATEMENT: the source's pages for this company carry an income"
            " statement and a balance sheet only. Operating cash flow, capital expenditure, free"
            " cash flow and cash conversion cannot be computed from anything here, and dividend"
            " cover can be tested against earnings only, never against cash.")
    if len({r.fiscal_year for r in items.rows if r.section == "Income Statement"}) < 2:
        p = items.period("Income Statement")
        out.append(
            f"ONE INCOME-STATEMENT WINDOW: {window_label(p) or 'one window'} is available and the"
            " prior year's income statement is not, because the source serves a rolling"
            " five-quarter grid. Year-on-year revenue or earnings cannot be compared from this"
            " dataset; the single quarters are the history there is.")
    flow, position = items.period("Income Statement"), items.period("Balance Sheet")
    if flow.period_end and position.period_end and flow.period_end != position.period_end:
        out.append(f"The income statement covers a window ending {flow.period_end} while the"
                   f" balance sheet is struck at {position.period_end}: any ratio of a flow over"
                   " a position mixes the two dates.")
    if sector == "bank":
        out.append(
            "BANK: revenue, gross margin, net margin on sales, price to sales, current ratio,"
            " interest coverage, return on invested capital, EV/EBITDA and free cash flow yield"
            " are not defined for this company and are not supplied. What it is read on is in"
            " `calculations`. Equity to assets there is leverage, not regulatory capital.")
    return out


def encoded_length(ds: EvidenceDataset) -> int:
    return len(json.dumps(ds.model_dump(), ensure_ascii=False, default=str))


def fit(ds: EvidenceDataset, budget: int = DATASET_BUDGET) -> EvidenceDataset:
    """Bring the dataset inside its character budget, and record what that cost.

    Statement sub-detail goes first, from the end of the longest section, skipping the lines any
    calculation divides (is_protected) — a trim that removed one of those would leave a
    calculation whose operands are nowhere in the statements beside it. Calculations and
    limitations are never trimmed: they are what says the numbers mean. The alternative to
    trimming is the prompt truncating the JSON mid-row, which changes a figure silently."""
    while encoded_length(ds) > budget:
        longest = max(
            (s for s in ds.statements
             if any(not is_protected(r[0]) for r in s.rows)),
            key=lambda s: len(json.dumps(s.model_dump(), ensure_ascii=False, default=str)),
            default=None,
        )
        if longest is None:
            if ds.quarters and len(ds.quarters.rows) > 3:
                ds.quarters.rows.pop()
                continue
            return ds  # nothing left that may be dropped; the caller's budget is too small
        for i in range(len(longest.rows) - 1, -1, -1):
            if not is_protected(longest.rows[i][0]):
                longest.row_rules.pop(longest.rows[i][0], None)
                longest.rows.pop(i)
                longest.rows_omitted += 1
                break
    return ds


def dataset_of(
    items: Items,
    *,
    ticker_key: str,
    sector: str,
    currency: str | None,
    dividends: list[dict] | None = None,
    price: float | None = None,
    budget: int = DATASET_BUDGET,
) -> EvidenceDataset:
    return fit(EvidenceDataset(
        ticker=ticker_key,
        currency=currency,
        unit="millions of the reporting currency, except share counts (millions of shares) and"
             " per-share figures (currency units per share)",
        basis="`statements` and `quarters` are reported: figures the source published, aggregated"
              " by the stated rule, nothing estimated or carried forward. `calculations` are"
              " derived here and carry their formula, operands and window — where one carries"
              " `missing` instead of a value there is no number to use. Rule-based votes are a"
              " different dataset and are not evidence.",
        source="company financial statements collected from the data provider's company pages."
               " Where `aggregation` says the figures were reconstructed, `source_columns` names"
               " the quarter-end columns added together.",
        sector=sector,
        statements=bounded_statements(items),
        quarters=bounded_quarters(items),
        calculations=calculations(items, sector=sector, dividends=dividends, price=price,
                                  currency=currency),
        limitations=limitations_of(items, sector),
    ), budget)
