# The Rise of AI: group story and student dashboards

The default **Story** page introduces the working group research question: **Is AI model development becoming dominated by a few organisations?** It connects sector participation, relative sector shares, sample selection and organisational concentration as distinct analytical questions. The intended audience is technology policymakers and AI researchers. Future chapters are labelled as planned until their analyses are available.

The separate **Industry vs Academia** dashboard asks: **Has AI model development recorded by Epoch AI shifted from academia towards industry?** The main analysis uses the **All AI Models** CSV. Chart 1 compares annual Industry, Academia and industry–academia Collaboration counts over 2003–2025. Chart 2 shows the shares of all five sector categories in a 100% stacked area chart. Below these, a separate **Notable comparison** examines whether the sector pattern changes with sample selection. A horizontal year-range slider stays at the top while scrolling and controls all three charts. The menu links to each section and the collapsed verification panel.

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

The app computes directly from the raw CSVs, so processed exports never become stale chart inputs. The command writes the All results to `data/processed/` and the separately calculated Notable results to `data/processed/notable/`. Each folder contains annual counts, annual shares, classified models in the analysis period, an undated-record exclusion file and a quality report. `annual_sector_shares.csv` contains `Year`, `Sector`, `Count`, `Total` and `Share` (in percent, without rounding). `data/processed/all_vs_notable.csv` compares the samples' counts, totals, shares and percentage-point gaps.

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

Pages can use `from src.data_access import load_source` to obtain the **All** source records and quality report. Pass `NOTABLE_SOURCE` from `src.preprocessing` to `load_source` for the separate Notable file. This helper preserves all original CSV fields and adds `Source record`, nullable `Year` and the sector module's `Sector` classification. Undated records remain available for audit but have no assigned year. If a teammate needs different attribution rules, add a separate field or processing module and document the distinction. The cache refreshes when the source file's modification time changes. Avoid editing the raw data or changing another student's classification implicitly.

The home page provides the narrative and links to evidence. Detailed filters, charts, record tables and downloads belong on each contribution's dashboard. Adding a page does not automatically imply that its findings have been incorporated into the shared story.

## Data and attribution

