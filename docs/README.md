# Project Documentation

Business, data, architecture and operations documentation of the **MLB Performance Intelligence Platform**,
in the order the project was built: from the business problem to the automated platform.

| # | Document | What it answers | Status |
|---|---|---|---|
| 01 | [Business Requirements Document](01_Business_Requirements_Document.md) | Problem, users, business questions, scope, requirements, success criteria | Complete |
| 02 | [KPI Catalog](02_KPI_Catalog.md) | Every KPI with its formula, Gold table and column | Complete |
| 03 | [Data Source Assessment](03_Data_Source_Assessment.md) | MLB Stats API endpoints, profiling findings and the decisions they drove | Complete |
| 04 | [Data Model & Architecture](04_Data_Model.md) | Medallion layers, star schema, incremental strategy, orchestration | Complete |
| 05 | [Data Dictionary](05_Data_Dictionary.md) | Every table and view, column by column, with grain and the notebook that builds it | Complete |
| 06 | [Pipeline & Notebooks Guide](06_Pipeline_and_Notebooks.md) | The 13-task job and what each notebook reads, does and writes | Complete |
| 07 | [Architecture Decisions](07_Architecture_Decisions.md) | Why the pipeline is built this way (12 ADRs) | Complete |
| 08 | [Data Quality & Validation](08_Data_Quality_and_Validation.md) | 14 automatic checks and the reconciliation with official MLB figures | Complete |
| 09 | [Win-Probability Model](09_Win_Probability_Model.md) | Features, results on an unseen season, calibration, limits | Complete |
| 10 | [Operations Runbook](10_Operations_Runbook.md) | Daily automation, safeguards, what to do when something fails | Complete |
| 11 | [Project Journey & Changelog](11_Project_Journey.md) | From v1 to v2.3 and the lessons learned | Complete |

Related: [Power BI assets](../powerbi/README.md) · [Web platform](../web/README.md) ·
[Live platform](https://stanly06.github.io/mlb-intelligence/)

## Suggested reading paths

| If you are… | Read |
|---|---|
| A recruiter or manager (5 minutes) | Repository README → 01 → 11 |
| A data analyst | 02 → 05 → 08 |
| A data engineer | 04 → 06 → 07 → 10 |
| A data scientist | 09 → 06 (features notebook) |
