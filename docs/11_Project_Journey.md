# Project Journey & Changelog

## MLB Performance Intelligence Platform

How the project grew from a daily ETL exercise into an analytics platform, and the reasoning at each step.

---

## v1 — MLB Daily Games ETL (initial version)

A Databricks job that pulled the previous day's games from the MLB Stats API, stored the raw JSON in Bronze,
parsed a Silver games table and built daily Gold KPIs with Delta `MERGE`. Notebooks are kept in
[`legacy/v1/`](../legacy/v1/).

**Limits found in v1:** one endpoint (schedule) only, no player or team statistics, logging code copied in three
notebooks, no data-quality checks, no documentation of requirements, no consumer for the data.

## v2 — Requirements first (October 2026)

1. **Business requirements** — who would use MLB data and which questions they ask
   ([01](01_Business_Requirements_Document.md)), turned into a KPI catalog with a formula and a target column for
   every number ([02](02_KPI_Catalog.md)).
2. **Data source assessment** — every endpoint profiled before modelling: payload shape, keys, game types,
   postponed and resumed games, players appearing for both teams, country codes ([03](03_Data_Source_Assessment.md)).
3. **Model and architecture** — medallion layers, star schema, incremental strategy
   ([04](04_Data_Model.md), [07](07_Architecture_Decisions.md)).
4. **Build** — 16 notebooks and a shared library; local end-to-end harness to test without the workspace.
5. **Load and reconcile** — 2024–2026 backfill; 14 quality checks; team W-L and runs reconciled 90 / 90 with the
   official standings ([08](08_Data_Quality_and_Validation.md)).
6. **Consume** — bilingual web platform (league, team, player, head-to-head, leaders, countries) and Power BI
   assets.

## v2.1 — Predictions and calendar

Pre-game features with point-in-time joins, win-probability model (56.0 % vs 52.9 % baseline on an unseen
season, [09](09_Win_Probability_Model.md)), probable starters, full season calendar with the model's pick.

## v2.2 — Automation

Databricks job deployed from the repository; GitHub Actions syncs the job every morning and publishes the page
after each run ([10](10_Operations_Runbook.md)). Fixes found in production: ANSI-mode casts on serverless,
Git-folder detection in the deploy script.

## v2.3 — League executive view

Audit first: which metrics the current Gold data could support and which needed new data. Result: league rates
were derivable, but team rankings could not be built from player-season tables (traded players). New export
tables from the game grain, validated against MLB's official team stats (batting 90 / 90 equal), then the League
page: KPIs vs previous season, monthly trends, team offense and pitching rankings.

---

## Lessons

- Profile the source before modelling: most bugs avoided in v2 came from edge cases found in the assessment.
- Reconcile with an external truth (official standings and team stats), not only with internal checks.
- Make every step re-runnable: watermarks, idempotent `MERGE`, files landed once.
- Test in the same SQL mode as production (ANSI).
