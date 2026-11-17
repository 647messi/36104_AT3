# The Rise of AI: group story and student dashboards

The default **Story** page introduces the working group research question: **Is AI model development becoming dominated by a few organisations?** It connects sector participation, relative sector shares, sample selection and organisational concentration as distinct analytical questions. The persona is a technology policy analyst preparing a briefing on whether AI model development is becoming concentrated, who needs to decide whether that concentration warrants policy attention.

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

The project now contains four individual dashboards. Each member maintains their dashboard and topic-specific processing code; `app.py` and `views/story.py` provide the shared navigation and narrative.

```text
app.py                               Shared entry point and automatic navigation
views/story.py                       Shared home page: question and narrative
dashboards/
  1_Industry_vs_Academia.py           Siqi Liu: sector counts, shares and sample comparison
  2_Organisational_Concentration.py   Organisational concentration
  4_Model_Access.py                  Model access
  5_Base_Model_Dependence.py         Base model dependence
src/
  data_access.py                     Cached loader available to shared and individual pages
  preprocessing.py                   Sector classification, aggregation and quality reports
  concentration.py                   Organisation mapping, concentration and rankings
  model_access.py                    Model access processing
  base_models.py                     Base model matching and owner attribution
data/raw/ai_models/                   Unchanged source snapshots
data/processed/                       Reproducible exports
data/dictionary/                      Topic-specific data dictionaries
tests/                               Data and navigation checks
  verify_sector_share.ipynb           Siqi Liu's independent numerical trace
DISCLOSURE.md                         Each member's data and AI disclosure
PROVENANCE.md                         AI uses and verification methods
templates/student_page.py             Starter for an additional dashboard
```

When updating a contribution:

1. Keep topic-specific changes in the relevant dashboard, processing module and tests. Coordinate changes to `app.py`, `views/story.py`, shared loading and classification rules, or `requirements.txt` with the group.
2. Run `streamlit run app.py` and check that the page opens through the shared navigation and that its filters, charts and verification controls work.
3. Run the relevant checks in `tests/`. If processing rules change, regenerate the affected exports and update the methodology and verification evidence.
4. Update the shared story when the contribution's findings change, and keep the member's entries in `DISCLOSURE.md` and `PROVENANCE.md` consistent with the work performed.

For an additional dashboard, copy `templates/student_page.py` into `dashboards/` with an unused numeric prefix and descriptive name, such as `6_Your_Topic.py`. Python files in this folder are discovered automatically; filenames are sorted alphabetically, underscores become spaces and the numeric prefix is omitted from the navigation label. Use two-digit prefixes consistently if the group grows to ten or more pages. Files beginning with `_` are ignored, and page filenames must produce unique URLs.

Keep helper files outside `dashboards/`, since its visible Python files become navigation entries. Page files should render their content without calling `st.set_page_config` or `st.navigation`; `app.py` owns those settings. Run the application through the shared entry point.

Pages can use `from src.data_access import load_source` to obtain the **All** source records and quality report. Pass `NOTABLE_SOURCE` from `src.preprocessing` to `load_source` for the separate Notable file. This helper preserves all original CSV fields and adds `Source record`, nullable `Year` and the sector module's `Sector` classification. Undated records remain available for audit but have no assigned year. If a teammate needs different attribution rules, add a separate field or processing module and document the distinction. The cache refreshes when the source file's modification time changes. Avoid editing the raw data or changing another student's classification implicitly.

The home page provides the narrative and links to evidence. Detailed filters, charts, record tables and downloads belong on each contribution's dashboard. Adding a page does not automatically imply that its findings have been incorporated into the shared story.

## Project checks

```bash
python -m unittest discover -s tests -v
```

The checks cover classification boundaries, zero-filled years, rejected duplicate records, count reconciliation and an independent raw-CSV recomputation. Streamlit's AppTest checks that Story opens first, that navigation can reach the dashboard and return home, and that the dashboard supports the full range, changed ranges, a single year and verification selections without a browser. An isolated fixture also verifies that an additional student page is discovered without changing the entry point.

## Industry vs. Academia (Siqi Liu)

**Sub-question:** Has AI model development recorded by Epoch AI shifted from academia towards industry?

**User story:** As a technology policy analyst, I want to compare the number and share of AI models developed by industry, academia and their collaborations over time, so that I can assess how sector participation is changing.

