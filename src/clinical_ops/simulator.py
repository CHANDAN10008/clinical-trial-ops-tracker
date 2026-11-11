"""Deterministic simulated trial operations data; no real patient data."""

from pathlib import Path

import numpy as np
import pandas as pd


TRIALS = [
    {"trial_id": "CT-ALPHA", "protocol_title": "ALPHA: Biomarker-Guided Therapy Study", "phase": "Phase II", "therapeutic_area": "Oncology", "start_date": "2024-01-15", "study_status": "Recruiting"},
    {"trial_id": "CT-BRAVO", "protocol_title": "BRAVO: Metabolic Outcomes Study", "phase": "Phase III", "therapeutic_area": "Metabolic", "start_date": "2024-02-01", "study_status": "Recruiting"},
    {"trial_id": "CT-CHARLIE", "protocol_title": "CHARLIE: Cardiovascular Safety Study", "phase": "Phase II", "therapeutic_area": "Cardiovascular", "start_date": "2024-03-01", "study_status": "Recruiting"},
]

GEOGRAPHY = [
    ("Boston", "United States", "North America"), ("Chicago", "United States", "North America"),
    ("Austin", "United States", "North America"), ("Toronto", "Canada", "North America"),
    ("Vancouver", "Canada", "North America"), ("London", "United Kingdom", "Europe"),
    ("Manchester", "United Kingdom", "Europe"), ("Berlin", "Germany", "Europe"),
    ("Munich", "Germany", "Europe"), ("Madrid", "Spain", "Europe"),
    ("Warsaw", "Poland", "Europe"), ("Bengaluru", "India", "Asia Pacific"),
    ("Hyderabad", "India", "Asia Pacific"), ("Pune", "India", "Asia Pacific"),
    ("Tokyo", "Japan", "Asia Pacific"), ("Osaka", "Japan", "Asia Pacific"),
    ("Sydney", "Australia", "Asia Pacific"), ("Sao Paulo", "Brazil", "Latin America"),
]


