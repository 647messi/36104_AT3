"""Organisational concentration: what share of notable models involve the top N organisations?

Unit of analysis: one notable model, counted once in the year of its `Publication date`.

Rules (explicit analytical choices, not supplied by Epoch AI):
1. `Organization` is split on commas into organisation names.
2. Known name variants of the same corporate group are merged into one parent
   (for example Google Brain, DeepMind and Google DeepMind become Google).
   Merging can be switched off to compare with the names as recorded.
3. For each year, organisations are ranked by the number of models they are
   listed on. Ties are broken alphabetically so the ranking is reproducible.
4. Top-N share = models listing at least one top-N organisation
   / models with at least one organisation name in that year.
   A model is never counted twice, so the share cannot exceed 100%.
5. Models with an empty `Organization` field are excluded from the share and
   reported separately. No organisation is inferred from a model's name.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.preprocessing import DEFAULT_SOURCE, load_models

ROOT = Path(__file__).resolve().parents[1]
FIRST_YEAR = 2003
LAST_YEAR = 2025          # 2026 is an incomplete calendar year and is excluded
DEFAULT_START = 2014      # before 2014 there are fewer than 20 notable models a year
TOP_N_OPTIONS = (3, 5)

# Source name -> parent organisation. Only corporate groups with several recorded
# names are merged; universities, joint labs and independent firms are left as recorded.
PARENT_MAP: dict[str, str] = {
    "Google": "Google",
    "Google DeepMind": "Google",
    "DeepMind": "Google",
    "Google Brain": "Google",
    "Google Research": "Google",
    "Google Cloud": "Google",
    "Google AI": "Google",
    "Meta AI": "Meta",
    "Facebook AI Research": "Meta",
    "Facebook": "Meta",
    "Facebook AI": "Meta",
    "Microsoft": "Microsoft",
    "Microsoft Research": "Microsoft",
    "Microsoft Research Asia": "Microsoft",
    "Alibaba": "Alibaba",
    "Alibaba DAMO Academy": "Alibaba",
    "Salesforce": "Salesforce",
    "Salesforce Research": "Salesforce",
    "Huawei": "Huawei",
    "Huawei Noah's Ark Lab": "Huawei",
    "Samsung": "Samsung",
    "Samsung R&D Institute Russia": "Samsung",
}


def split_organisations(value: str, merge: bool = True) -> list[str]:
    """Return the distinct organisations listed for one model, sorted."""
    names = {name.strip() for name in str(value).split(",") if name.strip()}
    if merge:
        names = {PARENT_MAP.get(name, name) for name in names}
    return sorted(names)


def attach_organisations(models: pd.DataFrame, merge: bool = True) -> pd.DataFrame:
    """Add an `Organisations` list column; keep every source field unchanged."""
    out = models.copy()
    out["Organisations"] = out["Organization"].map(lambda v: split_organisations(v, merge))
    return out


def rank_organisations(year_models: pd.DataFrame) -> pd.Series:
    """Models per organisation for one year, ranked; ties broken alphabetically."""
    counts = year_models["Organisations"].explode().dropna().value_counts()
    ranked = counts.rename_axis("org").reset_index(name="models")
    ranked = ranked.sort_values(["models", "org"], ascending=[False, True])
    return ranked.set_index("org")["models"]


def top_n_for_year(year_models: pd.DataFrame, n: int) -> tuple[list[str], pd.Series]:
    """Top-N organisation names and a boolean mask of models involving any of them."""
    ranked = rank_organisations(year_models)
    top = list(ranked.index[:n])
    involved = year_models["Organisations"].map(lambda orgs: any(o in top for o in orgs))
    return top, involved


def annual_concentration(
    models: pd.DataFrame, n: int, start: int = FIRST_YEAR, end: int = LAST_YEAR,
    merge: bool = True,
) -> pd.DataFrame:
    """One row per year: models with an organisation, top-N models, share and the top-N names."""
    if n < 1:
        raise ValueError("N must be at least 1.")
    if not FIRST_YEAR <= start <= end <= LAST_YEAR:
        raise ValueError(f"Select years within {FIRST_YEAR}–{LAST_YEAR}.")
    data = attach_organisations(models, merge)
    rows = []
    for year in range(start, end + 1):
        in_year = data.loc[data["Year"] == year]
        known = in_year.loc[in_year["Organisations"].str.len() > 0]
        if known.empty:
            rows.append({"Year": year, "Models with organisation": 0, "Missing organisation": len(in_year),
                         "Organisations": 0, "Top N models": 0, "Top N share (%)": float("nan"),
                         "Top N organisations": ""})
            continue
        ranked = rank_organisations(known)
        top, involved = top_n_for_year(known, n)
        top_models = int(involved.sum())
        rows.append({
            "Year": year,
            "Models with organisation": len(known),
            "Missing organisation": len(in_year) - len(known),
            "Organisations": len(ranked),
            "Top N models": top_models,
            "Top N share (%)": round(100 * top_models / len(known), 1),
            "Top N organisations": "; ".join(f"{o} ({ranked[o]})" for o in top),
        })
    result = pd.DataFrame(rows)
    if (result["Top N models"] > result["Models with organisation"]).any():
        raise ValueError("A top-N count exceeds the number of models; check the attribution rules.")
    return result


def year_records(models: pd.DataFrame, year: int, n: int, merge: bool = True) -> tuple[list[str], pd.DataFrame]:
    """Every model in one year with its organisations and whether it counts toward the top N."""
    data = attach_organisations(models, merge)
    in_year = data.loc[data["Year"] == year].copy()
    known = in_year.loc[in_year["Organisations"].str.len() > 0]
    top, _ = top_n_for_year(known, n) if not known.empty else ([], None)
    in_year["Counts toward top N"] = in_year["Organisations"].map(lambda orgs: any(o in top for o in orgs))
    in_year["Organisations (after merging)"] = in_year["Organisations"].str.join("; ")
    columns = ["Source record", "Model", "Publication date", "Organization",
               "Organisations (after merging)", "Counts toward top N", "Training compute (FLOP)"]
    return top, in_year[columns].sort_values(["Counts toward top N", "Source record"], ascending=[False, True])


def missing_compute(models: pd.DataFrame, start: int, end: int) -> tuple[int, int]:
    """Models in the range with no `Training compute (FLOP)` value, and the total."""
    in_range = models.loc[models["Year"].between(start, end)]
    missing = int(in_range["Training compute (FLOP)"].str.strip().eq("").sum())
    return missing, len(in_range)


def name_map_table() -> pd.DataFrame:
    return (pd.DataFrame(sorted(PARENT_MAP.items(), key=lambda kv: (kv[1], kv[0])),
                         columns=["Name in source", "Parent organisation"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed")
    args = parser.parse_args()
    models, _ = load_models(args.source)
    frames = []
    for n in TOP_N_OPTIONS:
        table = annual_concentration(models, n).assign(N=n)
        frames.append(table)
    out = pd.concat(frames)[["N", *frames[0].columns]]
    args.output.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output / "annual_concentration.csv", index=False)
    name_map_table().to_csv(args.output / "organisation_name_map.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
