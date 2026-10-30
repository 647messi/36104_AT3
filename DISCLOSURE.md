# Data and AI disclosure statement

Each member adds their part under their own heading.

## Vaishnavi – Organisational Concentration

**Data.** Epoch AI, 'Data on AI models' (Notable AI Models), licensed CC BY 4.0, retrieved from https://epoch.ai/data/ai-models. A local snapshot (`data/raw/ai_models/notable_ai_models.csv`, 1,078 records, latest publication date 2026-09-30) was committed to the repository on 22 October 2026 and is used unchanged. Processed files are generated from it by `src/concentration.py` and documented in `data/dictionary/concentration.yml`.

**AI.** I used Claude (Anthropic) to explore the dataset, propose the concentration measure, and draft the processing code, page and tests. I treated its output as an unverified draft. All displayed numbers were checked against the raw CSV by an independent Excel recount and by automated tests, and the app was checked for colour vision deficiency and at 1366×768. Two checks failed and led to fixes (chart display in the dark theme; line endings in the regenerated files). Each AI use and its check is listed in `PROVENANCE.md`.

## Rebecca (Zihan Guo) – Model Access

**Data.** Epoch AI, 'Data on AI models' (Notable AI Models), licensed CC BY 4.0, retrieved from https://epoch.ai/data/ai-models. The page reads the local snapshot `data/raw/ai_models/notable_ai_models.csv` (1,078 records, latest publication date 2026-09-30, committed to the repository on 22 October 2026) unchanged, and computes its counts and shares from it in `src/model_access.py`. The access types are my analytical grouping of the source field *Model accessibility*, documented on the page under Source and methodology.

**AI.** I used Claude (Anthropic) to draft the processing module, the page, the tests and my Part 1 recording script, and to review the page against the Part 2 checks. I treated its output as a draft to check. I recounted the 2025 API access figure myself from the raw CSV in a spreadsheet (46 API access models out of 107 with a recorded accessibility), and the automated tests check the classification, the annual counts and an independent recount from the raw file. One check failed and led to a fix (an unrecognised "Limited access" category). Each AI use and its check is listed in `PROVENANCE.md`.
