# Data Dictionary

## MLB Performance Intelligence Platform

Every table and view in the Unity Catalog catalog `mlb_intelligence`, generated from the Lakehouse itself
(column names and types as stored). Row counts are from the 2024–2026 load (October 2026); they grow every day.

Formulas of the KPI columns are in [02 KPI Catalog](02_KPI_Catalog.md); relationships in [04 Data Model](04_Data_Model.md).

| Schema | Objects | Role |
|---|---|---|
| `bronze` | 1 | Raw API responses exactly as received |
| `silver` | 9 | Cleaned, typed and conformed dimensions and facts |
| `gold` | 26 | Business KPIs, serving layer (star schema), ML features and predictions |
| `metadata` | 3 | Run log, extraction register, watermarks |
| `quality` | 1 | Data-quality results per run |

## `bronze`

### `bronze.mlb_api_responses` (table)

**Grain:** one row per landed API file · **Built by:** `src/bronze/02_MLB_API_Bronze` · **Rows:** 7,485

Bronze: every MLB Stats API response landed in the raw archive, one row per file, payload kept as raw JSON. Append-only; Silver uses the latest extraction per (endpoint, request_key).

<details><summary>13 columns</summary>

| Column | Type |
|---|---|
| `endpoint` | string |
| `request_key` | string |
| `request_url` | string |
| `status_code` | int |
| `extracted_at` | timestamp |
| `extract_run_id` | string |
| `payload_sha256` | string |
| `payload` | string |
| `_source_file` | string |
| `_source_file_size` | bigint |
| `_source_modified_at` | timestamp |
| `_ingested_at` | timestamp |
| `_batch_id` | string |

</details>

## `silver`

### `silver.dim_player` (table)

**Grain:** one row per player · **Built by:** `src/silver/01_Silver_Dimensions` · **Rows:** 2,101

Silver: player profiles (birth country, position, handedness, debut) for every player in a boxscore

<details><summary>20 columns</summary>

| Column | Type |
|---|---|
| `player_id` | int |
| `player_name` | string |
| `first_name` | string |
| `last_name` | string |
| `birth_date` | date |
| `birth_city` | string |
| `birth_state_province` | string |
| `birth_country` | string |
| `is_dominican` | boolean |
| `height_in` | int |
| `weight_lb` | int |
| `primary_position` | string |
| `primary_position_name` | string |
| `position_type` | string |
| `bats` | string |
| `throws` | string |
| `mlb_debut_date` | date |
| `is_active` | boolean |
| `current_team_id` | int |
| `updated_at` | timestamp |

</details>

### `silver.dim_team` (table)

**Grain:** one row per team · **Built by:** `src/silver/01_Silver_Dimensions` · **Rows:** 30

Silver: MLB teams (current attributes from the latest season extracted)

<details><summary>16 columns</summary>

| Column | Type |
|---|---|
| `team_id` | int |
| `team_name` | string |
| `team_abbreviation` | string |
| `club_name` | string |
| `location_name` | string |
| `short_name` | string |
| `league_id` | int |
| `league_name` | string |
| `league_abbreviation` | string |
| `division_id` | int |
| `division_name` | string |
| `home_venue_id` | int |
| `home_venue_name` | string |
| `first_year_of_play` | int |
| `latest_season` | int |
| `updated_at` | timestamp |

</details>

### `silver.dim_venue` (table)

**Grain:** one row per venue · **Built by:** `src/silver/01_Silver_Dimensions` · **Rows:** 41

Silver: ballparks where in-scope games were played

<details><summary>10 columns</summary>

| Column | Type |
|---|---|
| `venue_id` | int |
| `venue_name` | string |
| `city` | string |
| `state` | string |
| `country` | string |
| `latitude` | double |
| `longitude` | double |
| `elevation_ft` | int |
| `is_active` | boolean |
| `updated_at` | timestamp |

</details>

### `silver.fact_batting_game` (table)

**Grain:** player × team × game · **Built by:** `src/silver/03_Silver_Boxscores` · **Rows:** 156,064

Silver: one batting line per player per game (lineup slot, PA, AB, H, 2B, 3B, HR, RBI, BB, SO, SB...)

<details><summary>35 columns</summary>

| Column | Type |
|---|---|
| `game_pk` | bigint |
| `player_id` | int |
| `player_name` | string |
| `team_id` | int |
| `opponent_id` | int |
| `is_home` | boolean |
| `season` | int |
| `game_type` | string |
| `season_type` | string |
| `official_date` | date |
| `batting_order` | int |
| `lineup_slot` | int |
| `is_starter` | boolean |
| `position` | string |
| `pa` | int |
| `ab` | int |
| `r` | int |
| `h` | int |
| `doubles` | int |
| `triples` | int |
| `hr` | int |
| `rbi` | int |
| `bb` | int |
| `ibb` | int |
| `so` | int |
| `hbp` | int |
| `sb` | int |
| `cs` | int |
| `sf` | int |
| `sh` | int |
| `tb` | int |
| `lob` | int |
| `gidp` | int |
| `singles` | int |
| `updated_at` | timestamp |

</details>

### `silver.fact_game` (table)

**Grain:** one row per game (completed, upcoming, postponed) · **Built by:** `src/silver/02_Silver_Games` · **Rows:** 9,852

