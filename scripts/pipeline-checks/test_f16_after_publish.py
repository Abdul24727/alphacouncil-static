"""The F-16 checker's data items on in-memory databases (review 20): missing data must FAIL, never pass.

    python -B -X utf8 scripts/pipeline-checks/test_f16_after_publish.py
"""
import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f16_after_publish as f16  # noqa: E402

CF_LINE = f16.CASH_FLOW_LINES[0]


def db(balance: dict[str, int], cash_flow: dict[str, int], misplaced: dict[str, int] | None = None,
       amlak_years: dict[int, int] | None = None) -> sqlite3.Connection:
    """balance/cash_flow: ticker -> rows of its own lines; misplaced: ticker -> cash-flow rows in its balance sheet."""
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE fundamentals_lineitems (ticker_key TEXT, fiscal_year INT, section TEXT, line_item_label TEXT)")
    rows = []
    for t, n in balance.items():
        if t == "AMLAK_DFM" and amlak_years is not None:
            continue
        rows += [(t, 2025, "Balance Sheet", f"line {i}") for i in range(n)]
    for y, n in (amlak_years or {}).items():
        rows += [("AMLAK_DFM", y, "Balance Sheet", f"line {i}") for i in range(n)]
    for t, n in cash_flow.items():
        rows += [(t, 2025, "Cash Flow Statement", f"cf {i}") for i in range(n)]
    for t, n in (misplaced or {}).items():
        rows += [(t, 2025, "Balance Sheet", CF_LINE)] * n
    c.executemany("INSERT INTO fundamentals_lineitems VALUES (?,?,?,?)", rows)
    return c


FIXED_BS = {t: 31 for t in f16.NINE}
FIXED_CF = {t: 19 for t in f16.WITH_CASH_FLOW}


def verdicts(conn) -> dict[str, bool]:
    return {what: ok for ok, what, _ in f16.data_checks(conn)}


class DataChecks(unittest.TestCase):
    def test_fixed_data_passes(self):
        self.assertTrue(all(verdicts(db(FIXED_BS, FIXED_CF)).values()))

    def test_cash_flow_left_in_a_balance_sheet_fails(self):
        v = verdicts(db(FIXED_BS, FIXED_CF, misplaced={"AMLAK_DFM": 19}))
        self.assertFalse(v["no cash-flow line in the nine companies' balance sheets"])

    def test_a_missing_balance_sheet_fails_for_each_of_the_nine(self):
        for t in f16.NINE:
            with self.subTest(ticker=t):
                bs = {k: v for k, v in FIXED_BS.items() if k != t}
                v = verdicts(db(bs, FIXED_CF))
                self.assertFalse(v["each of the nine has a balance sheet"], t)

    def test_no_balance_sheets_at_all_fails(self):
        self.assertFalse(all(verdicts(db({}, FIXED_CF)).values()))

    def test_amlak_with_no_rows_fails(self):
        bs = {k: v for k, v in FIXED_BS.items() if k != "AMLAK_DFM"}
        v = verdicts(db(bs, FIXED_CF))
        self.assertFalse(v["AMLAK's newest balance sheet is back to its own lines"])

    def test_amlak_still_at_fifty_fails(self):
        v = verdicts(db(FIXED_BS, FIXED_CF, amlak_years={2024: 31, 2025: 50}))
        self.assertFalse(v["AMLAK's newest balance sheet is back to its own lines"])

    def test_a_missing_cash_flow_statement_fails(self):
        cf = {k: v for k, v in FIXED_CF.items() if k != "QIC_ADX"}
        self.assertFalse(verdicts(db(FIXED_BS, cf))["the eight have a Cash Flow Statement"])

    def test_adnic_with_a_cash_flow_statement_fails(self):
        cf = dict(FIXED_CF, ADNIC_ADX=5)
        self.assertFalse(verdicts(db(FIXED_BS, cf))["ADNIC has none (its cash-flow lines carry no figures)"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
