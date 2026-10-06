-- One row per unique advert observation on each retrieval date.
-- Only selected fields and derived tags are retained. Do not add raw descriptions.
CREATE TABLE IF NOT EXISTS jobs (
    posting_id TEXT NOT NULL,
    title TEXT NOT NULL,
    employer TEXT NOT NULL,
    location TEXT NOT NULL,
    region TEXT NOT NULL,
    role_family TEXT NOT NULL,
    role_taxonomy_version TEXT NOT NULL,
    matched_search_families TEXT NOT NULL,
    posted_date TEXT,
    retrieved_on TEXT NOT NULL,
    salary_min REAL,
    salary_max REAL,
    salary_period TEXT NOT NULL,
    salary_is_predicted INTEGER NOT NULL,
    contract_type TEXT NOT NULL,
    skills TEXT NOT NULL,
    skill_taxonomy_version TEXT NOT NULL,
    source TEXT NOT NULL,
    is_synthetic INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (posting_id, retrieved_on)
);

CREATE INDEX IF NOT EXISTS idx_jobs_posted_date ON jobs(posted_date);
CREATE INDEX IF NOT EXISTS idx_jobs_region_role ON jobs(region, role_family);