Silver: one row per MLB game in scope (regular season + postseason), final score, line score, decisions and status

<details><summary>51 columns</summary>

| Column | Type |
|---|---|
| `game_pk` | bigint |
| `season` | int |
| `game_type` | string |
| `game_type_name` | string |
| `season_type` | string |
| `official_date` | date |
| `game_datetime_utc` | timestamp |
| `status_code` | string |
| `status_detail` | string |
| `status_reason` | string |
| `start_time_tbd` | boolean |
| `is_completed` | boolean |
| `is_tie` | boolean |
| `home_team_id` | int |
| `away_team_id` | int |
| `home_score` | int |
| `away_score` | int |
| `home_hits` | int |
| `away_hits` | int |
| `home_errors` | int |
| `away_errors` | int |
| `home_left_on_base` | int |
| `away_left_on_base` | int |
| `innings_played` | int |
| `scheduled_innings` | int |
| `venue_id` | int |
| `venue_name` | string |
| `day_night` | string |
| `double_header` | string |
| `game_number` | int |
| `game_description` | string |
| `series_description` | string |
| `series_game_number` | int |
| `games_in_series` | int |
| `winning_pitcher_id` | int |
| `losing_pitcher_id` | int |
| `save_pitcher_id` | int |
| `home_probable_pitcher_id` | int |
| `home_probable_pitcher` | string |
| `away_probable_pitcher_id` | int |
| `away_probable_pitcher` | string |
| `rescheduled_from_utc` | timestamp |
| `was_rescheduled` | boolean |
| `source_extracted_at` | timestamp |
| `winning_team_id` | int |
| `losing_team_id` | int |
| `total_runs` | int |
| `run_margin` | int |
| `is_extra_innings` | boolean |
| `is_one_run_game` | boolean |
| `updated_at` | timestamp |

</details>

### `silver.fact_pitching_game` (table)

**Grain:** pitcher appearance (player × team × game) · **Built by:** `src/silver/03_Silver_Boxscores` · **Rows:** 63,653

Silver: one pitching line per pitcher appearance (outs, IP, H, ER, BB, SO, HR, pitches, decision, quality start)

<details><summary>40 columns</summary>

| Column | Type |
|---|---|
| `game_pk` | bigint |
| `player_id` | int |
| `player_name` | string |
| `team_id` | int |
| `opponent_id` | int |
| `is_home` | boolean |
| `season` | int |
| `game_type` | string |
| `season_type` | string |
| `official_date` | date |
| `appearance_order` | int |
| `is_starter` | boolean |
| `outs` | int |
| `innings_pitched` | double |
| `innings_pitched_display` | string |
| `batters_faced` | int |
| `pitches` | int |
| `strikes` | int |
| `h` | int |
| `r` | int |
| `er` | int |
| `bb` | int |
| `ibb` | int |
| `so` | int |
| `hr` | int |
| `hbp` | int |
| `wp` | int |
| `w` | int |
| `l` | int |
| `sv` | int |
| `svo` | int |
| `hld` | int |
| `bs` | int |
| `cg` | int |
| `sho` | int |
| `inherited_runners` | int |
| `inherited_runners_scored` | int |
| `is_quality_start` | boolean |
| `decision` | string |
| `updated_at` | timestamp |

</details>

### `silver.fact_team_game` (table)

**Grain:** two rows per game (one per team) · **Built by:** `src/silver/02_Silver_Games` · **Rows:** 19,704

Silver: two rows per game (one per team) with runs scored/allowed, hits, errors and result

<details><summary>26 columns</summary>

| Column | Type |
|---|---|
| `game_pk` | bigint |
| `season` | int |
| `game_type` | string |
| `season_type` | string |
| `official_date` | date |
| `game_datetime_utc` | timestamp |
| `is_completed` | boolean |
| `team_id` | int |
| `opponent_id` | int |
| `is_home` | boolean |
| `runs_scored` | int |
| `runs_allowed` | int |
| `hits` | int |
| `hits_allowed` | int |
| `errors` | int |
| `left_on_base` | int |
| `is_win` | boolean |
| `is_loss` | boolean |
| `run_differential` | int |
| `venue_id` | int |
| `day_night` | string |
| `double_header` | string |
| `game_number` | int |
| `is_extra_innings` | boolean |
| `is_one_run_game` | boolean |
| `updated_at` | timestamp |

</details>

### `silver.game_details` (table)

**Grain:** one row per completed game · **Built by:** `src/silver/03_Silver_Boxscores` · **Rows:** 7,414

Silver: attendance, duration, weather and home-plate umpire per completed game

<details><summary>8 columns</summary>

| Column | Type |
|---|---|
| `game_pk` | bigint |
| `attendance` | int |
| `duration_minutes` | int |
| `weather` | string |
| `wind` | string |
| `first_pitch_local` | string |
| `home_plate_umpire` | string |
| `updated_at` | timestamp |

</details>

### `silver.official_standings` (table)

**Grain:** team × season (official MLB standings) · **Built by:** `src/silver/01_Silver_Dimensions` · **Rows:** 90

Silver: official MLB regular-season standings, used to reconcile the W-L and runs computed from games

<details><summary>18 columns</summary>

