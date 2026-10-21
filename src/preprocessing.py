"""Classify each notable model once, then count models by year and sector."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data/raw/ai_models/notable_ai_models.csv"
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
    exact_duplicates = int(raw.duplicated().sum())
    key_duplicates = int(raw.duplicated(["Model", "Publication date"]).sum())
    if dates.isna().any():
        raise ValueError(f"{int(dates.isna().sum())} records have missing or invalid dates.")
    if raw["Model"].str.strip().eq("").any():
        raise ValueError("Some records have no model name.")
    if exact_duplicates or key_duplicates:
        raise ValueError("Duplicate records or model/date pairs require review before counting.")

    models = raw.copy()
    # One-based data-record ordinal, excluding the header; not a physical line number.
    models.insert(0, "Source record", range(1, len(models) + 1))
    models["Year"] = dates.dt.year
    models["Sector"] = models["Organization categorization"].map(classify_sector)
    if not models["Sector"].isin(ALL_SECTORS).all():
        raise ValueError("A model has not been assigned to a recognised analysis category.")

    quality = {
        "source_file": source.name,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "raw_rows": len(raw),
        "raw_columns": len(raw.columns),
        "earliest_date": dates.min().strftime("%Y-%m-%d"),
        "latest_date": dates.max().strftime("%Y-%m-%d"),
        "missing_organization": int(raw["Organization"].str.strip().eq("").sum()),
        "missing_categorization": int(raw["Organization categorization"].str.strip().eq("").sum()),
        "exact_duplicates": exact_duplicates,
        "duplicate_model_date_pairs": key_duplicates,
        "invalid_dates": int(dates.isna().sum()),
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed")
    args = parser.parse_args()
    models, quality = load_models(args.source)
    selected = models.loc[models["Year"].between(FIRST_YEAR, LAST_YEAR)]
    annual = aggregate_counts(models, FIRST_YEAR, LAST_YEAR)
    quality["analysis_years"] = [FIRST_YEAR, LAST_YEAR]
    quality["analysis_models"] = len(selected)
    quality["analysis_sector_counts"] = {
        sector: int(selected["Sector"].eq(sector).sum()) for sector in ALL_SECTORS
    }
    args.output.mkdir(parents=True, exist_ok=True)
    annual.to_csv(args.output / "annual_sector_counts.csv", index=False)
    selected.to_csv(args.output / "classified_models.csv", index=False)
    (args.output / "data_quality.json").write_text(
        json.dumps(quality, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(quality, indent=2))


if __name__ == "__main__":
    main()
