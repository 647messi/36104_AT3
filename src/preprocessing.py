"""Count Epoch AI's All models, with a separately processed Notable comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data/raw/ai_models/all_ai_models.csv"
NOTABLE_SOURCE = ROOT / "data/raw/ai_models/notable_ai_models.csv"
FIRST_YEAR = 2003
LAST_YEAR = 2025
CHART_SECTORS = ("Industry", "Academia", "Collaboration")
ALL_SECTORS = (*CHART_SECTORS, "Other", "Unknown")
REQUIRED_COLUMNS = (
    "Model",
    "Organization",
    "Publication date",
    "Organization categorization",
    "Link",
)


def classify_sector(value: str) -> str:
    """Use distinct sector tags, rather than the number of organisations."""
    tags = {tag.strip() for tag in value.split(",") if tag.strip()}
    if not tags:
        return "Unknown"
    if tags == {"Industry"}:
        return "Industry"
    if tags == {"Academia"}:
        return "Academia"
    if {"Industry", "Academia"}.issubset(tags):
        return "Collaboration"
    return "Other"


def load_models(source: Path = DEFAULT_SOURCE) -> tuple[pd.DataFrame, dict]:
    """Preserve source fields and add a traceable record number, year and sector."""
    source = Path(source)
    raw = pd.read_csv(source, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    missing = sorted(set(REQUIRED_COLUMNS) - set(raw.columns))
    if missing:
        raise ValueError(f"Required CSV columns are missing: {', '.join(missing)}")
    if raw.empty:
        raise ValueError("The source CSV contains no model records.")

    dates = pd.to_datetime(raw["Publication date"], format="%Y-%m-%d", errors="coerce")
    missing_dates = raw["Publication date"].str.strip().eq("")
    invalid_dates = dates.isna() & ~missing_dates
    exact_duplicates = int(raw.duplicated().sum())
    key_duplicates = int(raw.duplicated(["Model", "Publication date"]).sum())
    if invalid_dates.any():
        raise ValueError(f"{int(invalid_dates.sum())} records have nonempty invalid dates; review required.")
    if raw["Model"].str.strip().eq("").any():
        raise ValueError("Some records have no model name.")
    if exact_duplicates or key_duplicates:
        raise ValueError("Duplicate records or model/date pairs require review before counting.")

    models = raw.copy()
    # One-based data-record ordinal, excluding the header; not a physical line number.
    models.insert(0, "Source record", range(1, len(models) + 1))
    # Keep undated records and their original ordinals for audit; annual filters
    # exclude their missing years without inventing dates or dropping raw rows.
    models["Year"] = dates.dt.year.astype("Int64")
    models["Sector"] = models["Organization categorization"].map(classify_sector)
    if not models["Sector"].isin(ALL_SECTORS).all():
        raise ValueError("A model has not been assigned to a recognised analysis category.")

    quality = {
        "source_file": source.name,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "raw_rows": len(raw),
        "raw_columns": len(raw.columns),
        "earliest_date": dates.min().strftime("%Y-%m-%d") if dates.notna().any() else None,
        "latest_date": dates.max().strftime("%Y-%m-%d") if dates.notna().any() else None,
        "missing_organization": int(raw["Organization"].str.strip().eq("").sum()),
        "missing_categorization": int(raw["Organization categorization"].str.strip().eq("").sum()),
        "exact_duplicates": exact_duplicates,
        "duplicate_model_date_pairs": key_duplicates,
        "missing_dates": int(missing_dates.sum()),
        "invalid_dates": int(invalid_dates.sum()),
        "valid_dated_rows": int(dates.notna().sum()),
        "excluded_undated_rows": int(missing_dates.sum()),
    }
    return models, quality


def aggregate_counts(models: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    """Include every selected year and category, even when its count is zero."""
    if not FIRST_YEAR <= start_year <= end_year <= LAST_YEAR:
        raise ValueError(f"Select years within {FIRST_YEAR}–{LAST_YEAR}.")
    selected = models.loc[models["Year"].between(start_year, end_year)]
    index = pd.MultiIndex.from_product(
        [range(start_year, end_year + 1), ALL_SECTORS], names=["Year", "Sector"]
    )
    annual = (
        selected.groupby(["Year", "Sector"]).size()
        .reindex(index, fill_value=0)
        .rename("Count")
        .reset_index()
    )
    if int(annual["Count"].sum()) != len(selected):
        raise ValueError("Annual counts do not reconcile with the number of source models.")
    return annual


def calculate_shares(annual: pd.DataFrame) -> pd.DataFrame:
    """Add annual totals and percentages to the complete five-category counts.

    The denominator includes Other and Unknown. An empty year has undefined
    shares (NaN), rather than an invented composition or five zero percentages.
    """
    shares = annual.copy()
    shares["Total"] = shares.groupby("Year")["Count"].transform("sum")
    denominator = shares["Total"].where(shares["Total"].gt(0))
    shares["Share"] = shares["Count"].div(denominator).mul(100)
    return shares


def compare_sector_shares(all_shares: pd.DataFrame, notable_shares: pd.DataFrame) -> pd.DataFrame:
    """Compare each sample's own denominator, without adding overlapping samples."""
    columns = ["Year", "Sector", "Count", "Total", "Share"]
    comparison = all_shares[columns].merge(
        notable_shares[columns], on=["Year", "Sector"], how="outer",
        suffixes=("_All", "_Notable"), validate="one_to_one",
    )
    comparison["Share_gap_pp"] = comparison["Share_Notable"] - comparison["Share_All"]
    return comparison


def export_dataset(source: Path, output: Path) -> tuple[pd.DataFrame, dict]:
    models, quality = load_models(source)
    selected = models.loc[models["Year"].between(FIRST_YEAR, LAST_YEAR)]
    annual = aggregate_counts(models, FIRST_YEAR, LAST_YEAR)
    shares = calculate_shares(annual)
    quality["analysis_years"] = [FIRST_YEAR, LAST_YEAR]
    quality["analysis_models"] = len(selected)
    quality["analysis_sector_counts"] = {
        sector: int(selected["Sector"].eq(sector).sum()) for sector in ALL_SECTORS
    }
    output.mkdir(parents=True, exist_ok=True)
    annual.to_csv(output / "annual_sector_counts.csv", index=False)
    shares.to_csv(output / "annual_sector_shares.csv", index=False)
    selected.to_csv(output / "classified_models.csv", index=False)
    undated = models.loc[models["Year"].isna()].copy()
    undated["Exclusion reason"] = "Missing publication date; excluded from annual analysis"
    undated.to_csv(output / "excluded_undated_models.csv", index=False)
    (output / "data_quality.json").write_text(
        json.dumps(quality, indent=2) + "\n", encoding="utf-8"
    )
    return shares, quality


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--notable-source", type=Path, default=NOTABLE_SOURCE)
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed")
    args = parser.parse_args()
    all_shares, all_quality = export_dataset(args.source, args.output)
    notable_shares, notable_quality = export_dataset(args.notable_source, args.output / "notable")
    compare_sector_shares(all_shares, notable_shares).to_csv(
        args.output / "all_vs_notable.csv", index=False
    )
    print(json.dumps({"All": all_quality, "Notable": notable_quality}, indent=2))


if __name__ == "__main__":
    main()
