-- Each query should return zero rows after the documented ETL controls.

-- Screening rows referencing an unknown assignment or mismatched study/site.
SELECT r.screening_id, r.assignment_id, r.trial_id, r.site_id
FROM trialops.screening_records r
LEFT JOIN trialops.site_trial_assignments a USING (assignment_id)
WHERE a.assignment_id IS NULL
   OR r.trial_id <> a.trial_id
   OR r.site_id <> a.site_id;

-- Invalid event sequence.
SELECT screening_id, screening_date, consent_date, randomization_date, withdrawal_date
FROM trialops.screening_records
WHERE (consent_date IS NOT NULL AND consent_date < screening_date)
   OR (randomization_date IS NOT NULL AND (consent_date IS NULL OR randomization_date < consent_date))
   OR (withdrawal_date IS NOT NULL AND (randomization_date IS NULL OR withdrawal_date < randomization_date));

-- Negative or duplicate monthly targets.
SELECT assignment_id, month, target_enrollments
FROM trialops.monthly_enrollment_targets
WHERE target_enrollments < 0;

SELECT assignment_id, month, COUNT(*) AS rows_per_month
FROM trialops.monthly_enrollment_targets
GROUP BY assignment_id, month
HAVING COUNT(*) > 1;

-- Data-quality issue counts for review.
SELECT issue_type, COUNT(*) AS issue_count
FROM trialops.data_quality_issues
GROUP BY issue_type
ORDER BY issue_count DESC;
