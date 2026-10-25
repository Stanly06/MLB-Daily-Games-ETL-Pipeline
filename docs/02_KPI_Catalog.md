# Business Questions & KPI Catalog

## MLB Performance Intelligence Platform

Every KPI below is implemented in a Gold table or view (column names in `code`). Grain columns
`season` and `season_type` (`Regular Season` / `Postseason`) apply to every season-level KPI.

---

## 1. Team KPIs — `gold.team_season_summary`, `gold.team_game_log`

| ID | KPI | Definition / formula | Column(s) |
|---|---|---|---|
| TEAM-001 | Record | Wins, losses and win % = W / G (completed games only) | `wins`, `losses`, `win_pct` |
| TEAM-002 | Run differential | Runs scored − runs allowed | `run_differential` |
| TEAM-003 | Runs per game | RS / G and RA / G | `runs_scored_per_game`, `runs_allowed_per_game` |
| TEAM-004 | Pythagorean win % | RS^1.83 / (RS^1.83 + RA^1.83) | `pythagorean_win_pct` |
| TEAM-005 | Expected wins | Pythagorean win % × G | `expected_wins` |
| TEAM-006 | Luck | Wins − expected wins (positive = won more than the run differential suggests) | `luck_wins` |
| TEAM-007 | Home / away split | W-L at home and on the road | `home_wins` … `away_losses` |
| TEAM-008 | Close games | W-L in one-run games and extra-inning games | `one_run_wins` … `extra_inning_losses` |
| TEAM-009 | Blowouts | Games won / lost by 5+ runs | `blowout_wins`, `blowout_losses` |
| TEAM-010 | Form | Last-10 record and current streak (e.g. `W4`) | `last_10_wins`, `last_10_losses`, `current_streak` |
| TEAM-011 | Longest streaks | Longest winning and losing streak in the season | `longest_win_streak`, `longest_losing_streak` |
| TEAM-012 | Season trajectory | Running W-L, win %, run differential and rolling last-10 per game | `team_game_log.*_to_date`, `wins_last_10` |
| TEAM-013 | Average home attendance | Mean attendance of completed home games | `avg_home_attendance` |

## 2. Head-to-head KPIs — `gold.head_to_head`

| ID | KPI | Definition | Column(s) |
|---|---|---|---|
| H2H-001 | Head-to-head record | W-L and win % of a team against one opponent | `wins`, `losses`, `win_pct` |
| H2H-002 | Runs in the matchup | Runs scored, allowed and differential | `runs_scored`, `runs_allowed`, `run_differential` |
| H2H-003 | Meetings | Number of games, home games, first and last meeting | `games`, `home_games`, `first_meeting`, `last_meeting` |
| H2H-004 | Last result | Result and score of the latest meeting (e.g. `W 5-3`) | `last_result` |

All-time (since 2024) head-to-head = sum over seasons (done in Power BI by not filtering season).

## 3. Batting KPIs — `gold.player_season_batting`

| ID | KPI | Formula | Column |
|---|---|---|---|
| BAT-001 | Batting average | H / AB | `avg` |
| BAT-002 | On-base percentage | (H + BB + HBP) / (AB + BB + HBP + SF) | `obp` |
| BAT-003 | Slugging | TB / AB | `slg` |
| BAT-004 | OPS | OBP + SLG | `ops` |
| BAT-005 | Isolated power | SLG − AVG | `iso` |
| BAT-006 | BABIP | (H − HR) / (AB − SO − HR + SF) | `babip` |
| BAT-007 | Strikeout / walk rate | SO / PA, BB / PA (%) | `k_pct`, `bb_pct` |
| BAT-008 | Counting stats | G, PA, AB, R, H, 2B, 3B, HR, RBI, BB, SO, SB, CS | `games` … `cs` |
| BAT-009 | Qualification | PA ≥ 3.1 × team games (regular season) | `is_qualified` |
| BAT-010 | League rank | OPS and AVG rank among qualified; HR, RBI, SB rank among all | `ops_rank_qualified`, `avg_rank_qualified`, `hr_rank`, `rbi_rank`, `sb_rank` |

## 4. Pitching KPIs — `gold.player_season_pitching`

| ID | KPI | Formula | Column |
|---|---|---|---|
| PIT-001 | ERA | 9 × ER / IP | `era` |
| PIT-002 | WHIP | (BB + H) / IP | `whip` |
| PIT-003 | Strikeouts per 9 | 9 × SO / IP | `k_per_9` |
| PIT-004 | Walks / HR per 9 | 9 × BB / IP, 9 × HR / IP | `bb_per_9`, `hr_per_9` |
| PIT-005 | K-BB % | (SO − BB) / batters faced | `k_minus_bb_pct` |
| PIT-006 | FIP | (13·HR + 3·(BB + HBP) − 2·SO) / IP + cFIP; cFIP = league ERA − league raw FIP for the season | `fip` |
| PIT-007 | Quality starts | Starts with ≥ 6 IP (18 outs) and ≤ 3 ER | `quality_starts` |
| PIT-008 | Role | Starter if GS ≥ G / 2, otherwise reliever | `role` |
| PIT-009 | Qualification | IP ≥ 1.0 × team games (regular season) | `is_qualified` |
| PIT-010 | League rank | ERA rank among qualified; SO, W, SV rank among all | `era_rank_qualified`, `so_rank`, `w_rank`, `sv_rank` |