| Column | Type |
|---|---|
| `season` | int |
| `team_id` | int |
| `division_id` | int |
| `games_played` | int |
| `wins` | int |
| `losses` | int |
| `runs_scored` | int |
| `runs_allowed` | int |
| `run_differential` | int |
| `win_pct` | double |
| `division_rank` | int |
| `league_rank` | int |
| `games_back` | string |
| `wild_card_games_back` | string |
| `clinch_indicator` | string |
| `streak` | string |
| `as_of` | timestamp |
| `updated_at` | timestamp |

</details>

## `gold`

### `gold.batting_game_log` (table)

**Grain:** player × game · **Built by:** `src/gold/02_Gold_Player_Metrics` · **Rows:** 156,064

Gold: batting game log with rolling last-15-games and season-to-date AVG/OPS/HR

<details><summary>28 columns</summary>

| Column | Type |
|---|---|
| `season` | int |
| `season_type` | string |
| `player_id` | int |
| `game_pk` | bigint |
| `official_date` | date |
| `team_id` | int |
| `opponent_id` | int |
| `is_home` | boolean |
| `lineup_slot` | int |
| `position` | string |
| `pa` | int |
| `ab` | int |
| `r` | int |
| `h` | int |
| `doubles` | int |
| `triples` | int |
| `hr` | int |
| `rbi` | int |
| `bb` | int |
| `so` | int |
| `sb` | int |
| `player_game_number` | int |
| `avg_last_15` | double |
| `ops_last_15` | double |
| `hr_last_15` | bigint |
| `avg_season_to_date` | double |
| `ops_season_to_date` | double |
| `hr_season_to_date` | bigint |

</details>

### `gold.country_season_summary` (table)

**Grain:** birth country × season × season type · **Built by:** `src/gold/03_Gold_Dominican_Players` · **Rows:** 120

Gold: players and production by birth country per season and season type, with share of league totals

<details><summary>18 columns</summary>

| Column | Type |
|---|---|
| `season` | int |
| `season_type` | string |
| `birth_country` | string |
| `players` | bigint |
| `hitters` | bigint |
| `pitchers` | bigint |
| `h` | bigint |
| `hr` | bigint |
| `rbi` | bigint |
| `sb` | bigint |
| `pitcher_wins` | bigint |
| `saves` | bigint |
| `pitcher_strikeouts` | bigint |
| `era` | double |
| `pct_of_players` | double |
| `pct_of_home_runs` | double |
| `pct_of_strikeouts` | double |
| `country_rank_by_players` | int |

</details>

### `gold.dim_date` (table)

**Grain:** one row per date · **Built by:** `src/gold/04_Gold_Semantic_Layer` · **Rows:** 1,461

Gold: calendar dimension covering every season in the platform

<details><summary>10 columns</summary>

| Column | Type |
|---|---|
| `date` | date |
| `year` | int |
| `month` | int |
| `month_name` | string |
| `month_year` | string |
| `month_key` | int |
| `week_of_year` | int |
| `day_of_week` | int |
| `day_name` | string |
| `is_weekend` | boolean |

</details>

### `gold.dim_player` (view)

**Built by:** `src/gold/04_Gold_Semantic_Layer` · **Rows:** 2,101

Gold: player dimension (birth country, position, handedness)

<details><summary>20 columns</summary>

| Column | Type |
|---|---|
| `player_id` | int |
| `player_name` | string |
| `first_name` | string |
| `last_name` | string |
| `birth_date` | date |
| `birth_city` | string |
| `birth_state_province` | string |
| `birth_country` | string |
| `is_dominican` | boolean |
| `height_in` | int |
| `weight_lb` | int |
| `primary_position` | string |
| `primary_position_name` | string |
| `position_type` | string |
| `bats` | string |
| `throws` | string |
| `mlb_debut_date` | date |
| `is_active` | boolean |
| `current_team_id` | int |
| `Storage Properties` | [serialization.format=1] |

</details>

### `gold.dim_team` (view)

**Built by:** `src/gold/04_Gold_Semantic_Layer` · **Rows:** 30

Gold: team dimension

<details><summary>16 columns</summary>

| Column | Type |
|---|---|
| `team_id` | int |
| `team_name` | string |
| `team_abbreviation` | string |
| `club_name` | string |
| `location_name` | string |
| `short_name` | string |
| `league_id` | int |
| `league_name` | string |
| `league_abbreviation` | string |
| `division_id` | int |
| `division_name` | string |
| `home_venue_id` | int |
| `home_venue_name` | string |
| `first_year_of_play` | int |
| `latest_season` | int |
| `Storage Properties` | [serialization.format=1] |

</details>

### `gold.dim_venue` (view)

**Built by:** `src/gold/04_Gold_Semantic_Layer` · **Rows:** 41

Gold: ballpark dimension

<details><summary>10 columns</summary>

| Column | Type |
|---|---|
| `venue_id` | int |
| `venue_name` | string |
| `city` | string |
| `state` | string |
| `country` | string |
| `latitude` | double |
| `longitude` | double |
| `elevation_ft` | int |
| `is_active` | boolean |
| `Storage Properties` | [serialization.format=1] |

</details>

### `gold.dominican_batting_season` (view)

**Built by:** `src/gold/03_Gold_Dominican_Players` · **Rows:** 233

Gold: Dominican-born hitters per season with rank among Dominicans and league ranks

