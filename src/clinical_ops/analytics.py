"""Recruitment cohort, site-performance, and monthly target calculations."""

import pandas as pd


def build_site_performance(
    trials: pd.DataFrame,
    sites: pd.DataFrame,
    assignments: pd.DataFrame,
    screenings: pd.DataFrame,
    targets: pd.DataFrame,
    start_date,
    end_date,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    period_start = start.to_period("M").to_timestamp()
    period_end = end.to_period("M").to_timestamp()
    period_end_exclusive = period_end + pd.offsets.MonthBegin(1)
    cohort = screenings.loc[screenings["screening_date"].between(start, end)].copy()
    monthly_targets = targets.loc[targets["month"].between(period_start, period_end)].copy()

    assignment_info = assignments.merge(sites, on="site_id", how="left").merge(trials, on="trial_id", how="left")
    denominator = monthly_targets.groupby("assignment_id", as_index=False)["target_enrollments"].sum().rename(columns={"target_enrollments": "target_enrollments"})
    cohort_counts = cohort.groupby("assignment_id").agg(
        screened=("screening_id", "nunique"),
        eligible=("eligibility_status", lambda s: int((s == "Eligible").sum())),
        consented=("consent_date", "count"),
        randomized=("randomization_date", "count"),
        withdrawn=("withdrawal_date", "count"),
    ).reset_index()
    consent_lag = cohort.loc[cohort["consent_date"].notna()].assign(
        days_to_consent=lambda frame: (frame["consent_date"] - frame["screening_date"]).dt.days
    ).groupby("assignment_id")["days_to_consent"].median().rename("median_days_to_consent").reset_index()
    randomized_in_period = screenings.loc[
        screenings["randomization_date"].notna()
        & screenings["randomization_date"].ge(period_start)
        & screenings["randomization_date"].lt(period_end_exclusive)
    ].groupby("assignment_id").agg(randomized_in_period=("screening_id", "nunique")).reset_index()
    metrics = (assignment_info.merge(denominator, on="assignment_id", how="left")
               .merge(cohort_counts, on="assignment_id", how="left")
               .merge(consent_lag, on="assignment_id", how="left")
               .merge(randomized_in_period, on="assignment_id", how="left"))
    for column in ["target_enrollments", "screened", "eligible", "consented", "randomized", "withdrawn", "randomized_in_period"]:
        metrics[column] = metrics[column].fillna(0).astype(int)
    target_denominator = metrics["target_enrollments"].where(metrics["target_enrollments"].ne(0))
    screen_denominator = metrics["screened"].where(metrics["screened"].ne(0))
    eligible_denominator = metrics["eligible"].where(metrics["eligible"].ne(0))
    consent_denominator = metrics["consented"].where(metrics["consented"].ne(0))
    metrics["attainment_pct"] = (metrics["randomized_in_period"].div(target_denominator) * 100).fillna(0)
    metrics["screen_failure_pct"] = ((metrics["screened"] - metrics["eligible"]).div(screen_denominator) * 100).fillna(0)
    metrics["consent_rate_pct"] = (metrics["consented"].div(eligible_denominator) * 100).fillna(0)
    metrics["randomization_rate_pct"] = (metrics["randomized"].div(consent_denominator) * 100).fillna(0)

    def flags(row):
        reasons = []
        if row["target_enrollments"] > 0 and row["attainment_pct"] < 60:
            reasons.append("Behind target")
        if row["screened"] > 0 and row["screen_failure_pct"] > 55:
            reasons.append("High screen-failure rate")
        if pd.notna(row["median_days_to_consent"]) and row["median_days_to_consent"] > 14:
            reasons.append("Slow consent cycle")
        if row["randomized_in_period"] == 0 and row["target_enrollments"] > 0:
            reasons.append("No randomizations")
        return "; ".join(dict.fromkeys(reasons)) if reasons else "On track"

    metrics["bottleneck"] = metrics.apply(flags, axis=1)
    metrics["at_risk"] = metrics["bottleneck"].ne("On track")
    metrics = metrics.sort_values(["at_risk", "attainment_pct", "trial_id"], ascending=[False, True, True])

    actual = screenings.loc[
        screenings["randomization_date"].notna()
        & screenings["randomization_date"].ge(period_start)
        & screenings["randomization_date"].lt(period_end_exclusive)
    ].copy()
    actual["month"] = actual["randomization_date"].dt.to_period("M").dt.to_timestamp()
    actual = actual.groupby(["assignment_id", "month"], as_index=False).agg(actual_enrollments=("screening_id", "nunique"))
    monthly = monthly_targets.merge(actual, on=["assignment_id", "month"], how="left")
    monthly["actual_enrollments"] = monthly["actual_enrollments"].fillna(0).astype(int)
    monthly = monthly.merge(assignment_info[["assignment_id", "trial_id", "site_id", "site_name", "region"]], on="assignment_id", how="left")
    monthly = monthly.groupby(["month", "trial_id", "site_id", "site_name", "region"], as_index=False).agg(
        target_enrollments=("target_enrollments", "sum"), actual_enrollments=("actual_enrollments", "sum")
    ).sort_values("month")
    return metrics.reset_index(drop=True), monthly, cohort
