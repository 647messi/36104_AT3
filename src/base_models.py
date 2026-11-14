"""Processing for the 'Base model dependence' page.

Question: is AI development becoming dependent on base models from a few organisations?

Reads data/raw/ai_models/all_ai_models.csv with load_all() below. The shared loader
(src.preprocessing.load_models) reads the Notable file and stops on undated records; the
All file has 12 undated records and many more Base model entries (693 vs 141), so this page
reads it the same way (all fields as text, one-based Source record, Year from Publication
date) but keeps undated records with no year instead of stopping. It does not change the
raw data or the shared sector classification.

Analytical rules specific to this page:

1. Derived model: a record whose 'Base model' field is not blank (Epoch records the model
   it was fine-tuned or built from).
2. Base-model owner: the 'Organization' of the base model's own record in the same file,
   matched on the exact model name. If several base models are listed, the first is used.
   Unmatched names are kept as 'Not in dataset' and shown in the verification table.
3. Credit: a base model owned by k organisations gives each owner 1/k.
4. Own base models: by default a derived model is excluded when its developer also owns
   the base model (e.g. Meta fine-tuning its own Llama), because the question is about
   depending on someone else. A toggle includes them.
5. Parent company (optional): labs of the same company are merged, using PARENT.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ALL_FILE = ROOT / "data/raw/ai_models/all_ai_models.csv"

ORG_COL = "Organization"
BASE_COL = "Base model"
NOT_FOUND = "Not in dataset"

PARENT = {
    "Google": "Alphabet", "Google Brain": "Alphabet", "Google Research": "Alphabet",
    "Google DeepMind": "Alphabet", "DeepMind": "Alphabet",
    "Meta AI": "Meta", "Facebook AI Research": "Meta", "Facebook": "Meta", "Facebook AI": "Meta",
    "Microsoft Research": "Microsoft",
    "Alibaba Cloud": "Alibaba", "Alibaba Group": "Alibaba", "Qwen Team": "Alibaba",
}


def load_all(source: Path = ALL_FILE) -> pd.DataFrame:
    """Read the All file unchanged, with the same conventions as the shared loader."""
    raw = pd.read_csv(source, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    missing = {"Model", ORG_COL, "Publication date", BASE_COL} - set(raw.columns)
    if missing:
        raise ValueError(f"Required CSV columns are missing: {', '.join(sorted(missing))}")
    models = raw.copy()
    # One-based data-record ordinal, excluding the header; not a physical line number.
    models.insert(0, "Source record", range(1, len(models) + 1))
    dates = pd.to_datetime(models["Publication date"], format="%Y-%m-%d", errors="coerce")
    models["Year"] = dates.dt.year.astype("Int64")  # undated records keep a blank year
    return models


def split(value) -> list[str]:
    if value is None or pd.isna(value):
        return []
    return list(dict.fromkeys(p.strip() for p in str(value).split(",") if p.strip()))


def _norm(orgs: list[str], parent: bool) -> list[str]:
    return list(dict.fromkeys(PARENT.get(o, o) for o in orgs)) if parent else orgs


def derived_models(records: pd.DataFrame, parent: bool = False,
                   include_own: bool = False) -> pd.DataFrame:
    """One row per (derived model, base-model owner) with 1/k credit."""
    dated = records[records["Year"].notna()]
    owner = dict(zip(records["Model"].str.strip(), records[ORG_COL]))

    d = dated[dated[BASE_COL].str.strip() != ""].copy()
    d["Base used"] = d[BASE_COL].map(lambda v: (split(v) or [""])[0])
    d["Owners"] = d["Base used"].map(lambda m: _norm(split(owner.get(m)), parent) or [NOT_FOUND])
    d["Developers"] = d[ORG_COL].map(lambda v: _norm(split(v), parent))
    d["Own base"] = d.apply(lambda r: bool(set(r["Owners"]) & set(r["Developers"])), axis=1)
    if not include_own:
        d = d[~d["Own base"]]
    d["Credit"] = 1 / d["Owners"].str.len()
    return d.explode("Owners").rename(columns={"Owners": "Base owner"}).reset_index(drop=True)


def derived_share_by_year(records: pd.DataFrame, derived: pd.DataFrame,
                          years: tuple[int, int]) -> pd.DataFrame:
    """Share of all models in each year that were built on another developer's model."""
    total = records[records["Year"].between(*years)].groupby("Year").size()
    n_derived = derived.drop_duplicates("Source record").groupby("Year").size()
    out = pd.DataFrame({"All models": total}).join(n_derived.rename("Derived models")).fillna(0)
    out["Derived models"] = out["Derived models"].astype(int)
    out["Share"] = out["Derived models"] / out["All models"] * 100
    return out.reset_index()


