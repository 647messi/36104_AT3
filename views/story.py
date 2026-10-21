"""The shared narrative; detailed analysis lives on individual student pages."""

import pandas as pd
import streamlit as st

from src.data_access import load_source
from src.preprocessing import FIRST_YEAR, LAST_YEAR, aggregate_counts


def sector_evidence() -> None:
    """Introduce the first chapter using numbers from the same source as its chart."""
    try:
        models, _ = load_source()
        annual = aggregate_counts(models, FIRST_YEAR, LAST_YEAR)
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        st.warning(f"The sector evidence could not be loaded: {exc}")
        return

    counts = annual.pivot(index="Year", columns="Sector", values="Count")
    comparison_year = max(FIRST_YEAR, LAST_YEAR - 10)
    industry_before = int(counts.loc[comparison_year, "Industry"])
    industry_after = int(counts.loc[LAST_YEAR, "Industry"])
    academia_before = int(counts.loc[comparison_year, "Academia"])
    academia_after = int(counts.loc[LAST_YEAR, "Academia"])
    st.markdown(
        f"In the local Epoch AI dataset, **{comparison_year}** records "
        f"**{industry_before} Industry-only models** and **{academia_before} Academia-only models**. "
        f"In **{LAST_YEAR}**, the corresponding counts are **{industry_after}** and "
        f"**{academia_after}**. These two years suggest a changing balance of participation; "
        "the full timeline shows whether that pattern holds across other years."
    )
    st.caption(
        "Industry–academia collaborations are counted separately. "
        "These are model counts in this snapshot, rather than relative sector shares."
    )


def main() -> None:
    st.caption("THE RISE OF ARTIFICIAL INTELLIGENCE · A GROUP DATA STORY")
    st.title("Who is driving the rise of AI?")
    st.markdown(
        "AI development is often described as a race between companies. "
        "To understand who is taking part, we begin with a broader comparison: "
        "industry, academia and the models they develop together. "
        "We then ask whether a change in sector participation also means that "
        "development is concentrated among a few organisations."
    )
    with st.container(border=True):
        st.markdown(
            "**Working group research question**\n\n"
            "Is the development of advanced AI becoming dominated by a few organisations?"
        )
        st.caption(
            "For technology policymakers and AI researchers interested in who develops "
            "notable AI models."
        )

    st.subheader("1. Start with who builds the models")
    sector_evidence()
    st.markdown(
        "The first dashboard compares annual model counts for Industry, Academia and "
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
        "Comparing sector shares is the next step in distinguishing these explanations."
    )
    st.caption("Next question for the story: how have relative sector shares changed?")

    st.subheader("3. Ask whether development is concentrated")
    st.markdown(
        "Industry includes many organisations. Even if industry produces most recorded "
        "models, that does not establish whether a few companies account for most of them. "
        "The planned Top 3 / Top 5 organisational analysis addresses that separate question."
    )
    st.caption("Planned chapter: organisational concentration. Its findings are still to be added.")

    st.divider()
    with st.expander("What this story measures"):
        st.markdown(
            f"The first chapter uses the local **Epoch AI Notable AI Models** dataset "
            f"for **{FIRST_YEAR}–{LAST_YEAR}**, with one count per model in its publication year. "
            "The incomplete 2026 calendar year is excluded.\n\n"
            "Notable models are a selected dataset, not an exhaustive census of AI research. "
            "These counts do not measure research quality or academic influence. "
            "Academia follows the source category and includes more than universities alone. "
            "Each dashboard documents its classifications and verification records.\n\n"
            "**Source:** Epoch AI, [Data on AI models](https://epoch.ai/data/ai-models). "
            "This app uses a local CSV snapshot; its download date was not recorded."
        )


if __name__ == "__main__":
    main()