Source: Epoch AI, [Data on AI models](https://epoch.ai/data/ai-models). The main analysis reads `data/raw/ai_models/all_ai_models.csv`; the comparison reads `data/raw/ai_models/notable_ai_models.csv`. See the source's accompanying README for its citation and Creative Commons Attribution licence. The download dates were not recorded. The two quality reports record each source hash, dimensions, date coverage and quality checks; they identify the exact local snapshots without establishing their download dates.

As described in the [official documentation](https://epoch.ai/data/ai-models-documentation), All contains all records in Epoch's database, including models collected through other research projects. It is not an exhaustive or statistically representative census of worldwide AI development. Notable uses Epoch's own inclusion criteria, such as benchmark improvements, citations, significant use, historical significance and development cost. The app uses the published Notable CSV rather than inventing a notability rule. The current Notable model/date keys are checked against the All file in the tests.

Each model is counted once in the year of `Publication date`, using distinct comma-separated tags from `Organization categorization`:

| Distinct source tags | Analysis category |
| --- | --- |
| Industry only | Industry |
| Academia only | Academia |
| Both Industry and Academia, with or without additional sectors | Collaboration |
| Other nonempty tag combinations | Other |
| No tags | Unknown |

`Industry,Industry` remains Industry. `Academia,Academia` remains Academia. Same-sector joint development does not become Collaboration. Industry–government and academia–research collective models are Other unless both Industry and Academia are present. These are explicit analytical rules rather than a new classification supplied by Epoch AI.

Other and Unknown are excluded from Chart 1's three lines and included in Chart 2's five-category composition. A model with a missing organisation name is retained when it has a sector tag; no organisation is inferred from its name. No organisation strings are split into separate observations. The incomplete 2026 calendar year and years before 2003 are excluded. Every selected year/category combination is present, including zero counts.

Missing publication dates are explicitly excluded from annual analysis, without assigning a year or shifting source record numbers. The original rows remain accessible in the loader, the app's methodology panel and `excluded_undated_models.csv`. In the current All snapshot, 12 records are undated. Nonempty dates that cannot be parsed, missing model names and duplicate model/date pairs stop processing for review. No raw records are silently deduplicated or changed.

## Interpreting growth

Chart 1 displays annual counts. The accompanying comparison reports start-year and end-year counts, their net difference, and that difference divided by elapsed years. It is an endpoint comparison, not a regression slope, compound growth rate or statistical significance test. A single selected year has no growth comparison. Changing the time window can change the conclusion, so inspect the full trajectory as well as the endpoints.

Chart 2 calculates `Share = Count / Total * 100`, where `Total` includes **all five categories** in the same publication year. Each model is attributed once, so there is no overlap between the bands. Categories with zero models have a zero share in a recorded year. A year with no models has undefined shares, is exported with blank shares, and is shown as a gap. Isolated years, including a single-year selection, use a 100% stacked bar because one observation cannot form a temporal area.

Percentages are calculated before plotting. The share chart does not use Plotly's automatic percentage normalisation; its legend visibility is fixed to preserve the full composition. Hover shows the share, category count and annual total. The accompanying endpoint comparison reports percentage-point change alongside the change in counts and total models. An increase in both count and share describes a change in composition alongside absolute growth; it does not establish a cause. Small annual totals can produce large percentage changes.

The source's Academia category should not be equated with universities alone. These observations describe Epoch's recorded models, not all AI research, model quality, academic influence or concentration among companies. Coverage, collection priorities and retrospective additions can affect trends.

## Notable comparison

The lower section compares Industry's annual share in All with its annual share in Notable. Each line has its **own** sample's annual denominator, including Other and Unknown; the overlapping samples are never added together. A table compares the five sectors in the selected end year, showing counts, shares and the gap `Notable share − All share` in percentage points. The interpretation compares the directions of the endpoint changes only when both samples have defined endpoint shares. The shared filter and CSV download support checking other windows and years.

This examines how measured sector participation changes with sample selection. A higher Industry share in Notable does not establish which inclusion criterion caused the difference or imply a higher share of research quality, capability or organisational concentration.

## Design and recording

The line chart supports temporal comparison across 23 years. A grouped bar chart was considered but would require 69 bars at the default range, making trajectories harder to follow. Shared axes, a zero baseline, integer counts, distinct colours and line patterns support comparison. Year filtering and hover help inspect changes; legend clicks hide or restore a series.

The 100% stacked area chart supports comparison of sector composition through time. A sequence of pie charts was rejected because it would require comparing many separate circles. Industry sits at the bottom with a common zero baseline. Other categories are read by band thickness and exact hover values. This chart hides absolute volume, so compare it with Chart 1 and the annual totals in its hover.

For a numerical demonstration, expand **Verify a displayed number**, which is collapsed by default. Choose **All or Notable**, then a year and sector. The app identifies the exact source file and displays the count and share formula. The first tab shows numerator records; the second shows **all source records in that sample's annual denominator**, including Other and Unknown. Both preserve relevant unchanged source fields, raw sector tags, notability criteria, original reference and a one-based source data-record number (excluding the header; not a physical file line). Download the matching rows and compare them with the indicated CSV. Annual downloads include counts, totals and shares for the selected sample. Switching verification samples leaves the All main analysis unchanged.

## Checks

```bash
python -m unittest discover -s tests -v
```

The checks cover classification boundaries, preserved source ordinals for undated records, rejected nonempty invalid dates and duplicates, zero-filled years, undefined empty-year shares, and independent raw-CSV recomputation of every annual count and share for **both** samples. Comparison checks verify sample membership, separate denominators and percentage-point gaps. Streamlit's AppTest checks the Story navigation, three charts with a shared range, percentages summing to 100%, single-year composition, and verification records for both All and Notable. An isolated fixture verifies that a new student page is discovered without changing the entry point.
