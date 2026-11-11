-- PostgreSQL schema for the synthetic Clinical Trial Operations Tracker.
-- Contains no personal health information or real participant data.
CREATE SCHEMA IF NOT EXISTS trialops;

CREATE TABLE IF NOT EXISTS trialops.trials (
    trial_id TEXT PRIMARY KEY,
    protocol_title TEXT NOT NULL,
    phase TEXT NOT NULL,
    therapeutic_area TEXT NOT NULL,
    start_date DATE NOT NULL,
    study_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trialops.sites (
    site_id TEXT PRIMARY KEY,
    site_name TEXT NOT NULL,
    country TEXT NOT NULL,
    region TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trialops.site_trial_assignments (
    assignment_id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL REFERENCES trialops.trials(trial_id),
    site_id TEXT NOT NULL REFERENCES trialops.sites(site_id),
    activation_date DATE NOT NULL,
    site_status TEXT NOT NULL CHECK (site_status IN ('Active', 'Paused', 'Closing')),
    UNIQUE (trial_id, site_id)
);

CREATE TABLE IF NOT EXISTS trialops.screening_records (
    screening_id TEXT PRIMARY KEY,
    assignment_id TEXT NOT NULL REFERENCES trialops.site_trial_assignments(assignment_id),
    trial_id TEXT NOT NULL REFERENCES trialops.trials(trial_id),
    site_id TEXT NOT NULL REFERENCES trialops.sites(site_id),
    screening_date DATE NOT NULL,
    eligibility_status TEXT NOT NULL CHECK (eligibility_status IN ('Eligible', 'Screen failure', 'Unknown')),
    consent_date DATE,
    randomization_date DATE,
    withdrawal_date DATE,
    screen_failure_reason TEXT,
    withdrawal_reason TEXT,
    referral_channel TEXT NOT NULL,
    CHECK (consent_date IS NULL OR consent_date >= screening_date),
    CHECK (randomization_date IS NULL OR (consent_date IS NOT NULL AND randomization_date >= consent_date)),
    CHECK (withdrawal_date IS NULL OR (randomization_date IS NOT NULL AND withdrawal_date >= randomization_date))
);

CREATE TABLE IF NOT EXISTS trialops.monthly_enrollment_targets (
    assignment_id TEXT NOT NULL REFERENCES trialops.site_trial_assignments(assignment_id),
    month DATE NOT NULL,
    target_enrollments INTEGER NOT NULL CHECK (target_enrollments >= 0),
    PRIMARY KEY (assignment_id, month)
);

CREATE TABLE IF NOT EXISTS trialops.data_quality_issues (
    issue_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    screening_id TEXT,
    issue_type TEXT NOT NULL,
    details TEXT NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_screening_assignment_date ON trialops.screening_records(assignment_id, screening_date);
CREATE INDEX IF NOT EXISTS idx_screening_randomization_date ON trialops.screening_records(randomization_date);
CREATE INDEX IF NOT EXISTS idx_targets_month ON trialops.monthly_enrollment_targets(month);
