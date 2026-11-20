"""The shared narrative; detailed analysis lives on individual student pages."""

from pathlib import Path

import pandas as pd
import streamlit as st

from src.data_access import load_source
from src.preprocessing import (
    DEFAULT_SOURCE,
    FIRST_YEAR,
    LAST_YEAR,
    NOTABLE_SOURCE,
    aggregate_counts,
    calculate_shares,
)


def load_evidence(source: Path) -> pd.DataFrame | None:
    """Use the dashboard's source and transformations for the story's evidence."""
    try:
        models, _ = load_source(source)
        return calculate_shares(
            aggregate_counts(models, FIRST_YEAR, LAST_YEAR)
        ).set_index(["Year", "Sector"])
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        st.warning(f"The {source.name} evidence could not be loaded: {exc}")
        return None


def sector_evidence(annual: pd.DataFrame, comparison_year: int) -> None:
    """Introduce the count comparison without treating shares as counts."""
    industry_before = int(annual.loc[(comparison_year, "Industry"), "Count"])
    industry_after = int(annual.loc[(LAST_YEAR, "Industry"), "Count"])
    academia_before = int(annual.loc[(comparison_year, "Academia"), "Count"])
    academia_after = int(annual.loc[(LAST_YEAR, "Academia"), "Count"])
    st.markdown(
        f"In the local Epoch AI **All** dataset, Industry-only model counts rise from "
        f"**{industry_before} in {comparison_year}** to **{industry_after} in {LAST_YEAR}**. "
        f"Academia-only counts change from **{academia_before}** to **{academia_after}** "
        "over the same years. The full timeline shows how the two trajectories develop "
        "between these endpoints."
    )
    st.caption(
        "Industry–academia collaborations are counted separately. "
        f"This ten-year comparison sits within the full {FIRST_YEAR}–{LAST_YEAR} timeline."
    )


