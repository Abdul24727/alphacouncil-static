"""Stand-in Copilot used while no AI model is configured.

It is not a language model. It recognises a few question types (dividends,
valuation, price, council, news, peers) in English or Arabic, answers only
from attached panel data and the same database tools Claude would use, and
cites them the same way. Every answer says it is a stand-in.
"""

from collections.abc import AsyncIterator
from datetime import date
from typing import Any

from fastapi import Request
from starlette.concurrency import run_in_threadpool

from . import tools
from .context import ChatInput, sources
from .stream import Writer, new_id

INTENTS: dict[str, tuple[str, ...]] = {
    "dividend": ("dividend", "payout", "yield", "توزيع", "التوزيعات", "توزيعات", "عائد التوزيع"),
    "valuation": ("p/e", "pe ", "valuation", "cheap", "expensive", "multiple", "مكرر", "تقييم"),
    "council": ("council", "seat", "vote", "المجلس", "مقعد", "تصويت"),
    "news": ("news", "disclosure", "announce", "أخبار", "خبر", "إفصاح"),
    "peers": ("peer", "compare", "competitor", "sector", "أقران", "مقارنة", "منافس"),
    "price": ("price", "perform", "return", "chart", "trend", "سعر", "أداء", "اتجاه"),
}

T = {
    "en": {
        "standin": "Stand-in answer: no AI model is configured yet, so this is assembled by fixed rules from the attached panels and the database.",
        "no_ticker": "I could not tell which company you mean. Attach a panel or name a ticker, for example 2222 or Al Rajhi.",
        "unknown": "The stand-in can answer questions about dividends, valuation, price, the council, news and peers. The full Copilot arrives once an AI model is configured.",
        "yield": "{name}'s dividend yield is {value}% {tag}.",
        "no_yield": "There is no dividend yield for {name} in the attached panels or the database.",
        "last_div": "The latest recorded dividend is {cur} {dps} per share ({period}), ex-date {ex}, paid {pay} [DB].",
        "div_count": "{n} dividend payments are recorded; the table lists the latest {k}.",
        "next_div": "Announced next: {cur} {dps} per share ({period}), ex-date {ex} [DB].",
        "no_divs": "No dividend payments are recorded for {name} in the database [DB].",
        "pe": "{name} trades at a P/E of {pe}x and a P/B of {pb}x {tag}.",
        "no_pe": "There is no P/E for {name} in the attached panels or the database.",
        "price": "Over {range}, {name}'s close moved from {cur} {first} ({frm}) to {cur} {last} ({to}), {chg}% [DB].",
        "council": "The council has {b} bullish, {n} neutral and {r} bearish seats for {name}; {a} abstain [DB].",
        "news_head": "Latest items touching {name} [DB]:",
        "no_news": "No news or disclosures for {name} in the database [DB].",
        "peers": "{name}'s largest same-sector peers are {list} [DB].",
        "no_peers": "No same-sector peers for {name} in the database [DB].",
        "div_title": "{symbol} dividends",
        "div_cols": ["Period", "Ex-date", "Paid", "Per share ({cur})"],
        "fu": {
            "dividend": ["How has the dividend per share changed over the last two years?", "What is the payout ratio?", "Show the price over the last year"],
            "valuation": ["How does the P/E compare with peers?", "What does the council's value seat say?"],
            "price": ["What moved the price recently?", "Show the 5-year chart"],
            "council": ["Why does the momentum seat vote that way?", "What is the dividend yield?"],
            "news": ["Summarise the latest disclosure", "How did the price react?"],
            "peers": ["Compare P/E across these peers", "Which peer has the highest dividend yield?"],
        },
    },
    "ar": {
        "standin": "إجابة بديلة: لم يُضبط نموذج ذكاء اصطناعي بعد، لذا جُمعت هذه الإجابة بقواعد ثابتة من اللوحات المرفقة وقاعدة البيانات.",
        "no_ticker": "لم أتمكن من تحديد الشركة المقصودة. أرفق لوحة أو اذكر رمزًا مثل 2222 أو الراجحي.",
        "unknown": "تجيب النسخة البديلة عن أسئلة التوزيعات والتقييم والسعر والمجلس والأخبار والأقران. يتوفر المساعد الكامل بعد ضبط نموذج الذكاء الاصطناعي.",
        "yield": "عائد التوزيعات لسهم {name} يبلغ {value}% {tag}.",
        "no_yield": "لا يوجد عائد توزيعات لسهم {name} في اللوحات المرفقة أو قاعدة البيانات.",
        "last_div": "آخر توزيع مسجل {dps} {cur} للسهم ({period})، تاريخ الاستحقاق {ex}، وتاريخ الصرف {pay} [DB].",
        "div_count": "سُجلت {n} دفعات توزيع، ويعرض الجدول آخر {k} منها.",
        "next_div": "التوزيع القادم المعلن: {dps} {cur} للسهم ({period})، تاريخ الاستحقاق {ex} [DB].",
        "no_divs": "لا توجد توزيعات مسجلة لسهم {name} في قاعدة البيانات [DB].",
        "pe": "يتداول سهم {name} بمكرر ربحية {pe} ومكرر قيمة دفترية {pb} {tag}.",
        "no_pe": "لا يوجد مكرر ربحية لسهم {name} في اللوحات المرفقة أو قاعدة البيانات.",
        "price": "خلال {range} تحرك إغلاق {name} من {first} {cur} ({frm}) إلى {last} {cur} ({to})، بتغير {chg}% [DB].",
        "council": "للمجلس {b} مقاعد إيجابية و{n} محايدة و{r} سلبية لسهم {name}، و{a} ممتنعة [DB].",
        "news_head": "آخر الأخبار المتعلقة بسهم {name} [DB]:",
        "no_news": "لا توجد أخبار أو إفصاحات لسهم {name} في قاعدة البيانات [DB].",
        "peers": "أكبر أقران {name} في القطاع: {list} [DB].",
        "no_peers": "لا يوجد أقران في القطاع لسهم {name} في قاعدة البيانات [DB].",
        "div_title": "توزيعات {symbol}",
        "div_cols": ["الفترة", "تاريخ الاستحقاق", "تاريخ الصرف", "للسهم ({cur})"],
        "fu": {
            "dividend": ["كيف تغير التوزيع للسهم خلال السنتين الماضيتين؟", "ما نسبة التوزيع؟", "اعرض السعر خلال السنة الماضية"],
            "valuation": ["كيف يقارن مكرر الربحية بالأقران؟", "ماذا يقول مقعد القيمة في المجلس؟"],
            "price": ["ما الذي حرك السعر مؤخرًا؟", "اعرض الرسم لخمس سنوات"],
            "council": ["لماذا يصوت مقعد الزخم بهذا الشكل؟", "ما عائد التوزيعات؟"],
            "news": ["لخص آخر إفصاح", "كيف تفاعل السعر؟"],
            "peers": ["قارن مكرر الربحية بين هؤلاء الأقران", "أي الأقران لديه أعلى عائد توزيعات؟"],
        },
    },
}


