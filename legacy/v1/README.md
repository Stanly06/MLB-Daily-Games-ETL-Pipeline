# v1 — MLB Daily Games ETL (archived)

The original pipeline: yesterday's `/schedule` → `bronze_mlb_schedule_raw` → `silver_mlb_games` →
`gold_mlb_daily_summary` in the `mlb_project` Hive database, plus `pipeline_logs`.
Video walkthrough: https://youtu.be/oDlRG3iUFq8

Superseded by v2 (repository root), which keeps the same Medallion idea and adds players, teams,
history, incremental processing, data-quality checks and BI. These notebooks are kept for reference.
