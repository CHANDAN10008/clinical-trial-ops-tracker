# QA and data-quality checks

The demo generator deliberately seeds source defects so the repair path can be inspected. Counts are generated from a fixed seed and are reported by the ETL at runtime.

| Defect class | Seeded example | ETL response | Visible evidence |
| --- | --- | --- | --- |
| Duplicate screening key | Repeated `screening_id` rows | Keep first occurrence | `duplicate_screening_id` issue and removal count |
| Orphan assignment | Screening points to an unknown assignment | Exclude row | `orphan_assignment` issue and removal count |
| Mismatched trial/site key | Assignment exists but screening dimensions disagree | Exclude row | `assignment_key_mismatch` issue |
| Missing screening date | Required cohort date is null | Exclude row | `missing_screening_date` issue |
| Consent before screening | Consent event predates screening | Clear consent and downstream dates | `consent_before_screening` issue |
| Randomization before consent | Randomization predates or has no valid consent | Clear randomization and withdrawal | `randomization_before_consent` issue |
| Withdrawal before randomization | Withdrawal predates or has no valid randomization | Clear withdrawal | `withdrawal_before_randomization` issue |

## Review checklist

- Compare raw row counts with clean row counts in `quality_report.json`.
- Confirm each detected defect type appears in the downloadable issue log.
- Confirm the cleaned event chronology satisfies screening ≤ consent ≤ randomization ≤ withdrawal.
- Confirm target tables contain non-negative integer targets and one row per assignment/month.
- Review site flags against their stated thresholds before interpreting them.

These checks demonstrate data-quality handling on a seeded synthetic dataset; they are not clinical validation or regulatory validation evidence.
