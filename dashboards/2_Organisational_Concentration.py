"""Organisational concentration: do the top organisations produce a growing share of notable AI models?"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.concentration import (
    DEFAULT_START, FIRST_YEAR, LAST_YEAR, NOTABLE_FILE, TOP_N_OPTIONS,
    annual_concentration, missing_compute, name_map_table, year_records,
)
from src.preprocessing import load_models


@st.cache_data(show_spinner=False)
def load_notable(modified_ns: int) -> tuple[pd.DataFrame, dict]:
    """Always read the Notable file; the modification time refreshes the cache."""
    return load_models(NOTABLE_FILE)

LINE_COLOUR = "#3b7dd8"      # mid blue: readable on light and dark themes, safe under colour vision deficiency
BAR_COLOUR = "#8c8c8c"


def concentration_chart(table: pd.DataFrame, n: int) -> go.Figure:
    data = table.dropna(subset=["Top N share (%)"])
    fig = go.Figure(go.Scatter(
        x=data["Year"], y=data["Top N share (%)"], mode="lines+markers+text",
        line={"color": LINE_COLOUR, "width": 3}, marker={"size": 8, "color": LINE_COLOUR},
        text=[f"{v:.0f}%" for v in data["Top N share (%)"]], textposition="top center",
        textfont={"size": 13},
        customdata=data[["Top N models", "Models with organisation", "Top N organisations"]],
        hovertemplate=("<b>%{x}</b><br>Top-" + str(n) + " share: %{y:.1f}%"
                       "<br>%{customdata[0]} of %{customdata[1]} models"
                       "<br>%{customdata[2]}<extra></extra>"),
    ))
    fig.update_layout(
        title=f"Share of notable AI models involving that year's top {n} organisations, {int(data['Year'].min())}–{int(data['Year'].max())}",
        xaxis={"title": "Publication year", "dtick": 1, "tickangle": 0},
        yaxis={"title": "Share of notable models (%)", "range": [0, 105],
               "ticksuffix": "%", "gridcolor": "rgba(128,128,128,0.25)"},
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=470, margin={"t": 60, "l": 70, "r": 20, "b": 50},
        font={"size": 13},
    )
    return fig


def organisations_chart(table: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=table["Year"], y=table["Organisations"], marker_color=BAR_COLOUR,
        text=table["Organisations"], textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y} distinct organisations<extra></extra>",
    ))
    fig.update_layout(
        title="Distinct organisations listed on notable AI models each year",
        xaxis={"title": "Publication year", "dtick": 1},
        yaxis={"title": "Organisations (count)", "gridcolor": "rgba(128,128,128,0.25)",
               "range": [0, max(1, table["Organisations"].max()) * 1.15]},
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=340, margin={"t": 60, "l": 70, "r": 20, "b": 50},
        font={"size": 13},
    )
    return fig


def main() -> None:
    st.page_link("views/story.py", label="Back to the story", icon=":material/arrow_back:")
    st.title("Are a few organisations producing a growing share of notable AI models?")
    st.markdown(
        "**Group question:** Is AI model development becoming dominated by a few organisations?  \n"
        "**Persona:** a technology policy analyst assessing who develops AI models and whether "
        "participation is becoming more concentrated.  \n"
        "**This page asks:** each year, what share of notable AI models involves that year's "
        "top 3 (or top 5) organisations — and is that share rising?"
    )

    try:
        models, quality = load_notable(NOTABLE_FILE.stat().st_mtime_ns)
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        st.error(f"The source data could not be loaded: {exc}")
        return

    controls = st.columns([1, 2, 1.4])
    n = controls[0].radio("Top organisations", TOP_N_OPTIONS, horizontal=True,
                          format_func=lambda v: f"Top {v}", key="conc_n")
    start, end = controls[1].slider("Publication years", FIRST_YEAR, LAST_YEAR,
                                    (DEFAULT_START, LAST_YEAR), key="conc_years")
    merge = controls[2].toggle("Merge company name variants", value=True, key="conc_merge",
                            help="Groups e.g. DeepMind, Google Brain and Google Research under Google. Full list under Source and methodology.")

    table = annual_concentration(models, n, start, end, merge)
    plotted = table.dropna(subset=["Top N share (%)"])
    if plotted.empty:
        st.info("No models with a recorded organisation fall in the selected years. Widen the year range.")
        return

    first, last = plotted.iloc[0], plotted.iloc[-1]
    peak = plotted.loc[plotted["Top N share (%)"].idxmax()]
    st.markdown(
        f"In **{int(first['Year'])}**, the top {n} organisations were involved in "
        f"**{first['Top N share (%)']:.0f}%** of notable models "
        f"({int(first['Top N models'])} of {int(first['Models with organisation'])}). "
        f"In **{int(last['Year'])}** the share was **{last['Top N share (%)']:.0f}%** "
        f"({int(last['Top N models'])} of {int(last['Models with organisation'])}); "
        f"the highest share in this range was **{peak['Top N share (%)']:.0f}%** in {int(peak['Year'])}."
    )

    st.plotly_chart(concentration_chart(table, n), use_container_width=True)
    st.caption(
        f"Each point is one publication year. A model counts once if any of its listed organisations "
        f"is among that year's top {n} by number of notable models; the share is out of all models with "
        f"at least one recorded organisation. "
        f"{'Corporate name variants are merged into their parent organisation.' if merge else 'Organisation names are used exactly as recorded.'} "
        "Source: Epoch AI, Notable AI Models (CC BY 4.0)."
    )
    if start < DEFAULT_START:
        st.warning("Before 2014 there are fewer than 20 notable models a year, so a few models can "
                   "move the share by tens of percentage points.")

    st.subheader("Who were the top organisations?")
    shown = table[["Year", "Top N organisations", "Top N models", "Models with organisation",
                   "Top N share (%)", "Organisations"]].rename(columns={
        "Top N organisations": f"Top {n} organisations (models each)",
        "Top N models": f"Models involving top {n}",
        "Models with organisation": "Models with an organisation",
        "Top N share (%)": f"Top-{n} share (%)",
        "Organisations": "Distinct organisations"})
    st.dataframe(shown.sort_values("Year", ascending=False), hide_index=True, use_container_width=True)

    st.subheader("How many organisations take part?")
    st.plotly_chart(organisations_chart(table), use_container_width=True)
    st.caption("Count of distinct organisations listed on that year's notable models. Large multi-institution "
               "papers can raise this count in a single year. Source: Epoch AI, Notable AI Models.")

    st.subheader("What this suggests")
    st.markdown(
        "With the default settings (2014–2025, merged names), the top organisations hold a large but not "
        "steadily growing share of notable models: "
        "it is higher around 2019–2022 than in 2023–2024. Concentration by this measure has not risen "
        "steadily. Read this together with the count of participating organisations and the limits below."
    )

    with st.expander("What this data cannot show", expanded=True):
        missing, total = missing_compute(models, max(start, 2023), end) if end >= 2023 else (0, 0)
        st.markdown(
            "- **Capability or compute concentration.** Counting models treats a small research model and a "
            "frontier model equally. "
            + (f"Training compute is missing for **{missing} of {total}** notable models published "
               f"{max(start, 2023)}–{end}, mostly large closed models, so a compute-based share would "
               "measure who discloses compute rather than who holds it. " if total else "")
            + "\n- **All AI development.** Epoch AI's notable list is a curated selection, not a census, and "
            "recent years may gain records retrospectively.\n"
            "- **Ownership or influence.** A model is attributed to every organisation listed on it; the data "
            "does not record who led the work. Merging uses current corporate parents (e.g. DeepMind before "
            "its 2014 acquisition is still grouped with Google).\n"
            "- **2026.** The incomplete calendar year is excluded."
        )

    st.subheader("Verify a displayed number")
    v_cols = st.columns([1, 3])
    available = [int(y) for y in plotted["Year"]]
    year = v_cols[0].selectbox("Year", available[::-1], key="conc_verify_year")
    top, records = year_records(models, year, n, merge)
    row = table.loc[table["Year"] == year].iloc[0]
    v_cols[1].markdown(
        f"**{year}, top {n}:** {', '.join(top)}  \n"
        f"Models listing at least one of them: **{int(row['Top N models'])}** · "
        f"models with an organisation: **{int(row['Models with organisation'])}** · "
        f"share: {int(row['Top N models'])} ÷ {int(row['Models with organisation'])} = "
        f"**{row['Top N share (%)']:.1f}%**"
        + (f"  \n{int(row['Missing organisation'])} model(s) with no organisation are excluded."
           if row["Missing organisation"] else "")
    )
    st.dataframe(records, hide_index=True, use_container_width=True)
    st.download_button("Download these records (CSV)", records.to_csv(index=False).encode("utf-8"),
                       file_name=f"concentration_{year}_top{n}.csv", mime="text/csv", key="conc_download")
    st.caption("`Source record` is the one-based record number in data/raw/ai_models/notable_ai_models.csv "
               "(excluding the header), so each row can be found in the unchanged source file.")

    with st.expander("Source and methodology"):
        st.markdown(
            f"**Source:** Epoch AI, [Data on AI models](https://epoch.ai/data/ai-models), "
            f"`{quality['source_file']}` ({quality['raw_rows']} records, latest publication date "
            f"{quality['latest_date']}). Licence: CC BY 4.0.\n\n"
            "**Unit:** one notable model, counted once in the year of `Publication date`.\n\n"
            "**Steps:** split `Organization` on commas; merge the corporate name variants listed below; "
            "rank organisations each year by the number of models listing them (ties broken alphabetically); "
            "count models listing at least one top-N organisation; divide by models with at least one organisation.\n\n"
            "**Processing module:** `src/concentration.py` (regenerate exports with `python -m src.concentration`)."
        )
        st.dataframe(name_map_table(), hide_index=True, use_container_width=True)


if __name__ == "__main__":
    main()
