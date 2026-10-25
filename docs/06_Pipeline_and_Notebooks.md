# Pipeline & Notebooks Guide

## MLB Performance Intelligence Platform

How the data moves from the MLB Stats API to the web platform: one Lakeflow Job, 13 tasks, one notebook per
task. Every notebook starts with a Markdown cell that explains its tables and business rules; this guide is the
map between them.

---

## 1. The daily job — `mlb_performance_intelligence_daily`

Defined in [`resources/jobs/mlb_performance_daily.job.json`](../resources/jobs/mlb_performance_daily.job.json) and
deployed by `src/setup/02_Deploy_Jobs` (first time) or `scripts/databricks_deploy.py` (GitHub Actions, every day).

```
extract_mlb_api ─► bronze_ingest ─┬─► silver_dimensions ───────────────┬─► gold_team_metrics ──┐
                                  └─► silver_games ─► silver_boxscores ┴─► gold_player_metrics ─┤
                                                                            gold_dominican_players ◄┘
                                                                                     │
                                                         gold_semantic_layer ◄───────┘
                                                          ├─► gold_game_features ─► ml_win_probability ─┐
                                                          └─► data_quality ─────────────────────────────┴─► web_platform_export
```

| # | Task | Notebook | Depends on | Writes |
|---|---|---|---|---|
| 1 | `extract_mlb_api` | `src/bronze/01_MLB_API_Extract` | — | JSON files in Volume `bronze.mlb_api_raw`, `metadata.extract_register` |
| 2 | `bronze_ingest` | `src/bronze/02_MLB_API_Bronze` | 1 | `bronze.mlb_api_responses` |
| 3 | `silver_dimensions` | `src/silver/01_Silver_Dimensions` | 2 | `silver.dim_team`, `dim_venue`, `dim_player`, `official_standings` |
| 4 | `silver_games` | `src/silver/02_Silver_Games` | 2 | `silver.fact_game`, `fact_team_game` |
| 5 | `silver_boxscores` | `src/silver/03_Silver_Boxscores` | 4 | `silver.fact_batting_game`, `fact_pitching_game`, `game_details` |
| 6 | `gold_team_metrics` | `src/gold/01_Gold_Team_Metrics` | 3, 4, 5 | `gold.team_game_log`, `team_season_summary`, `head_to_head` |
| 7 | `gold_player_metrics` | `src/gold/02_Gold_Player_Metrics` | 3, 5 | `gold.player_season_batting`, `player_season_pitching`, `batting_game_log`, `pitching_game_log` |
| 8 | `gold_dominican_players` | `src/gold/03_Gold_Dominican_Players` | 7 | `gold.country_season_summary` + views by country |
| 9 | `gold_semantic_layer` | `src/gold/04_Gold_Semantic_Layer` | 6, 8 | `gold.dim_*`, `fact_*` views, `league_daily_summary` |
| 10 | `gold_game_features` | `src/gold/05_Gold_Game_Features` | 9 | `gold.game_features` |
| 11 | `ml_win_probability` | `src/ml/01_Win_Probability_Model` | 10 | `gold.game_predictions`, `win_model_metrics`, `win_model_calibration`, `win_model_features` |
| 12 | `data_quality` | `src/quality/01_Data_Quality_Checks` | 9 | `quality.dq_results` (fails the job on a CRITICAL check) |
| 13 | `web_platform_export` | `src/exports/01_Web_Platform_Export` | 11, 12 | `/Volumes/mlb_intelligence/gold/exports/mlb_web_data.json` |

Job parameters (defaults): `mode=daily`, `lookback_days=3`, `seasons=2024,2025,2026`, `future_days=400`,
`full_refresh=false`. A historical load is the same job with `mode=backfill`.

---

## 2. Notebook by notebook

Shared code lives in `src/shared/` and is imported by every notebook:

| Module | What it holds |
|---|---|
| `config.py` | Catalog name, Volume paths, game types (R, F, D, L, W), country aliases, sabermetric constants, table names |
| `mlb_api.py` | `MlbApiClient` (retries, parallel requests), request builders, date windows, JSON envelope + SHA-256 |
| `pipeline.py` | `log_step` (run log), `merge_upsert` (idempotent MERGE with additive schema evolution), `replace_table`, watermarks, `latest_payloads`, `num` (ANSI-safe cast), `record_dq` |
| `schemas.py` | `from_json` schemas for schedule, boxscore, people, teams, venues and standings |

### Setup

