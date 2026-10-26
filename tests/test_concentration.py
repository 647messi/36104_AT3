"""Checks for the organisational concentration module and page."""

import csv
import unittest
from pathlib import Path

import pandas as pd

from src.concentration import (
    NOTABLE_FILE, PARENT_MAP, annual_concentration, split_organisations, year_records,
)
from src.preprocessing import load_models

ROOT = Path(__file__).resolve().parents[1]


def fixture() -> pd.DataFrame:
    rows = [
        ("A", "2020-01-01", "Google Brain"),
        ("B", "2020-02-01", "DeepMind,University X"),   # merged into Google: counted once
        ("C", "2020-03-01", "OpenAI"),
        ("D", "2020-04-01", "University X"),
        ("E", "2020-05-01", "Lab Y"),
        ("F", "2020-06-01", ""),                       # no organisation: excluded
    ]
    df = pd.DataFrame(rows, columns=["Model", "Publication date", "Organization"])
    df.insert(0, "Source record", range(1, len(df) + 1))
    df["Year"] = 2020
    df["Training compute (FLOP)"] = ""
    return df


class ConcentrationRules(unittest.TestCase):
    def test_merge_and_dedupe(self):
        self.assertEqual(split_organisations("Google Brain, DeepMind ,Google"), ["Google"])
        self.assertEqual(split_organisations("Google Brain,DeepMind", merge=False), ["DeepMind", "Google Brain"])
        self.assertEqual(split_organisations(""), [])

    def test_fixture_share(self):
        row = annual_concentration(fixture(), 1, 2020, 2020).iloc[0]
        # Google is on A and B (2 models); 5 models have an organisation.
        self.assertEqual(row["Models with organisation"], 5)
        self.assertEqual(row["Missing organisation"], 1)
        self.assertEqual(row["Top N models"], 2)
        self.assertEqual(row["Top N share (%)"], 40.0)

    def test_overlapping_top_orgs_not_double_counted(self):
        # Top 2 = Google (2) and University X (2); model B lists both but counts once.
        row = annual_concentration(fixture(), 2, 2020, 2020).iloc[0]
        self.assertEqual(row["Top N models"], 3)

    def test_ties_break_alphabetically(self):
        top, _ = year_records(fixture(), 2020, 3)
        self.assertEqual(top, ["Google", "University X", "Lab Y"])

    def test_parent_map_values_are_parents(self):
        for parent in set(PARENT_MAP.values()):
            self.assertEqual(PARENT_MAP.get(parent, parent), parent)


class RealData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models, _ = load_models(NOTABLE_FILE)

    def test_shares_within_bounds_and_reconcile(self):
        for n in (3, 5):
            table = annual_concentration(self.models, n)
            self.assertTrue((table["Top N models"] <= table["Models with organisation"]).all())
            share = table["Top N share (%)"].dropna()
            self.assertTrue(share.between(0, 100).all())

    def test_independent_recount_from_raw_csv(self):
        """Recount one year straight from the CSV with the csv module, not pandas."""
        year, n = 2025, 3
        top, _ = year_records(self.models, year, n)
        involved = known = 0
        with open(NOTABLE_FILE, encoding="utf-8-sig", newline="") as handle:
            for record in csv.DictReader(handle):
                if not record["Publication date"].startswith(str(year)):
                    continue
                orgs = {PARENT_MAP.get(o.strip(), o.strip()) for o in record["Organization"].split(",") if o.strip()}
                if orgs:
                    known += 1
                    involved += bool(orgs & set(top))
        row = annual_concentration(self.models, n, year, year).iloc[0]
        self.assertEqual((row["Top N models"], row["Models with organisation"]), (involved, known))


class PageRuns(unittest.TestCase):
    def test_page_renders_and_responds(self):
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30)
        at.run()
        at.switch_page("dashboards/2_Organisational_Concentration.py").run()
        self.assertFalse(at.exception)
        self.assertIn("Are a few organisations", at.title[0].value)
        at.radio(key="conc_n").set_value(5).run()
        self.assertFalse(at.exception)
        at.slider(key="conc_years").set_value((2025, 2025)).run()
        self.assertFalse(at.exception)
        at.toggle(key="conc_merge").set_value(False).run()
        self.assertFalse(at.exception)


if __name__ == "__main__":
    unittest.main()