<details><summary>51 columns</summary>

| Column | Type |
|---|---|
| `season` | int |
| `season_type` | string |
| `player_id` | int |
| `player_name` | string |
| `birth_country` | string |
| `is_dominican` | boolean |
| `primary_position` | string |
| `bats` | string |
| `age` | bigint |
| `team_id` | int |
| `team_abbreviation` | string |
| `teams_played` | bigint |
| `games` | bigint |
| `games_started` | bigint |
| `pa` | bigint |
| `ab` | bigint |
| `r` | bigint |
| `h` | bigint |
| `singles` | bigint |
| `doubles` | bigint |
| `triples` | bigint |
| `hr` | bigint |
| `rbi` | bigint |
| `bb` | bigint |
| `ibb` | bigint |
| `so` | bigint |
| `hbp` | bigint |
| `sb` | bigint |
| `cs` | bigint |
| `sf` | bigint |
| `sh` | bigint |
| `tb` | bigint |
| `gidp` | bigint |
| `avg` | double |
| `obp` | double |
| `slg` | double |
| `ops` | double |
| `iso` | double |
| `babip` | double |
| `k_pct` | double |
| `bb_pct` | double |
| `sb_success_rate` | double |
| `is_qualified` | boolean |
| `ops_rank_qualified` | int |
| `avg_rank_qualified` | int |
| `hr_rank` | int |
| `rbi_rank` | int |
| `sb_rank` | int |
| `dominican_ops_rank` | int |
| `dominican_hr_rank` | int |
| `Storage Properties` | [serialization.format=1] |

</details>

### `gold.dominican_latest_games` (view)

**Built by:** `src/gold/03_Gold_Dominican_Players` · **Rows:** 4

Gold: batting and pitching lines of every Dominican player on the most recent game day

<details><summary>19 columns</summary>

| Column | Type |
|---|---|
| `line_type` | string |
| `official_date` | date |
| `game_pk` | bigint |
| `player_id` | int |
| `player_name` | string |
| `birth_country` | string |
| `is_dominican` | boolean |
| `team_abbreviation` | string |
| `opponent` | string |
| `position` | string |
| `line` | string |
| `hits` | int |
| `home_runs` | int |
| `rbi` | int |
| `innings` | string |
| `strikeouts` | int |
| `earned_runs` | int |
| `decision` | string |
| `Storage Properties` | [serialization.format=1] |

</details>

### `gold.dominican_pitching_season` (view)

**Built by:** `src/gold/03_Gold_Dominican_Players` · **Rows:** 286

Gold: Dominican-born pitchers per season with rank among Dominicans and league ranks

<details><summary>54 columns</summary>

| Column | Type |
|---|---|
| `season` | int |
| `season_type` | string |
| `player_id` | int |
| `player_name` | string |
| `birth_country` | string |
| `is_dominican` | boolean |
| `throws` | string |
| `age` | bigint |
| `team_id` | int |
| `team_abbreviation` | string |
| `teams_played` | bigint |
| `role` | string |
| `games` | bigint |
| `games_started` | bigint |
| `w` | bigint |
| `l` | bigint |
| `sv` | bigint |
| `svo` | bigint |
| `hld` | bigint |
| `bs` | bigint |
| `cg` | bigint |
| `sho` | bigint |
| `quality_starts` | bigint |
| `outs` | bigint |
| `ip` | double |
| `ip_display` | string |
| `batters_faced` | bigint |
| `pitches` | bigint |
| `h` | bigint |
| `r` | bigint |
| `er` | bigint |
| `bb` | bigint |
| `ibb` | bigint |
| `so` | bigint |
| `hr` | bigint |
| `hbp` | bigint |
| `era` | double |
| `whip` | double |
| `k_per_9` | double |
| `bb_per_9` | double |
| `hr_per_9` | double |
| `k_bb_ratio` | double |
| `k_pct` | double |
| `bb_pct` | double |
| `k_minus_bb_pct` | double |
| `fip` | double |
| `is_qualified` | boolean |
| `era_rank_qualified` | int |
| `so_rank` | int |
| `w_rank` | int |
| `sv_rank` | int |
| `dominican_so_rank` | int |
| `dominican_sv_rank` | int |
| `Storage Properties` | [serialization.format=1] |

</details>

### `gold.fact_batting_game` (view)

**Built by:** `src/gold/04_Gold_Semantic_Layer` · **Rows:** 156,064

Gold: batting line per player per game

<details><summary>35 columns</summary>

| Column | Type |
|---|---|
| `game_pk` | bigint |
| `player_id` | int |
| `player_name` | string |
| `team_id` | int |
| `opponent_id` | int |
| `is_home` | boolean |
| `season` | int |
| `game_type` | string |
| `season_type` | string |
| `official_date` | date |
| `batting_order` | int |
| `lineup_slot` | int |
| `is_starter` | boolean |
| `position` | string |
| `pa` | int |
| `ab` | int |
| `r` | int |
| `h` | int |
| `doubles` | int |
| `triples` | int |
| `hr` | int |
| `rbi` | int |
| `bb` | int |
| `ibb` | int |
| `so` | int |
| `hbp` | int |
| `sb` | int |
| `cs` | int |
| `sf` | int |
| `sh` | int |
| `tb` | int |
| `lob` | int |
| `gidp` | int |
| `singles` | int |
| `Storage Properties` | [serialization.format=1] |

