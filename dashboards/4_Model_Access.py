"""Open weights or developer-controlled APIs: how notable AI models are made available."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.model_access import (
    ACCESS_TYPES,
    CONTROLLED,
    DEFAULT_START,
    MIN_RECORDED,
    NOT_RECORDED,
    NOTABLE_FILE,
    SNAPSHOT_ADDED,
    add_access,
    annual_access,
    share_of,
    values_table,
)
from src.preprocessing import FIRST_YEAR, LAST_YEAR, load_models

# Okabe-Ito colours, distinguishable with common colour-vision deficiencies.
COLOURS = {
    "Open weights": "#0072B2",
    "API access": "#E69F00",
    "Hosted or limited access": "#CC79A7",
    "Unreleased": "#7F7F7F",
}
SOURCE_FIELDS = [
    "Source record", "Model", "Organization", "Publication date",
    "Model accessibility", "Access", "Link",
]


@st.cache_data(show_spinner=False)
def load_notable(modified_ns: int) -> tuple[pd.DataFrame, dict]:
    """Always read the Notable file, whatever the shared default source is.

    The modification time is part of the cache key, so an updated file is reread.
    """
    return load_models(NOTABLE_FILE)


def pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.0%}"


def composition_chart(annual: pd.DataFrame, as_share: bool) -> go.Figure:
    data = annual.loc[annual["Access"] != NOT_RECORDED].copy()
    data["Value"] = data["Share"] * 100 if as_share else data["Count"]
    data["Label"] = data.apply(
        lambda r: (f"{r['Share']:.0%}" if as_share else f"{r['Count']:d}")
        if r["Count"] > 0 else "", axis=1)
    fig = px.bar(
        data, x="Year", y="Value", color="Access", text="Label",
        category_orders={"Access": list(ACCESS_TYPES)},
        color_discrete_map=COLOURS,
        custom_data=["Count", "Recorded", "Share"],
    )
    fig.update_traces(
        textposition="inside", insidetextanchor="middle", textfont_size=11,
        hovertemplate="%{x} · %{fullData.name}<br>%{customdata[0]} of "
                      "%{customdata[1]} recorded models (%{customdata[2]:.0%})<extra></extra>",
    )
    # Fade years with too few recorded models for a stable share.
    thin = set(data.loc[data["Thin year"], "Year"])
    for trace in fig.data:
        trace.marker.opacity = [0.35 if year in thin else 1 for year in trace.x]
    totals = data.groupby("Year")["Recorded"].first()
    fig.add_trace(go.Scatter(
        x=totals.index, y=[100 if as_share else v for v in totals.values],
        mode="text", text=[f"n={v}" for v in totals.values], textposition="top center",
        textfont=dict(size=10, color="#59616f"), showlegend=False, hoverinfo="skip",
    ))
    fig.update_layout(
        barmode="stack", height=460, margin=dict(t=40, b=10, l=10, r=10),
        legend=dict(orientation="h", y=1.1, x=0, title=None),
        uniformtext_minsize=9, uniformtext_mode="hide",
        yaxis_title="Share of models with recorded access (%)" if as_share
        else "Number of notable models",
        xaxis=dict(title="Publication year", dtick=1),
    )
    if as_share:
        fig.update_yaxes(range=[0, 108], ticksuffix="%")
    return fig


def trend_chart(annual: pd.DataFrame) -> go.Figure | None:
    rows = []
    for year in sorted(annual["Year"].unique()):
        recorded = int(annual.loc[annual["Year"] == year, "Recorded"].iloc[0])
        for label, group in (("Open weights", ("Open weights",)),
                             ("Developer-controlled (API, hosted or limited)", CONTROLLED),
                             ("Unreleased", ("Unreleased",))):
            share = share_of(annual, year, group)
            if share is not None and recorded >= MIN_RECORDED:
                rows.append({"Year": year, "Group": label, "Share": share * 100})
    data = pd.DataFrame(rows)
    if data.empty:
        return None
    fig = px.line(
        data, x="Year", y="Share", color="Group", markers=True,
        line_dash="Group", text=data["Share"].round(0).astype(int).astype(str) + "%",
        color_discrete_map={
            "Open weights": COLOURS["Open weights"],
            "Developer-controlled (API, hosted or limited)": COLOURS["API access"],
            "Unreleased": COLOURS["Unreleased"],
        },
    )
    fig.update_traces(textposition="top center", textfont_size=10,
                      hovertemplate="%{x} · %{fullData.name}: %{y:.0f}%<extra></extra>")
    fig.update_layout(
        height=400, margin=dict(t=40, b=10, l=10, r=10),
        legend=dict(orientation="h", y=1.12, x=0, title=None),
        yaxis=dict(title="Share of models with recorded access (%)", range=[0, 105],
                   ticksuffix="%"),
        xaxis=dict(title="Publication year", dtick=1),
    )
    return fig


def moved(before: float, after: float) -> str:
    """Describe a change in share without assuming its direction."""
    points = (after - before) * 100
    if abs(points) < 1:
        return f"stayed at about {pct(after)}"
    return f"{'rose' if points > 0 else 'fell'} from {pct(before)} to {pct(after)}"


def summary(annual: pd.DataFrame, first: int, last: int) -> str:
    """Answer the question in words, using only the two endpoint years shown."""
    unrel = [share_of(annual, y, ("Unreleased",)) for y in (first, last)]
    ctrl = [share_of(annual, y, CONTROLLED) for y in (first, last)]
    open_ = [share_of(annual, y, ("Open weights",)) for y in (first, last)]
    text = (f"**What it shows:** between {first} and {last}, the share of notable models that "
            f"were never released {moved(*unrel)}. Developer-controlled access (API, hosted or "
            f"limited) {moved(*ctrl)}, and open weights {moved(*open_)}. ")
    ctrl_gain, open_gain = ctrl[1] - ctrl[0], open_[1] - open_[0]
    if ctrl_gain > open_gain and ctrl_gain > 0:
        text += ("More models became usable by outsiders, but most of that gain is access on "
                 "the developer's terms rather than downloadable weights.")
    elif open_gain >= ctrl_gain and open_gain > 0:
        text += "In this window, openly downloadable weights grew at least as fast as controlled access."
    else:
        text += "Neither open nor controlled access grew in this window."
    return text + " These are endpoint comparisons; check the full trajectory below."


def main() -> None:
    st.page_link("views/story.py", label="Back to the story", icon=":material/arrow_back:")
    st.title("Open weights or controlled access?")
    st.markdown(
        "**Research question:** Are notable AI models becoming more openly available, "
        "or is access shifting to developer-controlled APIs?"
    )
    st.write(
        "Concentration is not only about who builds models. It is also about who decides "
        "how others can use them. A model with open weights can be downloaded and run by "
        "anyone; a model behind an API or hosted service stays under its developer's control."
    )

    try:
        models, quality = load_notable(NOTABLE_FILE.stat().st_mtime_ns)
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        st.warning(f"The model data could not be loaded: {exc}")
        return
    st.caption(f"Source: Epoch AI, Notable AI Models (CC BY 4.0) · last data refresh: snapshot added "
               f"{SNAPSHOT_ADDED} · latest publication date in the file: {quality['latest_date']} · "
               f"{quality['raw_rows']:,} records")

    c1, c2 = st.columns([3, 2])
    start, end = c1.slider(
        "Publication years", FIRST_YEAR, LAST_YEAR, (DEFAULT_START, LAST_YEAR),
        key="ma_years",
    )
    as_share = c2.radio(
        "Show", ["Share of recorded models", "Number of models"],
        horizontal=True, key="ma_measure",
    ) == "Share of recorded models"

    annual = annual_access(models, start, end)
    recorded_total = int(annual.loc[annual["Access"] != NOT_RECORDED, "Count"].sum())
    if recorded_total == 0:
        st.info("No model in the selected years has a recorded accessibility. "
                f"Widen the year range; recorded access is sparse before {DEFAULT_START}.")
        return

    years = sorted(annual["Year"].unique())
    usable = [y for y in years
              if int(annual.loc[annual["Year"] == y, "Recorded"].iloc[0]) >= MIN_RECORDED]
    if len(usable) >= 2:
        first, last = usable[0], usable[-1]
        st.subheader(f"How access changed, {first} to {last}")
        k1, k2, k3 = st.columns(3)
        for col, label, group in ((k1, "Unreleased", ("Unreleased",)),
                                  (k2, "Developer-controlled", CONTROLLED),
                                  (k3, "Open weights", ("Open weights",))):
            before, after = share_of(annual, first, group), share_of(annual, last, group)
            col.metric(f"{label}, {last}", pct(after), f"{(after - before) * 100:+.0f} pts since {first}",
                       delta_color="off",
                       help=f"{first}: {pct(before)}. Share of models with recorded access.")
        st.info(summary(annual, first, last))
    else:
        st.warning(
            f"Fewer than two years in this range have {MIN_RECORDED} or more recorded models, "
            "so no change is summarised. Widen the year range for a reliable comparison."
        )

    st.subheader("Access type of notable AI models, by publication year")
    st.plotly_chart(composition_chart(annual, as_share), width="stretch", key="ma_stack")
    st.caption(
        f"Each bar is one publication year; n = models with a recorded accessibility in that "
        f"year. Faded bars have fewer than {MIN_RECORDED} recorded models, so their shares are "
        "unstable. Models with no recorded accessibility are excluded from the bars and listed "
        "in the verification table below. Segments too thin for a label are listed in the "
        "table that follows."
    )
    st.markdown("**Every value in the chart**" + (
        " (share of recorded models, with the number of models in brackets)" if as_share
        else " (number of models)"))
    values = values_table(annual, as_share)
    # Tall enough for every year (35 px per row plus the header), so no row is hidden.
    st.dataframe(values, hide_index=True, width="stretch", height=35 * (len(values) + 1) + 3,
                 key="ma_values")

    st.subheader("Open weights against developer-controlled access")
    trend = trend_chart(annual)
    if trend is None:
        st.info(f"No year in this range has {MIN_RECORDED} or more recorded models. "
                "Widen the year range to compare trajectories.")
    else:
        st.plotly_chart(trend, width="stretch", key="ma_trend")
    st.caption(
        "The same shares as the bars above, drawn as lines so the three trajectories can be "
        f"compared directly. Years with fewer than {MIN_RECORDED} recorded models are omitted."
    )

    with st.expander("Verify a displayed number", expanded=False):
        v1, v2 = st.columns(2)
        year = v1.selectbox("Year", years, index=len(years) - 1, key="ma_verify_year")
        access = v2.selectbox("Access type", [*ACCESS_TYPES, NOT_RECORDED], key="ma_verify_access")
        row = annual.loc[(annual["Year"] == year) & (annual["Access"] == access)].iloc[0]
        if access == NOT_RECORDED:
            st.markdown(f"**{int(row['Count'])}** models in {year} have no recorded accessibility "
                        "(excluded from the shares).")
        else:
            st.markdown(
                f"**{int(row['Count'])} of {int(row['Recorded'])}** recorded models in {year} are "
                f"**{access}** = **{pct(row['Share'] if row['Recorded'] else None)}**."
            )
        matches = add_access(models).loc[lambda d: (d["Year"] == year) & (d["Access"] == access),
                                         SOURCE_FIELDS]
        st.dataframe(matches, hide_index=True, width="stretch")
        st.download_button(
            "Download these source rows (CSV)", matches.to_csv(index=False).encode("utf-8"),
            file_name=f"model_access_{year}_{access.replace(' ', '_').lower()}.csv",
            mime="text/csv", key="ma_download",
        )
        st.caption("Source record is the one-based data-record number in "
                   "data/raw/ai_models/notable_ai_models.csv (excluding the header).")

    with st.expander("Source and methodology"):
        st.markdown(
            f"""
**Source:** Epoch AI, [Data on AI models](https://epoch.ai/data/ai-models), local file
`data/raw/ai_models/notable_ai_models.csv` (CC BY 4.0). Unit: one notable model, counted once
in the year of its *Publication date*, {FIRST_YEAR}–{LAST_YEAR} (2026 is incomplete and excluded).

**Access types** come from the source field *Model accessibility*, grouped in `src/model_access.py`:

| Source value | Access type |
| --- | --- |
| Open weights (unrestricted), Open weights (non-commercial), Open weights (restricted use) | Open weights |
| API access | API access |
| Hosted access (no API), Limited access | Hosted or limited access |
| Unreleased | Unreleased |
| blank | Not recorded (excluded from shares) |

API access and Hosted or limited access together are **developer-controlled**: outsiders can use the model,
but the developer keeps the weights and sets the terms. Shares use models with a recorded
accessibility as the denominator.

**What the data cannot show:** accessibility is the status Epoch AI recorded, not necessarily the
status at release, and it is missing for about one in five models (mostly before {DEFAULT_START}).
Notable models are a curated selection, not every AI model. The counts say how models are made
available, not how widely they are used, how capable they are, or which licences apply in detail.
"""
        )


if __name__ == "__main__":
    main()
