# Portfolio case study

## UK Data Careers Observatory

### The problem

People comparing analyst roles often see job-board counts and salary figures without knowing how adverts were collected, how duplicate results were handled, or whether a salary was supplied by an employer or estimated by the platform. This project makes those limits visible while exploring advertised analyst skills and regional coverage.

### The question

Across consistent weekly Adzuna captures, how do analyst advert titles and skill mentions vary by role and region, especially in the North West, and how much usable employer-reported annual pay is available?

### What the first capture says

The first live pull returned 112 unique adverts across three search phrases and one page per phrase. Title-based rules classified 21 as Data Analyst, 19 as BI Analyst and 6 as MI Analyst. The remaining 66 are retained as 30 `Other analyst` and 36 `Other / review` rather than being forced into a target role. Region mapping succeeded for 83% of observations. All returned pay ranges were marked predicted by the API, so there was no employer-reported annual pay range suitable for a pay comparison.

These are a dated sample and a data-quality baseline, not a claim about the whole UK jobs market. The first capture also predates query-provenance tracking; it is explicitly labelled legacy in that field.

### How it works

Python collects bounded API pages, waits between requests, deduplicates an advert across searches, and records which search families returned it. The advert title determines role family independently. Description snippets are scanned in memory for a versioned skill vocabulary and then discarded. The resulting dated CSV snapshots are checked for schema and value issues, then loaded into SQLite or Power BI.

Power BI uses an advert-snapshot fact table, date/role/region dimensions, and bridge tables for skill mentions and search families. The report separates employer-reported salary from predicted salary, and snapshot changes are labelled as changes in what the configured searches returned.

### Skills demonstrated

- API ingestion, pagination, rate-limit handling and credential hygiene
- Python data shaping, deduplication and versioned rule-based classification
- Data-quality checks, geographic normalization and a rebuildable SQLite warehouse
- Power Query, DAX measures, dimensional modeling and report design
- Honest interpretation of sampling, missing data, platform estimates and taxonomy limits
- Communication of findings with source attribution and decision-focused caveats

### What would make the next release stronger

Capture one consistent sample per week for 6–8 weeks, beginning with two pages per search. Review a sample of titles to refine role rules and inspect unmapped locations before expanding the dictionaries. Add ONS ASHE earnings only as a separately labelled occupational benchmark, since its population and collection period differ from online adverts. Compare trends within a fixed role and skill taxonomy version.