</details>

### `gold.fact_game` (view)

**Built by:** `src/gold/04_Gold_Semantic_Layer` · **Rows:** 9,852

Gold: one row per game with team names, attendance and duration

<details><summary>57 columns</summary>

| Column | Type |
|---|---|
| `game_pk` | bigint |
| `season` | int |
| `game_type` | string |
| `game_type_name` | string |
| `season_type` | string |
| `official_date` | date |
| `game_datetime_utc` | timestamp |
| `status_code` | string |
| `status_detail` | string |
| `status_reason` | string |
| `start_time_tbd` | boolean |
| `is_completed` | boolean |
| `is_tie` | boolean |
| `home_team_id` | int |
| `away_team_id` | int |
| `home_score` | int |
| `away_score` | int |
| `home_hits` | int |
| `away_hits` | int |
| `home_errors` | int |
| `away_errors` | int |
| `home_left_on_base` | int |
| `away_left_on_base` | int |
| `innings_played` | int |
| `scheduled_innings` | int |
| `venue_id` | int |
| `venue_name` | string |
| `day_night` | string |
| `double_header` | string |
| `game_number` | int |
| `game_description` | string |
| `series_description` | string |
| `series_game_number` | int |
| `games_in_series` | int |
| `winning_pitcher_id` | int |
| `losing_pitcher_id` | int |
| `save_pitcher_id` | int |
| `home_probable_pitcher_id` | int |
| `home_probable_pitcher` | string |
| `away_probable_pitcher_id` | int |
| `away_probable_pitcher` | string |
| `rescheduled_from_utc` | timestamp |
| `was_rescheduled` | boolean |
| `winning_team_id` | int |
| `losing_team_id` | int |
| `total_runs` | int |
| `run_margin` | int |
| `is_extra_innings` | boolean |
| `is_one_run_game` | boolean |
| `home_team` | string |
| `away_team` | string |
| `matchup` | string |
| `attendance` | int |
| `duration_minutes` | int |
| `weather` | string |
| `home_plate_umpire` | string |
| `Storage Properties` | [serialization.format=1] |

</details>

### `gold.fact_pitching_game` (view)

**Built by:** `src/gold/04_Gold_Semantic_Layer` · **Rows:** 63,653

Gold: pitching line per appearance

<details><summary>40 columns</summary>

| Column | Type |
|---|---|
| `game_pk` | bigint |
| `player_id` | int |
| `player_name` | string |
| `team_id` | int |
| `opponent_id` | int |
| `is_home` | boolean |
| `season` | int |
| `game_type` | string |
| `season_type` | string |
| `official_date` | date |
| `appearance_order` | int |
| `is_starter` | boolean |
| `outs` | int |
| `innings_pitched` | double |
| `innings_pitched_display` | string |
| `batters_faced` | int |
| `pitches` | int |
| `strikes` | int |
| `h` | int |
| `r` | int |
| `er` | int |
| `bb` | int |
| `ibb` | int |
| `so` | int |
| `hr` | int |
| `hbp` | int |
| `wp` | int |
| `w` | int |
| `l` | int |
| `sv` | int |
| `svo` | int |
| `hld` | int |
| `bs` | int |
| `cg` | int |
| `sho` | int |
| `inherited_runners` | int |
| `inherited_runners_scored` | int |
| `is_quality_start` | boolean |
| `decision` | string |
| `Storage Properties` | [serialization.format=1] |

</details>

### `gold.fact_team_game` (view)

**Built by:** `src/gold/04_Gold_Semantic_Layer` · **Rows:** 14,828

Gold: completed games from each team perspective

<details><summary>26 columns</summary>

| Column | Type |
|---|---|
| `game_pk` | bigint |
| `season` | int |
| `game_type` | string |
| `season_type` | string |
| `official_date` | date |
| `game_datetime_utc` | timestamp |
| `is_completed` | boolean |
| `team_id` | int |
| `opponent_id` | int |
| `is_home` | boolean |
| `runs_scored` | int |
| `runs_allowed` | int |
| `hits` | int |
| `hits_allowed` | int |
| `errors` | int |
| `left_on_base` | int |
| `is_win` | boolean |
| `is_loss` | boolean |
| `run_differential` | int |
| `venue_id` | int |
| `day_night` | string |
| `double_header` | string |
| `game_number` | int |
| `is_extra_innings` | boolean |
| `is_one_run_game` | boolean |
| `Storage Properties` | [serialization.format=1] |

</details>

### `gold.game_features` (table)

**Grain:** one row per game (home-team view, pre-game) · **Built by:** `src/gold/05_Gold_Game_Features` · **Rows:** 9,850

Gold: one row per game with point-in-time pre-game features (home minus away) for the win-probability model

<details><summary>48 columns</summary>

