# Data dictionary

| Field | Meaning |
|---|---|
| `posting_id` | Unique posting identifier from the source; demo IDs are fictional. |
| `title`, `employer` | Title and employer label returned by the source. |
| `location` | Source display location. |
| `region` | UK region/nation when found in the API location hierarchy or known county mapping; otherwise `Unclassified`. |
| `role_family` | Classified from the advert title only: Data Analyst, BI Analyst, MI Analyst, Other analyst or Other / review. Search phrases are not used as classification evidence. BI/MI classification requires an analyst title. |
| `role_taxonomy_version` | Version of title-based role rules. Version 2.0 introduces explicit `Other analyst` and `Other / review` groups and separates search provenance from the role label. |
| `matched_search_families` | Pipe-separated search families that returned this advert. This is collection provenance, not the advert's role classification. Legacy first-pull records are marked `Legacy extraction` because query-level overlap was not retained then. |
| `posted_date` | Date parsed from the source's advert creation timestamp. |
| `retrieved_on` | Local collection date. Repeated captures form advert-level snapshots. |
| `salary_min`, `salary_max` | Numeric bounds returned by the source. The amount is not converted. |
| `salary_period` | Explicit period detected in title and fetched description snippet: annual, hourly, weekly, monthly or unspecified. A failure to detect a period does not mean the advert has no salary. |
| `salary_is_predicted` | Source flag for estimated/predicted salary. Predicted values are excluded from employer-reported pay charts and the dashboard links them to Adzuna Jobsworth. |
| `contract_type` | Contract type when returned; otherwise `Not stated`. |
| `skills` | Pipe-separated matches from the project vocabulary. On real records, derived from text in memory; raw description text is discarded. |
| `skill_taxonomy_version` | Version of the keyword dictionary used to derive `skills`; compare mention rates across captures with the same version. |
| `source` | `Adzuna API` for live rows or `Fictional preview data` for demo rows. |
| `is_synthetic` | Explicitly marks fictional preview rows. |

## Interpretation

Salary chart rows require both numeric bounds and `salary_period = annual`. Values with missing or ambiguous periods stay in the dataset and do not enter the chart. The midpoint is a simple descriptive statistic, not a take-home pay estimate or a measure of accepted offers.

Skill mention rates are the share of collected records matching each keyword. They depend on the source's returned text snippet and this project's dictionary. Mentions do not prove skill proficiency or employer priority.

Region coverage depends on how each location is represented by the source. Keep unclassified values visible in data-quality review and widen the mapping only when records support it.
