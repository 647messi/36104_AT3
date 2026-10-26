# The Rise of AI: group story and student dashboards

The default **Story** page introduces the working group research question: **Is the development of advanced AI becoming dominated by a few organisations?** It connects sector participation, relative sector shares and organisational concentration as distinct analytical questions. The intended audience is technology policymakers and AI researchers. Future chapters are labelled as planned until their analyses are available.

The separate **Industry vs Academia** dashboard asks: **Has the annual number of industry-developed notable AI models grown faster than academia's?** A multi-series line chart compares Industry, Academia and industry–academia Collaboration over 2003–2025.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Regenerate the processed data and quality report from the unchanged local CSV:

```bash
python -m src.preprocessing
```

The app computes from the same raw CSV directly, so processed exports never become a stale input to the chart.

## Working together

```text
app.py                              Shared entry point and automatic navigation
views/story.py                      Shared home page: question and narrative
dashboards/
  1_Industry_vs_Academia.py          Existing individual dashboard
templates/student_page.py           Starter for another student's page
src/
  data_access.py                    Cached source access for all pages
  preprocessing.py                  Existing sector classification and aggregation
data/raw/ai_models/                  Unchanged source snapshots
data/processed/                      Reproducible exports
tests/                              Data and navigation checks
```

Each student maintains their own page and any topic-specific processing module. To add a contribution:

1. Copy `templates/student_page.py` to `dashboards/2_Your_Topic.py`, using a unique number and descriptive name. Use two-digit prefixes such as `01_` if the group will have ten or more pages; filenames are sorted alphabetically.
2. Replace the starter content with the individual question, charts, narrative, source and numerical verification. Put any substantial data processing in a separate module such as `src/your_topic.py`.
3. Run `streamlit run app.py`. New Python files in `dashboards/` automatically appear in the navigation; underscores become spaces and the numeric prefix is omitted from the label. Files beginning with `_` are ignored. Page filenames must produce unique URLs.
4. Once the contribution is ready, add its evidence and a page link to the shared story. Coordinate edits to `views/story.py`, shared source definitions and `requirements.txt` with the group.

Keep helper files outside `dashboards/`, since its visible Python files become navigation entries. The template stays outside that directory until copied. The custom `dashboards/` directory lets the shared entry point own navigation without invoking Streamlit's separate legacy `pages/` mechanism. Page files should render their content without calling `st.set_page_config` or `st.navigation`; `app.py` owns those settings. Do not add code to run another Streamlit server from an individual page.

Pages can use `from src.data_access import load_source` to obtain the source records and quality report. This helper preserves all original CSV fields and adds `Source record`, `Year` and the sector module's `Sector` classification. If a teammate needs different attribution rules, add a separate field or processing module and document the distinction. The cache refreshes when the source file's modification time changes. Avoid editing the raw data or changing another student's classification implicitly.

The home page provides the narrative and links to evidence. Detailed filters, charts, record tables and downloads belong on each contribution's dashboard. Adding a page does not automatically imply that its findings have been incorporated into the shared story.

## Data and attribution

