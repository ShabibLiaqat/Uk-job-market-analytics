# Power BI import queries

The Python collector remains the only component that uses the Adzuna credentials. Power BI reads the dated CSV snapshots, so the API key never enters the PBIX/PBIP file or a Power Query web request.

## 1. Add a folder parameter

In Power Query, choose **Manage Parameters → New Parameter**. Name it `SnapshotFolderPath`, set type to **Text**, and enter the full path to this project's `data\snapshots` folder. For example:

```text
C:\path\to\uk-data-careers-observatory\data\snapshots
```

The parameter remains local to the PBIX. When sharing the PBIX/PBIP, recipients must point it at their own snapshots folder.

## 2. Create the `Jobs` query

Choose **New Source → Blank Query → Advanced Editor**, paste this query, and name it `Jobs`:

```powerquery
let
    Source = Folder.Files(SnapshotFolderPath),
    CsvFiles = Table.SelectRows(
        Source,
        each [Extension] = ".csv" and Text.StartsWith([Name], "jobs_")
    ),
    ReadCsv = Table.AddColumn(
        CsvFiles,
        "Rows",
        each Table.PromoteHeaders(
            Csv.Document(
                [Content],
                [Delimiter = ",", Columns = 19, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
            ),
            [PromoteAllScalars = true]
        )
    ),
    Fields = {
        "posting_id", "title", "employer", "location", "region", "role_family", "role_taxonomy_version", "matched_search_families",
        "posted_date", "retrieved_on", "salary_min", "salary_max", "salary_period",
        "salary_is_predicted", "contract_type", "skills", "skill_taxonomy_version", "source", "is_synthetic"
    },
    ExpandRows = Table.ExpandTableColumn(ReadCsv, "Rows", Fields, Fields),
    KeepFields = Table.SelectColumns(ExpandRows, Fields),
    ConvertTypes = Table.TransformColumns(
        KeepFields,
        {
            {"posted_date", each try Date.FromText(Text.From(_), [Culture = "en-GB"]) otherwise null, type nullable date},
            {"retrieved_on", each Date.FromText(Text.From(_), [Culture = "en-GB"]), type date},
            {"salary_min", each try Number.FromText(Text.From(_), "en-GB") otherwise null, type nullable number},
            {"salary_max", each try Number.FromText(Text.From(_), "en-GB") otherwise null, type nullable number},
            {"salary_is_predicted", each List.Contains({"true", "1", "yes"}, Text.Lower(Text.From(_))), type logical},
            {"is_synthetic", each List.Contains({"true", "1", "yes"}, Text.Lower(Text.From(_))), type logical}
        }
    ),
    AddSnapshotKey = Table.AddColumn(
        ConvertTypes,
        "SnapshotKey",
        each [posting_id] & "|" & Date.ToText([retrieved_on], "yyyy-MM-dd"),
        type text
    ),
    OneObservationPerKey = Table.Distinct(AddSnapshotKey, {"SnapshotKey"})
in
    OneObservationPerKey
```

## 3. Create the `JobSkills` bridge query

Create another blank query, paste this code, and name it `JobSkills`:

```powerquery
let
    Source = Table.SelectColumns(Jobs, {"SnapshotKey", "posting_id", "retrieved_on", "skills", "skill_taxonomy_version"}),
    SplitSkills = Table.AddColumn(
        Source,
        "skill",
        each if [skills] = null or Text.Trim([skills]) = "" then {} else Text.Split([skills], "|"),
        type list
    ),
    ExpandSkills = Table.ExpandListColumn(SplitSkills, "skill"),
    TrimSkills = Table.TransformColumns(ExpandSkills, {{"skill", each Text.Trim(_), type text}}),
    KeepMatches = Table.SelectRows(TrimSkills, each [skill] <> null and [skill] <> ""),
    RemovePackedField = Table.RemoveColumns(KeepMatches, {"skills"}),
    UniqueSkillObservations = Table.Distinct(RemovePackedField, {"SnapshotKey", "skill"})
in
    UniqueSkillObservations
```

This makes one row per skill mention per advert snapshot. It avoids treating a pipe-separated string as one skill and preserves the advert snapshot grain.

## 4. Create dimensions

Create three more blank queries named `DimSkill`, `DimRole` and `DimRegion`:

```powerquery
// DimSkill
let Source = Table.Distinct(Table.SelectColumns(JobSkills, {"skill"})) in Source
```

```powerquery
// DimRole
let Source = Table.Distinct(Table.SelectColumns(Jobs, {"role_family"})) in Source
```

```powerquery
// DimRegion
let Source = Table.Distinct(Table.SelectColumns(Jobs, {"region"})) in Source
```

Create `DimTaxonomyVersion` from the bridge:

```powerquery
let Source = Table.Distinct(Table.SelectColumns(JobSkills, {"skill_taxonomy_version"})) in Source
```

Create a `JobSearches` bridge so the report can audit which search families returned each advert. Search-family provenance is not the same as the title-based role classification. The initial 29 September extract predates provenance capture and is labelled `Legacy extraction`:

```powerquery
let
    Source = Table.SelectColumns(Jobs, {"SnapshotKey", "posting_id", "retrieved_on", "matched_search_families"}),
    SplitFamilies = Table.AddColumn(
        Source,
        "search_family",
        each if [matched_search_families] = null or Text.Trim([matched_search_families]) = "" then {} else Text.Split([matched_search_families], "|"),
        type list
    ),
    ExpandFamilies = Table.ExpandListColumn(SplitFamilies, "search_family"),
    TrimFamilies = Table.TransformColumns(ExpandFamilies, {{"search_family", each Text.Trim(_), type text}}),
    KeepMatches = Table.SelectRows(TrimFamilies, each [search_family] <> null and [search_family] <> ""),
    RemovePackedField = Table.RemoveColumns(KeepMatches, {"matched_search_families"}),
    UniqueSearchObservations = Table.Distinct(RemovePackedField, {"SnapshotKey", "search_family"})
in
    UniqueSearchObservations
```

Create `DimSearchFamily` from `JobSearches[search_family]`, and `DimRoleTaxonomyVersion` from `Jobs[role_taxonomy_version]`:

```powerquery
let Source = Table.Distinct(Table.SelectColumns(JobSearches, {"search_family"})) in Source
```

```powerquery
let Source = Table.Distinct(Table.SelectColumns(Jobs, {"role_taxonomy_version"})) in Source
```

Create date tables in DAX using the formulas in [Model and report design](Model.md). Mark each as a date table.

## Refresh

Run `python -m src.collect_adzuna --pages 2 --days 30` to capture today's sample and append a dated snapshot file. Then refresh the PBIX. The collector replaces the snapshot if run again on the same date, so schedule at most one official capture per day.