def main() -> None:
    st.caption("THE RISE OF ARTIFICIAL INTELLIGENCE · A GROUP DATA STORY")
    st.title("Who is driving the rise of AI?")
    st.markdown(
        "Who develops the AI models recorded by Epoch AI, and how has that changed? "
        "We begin by comparing industry, academia and the models they develop together. "
        "We then ask whether a change in sector participation also means that "
        "development is concentrated among a few organisations."
    )
    with st.container(border=True):
        st.markdown(
            "**Working group research question**\n\n"
            "Is AI model development becoming dominated by a few organisations?"
        )
        st.caption(
            "Proposed target persona: a technology policy analyst assessing who develops "
            "AI models and whether participation is becoming more concentrated."
        )

    st.subheader("1. Start with who builds the models")
    annual = load_evidence(DEFAULT_SOURCE)
    comparison_year = max(FIRST_YEAR, LAST_YEAR - 10)
    if annual is not None:
        sector_evidence(annual, comparison_year)
    st.markdown(
        "The first chart compares annual model counts for Industry, Academia and "
        "their joint development. Explore different time windows, compare the trajectories, "
        "and trace a displayed number back to its source records."
    )
    st.page_link(
        "dashboards/1_Industry_vs_Academia.py",
        label="Explore the Industry vs Academia dashboard",
        icon=":material/arrow_forward:",
    )

    st.subheader("2. Put growth in context")
    st.markdown(
        "An increase in industry model counts could reflect growth across the whole "
        "dataset, an increase in industry's relative contribution, or both. "
        "Chart 2 compares the shares of all recorded models in each category to distinguish "
        "these explanations. Other and Unknown remain in the denominator, so the full "
        "composition adds up to 100%."
    )
    if annual is not None:
        industry_before = annual.loc[(comparison_year, "Industry")]
        industry_after = annual.loc[(LAST_YEAR, "Industry")]
        academia_before = annual.loc[(comparison_year, "Academia")]
        academia_after = annual.loc[(LAST_YEAR, "Academia")]
        if industry_before["Total"] > 0 and industry_after["Total"] > 0:
            st.markdown(
                f"Industry accounts for **{industry_before['Share']:.1f}%** of All records "
                f"in {comparison_year} ({int(industry_before['Count'])} of "
                f"{int(industry_before['Total'])}), compared with "
                f"**{industry_after['Share']:.1f}%** in {LAST_YEAR} "
                f"({int(industry_after['Count'])} of {int(industry_after['Total'])}). "
                "Its growth therefore includes an increase in relative share. "
                f"Academia's share falls from **{academia_before['Share']:.1f}%** to "
                f"**{academia_after['Share']:.1f}%**, even though its recorded count "
                "does not fall between these endpoints. A smaller share alone does not "
                "show a decline in academic research quality or influence."
            )
    st.page_link(
        "dashboards/1_Industry_vs_Academia.py",
        label="Compare relative shares in Chart 2",
        icon=":material/arrow_forward:",
    )

    st.subheader("3. Check the Notable sample")
    st.markdown(
        "The broader All dataset and Epoch's selected Notable models can produce different "
        "sector shares. The comparison below the two main charts asks whether the direction "
        "of industry's change is consistent across both samples, using the same years and "
        "sector classification. Each sample keeps its own denominator."
    )
    notable = load_evidence(NOTABLE_SOURCE)
    if annual is not None and notable is not None:
        all_latest = annual.loc[(LAST_YEAR, "Industry")]
        notable_latest = notable.loc[(LAST_YEAR, "Industry")]
        if all_latest["Total"] > 0 and notable_latest["Total"] > 0:
            gap = notable_latest["Share"] - all_latest["Share"]
            st.markdown(
                f"In **{LAST_YEAR}**, Industry represents "
                f"**{notable_latest['Share']:.1f}%** of Notable models "
                f"({int(notable_latest['Count'])} of {int(notable_latest['Total'])}), "
                f"compared with **{all_latest['Share']:.1f}%** in All: "
                f"a difference of **{gap:+.1f} percentage points** (Notable minus All). "
                "The strength of the sector imbalance depends on which sample is used. "
                "Notable is a selected subset of All, so these are overlapping samples, "
                "rather than independent confirmation."
            )
    st.page_link(
        "dashboards/1_Industry_vs_Academia.py", label="Examine the Notable comparison",
        icon=":material/arrow_forward:",
    )

    st.subheader("4. Ask whether development is concentrated")
    st.markdown(
        "Industry includes many organisations. Even if industry produces most recorded "
        "models, that does not establish whether a few companies account for most of them."
    )
    st.markdown(
        "In Epoch AI's **Notable** models, the three organisations with the most models each "
        "year were involved in **36%** of models in 2014, a peak of **60%** in 2020, **32%** in "
        "2024 and **44%** in 2025 (share of models with a recorded organisation). Over "
        "2014–2025, Google appears on 194 of 814 models (24%), followed by Meta (11%) and "
        "OpenAI (8%). Development is concentrated, but on this measure it is not steadily "
        "becoming more so."
    )
    st.caption(
        "Counts models, not computing power: training compute is missing for over half of "
        "recent notable models, mostly the largest closed ones."
    )
    st.page_link(
        "dashboards/2_Organisational_Concentration.py",
        label="Explore organisational concentration",
        icon=":material/arrow_forward:",
    )

    st.divider()
    with st.expander("What this story measures"):
        st.markdown(
            f"The two main charts use the local **Epoch AI All AI Models** dataset "
            f"for **{FIRST_YEAR}–{LAST_YEAR}**, with one count per model in its publication year. "
            "The incomplete 2026 calendar year and records without a publication date are excluded "
            "from annual comparisons. A separate section compares the Notable sample.\n\n"
            "All refers to all records in Epoch's database snapshot. It is a selected collection, "
            "not an exhaustive census of AI research. "
            "These counts do not measure research quality or academic influence. "
            "Academia follows the source category and includes more than universities alone. "
            "Each dashboard documents its classifications and verification records.\n\n"
            "**Source:** Epoch AI, [Data on AI models](https://epoch.ai/data/ai-models). "
            "This app uses a local CSV snapshot; its download date was not recorded."
        )


if __name__ == "__main__":
    main()
