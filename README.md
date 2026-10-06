# UK Job Market Analytics Dashboard

## 📌 Project Overview

This project analyzes the technical hiring landscape in the United Kingdom, focusing on data-centric roles (BI, Data, and MI Analysts). The objective is to identify geographic hiring hotspots, salary parity across technical disciplines, and the specific skill combinations demanded by modern employers.

## 🏗️ Data Architecture & Pipeline

Data is ingested automatically using a custom ETL pipeline, transforming raw web data into a highly structured dimensional model for business intelligence reporting.

* **Extraction:** Python script querying the Adzuna API for live job postings.
* **Storage:** Data is written to a SQL database for persistent staging.
* **Visualization:** Power BI connects directly to the SQL backend, processing the data through a Star Schema.
* **Automation:** Weekly data refreshes scheduled via Windows Task Scheduler executing the Python ingestion script.

## 🗄️ Data Schema

The semantic model utilizes a standard Star Schema optimized for DAX aggregations:

* **Fact Table:** `JOBS` (Contains `employer`, `role`, `posted_date`, `contract_type`, `location`, `salary` metrics, and `posting_id`).
* **Dimension Tables:** `DimRole`, `DimRegion`, `DimSkill`, `DimSnapshotDate`.
* **Bridge Table:** `JobSkills` (Resolves the many-to-many relationship between individual job postings and multiple required skills).

## 📊 Key Findings

1. **Geographic Concentration:** London drives the vast majority of hiring volume within the captured dataset.
2. **Salary Parity:** Advertised compensation remains virtually flat across data disciplines, averaging £52K for BI, Data, and MI Analysts.
3. **Contract Preferences:** Employers predominantly utilize 'contract' arrangements or leave terms 'Not stated', with 'permanent' roles representing a distinct minority.

## ⚠️ Methodology & Data Limitations

To maintain analytical rigor, the following constraints apply to this dataset:

* **Algorithmic Estimates:** Salary figures (`salary_is_predicted = True`) are algorithmic estimates provided by the Adzuna API, not direct employer-confirmed payroll data.
* **Time Context:** The `salary_period` reflects the data capture and platform refresh cadence, not a guaranteed pay frequency.
* **Sample Scope:** The current dashboard reflects a targeted snapshot of 108 records captured over a specific date range. It serves as an exploratory structural model rather than an exhaustive market census. Multiple postings for the same role in distinct towns by the same employer indicate job-board syndication, not ingestion duplication.