| Notebook | Purpose | Key points |
|---|---|---|
| `setup/00_Create_Catalog_Schemas` | Catalog `mlb_intelligence`, schemas `bronze` `silver` `gold` `metadata` `quality`, Volumes | Idempotent (`IF NOT EXISTS`); run once |
| `setup/01_Create_Metadata_Tables` | `metadata.pipeline_runs`, `extract_register`, `watermarks`, `quality.dq_results` | Bronze/Silver/Gold tables are created by their own notebooks on first write |
| `setup/02_Deploy_Jobs` | Creates the setup and daily jobs from the repository and optionally starts the backfill | Uses the notebook's own session: no tokens |

### Bronze — raw data, exactly as received

| Notebook | Purpose | Key points |
|---|---|---|
| `bronze/01_MLB_API_Extract` | Calls `/schedule`, `/game/{pk}/boxscore`, `/people`, `/teams`, `/venues`, `/standings` | Widgets `mode` (daily / backfill / range), `lookback_days`, `future_days`. Each response is wrapped in an envelope (URL, params, HTTP status, timestamp, SHA-256) and written as a file; an identical payload is not written twice. Boxscores are requested only for completed games not yet landed |
| `bronze/02_MLB_API_Bronze` | Ingests the new files into `bronze.mlb_api_responses` | **Auto Loader** (`cloudFiles`, `availableNow`) with a checkpoint, so each file is read exactly once; payload kept as a string, so an API change never blocks ingestion |

### Silver — clean, typed, conformed

| Notebook | Purpose | Key points |
|---|---|---|
| `silver/01_Silver_Dimensions` | Teams, venues, players (birth country normalized, e.g. `VEN` → Venezuela), official standings | `MERGE` upserts on the natural key |
| `silver/02_Silver_Games` | One row per game and two rows per game (team view) | Incremental with a watermark; **guarded MERGE**: a completed game is never overwritten by a later "postponed" entry of the same `game_pk`; probable starters and `start_time_tbd` for upcoming games |
| `silver/03_Silver_Boxscores` | Player batting and pitching lines per game, attendance, duration | Boxscore players come as a map keyed `ID<playerId>`: parsed with a typed schema and `explode`d (no UDFs). Key `(game_pk, player_id, team_id)` because a player can appear for both teams in a resumed game |

### Gold — business KPIs and serving layer

| Notebook | Purpose | Key points |
|---|---|---|
| `gold/01_Gold_Team_Metrics` | Record, run differential, Pythagorean expected wins and "luck", splits, streaks, head-to-head | Fully recomputed from Silver on every run (small tables, always consistent) |
| `gold/02_Gold_Player_Metrics` | Season batting and pitching lines, rolling form, league ranks | Innings stored as outs; FIP with a league constant per season; qualification rules |
| `gold/03_Gold_Dominican_Players` | Production by birth country, Dominicans in focus | Share of league players, HR and strikeouts; latest game-day lines |
| `gold/04_Gold_Semantic_Layer` | Star schema for Power BI and SQL, daily league summary | Views over Silver so BI never reads Silver directly |
| `gold/05_Gold_Game_Features` | Pre-game features for every game | Point-in-time ("as-of") joins: only information known before first pitch |

### ML, quality and export

| Notebook | Purpose | Key points |
|---|---|---|
| `ml/01_Win_Probability_Model` | Trains, evaluates and scores the win-probability model | Time-based split; see [09 Win-Probability Model](09_Win_Probability_Model.md) |
| `quality/01_Data_Quality_Checks` | 14 checks incl. reconciliation with official standings | See [08 Data Quality & Validation](08_Data_Quality_and_Validation.md) |
| `exports/01_Web_Platform_Export` | Writes the JSON that feeds the web platform | Columnar layout; League tables built from the game grain |

---

## 3. Where to find each piece in the Databricks workspace

| What | Path in the workspace |
|---|---|
| Notebooks (Git folder) | **Workspace → Users → *your user* → MLB-Daily-Games-ETL-Pipeline → src** |
| Tables | **Catalog → mlb_intelligence → bronze / silver / gold / metadata / quality** |
| Raw files | **Catalog → mlb_intelligence → bronze → Volumes → mlb_api_raw** |
| Web export | **Catalog → mlb_intelligence → gold → Volumes → exports** |
| Job, graph and run history | **Jobs & Pipelines → mlb_performance_intelligence_daily** (tabs *Runs* and *Tasks*) |
| Run log as a table | `SELECT * FROM mlb_intelligence.metadata.pipeline_runs ORDER BY started_at DESC` |
