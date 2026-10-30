"""Checks for the Model Access classification and annual shares."""

import unittest

import pandas as pd

from src.model_access import (
    NOT_RECORDED, NOTABLE_FILE, annual_access, classify_access, share_of,
)
from src.preprocessing import load_models


class ClassifyAccessTest(unittest.TestCase):
    def test_source_values(self):
        cases = {
            "Open weights (unrestricted)": "Open weights",
            "Open weights (non-commercial)": "Open weights",
            "Open weights (restricted use)": "Open weights",
            "API access": "API access",
            "Hosted access (no API)": "Hosted or limited access",
            "Limited access": "Hosted or limited access",
            "Unreleased": "Unreleased",
            "": NOT_RECORDED,
            "  ": NOT_RECORDED,
        }
        for value, expected in cases.items():
            self.assertEqual(classify_access(value), expected, value)

    def test_unknown_value_is_rejected(self):
        with self.assertRaises(ValueError):
            classify_access("Something new")


class AnnualAccessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models, _ = load_models(NOTABLE_FILE)

    def test_counts_reconcile_and_shares_sum_to_one(self):
        annual = annual_access(self.models, 2015, 2025)
        selected = self.models["Year"].between(2015, 2025).fillna(False).sum()
        self.assertEqual(int(annual["Count"].sum()), int(selected))
        shares = annual.dropna(subset=["Share"]).groupby("Year")["Share"].sum()
        for year, total in shares.items():
            self.assertAlmostEqual(total, 1.0, places=9, msg=year)

    def test_independent_recount_from_raw_csv(self):
        raw = pd.read_csv(NOTABLE_FILE, dtype=str,
                          keep_default_na=False)
        in_2025 = raw[raw["Publication date"].str.startswith("2025")]
        api = int((in_2025["Model accessibility"] == "API access").sum())
        recorded = int((in_2025["Model accessibility"].str.strip() != "").sum())
        annual = annual_access(self.models, 2025, 2025)
        row = annual.loc[annual["Access"] == "API access"].iloc[0]
        self.assertEqual(int(row["Count"]), api)
        self.assertEqual(int(row["Recorded"]), recorded)
        self.assertAlmostEqual(share_of(annual, 2025, ("API access",)), api / recorded)

    def test_every_year_present_with_zero_counts(self):
        annual = annual_access(self.models, 2003, 2005)
        self.assertEqual(len(annual), 3 * 5)


if __name__ == "__main__":
    unittest.main()
