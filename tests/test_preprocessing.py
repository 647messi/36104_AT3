import csv
import tempfile
import unittest
from collections import Counter
from datetime import date
from pathlib import Path

import pandas as pd

from src.preprocessing import (
    ALL_SECTORS,
    DEFAULT_SOURCE,
    NOTABLE_SOURCE,
    REQUIRED_COLUMNS,
    aggregate_counts,
    calculate_shares,
    compare_sector_shares,
    classify_sector,
    load_models,
)


class ClassificationTests(unittest.TestCase):
    def test_same_sector_does_not_become_collaboration(self):
        self.assertEqual(classify_sector("Industry,Industry"), "Industry")
        self.assertEqual(classify_sector(" Academia,Academia "), "Academia")

    def test_cross_sector_boundaries(self):
        self.assertEqual(classify_sector("Academia,Industry"), "Collaboration")
        self.assertEqual(classify_sector("Industry,Government,Academia"), "Collaboration")
        self.assertEqual(classify_sector("Industry,Government"), "Other")
        self.assertEqual(classify_sector("Academia,Research collective"), "Other")
        self.assertEqual(classify_sector(" , "), "Unknown")

    def test_duplicate_model_date_requires_review(self):
        record = dict.fromkeys(REQUIRED_COLUMNS, "")
        record.update({"Model": "Test model", "Publication date": "2020-01-01"})
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "models.csv"
            with source.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
                writer.writeheader()
                writer.writerows([record, record])
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                load_models(source)

    def test_undated_record_is_auditable_without_shifting_source_ordinals(self):
        records = []
        for model, publication in [("Dated A", "2020-01-01"), ("Undated", ""), ("Dated B", "2020-02-01")]:
            row = dict.fromkeys(REQUIRED_COLUMNS, "")
            row.update({"Model": model, "Publication date": publication, "Organization categorization": "Industry"})
            records.append(row)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "models.csv"
            with source.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
                writer.writeheader()
                writer.writerows(records)
            models, report = load_models(source)
            self.assertEqual(models["Source record"].tolist(), [1, 2, 3])
            self.assertTrue(pd.isna(models.loc[1, "Year"]))
            self.assertEqual(report["missing_dates"], 1)
            self.assertEqual(report["invalid_dates"], 0)
            self.assertEqual(int(aggregate_counts(models, 2020, 2020)["Count"].sum()), 2)
            records[1]["Publication date"] = "2020-99-99"
            with source.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
                writer.writeheader()
                writer.writerows(records)
            with self.assertRaisesRegex(ValueError, "nonempty invalid"):
                load_models(source)


class SourceReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models, cls.quality = load_models()

    def test_every_model_counted_once_and_empty_cells_are_zero(self):
        counts = aggregate_counts(self.models, 2003, 2025)
        self.assertEqual(len(counts), 23 * len(ALL_SECTORS))
        self.assertEqual(int(counts["Count"].sum()), int(self.models["Year"].between(2003, 2025).sum()))
        empty = aggregate_counts(self.models.iloc[:0], 2003, 2003)
        self.assertTrue(empty["Count"].eq(0).all())

    def test_all_year_sector_counts_against_independent_raw_csv_pass(self):
        # Deliberately bypass pandas and classify_sector in this independent pass.
        for source in [DEFAULT_SOURCE, NOTABLE_SOURCE]:
            with self.subTest(source=source.name):
                expected = Counter()
                undated = 0
                with source.open(encoding="utf-8-sig", newline="") as f:
                    for record in csv.DictReader(f):
                        if not record["Publication date"].strip():
                            undated += 1
                            continue
                        year = date.fromisoformat(record["Publication date"]).year
                        if not 2003 <= year <= 2025:
                            continue
                        labels = sorted(set(x.strip() for x in record["Organization categorization"].split(",") if x.strip()))
                        if not labels:
                            sector = "Unknown"
                        elif labels == ["Industry"]:
                            sector = "Industry"
                        elif labels == ["Academia"]:
                            sector = "Academia"
                        elif "Industry" in labels and "Academia" in labels:
                            sector = "Collaboration"
                        else:
                            sector = "Other"
                        expected[year, sector] += 1
                models, quality = load_models(source)
                self.assertEqual(quality["missing_dates"], undated)
                actual = calculate_shares(aggregate_counts(models, 2003, 2025))
                for row in actual.itertuples(index=False):
                    self.assertEqual(row.Count, expected[row.Year, row.Sector], (source.name, row.Year, row.Sector))
                    total = sum(expected[row.Year, sector] for sector in ALL_SECTORS)
                    self.assertEqual(row.Total, total)
                    self.assertAlmostEqual(row.Share, expected[row.Year, row.Sector] / total * 100)

    def test_notable_comparison_uses_each_samples_own_denominator(self):
        notable, _ = load_models(NOTABLE_SOURCE)
        all_shares = calculate_shares(aggregate_counts(self.models, 2025, 2025))
        notable_shares = calculate_shares(aggregate_counts(notable, 2025, 2025))
        comparison = compare_sector_shares(all_shares, notable_shares)
        for row in comparison.itertuples(index=False):
            self.assertAlmostEqual(row.Share_All, row.Count_All / row.Total_All * 100)
            self.assertAlmostEqual(row.Share_Notable, row.Count_Notable / row.Total_Notable * 100)
            self.assertAlmostEqual(row.Share_gap_pp, row.Share_Notable - row.Share_All)
        self.assertNotEqual(comparison.iloc[0]["Total_All"], comparison.iloc[0]["Total_Notable"])
        keys = ["Model", "Publication date"]
        self.assertTrue(set(map(tuple, notable[keys].to_numpy())) <= set(map(tuple, self.models[keys].to_numpy())))

    def test_share_denominator_includes_other_and_unknown(self):
        models = pd.DataFrame({
            "Year": [2020] * 7,
            "Sector": ["Industry", "Industry", "Academia", "Collaboration", "Other", "Unknown", "Unknown"],
        })
        shares = calculate_shares(aggregate_counts(models, 2020, 2020)).set_index("Sector")
        self.assertTrue(shares["Total"].eq(7).all())
        self.assertAlmostEqual(shares.loc["Industry", "Share"], 2 / 7 * 100)
        self.assertAlmostEqual(shares.loc["Unknown", "Share"], 2 / 7 * 100)
        self.assertAlmostEqual(shares["Share"].sum(), 100)

    def test_empty_year_has_undefined_shares_but_zero_category_has_zero_share(self):
        empty = calculate_shares(aggregate_counts(self.models.iloc[:0], 2020, 2021))
        self.assertTrue(empty["Total"].eq(0).all())
        self.assertTrue(empty["Share"].isna().all())
        only_industry = pd.DataFrame({"Year": [2020], "Sector": ["Industry"]})
        recorded = calculate_shares(aggregate_counts(only_industry, 2020, 2020))
        self.assertEqual(recorded.loc[recorded["Sector"].eq("Academia"), "Share"].iloc[0], 0)

    def test_single_year_and_invalid_range(self):
        counts = aggregate_counts(self.models, 2025, 2025)
        self.assertEqual(len(counts), len(ALL_SECTORS))
        for start, end in [(2025, 2024), (2002, 2020), (2020, 2026)]:
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                aggregate_counts(self.models, start, end)


if __name__ == "__main__":
    unittest.main()