The **Industry vs Academia** dashboard uses the **All AI Models** CSV for its main analysis. Chart 1 compares annual Industry, Academia and industry–academia Collaboration counts over 2003–2025. Chart 2 shows the shares of all five sector categories in a 100% stacked area chart. Below these, a separate **Notable comparison** examines whether the sector pattern changes with sample selection. A horizontal year-range slider stays at the top while scrolling and controls all three charts. The menu links to each section and the collapsed verification panel.

**Walkthrough:** Open **Industry vs Academia** in the sidebar → compare annual model counts → inspect sector shares → compare All and Notable → expand **Verify a displayed number** to trace a value back to the source records. Change the year-range slider to inspect other periods.

**Key findings (2003–2025):** In All, Industry-only models increase from 1 of 10 recorded models (10.0%) in 2003 to 479 of 578 (82.9%) in 2025. Academia-only counts rise from 9 to 15 over the same endpoints, so a lower relative share does not imply fewer models. In 2025, Industry's share is 91.6% in Notable (98 of 107), compared with 82.9% in All, a gap of 8.7 percentage points. These figures support a shift towards industry within Epoch's recorded models; sample selection affects the measured share. The 2003 sample is small, and the comparison does not establish a cause or measure concentration among individual organisations.

**Disclosure and verification:** Data and AI disclosures are documented in [DISCLOSURE.md](DISCLOSURE.md#siqi-liu--industry-vs-academia), with AI uses and verification methods recorded in [PROVENANCE.md](PROVENANCE.md#siqi-liu--industry-vs-academia). The numerical trace is in [tests/verify_sector_share.ipynb](tests/verify_sector_share.ipynb), with automated data checks in [tests/test_preprocessing.py](tests/test_preprocessing.py).

### Files

```text
dashboards/1_Industry_vs_Academia.py   Dashboard: counts, shares, comparison and verification
src/preprocessing.py                 Sector classification, aggregation and exports
tests/test_preprocessing.py          Classification and independent numerical checks
tests/verify_sector_share.ipynb      Notebook recount of All / 2025 / Industry
data/processed/                     All exports and All-versus-Notable comparison
data/processed/notable/              Separate Notable exports
```

### Data and attribution

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

### Interpreting growth

Chart 1 displays annual counts. The accompanying comparison reports start-year and end-year counts, their net difference, and that difference divided by elapsed years. It is an endpoint comparison, not a regression slope, compound growth rate or statistical significance test. A single selected year has no growth comparison. Changing the time window can change the conclusion, so inspect the full trajectory as well as the endpoints.

Chart 2 calculates `Share = Count / Total * 100`, where `Total` includes **all five categories** in the same publication year. Each model is attributed once, so there is no overlap between the bands. Categories with zero models have a zero share in a recorded year. A year with no models has undefined shares, is exported with blank shares, and is shown as a gap. Isolated years, including a single-year selection, use a 100% stacked bar because one observation cannot form a temporal area.

Percentages are calculated before plotting. The share chart does not use Plotly's automatic percentage normalisation; its legend visibility is fixed to preserve the full composition. Hover shows the share, category count and annual total. The accompanying endpoint comparison reports percentage-point change alongside the change in counts and total models. An increase in both count and share describes a change in composition alongside absolute growth; it does not establish a cause. Small annual totals can produce large percentage changes.

The source's Academia category should not be equated with universities alone. These observations describe Epoch's recorded models, not all AI research, model quality, academic influence or concentration among companies. Coverage, collection priorities and retrospective additions can affect trends.

### Notable comparison

The lower section compares Industry's annual share in All with its annual share in Notable. Each line has its **own** sample's annual denominator, including Other and Unknown; the overlapping samples are never added together. A table compares the five sectors in the selected end year, showing counts, shares and the gap `Notable share − All share` in percentage points. The interpretation compares the directions of the endpoint changes only when both samples have defined endpoint shares. The shared filter and CSV download support checking other windows and years.

This examines how measured sector participation changes with sample selection. A higher Industry share in Notable does not establish which inclusion criterion caused the difference or imply a higher share of research quality, capability or organisational concentration.

### Design and recording

The line chart supports temporal comparison across 23 years. A grouped bar chart was considered but would require 69 bars at the default range, making trajectories harder to follow. Shared axes, a zero baseline, integer counts, distinct colours and line patterns support comparison. Year filtering and hover help inspect changes; legend clicks hide or restore a series.

The 100% stacked area chart supports comparison of sector composition through time. A sequence of pie charts was rejected because it would require comparing many separate circles. Industry sits at the bottom with a common zero baseline. Other categories are read by band thickness and exact hover values. This chart hides absolute volume, so compare it with Chart 1 and the annual totals in its hover.

For a numerical demonstration, expand **Verify a displayed number**, which is collapsed by default. Choose **All or Notable**, then a year and sector. The app identifies the exact source file and displays the count and share formula. The first tab shows numerator records; the second shows **all source records in that sample's annual denominator**, including Other and Unknown. Both preserve relevant unchanged source fields, raw sector tags, notability criteria, original reference and a one-based source data-record number (excluding the header; not a physical file line). Download the matching rows and compare them with the indicated CSV. Annual downloads include counts, totals and shares for the selected sample. Switching verification samples leaves the All main analysis unchanged.

For a notebook demonstration, open [tests/verify_sector_share.ipynb](tests/verify_sector_share.ipynb), select the project's `.venv` Python kernel and run all cells. Install `ipykernel` in a fresh environment with `python -m pip install ipykernel` if needed. The notebook verifies All / 2025 / Industry. It reads the original CSV with Python's `csv` reader, calculates the annual denominator and Industry count independently, and checks both counts and the share rounded to one decimal place against the dashboard's processing functions. The saved outputs provide a preview; rerun the cells on screen for the live trace. Chart 2 hover uses one decimal place and the Verify panel uses two, so their displayed percentages can differ in rounding.

### Regenerate and check

From the project root, with the project's Python environment activated:

```bash
python -m src.preprocessing
python -m unittest discover -s tests -p 'test_preprocessing.py' -v
python -m unittest discover -s tests -p 'test_app.py' -v
```

The regeneration command reads the unchanged All and Notable snapshots and writes their separate counts, shares, classified records, undated-record exclusions and quality reports, plus `data/processed/all_vs_notable.csv`. The dashboard calculates from the raw snapshots rather than these exports.

The preprocessing checks cover sector classification, duplicate rejection, auditable undated records, zero counts, undefined shares in empty years, and separate sample denominators. An independent pass through the raw CSV checks annual sector counts. The app checks cover shared navigation, year filtering, single-year displays and verification selections. For a manual numerical trace, run all cells in [tests/verify_sector_share.ipynb](tests/verify_sector_share.ipynb): it independently recalculates All / 2025 / Industry and compares the count, denominator and rounded share with the dashboard calculations.

### Limits

Epoch AI's database is a collected sample, not a comprehensive or statistically representative census of worldwide AI development. Coverage, collection priorities and retrospective additions can affect the apparent trends. Notable applies additional selection criteria, so differences from All describe sample selection rather than proving differences in research quality or capability.

Each model receives one sector category based on its recorded organisation tags. Industry-only and Academia-only counts exclude industry–academia collaborations, which are shown separately; Academia should not be interpreted as universities alone. Missing sector tags remain Unknown, and undated records cannot contribute to annual comparisons. The analysis excludes years before 2003 and the incomplete 2026 calendar year.

Counts and shares measure recorded model output, not compute, investment, model capability or concentration among individual organisations. Small annual samples can produce large percentage changes. Endpoint comparisons depend on the selected years and do not establish a causal relationship or statistical significance; a declining share can occur alongside a rising model count.

## Organisational Concentration (Vaishnavi)

**Sub-question:** Each year, what share of notable AI models involves that year's top 3 (or top 5) organisations, and is that share rising?

**User story:** As a technology policy analyst, I want to see what share of notable AI models involves the top 3 or top 5 organisations each year, so that I can judge whether AI model development is becoming dominated by a few organisations.

**Walkthrough:** open **Organisational Concentration** in the sidebar → read the line chart (top-3 share 36% in 2014, peak 60% in 2020, 44% in 2025) → switch **Top 3 / Top 5** in the sidebar → scroll to **Which organisations produce the most notable models?** to see the leaders.

**Answer on screen:** by number of notable models, the top organisations hold a large share (around half) but it has not risen steadily: it is higher in 2019–2022 than in 2023–2024.

### Files

```text
dashboards/2_Organisational_Concentration.py   Page: charts, sidebar controls, answer, limits, verification
src/concentration.py                           Name merging, top-N shares, ranking, exports
tests/test_concentration.py                    Rules, real-data reconciliation, regeneration and page checks
data/dictionary/concentration.yml              Data dictionary for the three processed files
data/processed/annual_concentration.csv        Top-3 and top-5 shares by year, 2003–2025
data/processed/organisation_name_map.csv       Corporate name variants and their parent organisation
data/processed/organisation_ranking_2014_2025.csv  Top 15 organisations by notable models, 2014–2025
```

### Data and attribution

Source: Epoch AI, [Data on AI models](https://epoch.ai/data/ai-models), Notable AI Models, local file `data/raw/ai_models/notable_ai_models.csv` (CC BY 4.0; 1,078 records; latest publication date 2026-09-30; snapshot added 22 October 2026). The page always reads the Notable file, whatever the shared default source is.

Each model is counted once in the year of `Publication date`. The rules are explicit analytical choices rather than a classification supplied by Epoch AI:

| Step | Rule |
| --- | --- |
| Split | `Organization` is split on commas into organisation names |
| Merge | Corporate name variants are merged into a current parent, e.g. Google Brain, DeepMind and Google DeepMind become Google; Facebook AI Research becomes Meta (22 names, 7 parents; see `organisation_name_map.csv`) |
| Rank | Each year, organisations are ranked by the number of models listing them; ties are broken alphabetically so the ranking is reproducible |
| Share | Models listing at least one top-N organisation ÷ models with at least one organisation × 100. A model is never counted twice, so the share cannot exceed 100% |
| Exclude | Models with an empty `Organization` are left out of the share and reported; no organisation is inferred from a model's name. The incomplete 2026 calendar year is excluded |

Universities, joint labs and independent firms are left as recorded. Acquired or sister companies (Maluuba, MetaMind Inc, Isomorphic Labs) are deliberately not merged; each appears on one model alongside its parent, so no share or ranking changes. The **Merge company name variants** toggle shows the effect of merging: with it off, the 2019 top-3 share falls from 53% to 28%.

In the ranking chart a jointly developed model counts once for each organisation listed, so shares can sum to more than 100%.

### Interpreting the share

The share measures how much of each year's notable output involves that year's leaders; the leaders can change from year to year (Google most years, OpenAI in 2025). Before 2014 there are fewer than 20 notable models a year, so a few models can move the share by tens of percentage points; the default view is therefore 2014–2025 and the page warns when earlier years are selected. A rise in the number of notable models is not concentration in itself, which is why the chart shows a share rather than counts (33 models in 2014, 107 in 2025).

### Design and recording

The main chart is a single line because the task is change over time in one measure; position on a common scale is the most accurate encoding. A stacked area chart with one band per organisation was rejected: with 29–119 organisations a year the bands would be thin and shifting, and readers would have to compare band thicknesses. Every point is labelled, with labels placed on the open side of the line, so values can be read without hovering. The ranking uses a sorted horizontal bar so names stay readable and order is immediate. Counting models was chosen over training compute because compute is missing for 173 of 324 models from 2023–2025, mostly the largest closed models, so a compute share would measure who discloses compute rather than who holds it. One colour family is used throughout and was checked under simulated protanopia, deuteranopia, tritanopia and achromatopsia. Controls sit in the sidebar so they stay visible beside the charts.

For a numerical demonstration, choose a year under **Verify a displayed number**: the page shows the top-N organisations, the calculation (e.g. 47 ÷ 107 = 43.9% for 2025) and every matching source record with its one-based `Source record` number in the unchanged CSV. The records can be downloaded and compared with the raw file.

### Regenerate and check

```bash
python -m src.concentration
python -m unittest tests.test_concentration -v
```

The 11 checks cover the merging and counting rules (including no double counting and alphabetical ties), the ranking and an empty year range, an independent recount of 2025 from the raw CSV using the `csv` module rather than pandas, a check that the committed processed files regenerate byte-for-byte (exports use Unix line endings; see `.gitattributes`), and a Streamlit AppTest that opens the page through `app.py` and exercises every control.

### Limits

Counts models, not compute or capability. Epoch AI's notable list is a curated selection, not every AI model, and recent years may gain records retrospectively. A model is attributed to every organisation listed; the data does not record who led the work. Merging uses current corporate parents, so DeepMind before its 2014 acquisition is grouped with Google.

## Base Model Dependence (Tuan Anh)

**Sub-question:** Is AI development becoming dependent on base models from a few organisations?

**User story:** As a technology policy analyst, I want to see how many new AI models are built on another organisation's base model, and whose base models they are, so that I can judge whether a few organisations control the foundations other developers rely on.

**Walkthrough:** open **Base Model Dependence** in the sidebar → read the line chart (share of new models built on another developer's model: 3% in 2020, 23% in 2023, 15% in 2025) → read the 100% stacked bar and its value table to see who they depend on each year (Meta 52% in 2023, Alibaba 50% in 2025) → read the ranking (Meta, Alibaba and Alphabet own the base models behind 64% of derived models in 2020–2025) → move the **Publication years** slider or switch the toggles and the charts, answer and ranking update.

**Answer on screen:** dependence on other developers' base models rose sharply from 2023 and is concentrated in a few organisations, but the leading owner keeps changing (Alphabet → OpenAI → Meta → Alibaba), so no single organisation holds this position.

It complements the Model Access page: that page asks how each model is released; this one asks whose models other developers build on.

### Files

```text
dashboards/5_Base_Model_Dependence.py             Page: three charts, value table, answer, limits, verification
src/base_models.py                                All-file loader, base-model owner matching, shares, exports
tests/test_base_models.py                         Loading, counting rules, raw-CSV recount, regeneration and page checks
data/dictionary/base_models.yml                   Data dictionary for the four processed files
data/processed/base_models/derived_models.csv     Every model built on another developer's base model, with its owner
data/processed/base_models/derived_share_by_year.csv   Share of each year's models that are derived, 2015–2025
data/processed/base_models/owner_shares_by_year.csv    Each owner's share of derived models per year, 2015–2025
data/processed/base_models/owner_ranking_2020_2025.csv Owners ranked by derived models, 2020–2025
```

### Data and attribution

Source: Epoch AI, [Data on AI models](https://epoch.ai/data/ai-models), All AI Models, local file `data/raw/ai_models/all_ai_models.csv` (CC BY 4.0; 3,628 records; latest publication date 2026-10-17; snapshot added to the repository on 22 October 2026). The page reads the All file rather than the shared Notable default because `Base model` is filled for 693 All records but only 141 Notable ones. The shared loader stops on the All file's 12 undated records, so `src/base_models.py` reads it with the same conventions (all fields as text, one-based `Source record`, `Year` from `Publication date`) and keeps undated records without a year. The raw file is not changed.

| Step | Rule |
| --- | --- |
| Derived model | A record whose `Base model` is not blank; if several are listed, the first is used |
| Owner | The `Organization` of the base model's own record in the same file, matched on its exact name; unmatched names are shown as "Not in dataset" (4 records) |
| Credit | A base model with k owners gives each owner 1/k, so credits add up to the number of derived models |
| Own base models | Excluded by default: Meta fine-tuning its own Llama is not dependence on someone else. A toggle includes them |
| Parent company | On by default: Google, Google Brain and DeepMind become Alphabet; Meta AI and Facebook AI Research become Meta; Qwen Team becomes Alibaba (`PARENT` in `src/base_models.py`) |
| Exclude | The incomplete 2026 calendar year |

### Design and recording

The owner chart is a 100% stacked bar because the task is part-to-whole over time. A stacked bar of raw counts was rejected: derived models rise from 16 in 2021 to 168 in 2024, so counts would mainly show growth and hide the shift in who the field depends on. Each bar's total is shown as n above it, and a value table below gives every share. The line chart shows change over time in one measure, and the sorted horizontal bar ranks owners. Colours follow the Okabe–Ito palette, which stays distinguishable with common colour vision deficiencies.

For a numerical demonstration, choose a year and owner under **Verify a displayed number**. Example: in 2025, 43 of 86 derived models were built on an Alibaba base model (50%). *K2 Think* (Source record 289, spreadsheet row 290) lists *Qwen2.5-32B* as its base model; Qwen2.5-32B's own record (1061, row 1062) has `Organization` = Alibaba.

### Regenerate and check

```bash
python -m src.base_models
python -m unittest tests.test_base_models -v
```

The 14 checks cover loading every record once with unchanged fields, shares that sum to 100% each year, credits that add up, the default exclusion of own base models, an independent recount of the 2025 Alibaba figure from the raw CSV using the `csv` module, byte-identical regeneration of the four processed files, and the page opening through `app.py` with working toggles, a single-year range and the verification table.

### Limits

Epoch AI records only the models it has catalogued, and `Base model` is filled only when the source states it, so dependence is a lower bound. Dependence here means being built on a model; it does not measure licence terms, usage or market share. Name matching is exact, so a base model recorded under a different name is shown as "Not in dataset". Years before 2023 have few derived models, so their shares are unstable.