Innings are stored as **outs** (exact integers) and converted: IP = outs / 3; display `6.1` = 6⅓ innings.

## 5. Form KPIs — `gold.batting_game_log`, `gold.pitching_game_log`

| ID | KPI | Definition | Column |
|---|---|---|---|
| FORM-001 | Rolling hitting form | AVG and OPS over the player's last 15 games | `avg_last_15`, `ops_last_15`, `hr_last_15` |
| FORM-002 | Season-to-date line | Cumulative AVG / OPS / HR after each game | `avg_season_to_date`, `ops_season_to_date`, `hr_season_to_date` |
| FORM-003 | Rolling pitching form | ERA and WHIP over the last 5 appearances vs season-to-date ERA | `era_last_5`, `whip_last_5`, `era_season_to_date` |

Hot / cold signal in Power BI: `ops_last_15 − ops_season_to_date`.

## 6. Players by country (Dominicans in focus) — `gold.country_season_summary`, `gold.latest_game_day_lines`, `gold.dominican_*` views

| ID | KPI | Definition | Object |
|---|---|---|---|
| DR-001 | Dominican players | Distinct players with `birth_country = 'Dominican Republic'` who batted or pitched | `country_season_summary.players` |
| DR-002 | Share of league | Dominican players / all players (%) | `pct_of_players` |
| DR-003 | Share of production | Share of league home runs and pitcher strikeouts (%) | `pct_of_home_runs`, `pct_of_strikeouts` |
| DR-004 | Country ranking | Rank of each country by number of players | `country_rank_by_players` |
| DR-005 | Top Dominicans | Dominican hitters / pitchers ranked by OPS, HR, SO, SV with their league rank | `dominican_batting_season`, `dominican_pitching_season` |
| DR-006 | Latest game day | Line of every Dominican player on the most recent game day | `dominican_latest_games` |
| DR-007 | Any country | DR-001…006 for any birth country (country explorer in the web platform) | `country_season_summary`, `latest_game_day_lines` |

## 7. Win-probability model — `gold.game_features`, `gold.game_predictions`, `gold.win_model_*`

| ID | Output | Definition | Object |
|---|---|---|---|
| ML-001 | Home win probability | P(home team wins) from the selected model; upcoming games scored with probable starters | `game_predictions.home_win_prob` |
| ML-002 | Predicted winner | Team with probability ≥ 50 % | `game_predictions.predicted_winner_id` |
| ML-003 | Out-of-sample accuracy | Share of test-season games where the predicted winner won, vs baselines | `win_model_metrics` |
| ML-004 | Log loss / Brier | Quality of the probabilities (lower is better) | `win_model_metrics` |
| ML-005 | Calibration | Favourite's predicted vs actual win rate by probability bucket | `win_model_calibration` |
| ML-006 | Drivers | Standardized coefficients and per-game top-3 factors | `win_model_features`, `game_predictions.top_factors` |
| ML-007 | Market comparison (web) | No-vig implied probability from American odds the user types, edge = model − market, expected value per $100 | web platform only |

Features (home minus away): win %, run differential per game, last-10, home/road split, starter FIP and
K−BB%, bullpen ERA and 3-day workload, rest days; plus park factor (previous seasons) and postseason flag.

## 7b. Schedule

| ID | Output | Definition | Object |
|---|---|---|---|
| CAL-001 | Season calendar | Every game by date, with result or probable starters and the model's pick | `fact_game` (completed and upcoming) |
| CAL-002 | Opponents | Games, home and away games and first date against each opponent for a team and season | web platform (from `fact_game`) |

## 7. League and operations KPIs — `gold.league_daily_summary`, `metadata`, `quality`

| ID | KPI | Definition | Object |
|---|---|---|---|
| LG-001 | Games per day | Scheduled, completed and currently postponed games, and make-up games played (originally postponed) | `scheduled_games`, `completed_games`, `postponed_games`, `makeup_games` |
| LG-002 | Scoring environment | Total runs, average runs per completed game, home runs | `total_runs`, `avg_runs_per_game`, `home_runs` |
| LG-003 | Close-game frequency | Extra-inning and one-run games | `extra_inning_games`, `one_run_games` |
| LG-004 | Fan engagement / pace | Average attendance and game duration (minutes) | `avg_attendance`, `avg_duration_minutes` |
| OPS-001 | Pipeline health | Status, records and duration per task and run | `metadata.pipeline_runs` |
| OPS-002 | Data quality | Result of each check per run, incl. reconciliation with official standings | `quality.dq_results` |

## 8. Dashboard mapping (Power BI)

| Page | Main KPIs | Gold source |
|---|---|---|
| League overview | TEAM-001, 002, 006, LG-001…004 | `team_season_summary`, `league_daily_summary` |
| Team | TEAM-001…013 | `team_season_summary`, `team_game_log` |
| Player | BAT-*, PIT-*, FORM-* | `player_season_batting`, `player_season_pitching`, game logs |
| Head-to-head | H2H-001…004 | `head_to_head`, `fact_game` |
| Countries (Dominicans in MLB by default) | DR-001…007 | `country_season_summary`, `latest_game_day_lines`, `dominican_*` |
| Predictions | ML-001…007 | `game_predictions`, `win_model_*` |
| Schedule | CAL-001, CAL-002 | `fact_game` |
| Data health | OPS-001, OPS-002 | `metadata.pipeline_runs`, `quality.dq_results` |
