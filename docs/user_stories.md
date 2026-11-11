# Vertical user stories and acceptance criteria

The CSV version drives the in-app backlog table. “Done” means the corresponding capability is represented by this portfolio demo, not that it was delivered for a real sponsor.

## Sprint 1 — recruitment dashboard

### CTO-01 · Filter the network (P0)
As a study manager, I can filter by study, region, and site status so I can focus review on a selected network slice.

- Filters narrow all site and chart outputs.
- Clearing a filter restores the corresponding rows.

### CTO-02 · Review the funnel (P0)
As a recruitment lead, I can see counts from screened through retained so I can identify where candidates leave the funnel.

- Show screened, eligible, consented, randomized, and retained counts.
- Keep the same selected screening-date cohort across funnel stages.

### CTO-03 · Compare monthly plan and actual (P0)
As a study manager, I can compare monthly enrollment targets with actual randomizations so I can review pace over time.

- Group targets and randomizations by calendar month.
- Apply the active study and region filters.

### CTO-04 · Prioritize site follow-up (P0)
As a site manager, I can see site/study attainment and an explained review flag so I can prioritize follow-up.

- Show target, randomized count, attainment, and the rule that triggered a flag.
- Show “On track” when no review rule is met.

### CTO-05 · Locate conversion friction (P1)
As an analyst, I can compare screening failure and consent-cycle measures across sites.

- Show failure rate and median screening-to-consent days.
- Suppress undefined conversion rates when a denominator is zero.

### CTO-06 · Export a review snapshot (P1)
As a stakeholder, I can export the filtered site report for a review meeting.

- Provide a CSV with visible metrics and study/site dimensions.
- Respect current filters in the export.

## Sprint 2 — data controls and reproducible reporting

### CTO-07 · Review data-quality exceptions (P0)
As a data steward, I can review the ETL issue log and understand what was repaired or excluded.

- Show source and clean counts, issue categories, and example records.
- Provide a CSV download of issue details.

### CTO-08 · Deduplicate screenings (P0)
As a data engineer, I can remove duplicate screening IDs so one screening is not counted twice.

- Keep the first row per screening ID.
- Report removed-row count and log later duplicates.

### CTO-09 · Validate site/study references (P0)
As a data engineer, I can reject screenings without a valid assignment so reports do not include orphans.

- Exclude unknown assignments and mismatched study/site keys.
- Record each exclusion in the quality issue log.

### CTO-10 · Enforce event chronology (P0)
As a data steward, I can prevent impossible event dates from distorting the recruitment funnel.

- Validate screening ≤ consent ≤ randomization ≤ withdrawal.
- Clear invalid downstream events and log the correction.

### CTO-11 · Reuse stakeholder SQL (P1)
As an analyst, I can use PostgreSQL CTE and window-function examples for repeatable reporting.

- Include a funnel CTE, cumulative monthly totals, LAG, RANK, and QA queries.
- Keep DDL and SQL compatible with the documented schema.

### CTO-12 · Inspect delivery scope (P1)
As a product reviewer, I can inspect a prioritized backlog and acceptance criteria.

- Expose at least 12 sprint-prioritized stories.
- Give each story a reviewable acceptance criterion and vertical slice.