def generate_synthetic_data(raw_dir: str | Path, seed: int = 20261111) -> dict[str, Path]:
    """Write trials, sites, assignments, screening records, and monthly targets."""
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    trials = pd.DataFrame(TRIALS)
    site_rows = []
    for index, (city, country, region) in enumerate(GEOGRAPHY, start=1):
        site_rows.append({
            "site_id": f"SITE-{index:03d}",
            "site_name": f"{city} Research Centre",
            "country": country,
            "region": region,
        })
    sites = pd.DataFrame(site_rows)

    assignments = []
    target_rows = []
    assignment_quality = {}
    final_month = pd.Timestamp("2025-12-01")
    for site_index, site in sites.iterrows():
        for trial_index, trial in trials.iterrows():
            assignment_id = f"ASG-{site_index + 1:03d}-{trial_index + 1:02d}"
            activation = pd.Timestamp("2024-02-01") + pd.Timedelta(days=int(rng.integers(0, 190)))
            status = rng.choice(["Active", "Active", "Active", "Paused", "Closing"], p=[0.42, 0.24, 0.16, 0.10, 0.08])
            assigned = {
                "assignment_id": assignment_id,
                "trial_id": trial["trial_id"],
                "site_id": site["site_id"],
                "activation_date": activation.strftime("%Y-%m-%d"),
                "site_status": str(status),
            }
            assignments.append(assigned)
            assignment_quality[assignment_id] = {
                "eligibility": float(rng.uniform(0.47, 0.86)),
                "consent": float(rng.uniform(0.58, 0.91)),
                "randomization": float(rng.uniform(0.68, 0.94)),
            }
            months = pd.date_range(activation.to_period("M").to_timestamp(), final_month, freq="MS")
            monthly_targets = rng.choice([1, 2, 2, 3], size=len(months), p=[0.20, 0.40, 0.25, 0.15])
            for month, target in zip(months, monthly_targets):
                target_rows.append({
                    "assignment_id": assignment_id,
                    "month": month.strftime("%Y-%m-%d"),
                    "target_enrollments": int(target),
                })

    assignments_df = pd.DataFrame(assignments)
    targets_df = pd.DataFrame(target_rows)
    assignment_ids = assignments_df["assignment_id"].to_numpy()
    probabilities = np.array([assignment_quality[a]["eligibility"] for a in assignment_ids])
    probabilities = probabilities / probabilities.sum()
    n_screenings = 3200
    chosen_assignments = rng.choice(assignment_ids, size=n_screenings, p=probabilities)
    assignment_map = assignments_df.set_index("assignment_id").to_dict("index")
    records = []
    referral_channels = ["Physician referral", "Community outreach", "Digital campaign", "Patient registry"]
    failure_reasons = ["Inclusion criterion not met", "Laboratory threshold", "Competing condition", "Participant declined screening"]
    withdrawal_reasons = ["Participant choice", "Adverse event", "Lost to follow-up", "Investigator decision"]

    for record_number, assignment_id in enumerate(chosen_assignments, start=1):
        assignment = assignment_map[assignment_id]
        start = pd.Timestamp(assignment["activation_date"])
        days_available = max(1, int((pd.Timestamp("2025-11-30") - start).days))
        screen_date = start + pd.Timedelta(days=int(rng.integers(0, days_available)))
        quality = assignment_quality[assignment_id]
        eligible = bool(rng.random() < quality["eligibility"])
        consent_date = pd.NaT
        randomization_date = pd.NaT
        withdrawal_date = pd.NaT
        failure_reason = None if eligible else str(rng.choice(failure_reasons))
        withdrawal_reason = None
        if eligible and rng.random() < quality["consent"]:
            consent_date = screen_date + pd.Timedelta(days=int(rng.integers(1, 22)))
            if rng.random() < quality["randomization"]:
                randomization_date = consent_date + pd.Timedelta(days=int(rng.integers(1, 16)))
                if rng.random() < 0.09:
                    withdrawal_date = randomization_date + pd.Timedelta(days=int(rng.integers(1, 150)))
                    withdrawal_reason = str(rng.choice(withdrawal_reasons))
        records.append({
            "screening_id": f"SIM-S-{record_number:06d}",
            "assignment_id": assignment_id,
            "trial_id": assignment["trial_id"],
            "site_id": assignment["site_id"],
            "screening_date": screen_date.strftime("%Y-%m-%d"),
            "eligibility_status": "Eligible" if eligible else "Screen failure",
            "consent_date": consent_date.strftime("%Y-%m-%d") if pd.notna(consent_date) else None,
            "randomization_date": randomization_date.strftime("%Y-%m-%d") if pd.notna(randomization_date) else None,
            "withdrawal_date": withdrawal_date.strftime("%Y-%m-%d") if pd.notna(withdrawal_date) else None,
            "screen_failure_reason": failure_reason,
            "withdrawal_reason": withdrawal_reason,
            "referral_channel": str(rng.choice(referral_channels)),
        })

    screenings = pd.DataFrame(records)
    # Seed source-system defects for the visible ETL and validation report.
    duplicate_rows = screenings.iloc[:18].copy()
    orphan_rows = screenings.iloc[18:28].copy()
    orphan_rows["screening_id"] = [f"SIM-ORPHAN-{n:03d}" for n in range(len(orphan_rows))]
    orphan_rows["assignment_id"] = [f"ASG-MISSING-{n:03d}" for n in range(len(orphan_rows))]
    missing_date_rows = screenings.iloc[28:36].copy()
    missing_date_rows["screening_id"] = [f"SIM-MISSING-DATE-{n:03d}" for n in range(len(missing_date_rows))]
    missing_date_rows["screening_date"] = None
    timeline_rows = screenings.iloc[36:48].copy()
    timeline_rows["screening_id"] = [f"SIM-TIMELINE-{n:03d}" for n in range(len(timeline_rows))]
    for idx in range(0, len(timeline_rows), 3):
        screen_date = pd.to_datetime(timeline_rows.iloc[idx]["screening_date"])
        timeline_rows.iloc[idx, timeline_rows.columns.get_loc("consent_date")] = (screen_date - pd.Timedelta(days=2)).strftime("%Y-%m-%d")
    for idx in range(1, len(timeline_rows), 3):
        consent = timeline_rows.iloc[idx]["consent_date"]
        if pd.notna(consent):
            timeline_rows.iloc[idx, timeline_rows.columns.get_loc("randomization_date")] = (pd.to_datetime(consent) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    for idx in range(2, len(timeline_rows), 3):
        randomized = timeline_rows.iloc[idx]["randomization_date"]
        if pd.notna(randomized):
            timeline_rows.iloc[idx, timeline_rows.columns.get_loc("withdrawal_date")] = (pd.to_datetime(randomized) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    screenings = pd.concat([screenings, duplicate_rows, orphan_rows, missing_date_rows, timeline_rows], ignore_index=True)

    frames = {
        "trials.csv": trials,
        "sites.csv": sites,
        "site_assignments.csv": assignments_df,
        "screenings.csv": screenings,
        "monthly_targets.csv": targets_df,
    }
    paths = {}
    for filename, frame in frames.items():
        path = raw_dir / filename
        frame.to_csv(path, index=False)
        paths[filename.removesuffix(".csv")] = path
    return paths
