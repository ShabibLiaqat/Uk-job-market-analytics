# First live extraction

Retrieved 29 September 2026 using one Adzuna API page for each configured search, limited to adverts posted in the previous 30 days. This is a small, time-bounded sample, not a census or a representative estimate of the UK labour market.

**Source: [The Adzuna API](https://www.adzuna.co.uk/).** Search descriptions and salary fields are returned by Adzuna; the API provides only a snippet of each job description ([search endpoint documentation](https://developer.adzuna.com/docs/search)).

| Check | Result |
|---|---:|
| Unique adverts after cross-search deduplication | 112 |
| Classified from title as Data Analyst | 21 |
| Classified from title as BI Analyst | 19 |
| Classified from title as MI Analyst | 6 |
| Classified from title as Other analyst | 30 |
| Classified from title as Other / review | 36 |
| UK region classified | 93 / 112 (83%) |
| Region unclassified | 19 / 112 (17%) |
| Returned salary ranges marked predicted by the API | 112 / 112 |
| Employer-reported, complete annual pay ranges | 0 |
| Records with at least one skill-dictionary match in the returned snippet | 24 / 112 (21%) |

The skill dictionary matched Power BI 9 times, stakeholder communication 7, SQL 5, Excel 4 and Azure 1. These are snippet keyword matches, not a ranking of the skills UK employers demand. Other terms did not match in this sample.

The original collector used the search phrase in its role label, which inflated the three requested categories. The current rule classifies from title text only; the corrected counts above leave ambiguous analyst titles visible for review. Search-term provenance was not retained in that first extraction, so its `matched_search_families` value is `Legacy extraction`. New collections will record query provenance separately. Role rules are versioned as 2.0.

The dashboard therefore withholds the predicted salary amounts from its employer-pay comparison and displays the required [Adzuna Jobsworth attribution](https://www.adzuna.co.uk/jobs/salary-predictor.html) beside the number of excluded estimates. The API flag does not establish whether the original employer advert contained pay; it only says these returned values are estimates.

The extract covers job adverts created from 1 to 29 September 2026. Search phrases, the 30-day window, pagination, snippet length, skill vocabulary and region mapping all constrain these results. Repeat the collection over time before drawing market-trend conclusions.
