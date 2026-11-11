# Data dictionary

All records are synthetic, generated with a fixed seed, and are not linked to real people.

| Entity | Field | Meaning |
| --- | --- | --- |
| Trial | `trial_id` | Synthetic study key |
| Trial | `phase`, `therapeutic_area`, `study_status` | Simulated protocol descriptors |
| Site | `site_id`, `site_name` | Synthetic research-site identifiers and labels |
| Site | `country`, `region` | Synthetic site geography |
| Assignment | `assignment_id` | Link between one study and one site |
| Assignment | `activation_date`, `site_status` | Simulated activation and operational status |
| Screening | `screening_id` | Synthetic screening-event key; not a person identifier |
| Screening | `screening_date`, `eligibility_status` | Simulated screening date and eligibility outcome |
| Screening | `consent_date`, `randomization_date`, `withdrawal_date` | Simulated event dates; null means event not reached or was cleared by a quality control |
| Screening | `screen_failure_reason`, `withdrawal_reason` | Simulated categorical reason, not medical history |
| Screening | `referral_channel` | Simulated source channel |
| Target | `month`, `target_enrollments` | Synthetic monthly plan for an assignment |
| Quality issue | `issue_type`, `details` | ETL-detected seeded source anomaly and handling note |

No direct identifiers, free-text clinical notes, exact age, address, phone number, or real patient records are generated.
