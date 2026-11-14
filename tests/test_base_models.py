"""Checks for page 5 (Base Model Dependence) and src/base_models.py.

Run from the repository root:
    python -m unittest discover -s tests -v
"""

import csv
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.base_models import (ALL_FILE, derived_models, derived_share_by_year,
                             load_all, owner_ranking, owner_shares)
from src.preprocessing import LAST_YEAR

ROOT = Path(__file__).resolve().parents[1]
PAGE = "dashboards/5_Base_Model_Dependence.py"


def raw_rows() -> list[dict]:
    """Read the CSV with the standard csv module, independently of pandas."""
    with open(ALL_FILE, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


class LoadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = raw_rows()
        cls.records = load_all()

    def test_every_csv_record_is_loaded_once(self):
        self.assertEqual(len(self.records), len(self.raw))

    def test_source_record_is_one_based_and_matches_the_csv(self):
        self.assertEqual(self.records["Source record"].tolist(), list(range(1, len(self.raw) + 1)))
        for n in (1, 289, 1061, len(self.raw)):
            self.assertEqual(self.records.iloc[n - 1]["Model"], self.raw[n - 1]["Model"])

    def test_raw_fields_are_unchanged(self):
        for col in ("Model", "Organization", "Base model", "Publication date"):
            self.assertEqual(self.records[col].tolist(), [r[col] for r in self.raw])


class CountingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        records = load_all()
        cls.records = records[records["Year"].isna() | (records["Year"] <= LAST_YEAR)]
        cls.derived = derived_models(cls.records, parent=True, include_own=False)

    def test_owner_shares_sum_to_100_each_year(self):
        shares = owner_shares(self.derived, (2020, LAST_YEAR))
        for year, total in shares.groupby("Year")["Share"].sum().items():
            self.assertAlmostEqual(total, 100.0, places=6, msg=str(year))

    def test_credit_adds_up_to_the_number_of_derived_models(self):
        per_year = self.derived.groupby("Year")["Credit"].sum()
        models = self.derived.drop_duplicates("Source record").groupby("Year").size()
        for year in models.index:
            self.assertAlmostEqual(per_year[year], models[year], places=6)

    def test_own_base_models_are_excluded_by_default(self):
        self.assertFalse(self.derived["Own base"].any())
        with_own = derived_models(self.records, parent=True, include_own=True)
        self.assertGreater(with_own["Source record"].nunique(), self.derived["Source record"].nunique())

    def test_derived_share_is_between_0_and_100(self):
        share = derived_share_by_year(self.records, self.derived, (2015, LAST_YEAR))
        self.assertTrue(share["Share"].between(0, 100).all())

    def test_ranking_is_sorted(self):
        rank = owner_ranking(self.derived, (2020, LAST_YEAR))
        self.assertEqual(rank["Models"].tolist(), sorted(rank["Models"], reverse=True))


class RecordingExampleTests(unittest.TestCase):
    """The number traced in the recording, recomputed from the raw CSV."""

    def test_k2_think_is_built_on_an_alibaba_model(self):
        raw = raw_rows()
        k2 = raw[289 - 1]
        self.assertEqual(k2["Model"], "K2 Think")
        self.assertEqual(k2["Base model"], "Qwen2.5-32B")
        base = [r for r in raw if r["Model"].strip() == "Qwen2.5-32B"]
        self.assertEqual(base[0]["Organization"], "Alibaba")
        self.assertEqual(raw.index(base[0]) + 1, 1061)

    def test_alibaba_2025_is_43_of_86(self):
        records = load_all()
        derived = derived_models(records, parent=True, include_own=False)
        row = owner_shares(derived, (2025, 2025)).set_index("Owner").loc["Alibaba"]
        self.assertAlmostEqual(row["Models"], 43.0)
        self.assertAlmostEqual(row["Total"], 86.0)
        self.assertAlmostEqual(row["Share"], 50.0)


class RegenerationTests(unittest.TestCase):
    def test_processed_files_regenerate_identically(self):
        """The committed exports must match a fresh run of the documented transform."""
        import filecmp
        import subprocess
        import sys
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([sys.executable, "-m", "src.base_models", "--output", tmp],
                           cwd=ROOT, check=True, capture_output=True)
            for name in ("derived_models.csv", "derived_share_by_year.csv",
                         "owner_shares_by_year.csv", "owner_ranking_2020_2025.csv"):
                self.assertTrue(
                    filecmp.cmp(Path(tmp) / name, ROOT / "data/processed/base_models" / name,
                                shallow=False),
                    f"{name} differs from a fresh regeneration")


class PageTests(unittest.TestCase):
    """The page opens through the shared app and its controls work."""

    def setUp(self):
        self.at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120)
        self.at.run()
        self.at.switch_page(PAGE).run()

    def test_page_opens_without_errors(self):
        self.assertFalse(self.at.exception)
        self.assertEqual(len(self.at.metric), 3)

    def test_controls_and_verification(self):
        for key, value in (("bm_own", True), ("bm_parent", False)):
            self.at.toggle(key=key).set_value(value).run()
            self.assertFalse(self.at.exception, key)
        self.at.toggle(key="bm_own").set_value(False).run()
        self.at.toggle(key="bm_parent").set_value(True).run()
        self.at.selectbox(key="bm_v_year").set_value(2025).run()
        self.at.selectbox(key="bm_v_owner").set_value("Alibaba").run()
        text = " ".join(m.value for m in self.at.markdown)
        self.assertIn("43.0 of 86", text)
        self.assertEqual(len(self.at.dataframe[-1].value), 43)

    def test_single_year_range(self):
        self.at.slider(key="bm_years").set_value((2017, 2017)).run()
        self.assertFalse(self.at.exception)


if __name__ == "__main__":
    unittest.main()
