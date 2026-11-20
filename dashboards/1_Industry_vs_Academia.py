"""Individual dashboard: All AI models, followed by a Notable sample comparison."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data_access import load_source
from src.preprocessing import (
    ALL_SECTORS,
    CHART_SECTORS,
    FIRST_YEAR,
    LAST_YEAR,
    NOTABLE_SOURCE,
    aggregate_counts,
    calculate_shares,
    compare_sector_shares,
)


COLORS = {
    "Industry": "#0072B2", "Academia": "#D55E00", "Collaboration": "#009E73",
    "Other": "#7A828D", "Unknown": "#D3D8E0",
}
DASHES = {"Industry": "solid", "Academia": "dash", "Collaboration": "dot"}


def make_chart(annual: pd.DataFrame, start: int, end: int) -> go.Figure:
    fig = go.Figure()
    for sector in CHART_SECTORS:
        points = annual.loc[annual["Sector"].eq(sector)]
        fig.add_trace(
            go.Scatter(
                x=points["Year"],
                y=points["Count"],
                name=sector,
                mode="lines+markers",
                line={"color": COLORS[sector], "width": 3, "dash": DASHES[sector]},
                marker={"size": 7},
                hovertemplate=f"{sector}: %{{y:d}} models<extra></extra>",
            )
        )
    fig.update_layout(
        template="plotly_white",
        height=470,
        margin={"t": 35, "b": 35, "l": 15, "r": 20},
        hovermode="x unified",
        legend={"orientation": "h", "x": 0, "y": 1.13, "title": {"text": ""}},
        font={"size": 15},
        xaxis={
            "title": "Publication year",
            "tickformat": "d",
            "dtick": 1 if end - start <= 12 else 2,
            "range": [start - 0.35, end + 0.35],
            "showgrid": False,
        },
        yaxis={"title": "Number of AI models (All dataset)", "rangemode": "tozero", "tickformat": "d"},
    )
    return fig


def make_share_chart(shares: pd.DataFrame, start: int, end: int) -> go.Figure:
    """Stack precomputed shares without renormalising when a category is hidden."""
    fig = go.Figure()
    valid_years = sorted(shares.loc[shares["Total"].gt(0), "Year"].unique().tolist())
    blocks = []
    for year in valid_years:
        if not blocks or year != blocks[-1][-1] + 1:
            blocks.append([])
        blocks[-1].append(year)

    # Separate blocks leave genuine gaps for undefined years. A single recorded
    # year uses a composition bar; it cannot supply an area over a time interval.
    for sector in ALL_SECTORS:
        for index, years in enumerate(blocks):
            points = shares.loc[shares["Sector"].eq(sector) & shares["Year"].isin(years)]
            options = {
                "x": points["Year"].tolist(),
                "y": points["Share"].tolist(),
                "name": sector,
                "legendgroup": sector,
                "showlegend": index == 0,
                "customdata": points[["Share", "Count", "Total"]].values.tolist(),
                "hovertemplate": (
                    f"{sector}: %{{customdata[0]:.1f}}%"
                    "<br>%{customdata[1]:.0f} / %{customdata[2]:.0f} models<extra></extra>"
                ),
            }
            if len(years) == 1:
                fig.add_trace(go.Bar(**options, marker_color=COLORS[sector], width=0.65))
            else:
                fig.add_trace(
                    go.Scatter(
                        **options,
                        mode="lines",
                        stackgroup=f"sector_block_{index}",
                        line={"color": COLORS[sector], "width": 0.5},
                        fillcolor=COLORS[sector],
                        connectgaps=False,
                    )
                )
    fig.update_layout(
        template="plotly_white",
        height=450,
        margin={"t": 35, "b": 35, "l": 15, "r": 20},
        hovermode="x unified",
        barmode="stack",
        legend={
            "orientation": "h", "x": 0, "y": 1.13, "title": {"text": ""},
            "traceorder": "normal", "itemclick": False, "itemdoubleclick": False,
        },
        font={"size": 15},
        xaxis={
            "title": "Publication year", "tickformat": "d",
            "dtick": 1 if end - start <= 12 else 2,
            "range": [start - 0.5, end + 0.5], "showgrid": False,
        },
        yaxis={
            "title": "Share of AI models (All dataset)", "range": [0, 100],
            "dtick": 20, "ticksuffix": "%",
        },
    )
    return fig


def share_comparison(shares: pd.DataFrame, start: int, end: int) -> None:
    industry = shares.loc[shares["Sector"].eq("Industry")].set_index("Year")
    first, last = industry.loc[start], industry.loc[end]
    if start == end or first["Total"] == 0 or last["Total"] == 0:
        return
    change = last["Share"] - first["Share"]
    count_change = last["Count"] - first["Count"]
    st.markdown(
        f"Industry's share changes from **{first['Share']:.1f}%** in {start} to "
        f"**{last['Share']:.1f}%** in {end}, a change of **{change:+.1f} percentage points**. "
        f"Its annual count changes from **{int(first['Count']):,}** to **{int(last['Count']):,}**, "
        f"while the annual total across all categories changes from "
        f"**{int(first['Total']):,}** to **{int(last['Total']):,}**."
    )
    if count_change > 0 and change > 1e-9:
        st.write(
            "Industry's count and relative share both increase between these endpoints. "
            "The increase is accompanied by a shift in sector composition."
        )
    elif count_change > 0:
        st.write(
            "Industry's count increases without an increase in its relative share. "
            "A higher model count alone does not demonstrate a shift towards industry."
        )
    elif change > 1e-9:
        st.write(
            "Industry's relative share increases without an increase in its annual count. "
            "A larger share can also reflect lower counts in other categories."
        )
    else:
        st.write("These endpoints show no increase in Industry's relative share.")
    st.caption(
        "This is an endpoint comparison; inspect the full series and change the time window. "
        "Small annual totals can produce large percentage changes."
    )


def notable_comparison(all_shares: pd.DataFrame, notable_shares: pd.DataFrame, start: int, end: int) -> None:
    st.markdown(
        "**Does the sector pattern change when we focus on notable models?** Epoch AI's "
        "Notable sample uses criteria such as benchmark improvements, citations, significant "
        "use, historical significance and development cost. We use its published Notable CSV "
        "and apply the same years and sector classification as the All analysis."
    )
    st.caption(
        f"{start}–{end} · All: {int(all_shares['Count'].sum()):,} models · "
        f"Notable: {int(notable_shares['Count'].sum()):,} models. "
        "The samples overlap and are compared separately; their counts are not added together."
    )
    fig = go.Figure()
    for name, data, color, dash in [
        ("All", all_shares, COLORS["Industry"], "solid"),
        ("Notable", notable_shares, "#A56CC1", "dash"),
    ]:
        points = data.loc[data["Sector"].eq("Industry")]
        fig.add_trace(go.Scatter(
            x=points["Year"].tolist(), y=points["Share"].tolist(),
            name=name, mode="lines+markers", connectgaps=False,
            line={"color": color, "width": 3, "dash": dash}, marker={"size": 6},
            customdata=points[["Count", "Total"]].values.tolist(),
            hovertemplate=(
                f"{name}: %{{y:.1f}}%<br>"
                "%{customdata[0]:.0f} Industry / %{customdata[1]:.0f} total<extra></extra>"
            ),
        ))
    fig.update_layout(
        template="plotly_white", height=370, hovermode="x unified",
        margin={"t": 35, "b": 35, "l": 15, "r": 20}, font={"size": 15},
        legend={"orientation": "h", "x": 0, "y": 1.13},
        xaxis={"title": "Publication year", "tickformat": "d", "range": [start - 0.35, end + 0.35]},
        yaxis={"title": "Industry share within each sample", "range": [0, 100], "ticksuffix": "%"},
    )
    st.plotly_chart(fig, width="stretch", key="notable_comparison_chart", config={"displaylogo": False})
    st.caption("Each line uses its own sample's annual total, including Other and Unknown, as its denominator.")

    comparison = compare_sector_shares(all_shares, notable_shares)
    latest = comparison.loc[comparison["Year"].eq(end)]
    st.markdown(f"**Sector comparison in {end}**")
    display = latest[["Sector", "Count_All", "Count_Notable", "Share_All", "Share_Notable", "Share_gap_pp"]].rename(columns={
        "Count_All": "All count", "Count_Notable": "Notable count",
        "Share_All": "All share (%)", "Share_Notable": "Notable share (%)",
        "Share_gap_pp": "Notable − All (pp)",
    })
    st.dataframe(display, hide_index=True, width="stretch", column_config={
        name: st.column_config.NumberColumn(format="%.2f")
        for name in ["All share (%)", "Notable share (%)", "Notable − All (pp)"]
    })
    last = latest.loc[latest["Sector"].eq("Industry")].iloc[0]
    if pd.notna(last["Share_gap_pp"]):
        st.markdown(
            f"In {end}, Industry accounts for **{last['Share_Notable']:.1f}%** of Notable models "
            f"(**{int(last['Count_Notable']):,}/{int(last['Total_Notable']):,}**) and "
            f"**{last['Share_All']:.1f}%** of All models "
            f"(**{int(last['Count_All']):,}/{int(last['Total_All']):,}**). "
            f"The difference is **{last['Share_gap_pp']:+.1f} percentage points**."
        )
    first = comparison.loc[comparison["Year"].eq(start) & comparison["Sector"].eq("Industry")].iloc[0]
    if start < end and pd.notna(first["Share_All"]) and pd.notna(first["Share_Notable"]) and pd.notna(last["Share_gap_pp"]):
        changes = [last[f"Share_{scope}"] - first[f"Share_{scope}"] for scope in ["All", "Notable"]]
        signs = [0 if abs(value) < 1e-9 else (1 if value > 0 else -1) for value in changes]
        if signs[0] == signs[1]:
            direction = {1: "an increase", -1: "a decrease", 0: "no change"}[signs[0]]
            st.write(
                f"Both samples show {direction} in Industry's share between {start} and {end}. "
                "The direction of this endpoint comparison is consistent across the two samples."
            )
        else:
            st.write("The direction of the endpoint share change differs between the samples in this window.")
    st.caption(
        "Sample selection changes the measured shares. This comparison does not identify which "
        "notability criterion causes a difference, measure model capability, or establish concentration among companies."
    )
    st.download_button(
        "Download All vs Notable comparison", comparison.to_csv(index=False).encode("utf-8"),
        file_name=f"all_vs_notable_{start}_{end}.csv", mime="text/csv",
    )


def main() -> None:
    st.page_link("views/story.py", label="Back to the story", icon=":material/arrow_back:")
    st.caption("INDUSTRY VS ACADEMIA · COUNTS AND SHARES")
    st.title("Industry vs Academia", anchor="dashboard-top")
    st.markdown(
        "**Has AI model development recorded by Epoch AI shifted from academia towards industry?** "
        "Start with the All dataset, then examine whether the pattern also holds among Notable models."
    )
    st.caption(
        "Persona: a technology policy analyst preparing a briefing on whether AI model "
        "development is becoming concentrated and whether it warrants policy attention. "
        "Main sample: the local Epoch AI All AI Models dataset. All refers to Epoch's recorded models."
    )
    st.caption(
        "Source: Epoch AI, All AI Models (main analysis) and Notable AI Models (comparison), "
        "CC BY 4.0 · Last data refresh: local snapshots added to the repository on 22 October 2026. "
        "Download dates were not recorded."
    )
    st.markdown(
        """
        <style>
        .sector-section-menu {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
            margin: 0.25rem 0 1rem;
        }
        .sector-section-menu a {
            color: inherit;
            text-decoration: none;
            font-weight: 600;
            padding: 0.55rem 0.95rem;
            border: 1px solid rgba(128, 128, 128, 0.35);
            border-radius: 0.5rem;
        }
        .sector-section-menu a:hover,
        .sector-section-menu a:focus-visible {
            color: #0072B2;
            border-color: #0072B2;
            background: rgba(0, 114, 178, 0.08);
        }
        [data-testid="stLayoutWrapper"]:has(> .st-key-sector-year-controls) {
            position: sticky;
            top: 3.75rem;
            z-index: 100;
        }
        .st-key-sector-year-controls {
            padding: 0.75rem 1.1rem 0.4rem;
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 0.75rem;
            background: #ffffff;
            background: light-dark(#ffffff, #0e1117);
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.08);
        }
        #dashboard-top {
            scroll-margin-top: 5rem;
        }
        #chart-1, #chart-2, #notable, #verify {
            scroll-margin-top: 12rem;
        }
        </style>
        <nav class="sector-section-menu" aria-label="Dashboard sections">
            <a href="#chart-1" target="_self">Chart 1 · Counts</a>
            <a href="#chart-2" target="_self">Chart 2 · Shares</a>
            <a href="#notable" target="_self">Notable · Comparison</a>
            <a href="#verify" target="_self">Verify · Source data</a>
        </nav>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        "**On this page**\n\n"
        "[Chart 1 · Counts](#chart-1)\n\n"
        "[Chart 2 · Shares](#chart-2)\n\n"
        "[Notable · Comparison](#notable)\n\n"
        "[Verify · Source data](#verify)"
    )

    try:
        models, quality = load_source()
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        st.error(f"The source dataset could not be loaded: {exc}")
        st.stop()

    with st.container(key="sector-year-controls"):
        start, end = st.slider(
            "Publication year range · All charts & Notable comparison",
            min_value=FIRST_YEAR,
            max_value=LAST_YEAR,
            value=(FIRST_YEAR, LAST_YEAR),
            help="Controls both All charts and the Notable comparison. 2026 is excluded as incomplete.",
        )
    selected = models.loc[models["Year"].between(start, end)]
    annual = aggregate_counts(models, start, end)
    shares = calculate_shares(annual)
    verification_samples = {"All": (models, shares, quality)}
    notable_error = None
    try:
        notable_models, notable_quality = load_source(NOTABLE_SOURCE)
        notable_shares = calculate_shares(aggregate_counts(notable_models, start, end))
        verification_samples["Notable"] = (notable_models, notable_shares, notable_quality)
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        notable_error = str(exc)
    shown = int(annual.loc[annual["Sector"].isin(CHART_SECTORS), "Count"].sum())
    other = int(selected["Sector"].eq("Other").sum())
    unknown = int(selected["Sector"].eq("Unknown").sum())
    st.subheader("Chart 1 — Number of AI Models by Sector · All", anchor="chart-1")
    st.markdown("**Has the annual industry model count grown faster than academia's?**")
    st.caption(
        f"All dataset · {start}–{end} · {shown:,} models in the three plotted categories · "
        f"Other: {other:,}; Unknown: {unknown:,} (not plotted in Chart 1). "
        "Collaboration means industry–academia participation; each model is counted once."
    )
    st.caption(
        f"{quality['missing_dates']:,} source records have no publication date and are excluded "
        "from annual analysis. Their original records are listed under Source, classification and limitations."
    )
    if selected.empty:
        st.info("No models are recorded for this period. Zeros mean no records in this dataset.")

    st.plotly_chart(
        make_chart(annual, start, end), width="stretch", key="sector_count_chart",
        config={"displaylogo": False},
    )
    st.caption("Hover to compare a year. Click a legend label to hide or restore a series.")

    st.subheader("Compare the change")
    comparison = annual.pivot(index="Year", columns="Sector", values="Count")
    columns = st.columns(3)
    changes = {}
    for column, sector in zip(columns, CHART_SECTORS):
        first = int(comparison.loc[start, sector])
        last = int(comparison.loc[end, sector])
        changes[sector] = last - first
        with column:
            st.metric(f"{sector} · {end}", f"{last:,} models")
            if start < end:
                st.caption(f"{start}: {first:,} → {end}: {last:,} · net change {last - first:+,}")
    if start < end:
        years = end - start
        industry_rate = changes["Industry"] / years
        academia_rate = changes["Academia"] / years
        if changes["Industry"] > changes["Academia"]:
            finding = "Industry has a larger net change in annual model counts than Academia in this selected period."
        elif changes["Industry"] < changes["Academia"]:
            finding = "Academia has a larger net change in annual model counts than Industry in this selected period."
        else:
            finding = "Industry and Academia have the same net change in this selected period."
        st.markdown(
            f"**{finding}** The change in annual model count per elapsed year is "
            f"{industry_rate:+.2f} for Industry and {academia_rate:+.2f} for Academia "
            f"(end-year count minus start-year count, divided by {years})."
        )
        st.caption(
            "This is a descriptive endpoint comparison, not a fitted trend or a statistical "
            "significance test. Change the time window and inspect the intervening years."
        )
    else:
        st.info("Select at least two years to compare changes over time.")

    st.subheader("Chart 2 — Share of AI Models by Sector · All", anchor="chart-2")
    st.markdown(
        "**Does industry simply produce more models as the total grows, "
        "or is its relative share also increasing?**"
    )
    st.caption(
        "Share = sector model count ÷ all recorded models in the same year × 100%. "
        "Other and Unknown are included, so the five mutually exclusive categories sum to 100%. "
        "Industry is at the bottom to give its share a consistent zero baseline."
    )
    if selected.empty:
        st.info("No sector shares can be calculated because this period contains no recorded models.")
    else:
        st.plotly_chart(
            make_share_chart(shares, start, end), width="stretch", key="sector_share_chart",
            config={"displaylogo": False},
        )
        if start == end:
            st.caption("A single year is shown as a 100% stacked bar; an area needs a time span.")
        if shares["Total"].eq(0).any():
            st.caption("Years without records are left as gaps; isolated recorded years use stacked bars.")
        st.caption(
            "Hover for the percentage, category count and annual total. "
            "All categories remain visible to preserve the full composition. "
            "The thickness of each band shows its share."
        )
        share_comparison(shares, start, end)

    st.subheader("Notable models — does the pattern change?", anchor="notable")
    if notable_error:
        st.warning(f"The All analysis is available, but the Notable comparison could not be loaded: {notable_error}")
    else:
        notable_comparison(shares, notable_shares, start, end)

    st.markdown('<div id="verify"></div>', unsafe_allow_html=True)
    with st.expander("Verify a displayed number", expanded=False):
        verify_scope = st.radio("Dataset to verify", list(verification_samples), horizontal=True)
        verify_models, verify_shares, verify_quality = verification_samples[verify_scope]
        st.write("Choose a year and sector to verify its count, share and denominator within the selected sample.")
        st.caption(f"Source: data/raw/ai_models/{verify_quality['source_file']}")
        year_column, sector_column = st.columns(2)
        with year_column:
            verify_year = st.selectbox("Year to verify", list(range(start, end + 1)), index=end - start)
        with sector_column:
            verify_sector = st.selectbox("Sector to verify", ALL_SECTORS)
        denominator = verify_models.loc[verify_models["Year"].eq(verify_year)]
        evidence = denominator.loc[denominator["Sector"].eq(verify_sector)]
        displayed = verify_shares.loc[
            verify_shares["Year"].eq(verify_year) & verify_shares["Sector"].eq(verify_sector)
        ].iloc[0]
        count = int(displayed["Count"])
        total = int(displayed["Total"])
        if count != len(evidence) or total != len(denominator):
            st.error("The displayed count or denominator does not match its underlying records.")
            st.stop()
        st.markdown(
            f"**{verify_scope} · {verify_year} · {verify_sector}: category count {count:,} = "
            f"{len(evidence):,} matching source records.**"
        )
        if total:
            st.markdown(
                f"**Share: {count:,} ÷ {total:,} × 100% = {displayed['Share']:.2f}%.** "
                f"The denominator includes all five categories within the {verify_scope} sample."
            )
        else:
            st.info("Share is undefined because there are no recorded models in this year.")
        st.caption(
            "Filter Publication date by year; apply the documented sector rule; count records. "
            "Source record is the one-based data-record number in the unchanged CSV, excluding its header."
        )
        evidence_columns = [
            "Source record", "Model", "Publication date", "Organization",
            "Organization categorization", "Sector", "Notability criteria", "Link",
        ]
        numerator_tab, denominator_tab = st.tabs(["Selected sector records", "All models in denominator"])
        with numerator_tab:
            st.dataframe(
                evidence[evidence_columns], hide_index=True, width="stretch",
                column_config={"Link": st.column_config.LinkColumn("Original reference")},
            )
        with denominator_tab:
            st.caption(f"{len(denominator):,} source records across all five categories in {verify_year}.")
            st.dataframe(
                denominator[evidence_columns], hide_index=True, width="stretch",
                column_config={"Link": st.column_config.LinkColumn("Original reference")},
            )
        download_column, annual_column = st.columns(2)
        with download_column:
            st.download_button(
                "Download matching source records",
                evidence[evidence_columns].to_csv(index=False).encode("utf-8"),
                file_name=f"{verify_scope.lower()}_evidence_{verify_year}_{verify_sector.lower()}.csv",
                mime="text/csv",
            )
        with annual_column:
            st.download_button(
                "Download annual counts and shares",
                verify_shares.to_csv(index=False).encode("utf-8"),
                file_name=f"{verify_scope.lower()}_annual_sector_shares_{start}_{end}.csv",
                mime="text/csv",
            )

    with st.expander("Source, classification and limitations"):
        st.markdown(
            "**Source:** Epoch AI, [Data on AI models](https://epoch.ai/data/ai-models), "
            "`all_ai_models.csv` for the main analysis and `notable_ai_models.csv` for the comparison. "
            "The download dates were not recorded. "
            "The app reads the local CSV rather than live data.\n\n"
            "**Unit:** one model record, counted once in its publication year. "
            "The source field `Organization categorization` supplies comma-separated sector tags.\n\n"
            "**Classification:** Industry = only Industry tags; Academia = only Academia tags. "
            "Repeated tags do not multiply the count. Collaboration = both Industry and Academia "
            "tags, including records that also involve a third sector. All remaining nonempty "
            "combinations are Other; an empty classification is Unknown. Other and Unknown are "
            "excluded from Chart 1's three lines and included in Chart 2's full composition.\n\n"
            "**Share denominator:** all valid-dated records in the same sample and publication year, "
            "including Other and Unknown. Each category's share is its model count divided by that total × 100. "
            "Shares are calculated before plotting and are not renormalised by the chart. "
            "A year without records has undefined shares and is shown as a gap.\n\n"
            "**Time coverage:** the analysis uses 2003–2025. 2026 is excluded as incomplete. "
            "A zero represents no recorded model in that category and year.\n\n"
            "**Missing dates:** undated records retain their source record numbers and raw fields, "
            "but are excluded from annual analysis. Nonempty invalid dates and duplicate model/date "
            "pairs stop processing for review.\n\n"
            "**Limitations:** All means every model in Epoch's local database snapshot, which is a "
            "selected collection rather than an exhaustive census of AI development. The Notable "
            "sample is defined by Epoch's inclusion criteria. "
            "Counts do not measure model quality, all academic research, research influence, "
            "or concentration among individual organisations. Academia follows the source label "
            "and should not be described as universities alone. Coverage and retrospective additions "
            "can affect comparisons. Industry-only counts exclude joint industry–academia models.\n\n"
            "**Design:** lines support comparison of annual trajectories across a long period. "
            "Grouped bars were rejected because three bars per year would crowd the full time range. "
            "Colour, line patterns and markers distinguish the series; the count axis starts at zero. "
            "The 100% stacked area chart shows changes in composition over time. A series of pie "
            "charts was rejected because comparing sectors across many separate circles is harder "
            "than following a continuous band. Industry uses the bottom baseline; other shares are "
            "read from band thickness and hover values. Annual totals are available in the hover "
            "because a 100% composition does not show absolute volume."
        )
        st.write(
            f"Source inspection: {quality['raw_rows']:,} rows × {quality['raw_columns']} columns; "
            f"{quality['earliest_date']} to {quality['latest_date']}. "
            f"Missing organisation: {quality['missing_organization']}; "
            f"missing classification: {quality['missing_categorization']}; "
            f"undated records excluded from annual analysis: {quality['missing_dates']}; "
            f"invalid dates: {quality['invalid_dates']}; "
            f"duplicate model/date pairs: {quality['duplicate_model_date_pairs']}."
        )
        st.caption("SHA-256 identifies the exact local snapshot used for these results.")
        st.code(quality["source_sha256"], language=None)
        undated = models.loc[models["Year"].isna(), [
            "Source record", "Model", "Publication date", "Organization", "Organization categorization"
        ]]
        st.markdown("**All records excluded because publication date is missing**")
        st.dataframe(undated, hide_index=True, width="stretch")
        st.download_button(
            "Download undated All source records", undated.to_csv(index=False).encode("utf-8"),
            file_name="all_undated_source_records.csv", mime="text/csv",
        )
        if "Notable" in verification_samples:
            st.caption("Notable comparison snapshot SHA-256:")
            st.code(notable_quality["source_sha256"], language=None)


if __name__ == "__main__":
    main()