def owner_shares(derived: pd.DataFrame, years: tuple[int, int], top_n: int = 5) -> pd.DataFrame:
    """Per year: each base-model owner's share of derived models. Owners outside the
    top_n of the whole period are grouped as 'Other'. Every year sums to 100%."""
    d = derived[derived["Year"].between(*years)]
    leaders = (d[d["Base owner"] != NOT_FOUND].groupby("Base owner")["Credit"].sum()
               .sort_values(ascending=False).head(top_n).index)
    d = d.assign(Owner=d["Base owner"].where(d["Base owner"].isin(leaders),
                                             d["Base owner"].where(d["Base owner"] == NOT_FOUND, "Other")))
    t = d.groupby(["Year", "Owner"])["Credit"].sum().unstack(fill_value=0)
    order = [*leaders, "Other", NOT_FOUND]
    t = t[[c for c in order if c in t.columns]]
    long = t.stack().rename("Models").reset_index()
    long["Total"] = long.groupby("Year")["Models"].transform("sum")
    long["Share"] = long["Models"] / long["Total"] * 100
    return long


def owner_ranking(derived: pd.DataFrame, years: tuple[int, int], n: int = 12) -> pd.DataFrame:
    d = derived[derived["Year"].between(*years)]
    r = d.groupby("Base owner")["Credit"].sum().sort_values(ascending=False)
    total = r.sum()
    r = r.head(n).rename("Models").reset_index()
    r["Share"] = r["Models"] / total * 100
    return r


PROCESSED_DIR = ROOT / "data/processed/base_models"
EXPORT_YEARS = (2015, 2025)


def export(out_dir: Path = PROCESSED_DIR) -> list[Path]:
    """Regenerate page 5's processed files from the unchanged raw CSV.

    Run from the repository root:  python -m src.base_models [--output DIR]
    Default page settings: parent companies merged, a developer's own base models excluded.
    Values are rounded and written with Unix line endings, so a fresh run is byte-identical.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    records = load_all()
    records = records[records["Year"].isna() | (records["Year"] <= EXPORT_YEARS[1])]
    derived = derived_models(records, parent=True, include_own=False)
    derived_out = derived[["Source record", "Model", "Organization", "Publication date", "Year",
                           "Base model", "Base used", "Base owner", "Credit"]].copy()
    derived_out["Credit"] = derived_out["Credit"].round(4)
    share = derived_share_by_year(records, derived, EXPORT_YEARS).round({"Share": 1})
    shares = owner_shares(derived, EXPORT_YEARS).round({"Models": 2, "Total": 2, "Share": 1})
    ranking = owner_ranking(derived, (2020, EXPORT_YEARS[1]), n=50).round({"Models": 2, "Share": 1})
    files = {
        "derived_models.csv": derived_out,
        "derived_share_by_year.csv": share,
        "owner_shares_by_year.csv": shares,
        "owner_ranking_2020_2025.csv": ranking,
    }
    paths = []
    for name, frame in files.items():
        path = out_dir / name
        frame.to_csv(path, index=False, lineterminator="\n")
        paths.append(path)
    return paths


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Regenerate page 5's processed files.")
    parser.add_argument("--output", type=Path, default=PROCESSED_DIR)
    args = parser.parse_args()
    for written in export(args.output):
        print(f"wrote {written}")
