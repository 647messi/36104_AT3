"""Base model dependence: whose models do other developers build on?"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.base_models import (ALL_FILE, NOT_FOUND, PARENT, derived_models,
                             derived_share_by_year, load_all, owner_ranking, owner_shares)
from src.preprocessing import LAST_YEAR

SOURCE_FILE = "data/raw/ai_models/all_ai_models.csv"
LAST_REFRESH = "22 October 2026"  # date the CSV snapshot was committed (commit eded8d5)
FIRST = 2015
# Okabe-Ito colours, distinguishable with common colour-vision deficiencies.
PALETTE = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00"]
SOURCE_FIELDS = ["Source record", "Model", "Organization", "Publication date",
                 "Base model", "Base used", "Base owner", "Credit"]


@st.cache_data(show_spinner=False)
def load_records(modified_ns: int) -> pd.DataFrame:
    """The modification time is part of the cache key, so an updated file is reread."""
    models = load_all()
    return models[models["Year"].isna() | (models["Year"] <= LAST_YEAR)]


def share_line(share: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=share["Year"], y=share["Share"], mode="lines+markers+text",
        text=[f"{v:.0f}%" for v in share["Share"]], textposition="top center",
        textfont_size=11, line_color="#0072B2",
        customdata=share[["Derived models", "All models"]],
        hovertemplate="%{x}: %{customdata[0]} of %{customdata[1]} models (%{y:.1f}%)<extra></extra>"))
    fig.update_layout(height=340, margin=dict(t=30, b=10, l=10, r=10), showlegend=False,
                      xaxis=dict(title="Publication year", dtick=1),
                      yaxis=dict(title="Built on another developer's model (%)",
                                 range=[0, max(30, share["Share"].max() * 1.25)], ticksuffix="%"))
    return fig


def owner_chart(shares: pd.DataFrame) -> go.Figure:
    owners = list(dict.fromkeys(shares["Owner"]))
    colours = {o: PALETTE[i] for i, o in enumerate(o for o in owners if o not in ("Other", NOT_FOUND))}
    colours.update({"Other": "#BBBBBB", NOT_FOUND: "#7F7F7F"})
    shares = shares.assign(Label=[f"{v:.0f}%" if v >= 6 else "" for v in shares["Share"]])
    fig = px.bar(shares, x="Year", y="Share", color="Owner", text="Label",
                 category_orders={"Owner": owners}, color_discrete_map=colours,
                 custom_data=["Models", "Total"])
    fig.update_traces(textposition="inside", insidetextanchor="middle", textfont_size=11,
                      hovertemplate="%{x} · %{fullData.name}: %{y:.0f}%<br>"
                                    "%{customdata[0]:.1f} of %{customdata[1]:.0f} derived models"
                                    "<extra></extra>")
    totals = shares.groupby("Year")["Total"].first()
    fig.add_trace(go.Scatter(x=totals.index, y=[100] * len(totals), mode="text",
                             text=[f"n={v:.0f}" for v in totals.values], textposition="top center",
                             textfont=dict(size=10, color="#59616f"), showlegend=False,
                             hoverinfo="skip"))
    fig.update_layout(barmode="stack", height=440, margin=dict(t=40, b=10, l=10, r=10),
                      legend=dict(orientation="h", y=1.14, x=0, title=dict(text="Base-model owner: ")),
                      xaxis=dict(title="Publication year of the derived model", dtick=1),
                      yaxis=dict(title="Share of derived models (%)", range=[0, 108], ticksuffix="%"))
    return fig


def ranking_chart(rank: pd.DataFrame) -> go.Figure:
    rank = rank.sort_values("Models")
    fig = go.Figure(go.Bar(
        x=rank["Share"], y=rank["Base owner"], orientation="h", marker_color="#0072B2",
        text=[f"{s:.0f}% ({m:.0f})" for s, m in zip(rank["Share"], rank["Models"])],
        textposition="outside",
        hovertemplate="%{y}: %{x:.1f}% of derived models<extra></extra>"))
    fig.update_layout(height=60 + 30 * len(rank), margin=dict(t=10, b=10, l=10, r=40),
                      yaxis=dict(title="Base-model owner"),
                      xaxis=dict(title="Share of derived models in the period (%)", ticksuffix="%",
                                 range=[0, rank["Share"].max() * 1.25]))
    return fig


def main() -> None:
    st.page_link("views/story.py", label="Back to the story", icon=":material/arrow_back:")
    st.title("Whose models does everyone build on?")
    st.markdown(
        "**Research question:** Is AI development becoming dependent on base models from a "
        "few organisations?"
    )
    st.write(
        "Many new models are not trained from scratch. Developers fine-tune or extend an "
        "existing base model. Even when that base model is openly available, everyone who "
        "builds on it depends on the organisation that made it. This page asks how common "
        "that is, and whose base models the rest of the field relies on."
    )

    try:
        records = load_records(ALL_FILE.stat().st_mtime_ns)
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        st.warning(f"The model data could not be loaded: {exc}")
        return

    latest = records["Publication date"].replace("", pd.NA).dropna().max()
    st.caption(f"Source: Epoch AI, [Data on AI models](https://epoch.ai/data/ai-models) (CC BY 4.0), "
               f"`{SOURCE_FILE}`. Latest record in this snapshot: {latest}. "
               f"Data last refreshed in the repository: {LAST_REFRESH}.")

    c1, c2, c3 = st.columns([2, 1, 1])
    years = c1.slider("Publication years", FIRST, LAST_YEAR, (2020, LAST_YEAR), key="bm_years")
    parent = c2.toggle("Group labs by parent company", value=True, key="bm_parent",
                       help="Merges e.g. Meta AI and Facebook AI Research into Meta.")
    include_own = c3.toggle("Include a developer's own base models", value=False, key="bm_own",
                            help="Off: Meta fine-tuning its own Llama is not counted as dependence.")

    derived = derived_models(records, parent, include_own)
    share = derived_share_by_year(records, derived, years)
    shares = owner_shares(derived, years)
    if shares.empty:
        st.info("No models built on another developer's model in the selected years. "
                "Widen the year range to see results.")
        return

    lead = (shares[shares["Owner"].isin(["Other", NOT_FOUND]) == False]  # noqa: E712
            .sort_values("Share").groupby("Year").tail(1).set_index("Year").sort_index())
    last = int(share["Year"].max())
    k1, k2, k3 = st.columns(3)
    k1.metric(f"Built on another's model, {last}",
              f"{share.set_index('Year').loc[last, 'Share']:.0f}%",
              f"{share.set_index('Year').loc[last, 'Share'] - share['Share'].iloc[0]:+.0f} pts "
              f"since {int(share['Year'].iloc[0])}", delta_color="off")
    if last in lead.index:
        k2.metric(f"Largest base-model owner, {last}", lead.loc[last, "Owner"],
                  f"{lead.loc[last, 'Share']:.0f}% of derived models", delta_color="off")
    leaders = lead["Owner"].tolist()
    k3.metric("Leaders across the years", len(dict.fromkeys(leaders)),
              " → ".join(dict.fromkeys(leaders)), delta_color="off")

    st.subheader("How many new models are built on another developer's model?")
    st.plotly_chart(share_line(share), width="stretch", key="bm_line")
    st.caption(f"Change over time, {years[0]}–{years[1]}: share (%) of all models published each "
               "year whose Base model field names another developer's model. Baseline: all models "
               "published that year, labelled on each point.")

    st.subheader("Whose base models are they built on?")
    st.plotly_chart(owner_chart(shares), width="stretch", key="bm_stack")
    st.caption("100% stacked: each year adds to 100% of that year's derived models, so the bars "
               "show who the field depends on, not how many models there are (n above each bar). "
               "Small n before 2023 makes those years unstable. Exact values are in the table.")
    table = (shares.pivot(index="Owner", columns="Year", values="Share").round(0)
             .reindex(list(dict.fromkeys(shares["Owner"]))))
    table.columns = [str(c) for c in table.columns]
    st.dataframe(table.map(lambda v: f"{v:.0f}%"), width="stretch",
                 column_config={"Owner": "Base-model owner"})

    st.subheader(f"Base-model owners ranked, {years[0]}–{years[1]}")
    rank = owner_ranking(derived, years)
    st.plotly_chart(ranking_chart(rank), width="stretch", key="bm_rank")
    st.caption(f"Ranking: each owner's share (%) and number of derived models across "
               f"{years[0]}–{years[1]} combined.")

    top = rank[rank["Base owner"] != NOT_FOUND].head(3)
    names = ", ".join(top["Base owner"].iloc[:-1]) + (" and " if len(top) > 1 else "") + top["Base owner"].iloc[-1]
    first_share = share["Share"].iloc[0]
    last_share = share.set_index("Year").loc[last, "Share"]
    st.info(
        f"**Answer for {years[0]}–{years[1]}:** the share of new models built on another "
        f"developer's model went from {first_share:.0f}% in {int(share['Year'].iloc[0])} to "
        f"{last_share:.0f}% in {last}. {names} owned the base models behind "
        f"{top['Share'].sum():.0f}% of them, so dependence is concentrated in a few organisations, "
        f"but the leading owner has changed over time ({' → '.join(dict.fromkeys(leaders))})."
    )
    st.warning(
        "**What this data cannot show:** licence terms, how widely each model is used, or market "
        "share. Epoch AI lists only the models it has catalogued, and Base model is filled only "
        "when the source states it, so dependence is a lower bound."
    )

    with st.expander("Verify a displayed number", expanded=False):
        v1, v2 = st.columns(2)
        yr_opts = sorted(shares["Year"].unique(), reverse=True)
        year = v1.selectbox("Year", yr_opts, key="bm_v_year")
        owner_opts = shares[shares["Year"] == year].sort_values("Share", ascending=False)["Owner"]
        owner = v2.selectbox("Base-model owner", owner_opts.tolist(), key="bm_v_owner")
        row = shares[(shares["Year"] == year) & (shares["Owner"] == owner)].iloc[0]
        st.markdown(f"**{row['Models']:.1f} of {row['Total']:.0f}** derived models in {year} were "
                    f"built on a base model owned by **{owner}** = **{row['Share']:.1f}%**.")
        d = derived[derived["Year"] == year]
        if owner == "Other":
            top = set(shares["Owner"]) - {"Other", NOT_FOUND}
            d = d[~d["Base owner"].isin(top | {NOT_FOUND})]
        else:
            d = d[d["Base owner"] == owner]
        rows = d[SOURCE_FIELDS].sort_values("Source record")
        st.dataframe(rows, hide_index=True, width="stretch",
                     column_config={"Base used": "Base model matched",
                                    "Base owner": "Owner of base model"})
        st.download_button("Download these source rows (CSV)", rows.to_csv(index=False).encode("utf-8"),
                           file_name=f"base_models_{year}.csv", mime="text/csv", key="bm_download")
        st.caption(f"Source record is the one-based data-record number in {SOURCE_FILE} "
                   "(excluding the header). The owner comes from the Organization field of the "
                   "base model's own record in the same file.")

    with st.expander("Source and methodology"):
        merges = ", ".join(f"{k} → {v}" for k, v in PARENT.items())
        st.markdown(f"""
**Source:** Epoch AI, [Data on AI models](https://epoch.ai/data/ai-models), local file
`{SOURCE_FILE}` (CC BY 4.0). The incomplete 2026 year is excluded, as in the rest of the app.
This page reads the **All** file rather than the shared Notable default, because the Base model
field is filled for 693 All records but only 141 Notable ones. Undated records (12) are kept in
the file but have no year, so they do not enter any yearly share.

**Derived model:** a record whose *Base model* field is filled in. If several base models are
listed, the first is used.

**Base-model owner:** the *Organization* of the base model's own record in the same file,
matched on its exact name. Names that cannot be matched are shown as "{NOT_FOUND}".
A base model with k owners gives each 1/k credit.

**Own base models** are excluded by default: the question is about depending on someone
else, so Meta fine-tuning Llama does not count. Switch the toggle to include them.

**Parent company** (on by default, because labs such as Meta AI and Facebook AI Research are the
same company): {merges}.

**What the data cannot show:** Epoch records only models it has catalogued, and the Base model
field is filled in when the source states it. Dependence here means being built on a model,
not licence terms, usage or market share.
""")


if __name__ == "__main__":
    main()
