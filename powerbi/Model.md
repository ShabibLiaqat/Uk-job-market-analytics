# Power BI model and report design

## Model

The fact grain is **one row per advert ID per collection date**. That makes repeated weekly captures comparable while preventing an advert returned by two overlapping search phrases from counting twice in one capture. `Adverts Captured` counts these observations; `Unique Adverts` counts IDs across the selected period.

Create these calculated tables in Power BI Desktop (**Modeling → New table**):

```DAX
DimSnapshotDate =
VAR MinDate = MINX ( ALL ( Jobs ), Jobs[retrieved_on] )
VAR MaxDate = MAXX ( ALL ( Jobs ), Jobs[retrieved_on] )
RETURN
    ADDCOLUMNS (
        CALENDAR ( MinDate, MaxDate ),
        "Year", YEAR ( [Date] ),
        "Month Number", MONTH ( [Date] ),
        "Month Start", DATE ( YEAR ( [Date] ), MONTH ( [Date] ), 1 ),
        "Month Label", FORMAT ( [Date], "MMM yyyy" ),
        "Month Sort", YEAR ( [Date] ) * 100 + MONTH ( [Date] )
    )
```

```DAX
DimPostedDate =
VAR DatedJobs = FILTER ( ALL ( Jobs ), NOT ISBLANK ( Jobs[posted_date] ) )
VAR MinDate = MINX ( DatedJobs, Jobs[posted_date] )
VAR MaxDate = MAXX ( DatedJobs, Jobs[posted_date] )
RETURN
    ADDCOLUMNS (
        CALENDAR ( MinDate, MaxDate ),
        "Year", YEAR ( [Date] ),
        "Month Number", MONTH ( [Date] ),
        "Month Start", DATE ( YEAR ( [Date] ), MONTH ( [Date] ), 1 ),
        "Month Label", FORMAT ( [Date], "MMM yyyy" ),
        "Month Sort", YEAR ( [Date] ) * 100 + MONTH ( [Date] )
    )
```

Mark both date tables as date tables using their `[Date]` column. In each date table, sort `[Month Label]` by `[Month Sort]`.

Add single-direction, one-to-many relationships:

| One side | Many side | Meaning |
|---|---|---|
| `DimSnapshotDate[Date]` | `Jobs[retrieved_on]` | When the collector observed an advert. |
| `DimPostedDate[Date]` | `Jobs[posted_date]` | When the advert says it was created. |
| `DimRole[role_family]` | `Jobs[role_family]` | The classified role family. |
| `DimRoleTaxonomyVersion[role_taxonomy_version]` | `Jobs[role_taxonomy_version]` | Keeps role trends interpretable when title-classification rules change. |
| `DimRegion[region]` | `Jobs[region]` | The mapped UK region. |
| `Jobs[SnapshotKey]` | `JobSkills[SnapshotKey]` | Skill tags attached to that advert observation. |
| `Jobs[SnapshotKey]` | `JobSearches[SnapshotKey]` | Search families that returned the advert; a search audit, not a role label. |
| `DimSearchFamily[search_family]` | `JobSearches[search_family]` | Supports search coverage and overlap review. |
| `DimSkill[skill]` | `JobSkills[skill]` | Skill slicers and charts. |
| `DimTaxonomyVersion[skill_taxonomy_version]` | `JobSkills[skill_taxonomy_version]` | Keeps comparisons within the same keyword dictionary version. |

Do not enable bidirectional filtering. Keep `DimSnapshotDate` and `DimPostedDate` separate so an analyst can distinguish changes in collection results from the age of adverts.

## Measures

Create the measures in [Measures.dax](Measures.dax). They count advert-snapshot observations, compare captures within one selected role-taxonomy version, calculate skill mention rates, and limit salary statistics to complete annual values the API has **not** marked as predicted. The existing one-snapshot extract is enough to check the import, but not to show meaningful change over time.

## Report pages

1. **Market pulse:** adverts in each capture, changes since the prior capture, role mix, and North West versus other regions.
2. **Skill signals:** skill mention rates by role family, region and capture date. Label the figures as keyword matches in source snippets.
3. **Pay evidence:** select one capture date and show employer-reported annual ranges only. If showing the number of predicted salary records, add the 24×24 icon and linked **Adzuna Jobsworth** attribution next to it. Do not mix estimates into employer-pay medians.
4. **Coverage & quality:** date coverage, classified/unclassified region share, source-estimated salary share, snippet skill-tag coverage, title roles marked `Other / review`, taxonomy versions, search families and overlap. Label the current capture's search provenance as legacy. Use the search-family measures on this page only; one advert may match several searches, and search-family filters intentionally do not filter the Jobs fact table.

Use `DimSnapshotDate[Date]` at day granularity and `Adverts Captured` for the time series. The `New Within Sample` and `No Longer Returned` measures compare with the previous capture that has the same selected role-taxonomy version; they return blank when multiple versions are selected. They indicate changes in what these searches returned, not confirmed job openings or closures. Use `[Month Label]` sorted by `[Month Sort]` only for broader month-level summaries. In titles and footnotes, call them **adverts returned by these searches**; they are not a count of every UK vacancy.

## Make the analysis stronger

- Capture one snapshot per week for at least 6–8 weeks with the same queries, page count and lookback window. The collector saves at most one snapshot per day and replaces that day's file if rerun.
- Start with `--pages 2`, which makes six API calls across the three searches. The current sample is one page per search and is capped, so its counts show coverage of those query results only.
- Keep unknown regions visible. Improve the mapping only when you can document the source hierarchy and add a data-quality check for the mapping rate.
- Expand skill aliases with evidence from the returned vocabulary; keep the original matched term and avoid claiming a skill is absent when the API snippet omits it. The `skill_taxonomy_version` field must change whenever the vocabulary changes; compare trends within a single version.
- Add ONS ASHE occupational earnings as a separately-labelled benchmark. Its employee pay population and annual survey period differ from online adverts, so don't merge it with Adzuna estimates or label them as the same measure.
- The Python validator already checks duplicate `(posting_id, retrieved_on)` keys, invalid dates, missing required fields, role and pay categories, and reversed salary bounds. Add review warnings for unusual week-to-week changes in sample size, geography or skill coverage.

The design follows Microsoft's guidance to separate fact observations from descriptive dimensions and to use dedicated date tables for Power BI time analysis: [star schema guidance](https://learn.microsoft.com/power-bi/guidance/star-schema), [date table guidance](https://learn.microsoft.com/power-bi/guidance/model-date-tables).
