# Data Quality & Validation

## MLB Performance Intelligence Platform

Two levels of control: automatic checks inside every job run, and one-off validations against official MLB
figures that prove the KPIs are correct.

---

## 1. Automatic checks — `src/quality/01_Data_Quality_Checks`

Results are stored per run in `quality.dq_results`. A failed **CRITICAL** check fails the job, so the web export
(which depends on it) does not run and the platform keeps the last good data.

| ID | Check | Layer | Severity |
|---|---|---|---|
| DQ-001 | Completed game without boxscore | Silver | CRITICAL |
| DQ-002 | Duplicate `game_pk` in `fact_game` | Silver | CRITICAL |
| DQ-003 | Completed game without two team rows | Silver | CRITICAL |
| DQ-004 | Completed game missing score or winner | Silver | CRITICAL |
| DQ-005 | Duplicate `(game_pk, player_id, team_id)` in batting | Silver | CRITICAL |
| DQ-006 | Duplicate `(game_pk, player_id, team_id)` in pitching | Silver | CRITICAL |
| DQ-007 | Invalid batting line (H > AB, HR > H or AB > PA) | Silver | CRITICAL |
| DQ-008 | Invalid pitching line (ER > R or negative outs) | Silver | CRITICAL |
| DQ-009 | Team runs (line score) differ from the sum of player runs (boxscore) | Silver | CRITICAL |
| DQ-010 | Opponent runs differ from runs allowed by pitchers | Silver | CRITICAL |
| DQ-011 | Player in facts without a profile in `dim_player` | Silver | WARNING |
| DQ-012 | Team or venue without a dimension row | Silver | WARNING |
| DQ-013 | W-L or runs differ from official MLB standings | Gold | CRITICAL |
| DQ-014 | Team-season not fully loaded (fewer games than official standings) | Gold | WARNING |

Latest run (October 2026): **14 / 14 PASS** — 7,414 completed games, 156,064 batting lines, 63,653 pitching
appearances; DQ-013 reconciles all **90 / 90** team-seasons with the official standings.

The publishing workflow adds a last gate before the page changes: the export must have ≥ 2,000 games, be at most
2 days old and contain no failed CRITICAL check.

---

## 2. Validation against official MLB figures

| What was compared | Source of truth | Result |
|---|---|---|
| Team W-L, runs scored and allowed, 2024–2026 | `/standings` (DQ-013, every run) | 90 / 90 equal |
| League AVG / OBP / SLG / OPS / ERA, 2024 | MLB published league totals | .243 / .312 / .399 / .711 / 4.08 — equal |
| Team batting (H, AB, HR, BB, SO, R, TB, SF, HBP), 2024–2026 | `/teams/stats?group=hitting` | 90 / 90 equal |
| Team pitching (outs, H, BB, SO, HR, HBP), 2024–2026 | `/teams/stats?group=pitching` | 90 / 90 equal |
| Team earned runs | `/teams/stats?group=pitching` | 46 team-seasons 1–4 ER higher (see note); max ERA difference 0.02 |

**Note on earned runs:** MLB computes team ERA with *team* earned runs. When an error happens before a reliever
enters, runs can be earned for the pitcher but unearned for the team, so the sum of pitchers' earned runs can be
slightly higher. The platform uses the sum of pitchers' earned runs (the only value in the boxscore lines) and
says so on the page.

**Note on player-season runs:** the web export keeps batting lines with at least one plate appearance; a pinch
runner who scored without batting is therefore not in that table (1 run in 2026). Team and league runs come from
the team-game facts and are complete.

---

## 3. Testing before deploying

| Test | How |
|---|---|
| Unit tests (API client, date windows, envelope) | `python -m pytest tests/` |
| Full pipeline on a laptop | `python tests/local_run.py --backfill 2024,2025,2026` runs every notebook unchanged on local Spark + Delta, in ANSI mode like Databricks serverless |
| Web platform | Built with `web/build.py` and checked in a headless browser: the 9 pages, Spanish and English, desktop / tablet / mobile, no console errors |
