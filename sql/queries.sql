-- 1) CTE: site-level screening funnel and recruitment attainment.
WITH cohort AS (
    SELECT assignment_id,
           COUNT(*) AS screened,
           COUNT(*) FILTER (WHERE eligibility_status = 'Eligible') AS eligible,
           COUNT(consent_date) AS consented,
           COUNT(randomization_date) AS randomized
    FROM trialops.screening_records
    WHERE screening_date >= DATE '2025-01-01'
      AND screening_date <  DATE '2026-01-01'
    GROUP BY assignment_id
), target AS (
    SELECT assignment_id, SUM(target_enrollments) AS target_enrollments
    FROM trialops.monthly_enrollment_targets
    WHERE month >= DATE '2025-01-01'
      AND month <  DATE '2026-01-01'
    GROUP BY assignment_id
)
SELECT t.trial_id, s.site_id, s.site_name, s.region,
       COALESCE(c.screened, 0) AS screened,
       COALESCE(c.eligible, 0) AS eligible,
       COALESCE(c.consented, 0) AS consented,
       COALESCE(c.randomized, 0) AS randomized,
       COALESCE(target.target_enrollments, 0) AS target_enrollments,
       ROUND(100.0 * COALESCE(c.randomized, 0) / NULLIF(target.target_enrollments, 0), 1) AS attainment_pct
FROM trialops.site_trial_assignments a
JOIN trialops.trials t USING (trial_id)
JOIN trialops.sites s USING (site_id)
LEFT JOIN cohort c USING (assignment_id)
LEFT JOIN target USING (assignment_id)
ORDER BY attainment_pct NULLS FIRST;

-- 2) Window functions: month-by-month and cumulative enrollment versus plan.
WITH monthly AS (
    SELECT assignment_id,
           date_trunc('month', randomization_date)::date AS month,
           COUNT(*) AS actual_enrollments
    FROM trialops.screening_records
    WHERE randomization_date IS NOT NULL
    GROUP BY assignment_id, date_trunc('month', randomization_date)::date
), target AS (
    SELECT assignment_id, month, target_enrollments
    FROM trialops.monthly_enrollment_targets
), combined AS (
    SELECT target.assignment_id, target.month, target.target_enrollments,
           COALESCE(monthly.actual_enrollments, 0) AS actual_enrollments
    FROM target LEFT JOIN monthly USING (assignment_id, month)
)
SELECT assignment_id, month, target_enrollments, actual_enrollments,
       SUM(target_enrollments) OVER (
           PARTITION BY assignment_id ORDER BY month
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS cumulative_target,
       SUM(actual_enrollments) OVER (
           PARTITION BY assignment_id ORDER BY month
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS cumulative_actual,
       LAG(actual_enrollments, 1, 0) OVER (PARTITION BY assignment_id ORDER BY month) AS prior_month_actual
FROM combined
ORDER BY assignment_id, month;

-- 3) Rank sites within each study using window functions.
WITH totals AS (
    SELECT assignment_id, COUNT(randomization_date) AS randomized
    FROM trialops.screening_records
    GROUP BY assignment_id
), scored AS (
    SELECT a.trial_id, a.site_id, s.site_name, COALESCE(totals.randomized, 0) AS randomized,
           SUM(target.target_enrollments) AS target
    FROM trialops.site_trial_assignments a
    JOIN trialops.sites s USING (site_id)
    LEFT JOIN totals USING (assignment_id)
    LEFT JOIN trialops.monthly_enrollment_targets target USING (assignment_id)
    GROUP BY a.trial_id, a.site_id, s.site_name, totals.randomized
)
SELECT *, RANK() OVER (PARTITION BY trial_id ORDER BY randomized DESC) AS site_rank
FROM scored
ORDER BY trial_id, site_rank;