def _period(note: str | None) -> str:
    """'Q 3 _ 2025 (including performance-linked ...)' -> 'Q3 2025'."""
    head = (note or "").split("(")[0].replace(" _ ", " ").strip()
    return head.replace("Q ", "Q", 1) if head.startswith("Q ") else head


def detect_intent(question: str) -> str | None:
    q = f" {question.lower()} "
    for intent, words in INTENTS.items():
        if any(w in q for w in words):
            return intent
    return None


def _find(data: Any, *path: str) -> Any:
    for key in path:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


class _Run:
    """One stand-in answer: records steps as tool calls so the UI shows its reasoning."""

    def __init__(self, request: Request, chat: ChatInput, w: Writer):
        self.request, self.chat, self.w = request, chat, w
        self.parts: list[str] = []

    async def tool(self, name: str, args: dict[str, Any]) -> Any:
        call = new_id("call")
        self.parts.append(self.w.tool_call(call, name, args))
        out = await run_in_threadpool(tools.run, self.request, name, args)
        self.parts.append(self.w.tool_result(call, {"error": out["error"]} if isinstance(out, dict) and "error" in out else {"ok": True}))
        return out

    def note(self, text: str) -> None:
        self.parts.append(self.w.reasoning(text))
        self.parts.append(self.w.close_reasoning())


