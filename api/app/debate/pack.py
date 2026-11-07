"""The data every seat reads: the Copilot's database tools for one ticker, run once per session.

Each dataset gets a citation tag (P1, P2, …), like an attached panel in the Copilot, so the
Copilot's checks attribute every figure to the dataset it was read from. Nothing here computes
a market figure; the only change is the one documented for returns below.
"""

import asyncio
import json
from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from ..copilot.context import numbers_in
from ..universe import Ticker

DATASET_CHARS = 12_000  # per dataset, after JSON encoding (the Copilot's PANEL_CHARS)
# P9 is the only dataset that carries the financial statements themselves, and it bounds itself
# (evidence.DATASET_BUDGET) rather than being cut here: a truncation lands mid-row and changes a
# figure without saying so, while the dataset's own trim drops whole rows and records how many.
# The budget is larger because a bank's statements plus the measures a bank is read on do not fit
# in 12,000; see evidence.DATASET_BUDGET for the measurements.
DATASET_CHARS_BY_TAG = {"P9": 16_000}

# tag, tool, arguments, title (en, ar)
DATASETS: tuple[tuple[str, str, dict[str, Any], str, str], ...] = (
    ("P1", "get_ticker_overview", {}, "Quote, valuation, returns and technicals", "السعر والتقييم والعوائد والمؤشرات الفنية"),
    ("P2", "get_fundamentals", {}, "Fundamentals, with each metric's sector standing where the peer group supports one", "الأساسيات، مع ترتيب كل مقياس داخل القطاع حيث تسمح مجموعة المقارنة بذلك"),
    ("P3", "get_dividends", {}, "Dividends and capital changes", "التوزيعات وتغيرات رأس المال"),
    ("P4", "get_council", {}, "Council seats (rule-based votes)", "مقاعد المجلس (تصويت بالقواعد)"),
    ("P5", "get_peers", {}, "Sector peers", "الشركات المماثلة في القطاع"),
    ("P6", "get_news", {"limit": 8}, "Latest news and disclosures", "آخر الأخبار والإفصاحات"),
    ("P7", "get_price_summary", {"range": "1Y"}, "Price summary, 1 year", "ملخص السعر، سنة"),
    ("P8", "get_price_summary", {"range": "5Y"}, "Price summary, 5 years", "ملخص السعر، خمس سنوات"),
    # P9 is the only dataset that carries the reporting period of every figure, so it is the one
    # a seat must read before comparing two years or dividing one figure by another.
    ("P9", "get_financial_statements", {}, "Financial statements, their periods, and the measures they support", "القوائم المالية وفتراتها والمؤشرات المحتسبة منها"),
)

# briefs.return_*, vol_1y and max_drawdown are fractions (0.155). Seats talk in percents, so the
# overview carries them as percents too (x100, nothing rounded but float noise), and only those:
# a seat quoting "15.5%" then matches the data, and "0.155" is not on offer to be misread.
FRACTIONS = ("return_1m", "return_3m", "return_6m", "return_12m", "vol_1y", "max_drawdown")


class Source(BaseModel):
    title_en: str
    title_ar: str
    ok: bool  # False when the tool answered with an error (for example Pro-only data on Free)


class Pack(BaseModel):
    ticker_key: str
    slug: str
    header: str
    fetched_at: str
    data: dict[str, Any]  # tag -> tool result
    sources: dict[str, Source]

    def numbers(self) -> dict[str, set[str]]:
        """Tag -> every number in that dataset (context.numbers_in), for missing_citations."""
        return {tag: numbers_in(value) for tag, value in self.data.items()}

    def seen(self) -> set[str]:
        return numbers_in(list(self.data.values()))

    def prompt(self) -> str:
        lines = [self.header]
        note = no_statements_note(self.data)
        if note:
            lines.append(note)
        for tag, value in self.data.items():
            text = json.dumps(value, ensure_ascii=False, default=str)
            budget = DATASET_CHARS_BY_TAG.get(tag, DATASET_CHARS)
            if len(text) > budget:
                text = text[:budget] + " …[truncated]"
            lines.append(f"[{tag}] {self.sources[tag].title_en}: {text}")
        return "\n".join(lines)


def no_statements_note(data: dict[str, Any]) -> str | None:
    """Said once, beside the header, when the pack holds no financial statements.

    Five of the six seats' briefs send them to [P9]'s statements. In the 2026-11-07 comparison the
    packs had no P9, nothing said so, and 22 of the room's 23 invented figures were statement data
    the briefs place in P9 (`docs/eval/presenter-comparison/audit.md` §5). A live pack has a P9, but
    for 50 of 714 companies on 2026-11-07 it holds no statements. In each of these cases the room is
    told plainly, here, rather than left to notice an absence."""
    p9 = data.get("P9")
    if p9 is None:
        why = "the pack has no [P9]"
    elif isinstance(p9, dict) and "error" in p9:
        why = "[P9] holds an error, not statements"
    elif isinstance(p9, dict) and not p9.get("statements"):
        why = "[P9] holds none for this company"
    else:
        return None
    return (
        f"NO FINANCIAL STATEMENTS IN THIS PACK ({why}): no income statement, balance sheet, cash"
        " flow statement or quarterly results for this company. Where a brief sends a seat to"
        " [P9]'s statements, the seat says plainly that they are not available and argues from the"
        " datasets that are here. Every figure a seat quotes must be one these datasets show: a"
        " statement figure stated, estimated or recalled from memory is invented, whatever tag it"
        " carries."
    )


