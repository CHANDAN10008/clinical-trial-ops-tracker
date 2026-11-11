"""Generate the demo CSVs and run the ETL from the repository root."""

import argparse
from pathlib import Path

from clinical_ops.etl import run_etl
from clinical_ops.simulator import generate_synthetic_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the synthetic TrialOps demo dataset")
    parser.add_argument("command", choices=["demo"], nargs="?", default="demo")
    parser.add_argument("--data-dir", default="data/generated")
    args = parser.parse_args()
    base = Path(args.data_dir)
    generate_synthetic_data(base / "raw")
    outputs = run_etl(base / "raw", base / "processed")
    print(f"Synthetic demo data generated. Clean screenings: {outputs['screenings']}")
    print(f"Quality report: {outputs['quality']}")


if __name__ == "__main__":
    main()
