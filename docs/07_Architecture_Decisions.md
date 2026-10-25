# Architecture Decision Records

## MLB Performance Intelligence Platform

Each record states the decision, why it was taken and what it costs. They explain choices a reviewer would
otherwise have to infer from the code.

---

### ADR-001 — Unity Catalog layout: one catalog, one schema per layer

**Decision:** catalog `mlb_intelligence` with schemas `bronze`, `silver`, `gold`, `metadata`, `quality`; raw
files and exports in governed Volumes.
**Why:** isolates the project, makes the medallion layers visible in Catalog Explorer and lets permissions be
granted per layer. **Cost:** none on Free Edition.

### ADR-002 — Land every API response as a file before reading it

**Decision:** the extractor writes each response as a JSON envelope (URL, parameters, HTTP status, timestamp,
SHA-256 of the payload) to the Volume `bronze.mlb_api_raw`; Auto Loader ingests the files.
**Why:** the raw data is kept forever and can be reprocessed without calling the API again; the hash avoids
storing identical payloads twice; Auto Loader guarantees each file is read once.
**Cost:** one extra hop (file → table).

### ADR-003 — Keep the payload as text in Bronze; parse in Silver with typed schemas

**Decision:** `bronze.mlb_api_responses.payload` is a string; Silver parses it with `from_json` and the schemas in
`src/shared/schemas.py`.
**Why:** a new or changed API field never breaks ingestion; only the fields the platform uses are declared.

### ADR-004 — Incremental processing with watermarks and idempotent MERGE

**Decision:** Silver reads only Bronze rows ingested after its watermark (`metadata.watermarks`) and upserts with
`MERGE` on natural keys; new source columns are added automatically (additive schema evolution).
**Why:** the daily run processes a few games instead of three seasons, and re-running any day never duplicates
data. **Cost:** a `full_refresh` widget is kept for rebuilding from Bronze.

### ADR-005 — Guarded MERGE for games

**Decision:** an update to `silver.fact_game` is skipped when the stored game is completed and the incoming row is
not.
**Why:** the API can return a postponed entry for a `game_pk` that was later completed (make-up dates); without
the guard a final score could be overwritten.

### ADR-006 — Gold is recomputed, not merged

**Decision:** Gold tables are rebuilt from Silver on every run (`replace_table`).
**Why:** they are small (thousands of rows); recomputation keeps every KPI consistent with Silver and makes
formula changes take effect for all history at once.

### ADR-007 — Team statistics from the game grain

**Decision:** team batting and pitching totals are aggregated from `fact_batting_game` / `fact_pitching_game`,
never from the player-season tables.
**Why:** a player-season row assigns a traded player's whole season to his last team; summing it by team would
misattribute 67–76 players per season. At game grain each line carries the team he played for that day. Result:
team batting equals MLB's official team stats for all 90 team-seasons.

### ADR-008 — Rates from summed components

**Decision:** league and team AVG, OBP, SLG, OPS, ERA, WHIP, K/9… are computed from summed numerators and
denominators; innings are stored as outs.
**Why:** an average of rates weights a 10-PA player like a 600-PA player; outs avoid the `6.1 = 6⅓` decimal
trap.

### ADR-009 — ANSI-safe SQL

**Decision:** casts of API text go through `pipeline.num()` (NULL when not numeric), array access uses `get()` and
divisions use `NULLIF`.
**Why:** Databricks serverless runs SQL in ANSI mode, where one bad value fails the whole query. The local test
harness runs with ANSI enabled to catch this before deploying.

### ADR-010 — Point-in-time features for the model

**Decision:** every pre-game feature comes from games played before that game (as-of joins); the park factor uses
previous seasons only; evaluation is a time-based split.
**Why:** prevents leakage, so the reported accuracy is what the model would have achieved live.

### ADR-011 — Static web platform fed by an export

**Decision:** the job exports a compact JSON to a Volume; GitHub Actions downloads it, validates it and publishes a
single HTML page on GitHub Pages.
**Why:** the public site never connects to Databricks (no credentials in the browser), costs nothing to host and
stays online even if the workspace is stopped. **Cost:** data is as fresh as the last daily run.

### ADR-012 — Code in Git, deployment by CI

**Decision:** notebooks live in a Databricks Git folder; a GitHub Actions workflow pulls it to `main` and resets
the job definitions from the repository every day.
**Why:** the repository is the single source of truth; the job graph is versioned like code.