Source: Epoch AI, [Data on AI models](https://epoch.ai/data/ai-models), local file `data/raw/ai_models/notable_ai_models.csv`. See the source's accompanying README for its citation and Creative Commons Attribution licence. The download date was not recorded. `data/processed/data_quality.json` records the source hash, dimensions, date coverage and quality checks; it does not establish provenance beyond the local snapshot.

Each model is counted once in the year of `Publication date`, using distinct comma-separated tags from `Organization categorization`:

| Distinct source tags | Analysis category |
| --- | --- |
| Industry only | Industry |
| Academia only | Academia |
| Both Industry and Academia, with or without additional sectors | Collaboration |
| Other nonempty tag combinations | Other |
| No tags | Unknown |

`Industry,Industry` remains Industry. `Academia,Academia` remains Academia. Same-sector joint development does not become Collaboration. Industry–government and academia–research collective models are Other unless both Industry and Academia are present. These are explicit analytical rules rather than a new classification supplied by Epoch AI.

Other and Unknown remain in the processed data and can be inspected in the app, but are excluded from the three plotted series. A model with a missing organisation name is retained when it has a sector tag; no organisation is inferred from its name. No organisation strings are split into separate observations. The incomplete 2026 calendar year and years before 2003 are excluded. Every selected year/category combination is present, including zero counts.

Missing or invalid dates, missing model names and duplicate model/date pairs stop processing for review. No raw records are silently deduplicated or changed.

## Interpreting growth

The chart displays annual counts. The accompanying comparison reports start-year and end-year counts, their net difference, and that difference divided by elapsed years. It is an endpoint comparison, not a regression slope, compound growth rate or statistical significance test. A single selected year has no growth comparison. Changing the time window can change the conclusion, so inspect the full trajectory as well as the endpoints.

The source's Academia category should not be equated with universities alone. These observations describe the local notable-model dataset, not all AI research, model quality, academic influence or concentration among companies. Coverage and retrospective additions can affect trends. This chart does not establish relative sector shares; that requires a separate composition analysis.

## Design and recording

The line chart supports temporal comparison across 23 years. A grouped bar chart was considered but would require 69 bars at the default range, making trajectories harder to follow. Shared axes, a zero baseline, integer counts, distinct colours and line patterns support comparison. Year filtering and hover help inspect changes; legend clicks hide or restore a series.

For a numerical demonstration, choose a year and sector under **Verify a displayed number**. The app displays the aggregate and the matching unchanged source fields, including the raw sector tags, original reference and a one-based source data-record number (excluding the header; not a physical file line). Download the matching rows and compare them with the CSV. Annual downloads include all five categories so exclusions can also be reconciled.

## Checks

```bash
python -m unittest discover -s tests -v
```

The checks cover classification boundaries, zero-filled years, rejected duplicate records, count reconciliation and an independent raw-CSV recomputation. Streamlit's AppTest checks that Story opens first, that navigation can reach the dashboard and return home, and that the dashboard supports the full range, changed ranges, a single year and verification selections without a browser. An isolated fixture also verifies that an additional student page is discovered without changing the entry point.

## Organisational Concentration (Vaishnavi)

**Sub-question:** Each year, what share of notable AI models involves that year's top 3 (or top 5) organisations, and is that share rising?

**User story:** As a technology policy analyst, I want to see what share of notable AI models involves the top 3 or top 5 organisations each year, so that I can judge whether AI model development is becoming dominated by a few organisations.

**Walkthrough:** open **Organisational Concentration** in the sidebar → read the line chart (top-3 share 36% in 2014, peak 60% in 2020, 44% in 2025) → switch **Top 3 / Top 5** in the sidebar → scroll to **Which organisations produce the most notable models?** to see the leaders.

**Charts:** top-N share of notable models by year (line; change over time), organisations ranked by number of notable models (sorted bar; ranking), distinct organisations per year (bar; magnitude).

**Interactions (sidebar):** Top 3 / Top 5; publication-year range; merge company name variants on/off.

**Answer on screen:** by number of notable models, the top organisations hold a large share (around half) but it has not risen steadily: it is higher in 2019–2022 than in 2023–2024.

**Data:** Epoch AI, Notable AI Models (CC BY 4.0), `data/raw/ai_models/notable_ai_models.csv`, snapshot added 22 October 2026. Data dictionary: `data/dictionary/concentration.yml`. Processed files: `data/processed/annual_concentration.csv`, `organisation_name_map.csv`, `organisation_ranking_2014_2025.csv`.

**Regenerate and check:**

```bash
python -m src.concentration
python -m unittest tests.test_concentration -v
```

The tests include an independent recount from the raw CSV and a check that the processed files regenerate identically.

**Limits:** counts models, not compute or capability (training compute is missing for 173 of 324 models from 2023–2025); the notable list is a curated selection, not every AI model; a jointly developed model counts for every organisation listed.
