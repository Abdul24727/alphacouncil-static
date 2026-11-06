# Output 07: review 06's step, the dollar as a currency unit in pair_from_gulf.py

Commit `509d7bf`. Record: `docs/arabic-statement-labels-2026-11-03.md`, "The dollar as a currency unit".

**Reproduced as review 06 said:** `saudi_arabic("Par Value (Riyal)", "القيمة الاسمية (دولار)")` gave
"القيمة الاسمية (دولار) (ريال)", because `CURRENCY_AR` had no dollar.

**The change** (`scripts/argaam_ar_labels/pair_from_gulf.py`):
- `CURRENCY_AR` gains `دولار(?: أمريكي)?`. The module docstring says why: five USD-traded Bahrain listings,
  and no harvested page carries a dollar label as of 2026-11-06.
- `from bs4 import BeautifulSoup` moved inside `rows()`, so the label rule imports and tests without bs4
  (this machine has none; the server venv does).

**Tests:** `scripts/argaam_ar_labels/test_pair_from_gulf.py` (unittest; `python -X utf8 <file>`), 4 tests,
OK:
- the dollar becomes "(ريال)" / "(هللة)", or goes when the English names no unit, including "دولار أمريكي";
- every existing Gulf currency (درهم, فلس, بيسة, ريال قطري/عماني/سعودي, ريال, دينار كويتي/بحريني, دينار,
  هللة) still maps the same, as subtests;
- non-currency parentheses stay ("(مليون)", "( المصاريف )");
- a label without a unit gets the English's unit and nothing else.

**Live effect, checked:**
- The database has no row in any year whose label contains دولار, USD or Dollar.
- The dictionary has none either.
- Old (HEAD) and new scripts run over every harvested page on the server give **byte-identical** output:
  27,096 bytes, sha256 `7e5e63cfc8f1…`. Both finished 23:51 UTC, before the nightly. Read-only, in
  `/tmp/f16/pfg`.

So this is a guard for future harvests; nothing shown changes.

**Still pending:**
- F-16's check after the 05:00 UTC publish, and the label sweep re-run.
- Nothing is released or pushed. That is the owner's go-ahead.

**The question for the review:** is this sound, and what is the single next step?