| Column | Type |
|---|---|
| `game_pk` | bigint |
| `season` | int |
| `season_type` | string |
| `game_type` | string |
| `official_date` | date |
| `game_datetime_utc` | timestamp |
| `status_detail` | string |
| `is_completed` | boolean |
| `home_team_id` | int |
| `away_team_id` | int |
| `venue_id` | int |
| `venue_name` | string |
| `home_win` | int |
| `home_starter_id` | int |
| `away_starter_id` | int |
| `home_starter_known` | boolean |
| `away_starter_known` | boolean |
| `home_games_before` | bigint |
| `away_games_before` | bigint |
| `home_wp` | double |
| `away_wp` | double |
| `home_rdpg` | double |
| `away_rdpg` | double |
| `home_last10` | double |
| `away_last10` | double |
| `home_split` | double |
| `away_split` | double |
| `home_sp_fip` | double |
| `away_sp_fip` | double |
| `home_sp_kbb` | double |
| `away_sp_kbb` | double |
| `home_bp_era` | decimal(38,17) |
| `away_bp_era` | decimal(38,17) |
| `home_bp_outs_3d` | bigint |
| `away_bp_outs_3d` | bigint |
| `home_rest` | int |
| `away_rest` | int |
| `d_win_pct` | double |
| `d_run_diff` | double |
| `d_last10` | double |
| `d_split` | double |
| `d_starter_fip` | double |
| `d_starter_kbb` | double |
| `d_bullpen_era` | decimal(38,16) |
| `d_bullpen_fatigue` | bigint |
| `d_rest` | int |
| `park_factor` | double |
| `is_postseason` | int |

</details>

### `gold.game_predictions` (table)

**Grain:** one row per game · **Built by:** `src/ml/01_Win_Probability_Model` · **Rows:** 9,850

Gold: home-team win probability per game (train in-sample, test out-of-sample, upcoming scored by the final model)

<details><summary>24 columns</summary>

| Column | Type |
|---|---|
| `game_pk` | bigint |
| `season` | bigint |
| `season_type` | string |
| `official_date` | date |
| `home_team_id` | bigint |
| `away_team_id` | bigint |
| `home_starter_id` | double |
| `away_starter_id` | double |
| `home_starter_known` | boolean |
| `away_starter_known` | boolean |
| `home_sp_fip` | double |
| `away_sp_fip` | double |
| `home_wp` | double |
| `away_wp` | double |
| `home_last10` | double |
| `away_last10` | double |
| `park_factor` | double |
| `home_win` | double |
| `home_win_prob` | double |
| `predicted_winner_id` | bigint |
| `correct` | boolean |
| `split` | string |
| `top_factors` | string |
| `model` | string |

</details>

### `gold.head_to_head` (table)

**Grain:** team × opponent × season × season type · **Built by:** `src/gold/01_Gold_Team_Metrics` · **Rows:** 2,676

Gold: team vs opponent record per season and season type (games, W-L, runs, first/last meeting, last result)

<details><summary>17 columns</summary>

| Column | Type |
|---|---|
| `season` | int |
| `season_type` | string |
| `team_id` | int |
| `team_name` | string |
| `opponent_id` | int |
| `opponent_name` | string |
| `games` | bigint |
| `wins` | bigint |
| `losses` | bigint |
| `win_pct` | double |
| `runs_scored` | bigint |
| `runs_allowed` | bigint |
| `run_differential` | bigint |
| `home_games` | bigint |
| `first_meeting` | date |
| `last_meeting` | date |
| `last_result` | string |

</details>

### `gold.latest_game_day_lines` (view)

**Grain:** player line on the latest game day · **Built by:** `src/gold/03_Gold_Dominican_Players` · **Rows:** 32

Gold: batting and pitching line of every player on the most recent game day, with birth country

<details><summary>19 columns</summary>

| Column | Type |
|---|---|
| `line_type` | string |
| `official_date` | date |
| `game_pk` | bigint |
| `player_id` | int |
| `player_name` | string |
| `birth_country` | string |
| `is_dominican` | boolean |
| `team_abbreviation` | string |
| `opponent` | string |
| `position` | string |
| `line` | string |
| `hits` | int |
| `home_runs` | int |
| `rbi` | int |
| `innings` | string |
| `strikeouts` | int |
| `earned_runs` | int |
| `decision` | string |
| `Storage Properties` | [serialization.format=1] |

</details>

### `gold.league_daily_summary` (table)

**Grain:** date × season type · **Built by:** `src/gold/04_Gold_Semantic_Layer` · **Rows:** 810

Gold: daily league KPIs (completed and postponed games, runs, home runs, extra innings, attendance, duration)

<details><summary>14 columns</summary>

| Column | Type |
|---|---|
| `game_date` | date |
| `season` | int |
| `season_type` | string |
| `scheduled_games` | bigint |
| `completed_games` | bigint |
| `postponed_games` | bigint |
| `makeup_games` | bigint |
| `total_runs` | bigint |
| `avg_runs_per_game` | double |
| `extra_inning_games` | bigint |
| `one_run_games` | bigint |
| `home_runs` | bigint |
| `avg_attendance` | double |
| `avg_duration_minutes` | double |

</details>

### `gold.pitching_game_log` (table)

**Grain:** pitcher appearance · **Built by:** `src/gold/02_Gold_Player_Metrics` · **Rows:** 63,653

Gold: pitching game log with rolling last-5-appearances and season-to-date ERA/WHIP

<details><summary>24 columns</summary>