def _percent_returns(overview: Any) -> Any:
    if not isinstance(overview, dict) or not isinstance(overview.get("returns"), dict):
        return overview
    r = overview["returns"]
    overview["returns"] = {
        f"{k}_pct" if k in FRACTIONS else k: (round(v * 100, 10) if k in FRACTIONS and isinstance(v, (int, float)) else v)
        for k, v in r.items()
    }
    return overview


def _standing(fundamentals: Any) -> Any:
    """The API's `sector_percentile` (and each group's `score`) is the pipeline's standing score, which
    is flipped for metrics where lower is better (compute_gauge_scores: `pct = 1 - pct`). Under its own
    name it reads as a plain percentile, and in the paid A-vs-P comparison of 2026-11-07 both arms read
    Al Rajhi's 22.7 on debt to equity as "less leveraged than most peers", the opposite of what it
    means. So the room gets it as `sector_standing`, which the header defines. Nothing is recomputed."""
    if not isinstance(fundamentals, dict) or not isinstance(fundamentals.get("groups"), list):
        return fundamentals
    for g in fundamentals["groups"]:
        if not isinstance(g, dict):
            continue
        if "score" in g:
            g["sector_standing"] = g.pop("score")
        for m in g.get("metrics") or []:
            if isinstance(m, dict) and "sector_percentile" in m:
                m["sector_standing"] = m.pop("sector_percentile")
    return fundamentals


def header_of(t: Ticker, fetched_at: str) -> str:
    name = t.name_en or t.name_ar or t.symbol
    return (
        f"DATA PACK. Company: {name}"
        + (f" / {t.name_ar}" if t.name_ar and t.name_ar != name else "")
        + f". Symbol {t.symbol} on {t.exchange}, listing currency {t.currency or 'unknown'}, sector {t.sector_en or 'unknown'}."
        f" Fetched {fetched_at} from AlphaCouncil's database."
        " Units: market_cap_mn and statement lines are millions of the listing currency; fields ending in _pct are percents."
        " In [P2], sector_standing is a metric's standing in its peer class from 0 to 100, and HIGHER IS BETTER for"
        " every metric: where higher_is_better is false (debt_equity, ev_ebitda, ps, payout), a high standing means"
        " a LOW value, so a standing of 20 on debt_equity means more debt relative to equity than about 80 per cent"
        " of the peer class."
        " A dataset holding an error has no data for this company."
        # The distinction a seat cannot recover once it is lost: which figures were reported,
        # which were computed, and which are only an opinion a threshold produced.
        " THREE KINDS OF THING ARE IN THIS PACK AND THEY ARE NOT INTERCHANGEABLE."
        " Reported: figures the source published, in [P9] under `statements` and `quarters`,"
        " each with the period it covers and the date it was struck."
        " Derived: figures computed from those, in [P9] under `calculations` and in [P2] where a"
        " metric carries a `formula` and `operands` — quote the formula when you use one, and"
        " where a calculation carries `missing` instead of a value, there is no number to use."
        " Opinion: [P4] is rule-based votes from fixed thresholds, not measurements; it is not"
        " evidence for or against anything, and a seat must not cite it as a figure."
        " [P9] `limitations` says what this company's data cannot answer at all."
    )


def _news(items: Any, locale: str) -> Any:
    """News without links and ids, with the summary in the session's language (the other if missing)."""
    if not isinstance(items, list):
        return items
    first, other = ("summary_ar", "summary_en") if locale == "ar" else ("summary_en", "summary_ar")
    keep = ("date", "section", "title", "title_en", "impact")
    return [{**{k: i.get(k) for k in keep}, "summary": i.get(first) or i.get(other)} for i in items if isinstance(i, dict)]


async def build(request: Request, t: Ticker, locale: str = "en") -> Pack:
    """Every dataset for one ticker, read in parallel through the Copilot's tools."""
    # Imported here, not at module scope. `copilot.tools` reaches into app.routers and through it
    # the market database, which made `app.debate.pack` - and so the whole eval harness -
    # unimportable without the full application. `tools` is used on one line in this function and
    # nowhere else in the module, so the import belongs where it is used. No behaviour changes:
    # `build` runs at request time, with the application already loaded.
    from ..copilot import tools

    calls = [(tag, name, {"ticker": t.ticker_key, **args}) for tag, name, args, _, _ in DATASETS]
    results = await asyncio.gather(*(run_in_threadpool(tools.run, request, name, args) for _, name, args in calls))
    data: dict[str, Any] = {}
    sources: dict[str, Source] = {}
    for (tag, name, _), result, (_, _, _, en, ar) in zip(calls, results, DATASETS, strict=True):
        if name == "get_ticker_overview":
            result = _percent_returns(result)
        if name == "get_news":
            result = _news(result, locale)
        if name == "get_fundamentals":
            result = _standing(result)
        data[tag] = result
        sources[tag] = Source(title_en=en, title_ar=ar, ok=not (isinstance(result, dict) and "error" in result))
    fetched = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    return Pack(ticker_key=t.ticker_key, slug=t.slug, header=header_of(t, fetched), fetched_at=fetched, data=data, sources=sources)
