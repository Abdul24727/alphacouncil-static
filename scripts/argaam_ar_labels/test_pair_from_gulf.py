"""The unit rule of pair_from_gulf.saudi_arabic(): a Gulf page's trailing currency unit becomes the unit
the Saudi English names, or goes; anything else in parentheses stays.

    python -X utf8 scripts/argaam_ar_labels/test_pair_from_gulf.py
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pair_from_gulf import saudi_arabic  # noqa: E402


class UnitRule(unittest.TestCase):
    def test_dollar_is_a_currency_unit(self):
        # review 06 (2026-11-06): the dollar stayed beside the riyal
        self.assertEqual(saudi_arabic("Par Value (Riyal)", "القيمة الاسمية (دولار)"), "القيمة الاسمية (ريال)")
        self.assertEqual(saudi_arabic("Par Value (Riyal)", "القيمة الاسمية (دولار أمريكي)"), "القيمة الاسمية (ريال)")
        self.assertEqual(saudi_arabic("EPS (Halala)", "ربح السهم (دولار)"), "ربح السهم (هللة)")
        self.assertEqual(saudi_arabic("Par Value", "القيمة الاسمية (دولار)"), "القيمة الاسمية")

    def test_every_gulf_currency_still_becomes_the_saudi_unit(self):
        for unit in ("درهم", "فلس", "بيسة", "ريال قطري", "ريال عماني", "ريال سعودي", "ريال",
                     "دينار كويتي", "دينار بحريني", "دينار", "هللة"):
            with self.subTest(unit=unit):
                self.assertEqual(saudi_arabic("EPS (Riyal)", f"ربح السهم ({unit})"), "ربح السهم (ريال)")
                self.assertEqual(saudi_arabic("EPS (Halala)", f"ربح السهم ({unit})"), "ربح السهم (هللة)")
                self.assertEqual(saudi_arabic("EPS", f"ربح السهم ({unit})"), "ربح السهم")

    def test_other_parentheses_stay(self):
        self.assertEqual(saudi_arabic("Shares Outstanding (Million)", "عدد الأسهم (مليون)"), "عدد الأسهم (مليون)")
        self.assertEqual(saudi_arabic("Net Non-Operating income (Expenses)", "صافي الايرادات ( المصاريف ) غير التشغيلية"),
                         "صافي الايرادات ( المصاريف ) غير التشغيلية")

    def test_no_unit_no_change(self):
        self.assertEqual(saudi_arabic("Total Assets", "إجمالي الموجودات"), "إجمالي الموجودات")
        # a Saudi unit on a Gulf label that carries none is not invented
        self.assertEqual(saudi_arabic("Book Value Per Share (Riyal)", "القيمة الدفترية"), "القيمة الدفترية (ريال)")


if __name__ == "__main__":
    unittest.main(verbosity=1)