| Column | Type |
|---|---|
| `season` | int |
| `season_type` | string |
| `player_id` | int |
| `game_pk` | bigint |
| `official_date` | date |
| `team_id` | int |
| `opponent_id` | int |
| `is_home` | boolean |
| `is_starter` | boolean |
| `innings_pitched_display` | string |
| `outs` | int |
| `h` | int |
| `er` | int |
| `bb` | int |
| `so` | int |
| `hr` | int |
| `pitches` | int |
| `decision` | string |
| `is_quality_start` | boolean |
| `appearance_number` | int |
| `era_last_5` | double |
| `whip_last_5` | double |
| `era_season_to_date` | double |
| `so_season_to_date` | bigint |

</details>

### `gold.player_season_batting` (table)

**Grain:** player × season × season type · **Built by:** `src/gold/02_Gold_Player_Metrics` · **Rows:** 2,732

Gold: batting season line per player, season and season type (AVG/OBP/SLG/OPS, ISO, BABIP, K%, BB%, qualification, ranks)

<details><summary>48 columns</summary>

| Column | Type |
|---|---|
| `season` | int |
| `season_type` | string |
| `player_id` | int |
| `player_name` | string |
| `birth_country` | string |
| `is_dominican` | boolean |
| `primary_position` | string |
| `bats` | string |
| `age` | bigint |
| `team_id` | int |
| `team_abbreviation` | string |
| `teams_played` | bigint |
| `games` | bigint |
| `games_started` | bigint |
| `pa` | bigint |
| `ab` | bigint |
| `r` | bigint |
| `h` | bigint |
| `singles` | bigint |
| `doubles` | bigint |
| `triples` | bigint |
| `hr` | bigint |
| `rbi` | bigint |
| `bb` | bigint |
| `ibb` | bigint |
| `so` | bigint |
| `hbp` | bigint |
| `sb` | bigint |
| `cs` | bigint |
| `sf` | bigint |
| `sh` | bigint |
| `tb` | bigint |
| `gidp` | bigint |
| `avg` | double |
| `obp` | double |
| `slg` | double |
| `ops` | double |
| `iso` | double |
| `babip` | double |
| `k_pct` | double |
| `bb_pct` | double |
| `sb_success_rate` | double |
| `is_qualified` | boolean |
| `ops_rank_qualified` | int |
| `avg_rank_qualified` | int |
| `hr_rank` | int |
| `rbi_rank` | int |
| `sb_rank` | int |

</details>

### `gold.player_season_pitching` (table)

**Grain:** player × season × season type · **Built by:** `src/gold/02_Gold_Player_Metrics` · **Rows:** 3,009

Gold: pitching season line per player, season and season type (ERA, WHIP, K/9, FIP, quality starts, qualification, ranks)

<details><summary>51 columns</summary>

| Column | Type |
|---|---|
| `season` | int |
| `season_type` | string |
| `player_id` | int |
| `player_name` | string |
| `birth_country` | string |
| `is_dominican` | boolean |
| `throws` | string |
| `age` | bigint |
| `team_id` | int |
| `team_abbreviation` | string |
| `teams_played` | bigint |
| `role` | string |
| `games` | bigint |
| `games_started` | bigint |
| `w` | bigint |
| `l` | bigint |
| `sv` | bigint |
| `svo` | bigint |
| `hld` | bigint |
| `bs` | bigint |
| `cg` | bigint |
| `sho` | bigint |
| `quality_starts` | bigint |
| `outs` | bigint |
| `ip` | double |
| `ip_display` | string |
| `batters_faced` | bigint |
| `pitches` | bigint |
| `h` | bigint |
| `r` | bigint |
| `er` | bigint |
| `bb` | bigint |
| `ibb` | bigint |
| `so` | bigint |
| `hr` | bigint |
| `hbp` | bigint |
| `era` | double |
| `whip` | double |
| `k_per_9` | double |
| `bb_per_9` | double |
| `hr_per_9` | double |
| `k_bb_ratio` | double |
| `k_pct` | double |
| `bb_pct` | double |
| `k_minus_bb_pct` | double |
| `fip` | double |
| `is_qualified` | boolean |
| `era_rank_qualified` | int |
| `so_rank` | int |
| `w_rank` | int |
| `sv_rank` | int |

</details>

### `gold.team_game_log` (table)

**Grain:** team × game · **Built by:** `src/gold/01_Gold_Team_Metrics` · **Rows:** 14,828

Gold: team game-by-game log with running record, run differential, rolling last-10 and streak

<details><summary>27 columns</summary>

| Column | Type |
|---|---|
| `season` | int |
| `season_type` | string |
| `game_type` | string |
| `team_id` | int |
| `game_pk` | bigint |
| `official_date` | date |
| `team_game_number` | int |
| `opponent_id` | int |
| `is_home` | boolean |
| `runs_scored` | int |
| `runs_allowed` | int |
| `run_differential` | int |
| `hits` | int |
| `errors` | int |
| `result` | string |
| `is_win` | boolean |
| `is_loss` | boolean |
| `is_extra_innings` | boolean |
| `is_one_run_game` | boolean |
| `wins_to_date` | bigint |
| `losses_to_date` | bigint |
| `win_pct_to_date` | double |
| `run_differential_to_date` | bigint |
| `wins_last_10` | bigint |
| `games_last_10` | bigint |
| `streak_length` | int |
| `streak_code` | string |

</details>

### `gold.team_season_summary` (table)

