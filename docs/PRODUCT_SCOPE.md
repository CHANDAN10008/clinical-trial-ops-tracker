# Product scope: TrialOps Monitor

## Problem

Clinical operations teams need a consistent view of recruitment progress across studies and sites. Source exports can contain duplicated screening IDs, broken site/study references, missing dates, and event dates in an impossible order. The demo models that workflow with generated data and makes the repair decisions visible.

## Intended users

- **Study manager:** compares enrollment pace and target attainment across sites.
- **Site manager:** reviews local funnel conversion and transparent bottleneck cues.
- **Data steward:** reviews exclusions, repairs, and quality issues before reporting.
- **Analyst:** reuses PostgreSQL reporting queries and exports a filtered site summary.

## Functional requirements

1. Filter by study, region, site status, and screening cohort date range.
2. Display the funnel from screened to eligible, consented, randomized, and retained.
3. Compare monthly targets with actual randomizations.
4. Show site/study metrics, including target, screening counts, conversion, attainment, and consent lag.
5. Apply review flags using documented thresholds and show the rule that raised each flag.
6. Validate duplicate keys, assignment references, required screening dates, and event chronology.
7. Preserve a quality issue log and provide CSV exports for the filtered site report and issue examples.
8. Support a deterministic synthetic-data mode and an optional PostgreSQL source using the documented schema.
9. Present a prioritized backlog with acceptance criteria.

## Non-functional requirements

- **Privacy:** synthetic records only; no names, contact details, exact ages, diagnoses, or real participant information.
- **Explainability:** every bottleneck flag has a visible rule; every ETL repair/exclusion has a quality issue.
- **Reproducibility:** fixed random seed; generated data and clean output can be recreated from the CLI.
- **Portability:** Python + Streamlit demo runs locally or on Community Cloud; PostgreSQL connection is optional.
- **Operational boundary:** this is a portfolio analytics demo, not a validated clinical trial system, EDC, CTMS, or source of medical decisions.

## Workflow and definitions

Screening → eligibility determination → consent → randomization → withdrawal (if applicable). The selected screening-date cohort drives funnel conversion. Monthly actual enrollment counts candidates by randomization date. Monthly target attainment compares those randomizations with the sum of assigned monthly targets in the selected period.

The app flags an assignment when attainment is below 60%, screen-failure rate is above 55%, median screening-to-consent time exceeds 14 days, or it has zero randomizations despite a non-zero selected target. These are example rules for review, not clinical or regulatory thresholds.