async def standin_stream(request: Request, chat: ChatInput) -> AsyncIterator[str]:
    w = Writer()
    lang = "ar" if chat.locale == "ar" else "en"
    s = T[lang]
    yield w.start()
    yield w.data("model", {"name": "stand-in", "stand_in": True})
    yield w.data("sources", sources(chat))
    yield w.start_step()

    run = _Run(request, chat, w)
    intent = detect_intent(chat.question)
    tags = chat.tags
    run.note(
        f"Intent: {intent or 'unrecognised'}. Attached panels: "
        + (", ".join(f"[{t}] {p.title}" for t, p in tags.items()) or "none")
    )

    # Which ticker: an attached panel's, the page's, or a name in the question.
    ticker = next((p.ticker for p in chat.panels if p.ticker), None) or chat.ticker
    if not ticker:
        hits = await run.tool("search_tickers", {"query": chat.question[:64]})
        ticker = hits[0]["slug"] if isinstance(hits, list) and hits else None

    lines: list[str] = [s["standin"], ""]
    table: dict[str, Any] | None = None
    chart: dict[str, Any] | None = None

    if intent is None:
        lines.append(s["unknown"])
    elif not ticker:
        lines.append(s["no_ticker"])
    else:
        overview = await run.tool("get_ticker_overview", {"ticker": ticker})
        ref = overview.get("ticker", {}) if isinstance(overview, dict) else {}
        name = (ref.get("name_ar") if lang == "ar" else ref.get("name_en")) or ref.get("name_en") or ref.get("symbol") or ticker
        cur = ref.get("currency") or ""

        def from_panels(*path: str) -> tuple[Any, str | None]:
            for tag, p in tags.items():
                v = _find(p.data, *path)
                if v is not None:
                    return v, f"[{tag}]"
            return None, None

        if intent == "dividend":
            value, tag = from_panels("valuation", "dividend_yield_pct")
            if value is None:
                value, tag = _find(overview, "valuation", "dividend_yield_pct"), "[DB]"
            lines.append(s["yield"].format(name=name, value=f"{value:.2f}", tag=tag) if value is not None else s["no_yield"].format(name=name))
            corp = await run.tool("get_dividends", {"ticker": ticker})
            all_divs = corp.get("dividends", []) if isinstance(corp, dict) else []
            today = date.today().isoformat()
            divs = [x for x in all_divs if (x.get("ex_date") or x.get("announce_date") or "") <= today]
            upcoming = sorted((x for x in all_divs if (x.get("ex_date") or "") > today), key=lambda x: x["ex_date"])
            if upcoming:
                u = upcoming[0]
                lines.append(s["next_div"].format(cur=cur, dps=u["dps"], period=_period(u.get("note")), ex=u["ex_date"]))
            if divs:
                d = divs[0]
                lines.append(s["last_div"].format(cur=cur, dps=d["dps"], period=_period(d.get("note")), ex=d.get("ex_date") or "—", pay=d.get("pay_date") or "—"))
                k = min(len(divs), 8)
                lines.append(s["div_count"].format(n=len(divs), k=k))
                table = {
                    "id": new_id("table"),
                    "title": s["div_title"].format(symbol=ref.get("symbol", ticker)),
                    "columns": [c.format(cur=cur) for c in s["div_cols"]],
                    "rows": [[_period(x.get("note")), x.get("ex_date"), x.get("pay_date"), x.get("dps")] for x in divs[:k]],
                    "source": "DB",
                    "unverified": [],
                }
            else:
                lines.append(s["no_divs"].format(name=name))
        elif intent == "valuation":
            pe, tag = from_panels("valuation", "pe")
            pb, _ = from_panels("valuation", "pb")
            if pe is None:
                pe, pb, tag = _find(overview, "valuation", "pe"), _find(overview, "valuation", "pb"), "[DB]"
            lines.append(s["pe"].format(name=name, pe=f"{pe:.2f}", pb=f"{pb:.2f}" if pb is not None else "—", tag=tag) if pe is not None else s["no_pe"].format(name=name))
        elif intent == "price":
            summ = await run.tool("get_price_summary", {"ticker": ticker, "range": "1Y"})
            if summ.get("has_history", True) and "error" not in summ:
                lines.append(s["price"].format(range="1Y", name=name, cur=cur, first=summ["first_close"], last=summ["last_close"], frm=summ["from"], to=summ["to"], chg=summ["change_pct"]))
                chart = {"id": new_id("chart"), "ticker": ref.get("slug", ticker), "ticker_key": ref.get("ticker_key"), "range": "1Y"}
        elif intent == "council":
            c = await run.tool("get_council", {"ticker": ticker})
            n = c.get("counts", {}) if isinstance(c, dict) else {}
            lines.append(s["council"].format(name=name, b=n.get("bullish", 0), n=n.get("neutral", 0), r=n.get("bearish", 0), a=n.get("abstain", 0)))
        elif intent == "news":
            items = await run.tool("get_news", {"ticker": ticker, "limit": 4})
            if isinstance(items, list) and items:
                lines.append(s["news_head"].format(name=name))
                lines += [f"- {(i.get('date') or '')[:10]} {i.get('title')}" for i in items]
            else:
                lines.append(s["no_news"].format(name=name))
        elif intent == "peers":
            p = await run.tool("get_peers", {"ticker": ticker})
            peers = p.get("peers", []) if isinstance(p, dict) else []
            if peers:
                names = [(x["ticker"].get("name_ar") if lang == "ar" else x["ticker"].get("name_en")) or x["ticker"]["symbol"] for x in peers[:4]]
                lines.append(s["peers"].format(name=name, list="، ".join(names) if lang == "ar" else ", ".join(names)))
            else:
                lines.append(s["no_peers"].format(name=name))

    for chunk in run.parts:
        yield chunk
    yield w.text("\n".join(lines))
    if table:
        yield w.data("table", table)
    if chart:
        yield w.data("chart", chart)
    yield w.data("followups", {"questions": s["fu"].get(intent or "dividend", [])[:3]})
    yield w.finish_step()
    yield w.finish()
