"""Classify how each notable model can be accessed, then count models by year.

This module adds its own Access field. It does not change the shared Sector
classification in src.preprocessing.
"""

from __future__ import annotations

import pandas as pd

from src.preprocessing import FIRST_YEAR, LAST_YEAR, ROOT

# This analysis is about notable models (Epoch AI's curated sample), so it reads
# that file explicitly rather than the shared default source.
NOTABLE_FILE = ROOT / "data/raw/ai_models/notable_ai_models.csv"
# The snapshot was committed to the repository on this date (commit eded8d5);
# the exact download time was not recorded.
SNAPSHOT_ADDED = "22 October 2026"

# Chart order: Open weights first so it sits on the shared baseline of a
# stacked bar, and Unreleased last at the top.
ACCESS_TYPES = ("Open weights", "API access", "Hosted or limited access", "Unreleased")
NOT_RECORDED = "Not recorded"
ALL_ACCESS = (*ACCESS_TYPES, NOT_RECORDED)
# Developer-controlled access: the developer keeps the weights and decides who
# may use the model and how.
CONTROLLED = ("API access", "Hosted or limited access")
# Years with fewer recorded models than this are flagged as unreliable shares.
MIN_RECORDED = 10
DEFAULT_START = 2015


def classify_access(value: str) -> str:
    """Group Epoch AI's Model accessibility values into four access types.

    Unknown values raise an error so that new source categories are reviewed
    rather than silently miscounted.

    Open weights (unrestricted), (non-commercial) and (restricted use) are all
    Open weights: anyone can download the weights, whatever the licence terms.
    """
    value = value.strip()
    if not value:
        return NOT_RECORDED
    if value.startswith("Open weights"):
        return "Open weights"
    if value == "API access":
        return "API access"
    # Hosted access (no API) and Limited access (selected partners only) both
    # leave the developer deciding who may use the model.
    if value.startswith("Hosted access") or value == "Limited access":
        return "Hosted or limited access"
    if value == "Unreleased":
        return "Unreleased"
    raise ValueError(f"Unrecognised Model accessibility value: {value!r}")


def add_access(models: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with an Access column; source fields are unchanged."""
    out = models.copy()
    out["Access"] = out["Model accessibility"].map(classify_access)
    return out


def annual_access(models: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    """Count models per year and access type, with shares of recorded models.

    Every year and access type in the window is present, including zero counts.
    Shares use models with a recorded accessibility as the denominator, so the
    four access types add up to 100% in each year.
    """
    if not FIRST_YEAR <= start_year <= end_year <= LAST_YEAR:
        raise ValueError(f"Select years within {FIRST_YEAR}–{LAST_YEAR}.")
    selected = add_access(models).loc[lambda d: d["Year"].between(start_year, end_year)]
    index = pd.MultiIndex.from_product(
        [range(start_year, end_year + 1), ALL_ACCESS], names=["Year", "Access"]
    )
    annual = (
        selected.groupby(["Year", "Access"]).size()
        .reindex(index, fill_value=0)
        .rename("Count")
        .reset_index()
    )
    if int(annual["Count"].sum()) != len(selected):
        raise ValueError("Annual access counts do not reconcile with the source models.")
    recorded = (
        annual.loc[annual["Access"] != NOT_RECORDED]
        .groupby("Year")["Count"].sum()
        .rename("Recorded")
    )
    annual = annual.merge(recorded, on="Year")
    annual["Share"] = annual["Count"].div(annual["Recorded"].where(annual["Recorded"] > 0))
    annual.loc[annual["Access"] == NOT_RECORDED, "Share"] = float("nan")
    annual["Thin year"] = annual["Recorded"] < MIN_RECORDED
    return annual


def share_of(annual: pd.DataFrame, year: int, access: tuple[str, ...]) -> float | None:
    """Combined share of the given access types in one year (None if no data)."""
    row = annual.loc[annual["Year"] == year]
    recorded = int(row["Recorded"].iloc[0]) if len(row) else 0
    if recorded == 0:
        return None
    return float(row.loc[row["Access"].isin(access), "Count"].sum() / recorded)


def values_table(annual: pd.DataFrame, as_share: bool) -> pd.DataFrame:
    """One row per year with every value in the stacked bar chart, as text.

    Small segments are too thin to carry a label inside the bar, so this table
    makes every value readable without hovering.
    """
    data = annual.loc[annual["Access"] != NOT_RECORDED]
    if as_share:
        cell = data.apply(
            lambda r: f"{r['Share']:.0%} ({r['Count']})" if r["Recorded"] else "n/a", axis=1)
    else:
        cell = data["Count"].astype(str)
    table = (data.assign(Cell=cell)
             .pivot(index="Year", columns="Access", values="Cell")
             .reindex(columns=list(ACCESS_TYPES)))
    table["Recorded models (n)"] = data.groupby("Year")["Recorded"].first()
    return table.reset_index().astype({"Year": str})
