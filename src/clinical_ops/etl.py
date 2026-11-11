"""ETL and data-quality controls for the synthetic recruitment dataset."""

import json
from pathlib import Path

import pandas as pd


def run_etl(raw_dir: str | Path, output_dir: str | Path) -> dict[str, Path]:
    raw_dir, output_dir = Path(raw_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    trials = pd.read_csv(raw_dir / "trials.csv")
    sites = pd.read_csv(raw_dir / "sites.csv")
    assignments = pd.read_csv(raw_dir / "site_assignments.csv", parse_dates=["activation_date"])
    targets = pd.read_csv(raw_dir / "monthly_targets.csv", parse_dates=["month"])
    screenings = pd.read_csv(raw_dir / "screenings.csv")

    issues: list[dict] = []
    report = {
        "trials": int(len(trials)),
        "sites": int(len(sites)),
        "site_trial_assignments": int(len(assignments)),
        "source_screening_rows": int(len(screenings)),
        "source_monthly_target_rows": int(len(targets)),
    }

    duplicate_mask = screenings.duplicated("screening_id", keep="first")
    for _, row in screenings.loc[duplicate_mask].iterrows():
        issues.append({"screening_id": row["screening_id"], "issue_type": "duplicate_screening_id", "details": "Repeated screening key; kept first occurrence."})
    report["duplicate_screening_rows_removed"] = int(duplicate_mask.sum())
    screenings = screenings.loc[~duplicate_mask].copy()

    assignment_ids = set(assignments["assignment_id"])
    orphan_mask = ~screenings["assignment_id"].isin(assignment_ids)
    for _, row in screenings.loc[orphan_mask].iterrows():
        issues.append({"screening_id": row["screening_id"], "issue_type": "orphan_assignment", "details": f"Unknown assignment_id {row['assignment_id']}."})
    report["orphan_assignment_rows_removed"] = int(orphan_mask.sum())
    screenings = screenings.loc[~orphan_mask].copy()

    assignment_lookup = assignments.set_index("assignment_id")[["trial_id", "site_id"]]
    joined = screenings.join(assignment_lookup, on="assignment_id", rsuffix="_assigned")
    mismatch = (joined["trial_id"] != joined["trial_id_assigned"]) | (joined["site_id"] != joined["site_id_assigned"])
    report["assignment_key_mismatches_removed"] = int(mismatch.sum())
    for _, row in joined.loc[mismatch].iterrows():
        issues.append({"screening_id": row["screening_id"], "issue_type": "assignment_key_mismatch", "details": "Screening trial/site does not match its assignment."})
    screenings = joined.loc[~mismatch].drop(columns=["trial_id_assigned", "site_id_assigned"]).copy()

    date_columns = ["screening_date", "consent_date", "randomization_date", "withdrawal_date"]
    for column in date_columns:
        screenings[column] = pd.to_datetime(screenings[column], errors="coerce")
    missing_screen = screenings["screening_date"].isna()
    report["missing_screening_dates_removed"] = int(missing_screen.sum())
    for _, row in screenings.loc[missing_screen].iterrows():
        issues.append({"screening_id": row["screening_id"], "issue_type": "missing_screening_date", "details": "Required screening date is missing; row excluded from the analytic cohort."})
    screenings = screenings.loc[~missing_screen].copy()

    consent_before_screen = screenings["consent_date"].notna() & (screenings["consent_date"] < screenings["screening_date"])
    for _, row in screenings.loc[consent_before_screen].iterrows():
        issues.append({"screening_id": row["screening_id"], "issue_type": "consent_before_screening", "details": "Consent date preceded screening date; consent and downstream dates cleared."})
    report["consent_before_screening_dates_cleared"] = int(consent_before_screen.sum())
    screenings.loc[consent_before_screen, ["consent_date", "randomization_date", "withdrawal_date"]] = pd.NaT

    random_before_consent = screenings["randomization_date"].notna() & (
        screenings["consent_date"].isna() | (screenings["randomization_date"] < screenings["consent_date"])
    )
    for _, row in screenings.loc[random_before_consent].iterrows():
        issues.append({"screening_id": row["screening_id"], "issue_type": "randomization_before_consent", "details": "Randomization date preceded or lacked valid consent; randomization and withdrawal dates cleared."})
    report["randomization_before_consent_dates_cleared"] = int(random_before_consent.sum())
    screenings.loc[random_before_consent, ["randomization_date", "withdrawal_date"]] = pd.NaT

    withdrawal_before_randomization = screenings["withdrawal_date"].notna() & (
        screenings["randomization_date"].isna() | (screenings["withdrawal_date"] < screenings["randomization_date"])
    )
    for _, row in screenings.loc[withdrawal_before_randomization].iterrows():
        issues.append({"screening_id": row["screening_id"], "issue_type": "withdrawal_before_randomization", "details": "Withdrawal date preceded or lacked randomization; withdrawal date cleared."})
    report["withdrawal_before_randomization_dates_cleared"] = int(withdrawal_before_randomization.sum())
    screenings.loc[withdrawal_before_randomization, "withdrawal_date"] = pd.NaT

    screenings["eligibility_status"] = screenings["eligibility_status"].fillna("Unknown")
    screenings["referral_channel"] = screenings["referral_channel"].fillna("Unknown")
    screenings = screenings.sort_values(["screening_date", "screening_id"]).reset_index(drop=True)
    targets["month"] = targets["month"].dt.to_period("M").dt.to_timestamp()
    targets["target_enrollments"] = pd.to_numeric(targets["target_enrollments"], errors="coerce").fillna(0).clip(lower=0).astype(int)

    clean_screenings = output_dir / "clean_screenings.csv"
    quality_path = output_dir / "quality_report.json"
    issues_path = output_dir / "quality_issues.csv"
    targets_path = output_dir / "monthly_targets.csv"
    screenings.to_csv(clean_screenings, index=False, date_format="%Y-%m-%d")
    targets.to_csv(targets_path, index=False, date_format="%Y-%m-%d")
    pd.DataFrame(issues, columns=["screening_id", "issue_type", "details"]).to_csv(issues_path, index=False)
    report["clean_screening_rows"] = int(len(screenings))
    report["quality_issue_count"] = int(len(issues))
    report["simulated_data_notice"] = "All records are synthetic. No real participant data is included."
    quality_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {
        "trials": raw_dir / "trials.csv",
        "sites": raw_dir / "sites.csv",
        "assignments": raw_dir / "site_assignments.csv",
        "screenings": clean_screenings,
        "targets": targets_path,
        "quality": quality_path,
        "issues": issues_path,
    }