**Grain:** team × season × season type · **Built by:** `src/gold/01_Gold_Team_Metrics` · **Rows:** 126

Gold: team record and splits per season and season type, run differential, Pythagorean expected wins and luck

<details><summary>41 columns</summary>

| Column | Type |
|---|---|
| `season` | int |
| `season_type` | string |
| `team_id` | int |
| `team_name` | string |
| `team_abbreviation` | string |
| `league_abbreviation` | string |
| `division_name` | string |
| `games` | bigint |
| `wins` | bigint |
| `losses` | bigint |
| `win_pct` | double |
| `runs_scored` | bigint |
| `runs_allowed` | bigint |
| `run_differential` | bigint |
| `runs_scored_per_game` | double |
| `runs_allowed_per_game` | double |
| `pythagorean_win_pct` | double |
| `expected_wins` | double |
| `luck_wins` | double |
| `home_wins` | bigint |
| `home_losses` | bigint |
| `away_wins` | bigint |
| `away_losses` | bigint |
| `one_run_wins` | bigint |
| `one_run_losses` | bigint |
| `extra_inning_wins` | bigint |
| `extra_inning_losses` | bigint |
| `blowout_wins` | bigint |
| `blowout_losses` | bigint |
| `last_10_wins` | bigint |
| `last_10_losses` | bigint |
| `current_streak` | string |
| `longest_win_streak` | int |
| `longest_losing_streak` | int |
| `avg_home_attendance` | double |
| `division_rank` | int |
| `league_rank` | int |
| `games_back` | string |
| `wild_card_games_back` | string |
| `clinch_indicator` | string |
| `last_game_date` | date |

</details>

### `gold.win_model_calibration` (table)

**Grain:** probability bucket · **Built by:** `src/ml/01_Win_Probability_Model` · **Rows:** 5

Gold: calibration of the selected model on the test season (predicted vs actual win rate of the favourite)

<details><summary>5 columns</summary>

| Column | Type |
|---|---|
| `bucket` | string |
| `games` | bigint |
| `predicted` | double |
| `actual` | double |
| `test_season` | bigint |

</details>

### `gold.win_model_features` (table)

**Grain:** one row per feature · **Built by:** `src/ml/01_Win_Probability_Model` · **Rows:** 11

Gold: standardized logistic-regression coefficients (what moves the win probability)

<details><summary>4 columns</summary>

| Column | Type |
|---|---|
| `feature` | string |
| `label` | string |
| `coefficient` | double |
| `abs_importance` | double |

</details>

### `gold.win_model_metrics` (table)

**Grain:** model × split · **Built by:** `src/ml/01_Win_Probability_Model` · **Rows:** 6

Gold: win-probability model metrics (train/test, baselines, selected model)

<details><summary>10 columns</summary>

| Column | Type |
|---|---|
| `model` | string |
| `split` | string |
| `games` | bigint |
| `accuracy` | double |
| `log_loss` | double |
| `brier` | double |
| `auc` | double |
| `selected` | boolean |
| `test_season` | bigint |
| `trained_at` | timestamp |

</details>

## `metadata`

### `metadata.extract_register` (table)

**Grain:** one row per API request · **Built by:** `src/setup/01_Create_Metadata_Tables` · **Rows:** 7,489

Extraction register: every MLB Stats API request with its outcome; drives incremental extraction

<details><summary>11 columns</summary>

| Column | Type |
|---|---|
| `endpoint` | string |
| `request_key` | string |
| `request_url` | string |
| `status_code` | int |
| `outcome` | string |
| `error` | string |
| `payload_sha256` | string |
| `file_path` | string |
| `bytes` | bigint |
| `extracted_at` | timestamp |
| `run_id` | string |

</details>

### `metadata.pipeline_runs` (table)

**Grain:** task × run · **Built by:** `src/setup/01_Create_Metadata_Tables` · **Rows:** 176

Run log: one row per pipeline task execution (UTC timestamps)

<details><summary>11 columns</summary>

| Column | Type |
|---|---|
| `pipeline_name` | string |
| `run_id` | string |
| `layer` | string |
| `task` | string |
| `status` | string |
| `message` | string |
| `execution_window` | string |
| `records_processed` | bigint |
| `started_at` | timestamp |
| `ended_at` | timestamp |
| `duration_seconds` | double |

</details>

### `metadata.watermarks` (table)

**Grain:** one row per incremental consumer · **Built by:** `src/setup/01_Create_Metadata_Tables` · **Rows:** 2

Incremental processing watermarks for Silver consumers

<details><summary>3 columns</summary>

| Column | Type |
|---|---|
| `consumer` | string |
| `high_watermark` | timestamp |
| `updated_at` | timestamp |

</details>

## `quality`

### `quality.dq_results` (table)

**Grain:** check × run · **Built by:** `src/quality/01_Data_Quality_Checks` · **Rows:** 154

Data-quality results: one row per check and run

<details><summary>11 columns</summary>

| Column | Type |
|---|---|
| `run_id` | string |
| `check_id` | string |
| `check_name` | string |
| `layer` | string |
| `table_name` | string |
| `severity` | string |
| `status` | string |
| `failed_rows` | bigint |
| `checked_rows` | bigint |
| `details` | string |
| `checked_at` | timestamp |

</details>
