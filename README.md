# UK Data Careers Observatory

An analyst's view of advertised demand for UK data roles: where adverts appear, what employers ask for, and how transparent advertised pay is.

**Status:** first working showcase. The included preview is synthetic. Live Adzuna collection is opt-in and needs your own API credentials.

## The question

How does the mix of UK analyst adverts and their skill mentions change across repeated captures, especially in the North West, and how much employer-reported pay is actually available?

The project is designed as a repeatable analysis rather than a snapshot presented as the whole UK market. Adverts are a changing, incomplete sample: collection windows, source coverage, duplicate ads and missing pay all affect the results.

## Open the showcase

```powershell
cd "Shabib/02 Portfolio/uk-data-careers-observatory"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

The dashboard opens on the bundled 60-row fictional preview so it can be explored without an API account. A banner marks it as synthetic. It is there to demonstrate the dashboard, not to support claims about real employers or the current market.

## Collect real adverts

1. Register for an Adzuna API account and review its current [API documentation](https://developer.adzuna.com/overview) and [terms](https://developer.adzuna.com/docs/terms_of_service).
2. Copy `.env.example` to `.env` and add your own `ADZUNA_APP_ID` and `ADZUNA_APP_KEY`. Keep `.env` private; it is ignored by Git.
3. Run `python -m src.collect_adzuna --pages 2 --days 30`. This saves the latest extract to `data/processed/jobs.csv` and a dated snapshot to `data/snapshots/`.
4. Run `python -m src.validate_extract` to check the snapshot schema, keys, dates, role values and pay ranges, then run `python -m src.build_warehouse` to rebuild the local SQLite database from dated snapshots.
5. Restart or refresh the Streamlit dashboard for the latest extract. Follow [the Power BI import guide](powerbi/PowerQuery.md) to import snapshot history and create the semantic model.

The collector and SQLite load use Python's standard library. The dashboard dependencies are listed separately in `requirements.txt`. The collector requests Data Analyst, BI Analyst and MI Analyst adverts in separate searches, deduplicates IDs, records which searches returned each advert, and classifies roles from advert titles alone. It records the retrieval date plus role- and skill-taxonomy versions, then extracts a small skills vocabulary from the returned text. It discards the advert description before writing output. The collector spaces calls to respect Adzuna's default rate limit. Check the API terms before publishing or redistributing derived data. Never commit credentials or raw advert text.

The annual-pay chart uses only complete ranges with an explicit annual period that the API has not marked as predicted. The first live sample marked every returned salary range as predicted, so the dashboard excludes those amounts and displays the required [Adzuna Jobsworth attribution](https://www.adzuna.co.uk/jobs/salary-predictor.html) beside their count. This is a source limitation, not evidence that none of the employers stated pay in their original adverts.

## What the dashboard shows

- Adverts in the selected sample, employer-reported annual salary coverage and locations.
- Advert posting dates in Streamlit; the Power BI model adds changes between collection snapshots as they accumulate.
- Mention rates for a small, visible vocabulary of analyst skills.
- Filters for role family, region and advert date.
- A sample-quality view with the synthetic/live source label and available-field coverage.

## Project structure

```text
app.py                    Streamlit dashboard
src/collect_adzuna.py     Adzuna API collection and text-to-tags processing
src/build_warehouse.py    Local SQLite load
src/validate_extract.py   Extract schema and value checks
src/data_model.py         Shared field, role, region, salary and skill rules
sql/schema.sql            Warehouse table definition
data/sample_jobs.csv      Fictional records for the self-contained preview
data/processed/           Local live extracts (ignored by Git)
data/snapshots/           Dated extracts for trend analysis (ignored by Git)
docs/data-dictionary.md  Field definitions and analytical cautions
powerbi/                  Power Query, DAX and semantic-model guide
```

## Current limitations and next steps

- The preview is synthetic; no market finding should be quoted from it.
- Live source access depends on an Adzuna account, API limits and current terms.
- Skill matching is a transparent keyword dictionary, not semantic classification. Variants and context can be missed.
- Search coverage is limited to the configured role phrases and pages; it is not a census of vacancies.
- The first live extract is one capture; it cannot show a change over time yet. Capture a consistent sample weekly for 6–8 weeks before interpreting snapshot trends.
- Search coverage is capped. With two pages per role, each run collects at most 100 results per query before cross-search deduplication.
- The first live pull marked all returned salary values as predicted. Those amounts are shown separately with Adzuna Jobsworth attribution and excluded from employer-pay comparisons.
- ONS earnings data is a possible later benchmark. It measures employee earnings, a different population from online job adverts, so it should be shown separately with its own source date and definitions.

## Source notes

- Adzuna API: [overview and endpoints](https://developer.adzuna.com/overview), [terms of service](https://developer.adzuna.com/docs/terms_of_service). Credentials are required. For personal research, its terms require salary and vacancy figures to acknowledge **The Adzuna API** and link to [Adzuna](https://www.adzuna.co.uk/); the live dashboard carries that attribution. Collection code stores only selected fields and derived skill tags.
- ONS Annual Survey of Hours and Earnings: [2025 release](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/bulletins/annualsurveyofhoursandearnings/2025). Potential contextual source for a later release.

See [the first live extraction note](docs/initial-extract.md) for dated sample coverage and interpretation limits.

See the [portfolio case study](docs/portfolio-story.md) for a concise project narrative, first-pull evidence and skills demonstrated.

