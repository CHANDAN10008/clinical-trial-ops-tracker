"""Load either the included synthetic CSV demo or configured PostgreSQL tables."""

import json
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from clinical_ops.etl import run_etl
from clinical_ops.simulator import generate_synthetic_data


def load_demo_bundle(project_root: str | Path) -> dict:
    root = Path(project_root)
    raw_dir = root / "data" / "generated" / "raw"
    output_dir = root / "data" / "generated" / "processed"
    required = [raw_dir / name for name in ["trials.csv", "sites.csv", "site_assignments.csv", "screenings.csv", "monthly_targets.csv"]]
    if any(not path.exists() for path in required):
        generate_synthetic_data(raw_dir)
    paths = run_etl(raw_dir, output_dir)
    return {
        "trials": pd.read_csv(paths["trials"], parse_dates=["start_date"]),
        "sites": pd.read_csv(paths["sites"]),
        "assignments": pd.read_csv(paths["assignments"], parse_dates=["activation_date"]),
        "screenings": pd.read_csv(paths["screenings"], parse_dates=["screening_date", "consent_date", "randomization_date", "withdrawal_date"]),
        "targets": pd.read_csv(paths["targets"], parse_dates=["month"]),
        "quality_issues": pd.read_csv(paths["issues"]),
        "quality_report": json.loads(paths["quality"].read_text(encoding="utf-8")),
        "source_mode": "Synthetic demo",
    }


def _normalize_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def load_postgres_bundle(database_url: str) -> dict:
    """Read the documented trialops schema; database credentials stay in secrets."""
    engine = create_engine(_normalize_url(database_url), pool_pre_ping=True, connect_args={"connect_timeout": 8})
    queries = {
        "trials": "SELECT * FROM trialops.trials ORDER BY trial_id",
        "sites": "SELECT * FROM trialops.sites ORDER BY site_id",
        "assignments": "SELECT * FROM trialops.site_trial_assignments ORDER BY assignment_id",
        "screenings": "SELECT * FROM trialops.screening_records ORDER BY screening_date, screening_id",
        "targets": "SELECT * FROM trialops.monthly_enrollment_targets ORDER BY month, assignment_id",
        "quality_issues": "SELECT screening_id, issue_type, details FROM trialops.data_quality_issues ORDER BY issue_id DESC LIMIT 1000",
    }
    with engine.connect() as connection:
        frames = {name: pd.read_sql(text(query), connection) for name, query in queries.items()}
        counts = {
            "trials": int(pd.read_sql(text("SELECT COUNT(*) AS n FROM trialops.trials"), connection)["n"].iloc[0]),
            "sites": int(pd.read_sql(text("SELECT COUNT(*) AS n FROM trialops.sites"), connection)["n"].iloc[0]),
            "screening_rows": int(pd.read_sql(text("SELECT COUNT(*) AS n FROM trialops.screening_records"), connection)["n"].iloc[0]),
        }
    engine.dispose()
    for column in ["start_date"]:
        frames["trials"][column] = pd.to_datetime(frames["trials"][column], errors="coerce")
    frames["assignments"]["activation_date"] = pd.to_datetime(frames["assignments"]["activation_date"], errors="coerce")
    for column in ["screening_date", "consent_date", "randomization_date", "withdrawal_date"]:
        frames["screenings"][column] = pd.to_datetime(frames["screenings"][column], errors="coerce")
    frames["targets"]["month"] = pd.to_datetime(frames["targets"]["month"], errors="coerce")
    counts["quality_issue_count"] = int(len(frames["quality_issues"]))
    return {**frames, "quality_report": counts, "source_mode": "PostgreSQL"}
