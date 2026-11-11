# TrialOps Monitor

**Clinical trial operations and patient enrollment tracker**  
Python · PostgreSQL · Streamlit · SQL CTEs/window functions · Agile backlog

TrialOps Monitor is a recruiter-friendly portfolio demo for reviewing enrollment progress across simulated studies and sites. It combines a recruitment funnel, target-versus-actual pace, explainable site review flags, an ETL quality log, PostgreSQL-ready schema and reporting queries, and a prioritized set of 12 vertical user stories.

> **Synthetic-data notice:** Every trial, site, screening, and participant reference is generated for this demo. No real patient information is used. This is not a clinical system and must not be used for patient care, trial decisions, or regulatory reporting.

## Live demo

[Open the public TrialOps Monitor dashboard](https://trialops-enrollment-monitor.streamlit.app/)

## Run locally (Windows PowerShell)

```powershell
cd .\clinical-trial-ops-tracker
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
python -m clinical_ops.cli demo
streamlit run app.py
```

Streamlit prints a local URL. The dashboard also creates the deterministic synthetic dataset on first launch, so the CLI step is optional for the app itself. To recreate source files and the ETL outputs explicitly, run `python -m clinical_ops.cli demo`.

## What the demo includes

- 3 simulated studies and 18 simulated research sites, with site/study assignments and monthly enrollment targets.
- 3,200 generated screening records plus seeded source defects for duplicate IDs, orphan assignments, missing dates, and invalid event chronology.
- ETL controls that deduplicate, validate assignment keys, exclude missing screening dates, clear invalid downstream event dates, and write a defect log.
- Study, region, site-status, and screening-date filters; screening-to-randomization funnel; monthly target versus actual chart; site-level performance table; and CSV exports.
- Transparent site review flags with the threshold and reason shown in the application.
- PostgreSQL schema, demo-load commands, funnel CTE, cumulative window metrics, `LAG`, `RANK`, and data-quality queries.
- A sprint-prioritized backlog of 12 stories with acceptance criteria in the dashboard, CSV, and Markdown docs.

## PostgreSQL integration

The public app runs without a database using generated CSV data. To use PostgreSQL locally:

1. Create a database, then apply `sql/schema.sql`.
2. Run `python -m clinical_ops.cli demo` from the repository root.
3. Load the generated clean tables with `psql -d YOUR_DATABASE -f sql/load_demo.psql`.
4. Set a connection URL in `.streamlit/secrets.toml`:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require"
```

For Streamlit Community Cloud, add the same `DATABASE_URL` value under the app's **Settings → Secrets**. Keep real credentials out of Git. With the secret present, the dashboard reads the `trialops` schema; without it, the dashboard uses the generated demo dataset. The seeded bad source rows remain in the generated raw CSVs and are filtered/reported by the Python ETL before database loading.

## Product scope and delivery artifacts

- `docs/PRODUCT_SCOPE.md` — users, requirements, definitions, and product boundary.
- `docs/user_stories.md` — 12 vertical stories with acceptance criteria.
- `docs/user_stories.csv` — prioritized sprint backlog rendered in the app.
- `docs/QA_DEFECT_LOG.md` — seeded defect classes, repair behavior, and review checklist.
- `docs/DATA_DICTIONARY.md` — core table and field definitions.
- `sql/` — PostgreSQL DDL, demo loader, stakeholder reports, and QA queries.

The backlog is version-controlled and visible in the demo. This repository does not claim a live GitHub Projects board or work performed at a real sponsor/site.

## Data and metric definitions

- **Screened:** distinct valid screening IDs whose screening date falls in the selected cohort window.
- **Eligible:** screened candidates with an eligibility outcome of `Eligible`.
- **Consented / randomized:** cohort candidates with a valid corresponding event date.
- **Actual monthly enrollment:** count of valid randomization dates in the calendar month.
- **Target attainment:** randomizations dated within the selected period divided by monthly target for the selected months. Funnel conversion uses the screening-date cohort and is displayed separately.
- **Bottleneck flags:** illustrative review thresholds for attainment, screen-failure rate, consent lag, and no randomization.

The synthetic values and thresholds are illustrative. Do not transfer these thresholds into an operational trial plan without clinical operations and data-governance review.

## Deployment

The public dashboard is deployed from this repository on Streamlit Community Cloud and uses Python 3.14. The app needs no database secret for the synthetic public demo.

For a local container:

```powershell
docker build -t trialops-monitor .
docker run --rm -p 8501:8501 trialops-monitor
```

## Resume-ready summary

Use a version that matches the work you can explain and the evidence you have:

**TrialOps Monitor — Clinical Trial Recruitment Operations Analytics** · Python, PostgreSQL, SQL, Streamlit  
Built a simulated multi-site enrollment dashboard for 3 studies and 18 sites, with a screening-to-randomization funnel, monthly target-versus-actual reporting, and transparent site review flags. Implemented ETL checks for duplicate screening IDs, orphan assignments, missing dates, and event chronology; documented repair outcomes, PostgreSQL CTE/window-function reports, and a 12-story prioritized backlog with acceptance criteria. All records are synthetic; no live sponsor data or clinical decisions are represented.
