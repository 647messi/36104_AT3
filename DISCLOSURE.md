# Data and AI disclosure statement

Each member adds their part under their own heading.

## Vaishnavi – Organisational Concentration

**Data.** Epoch AI, 'Data on AI models' (Notable AI Models), licensed CC BY 4.0, retrieved from https://epoch.ai/data/ai-models. A local snapshot (`data/raw/ai_models/notable_ai_models.csv`, 1,078 records, latest publication date 2026-09-30) was committed to the repository on 22 October 2026 and is used unchanged. Processed files are generated from it by `src/concentration.py` and documented in `data/dictionary/concentration.yml`.

**AI.** I used Claude (Anthropic) to explore the dataset, propose the concentration measure, and draft the processing code, page and tests. I treated its output as an unverified draft. All displayed numbers were checked against the raw CSV by an independent Excel recount and by automated tests, and the app was checked for colour vision deficiency and at 1366×768. Two checks failed and led to fixes (chart display in the dark theme; line endings in the regenerated files). Each AI use and its check is listed in `PROVENANCE.md`.

## Tuan Anh – Base Model Dependence

**Data.** Epoch AI, 'Data on AI models' (All AI Models), licensed CC BY 4.0, retrieved from https://epoch.ai/data/ai-models. A local snapshot (`data/raw/ai_models/all_ai_models.csv`, 3,628 records, latest publication date 2026-10-17) was committed to the repository on 22 October 2026 and is used unchanged. Processed files are generated from it by `src/base_models.py` and documented in `data/dictionary/base_models.yml`.

**AI.** I used Claude (Anthropic) to suggest the sub-question, draft the page, processing code, tests and documentation, and plan my Part 1 recording. I treated its output as an unverified draft. Displayed numbers were checked against the raw CSV by hand (Power Query import in Excel) and by automated tests, including a byte-for-byte regeneration test. Three checks failed and led to fixes (the shared loader and blank cells; Excel splitting quoted line breaks; a test reading the wrong table). Each AI use and its check is listed in `PROVENANCE.md`.
