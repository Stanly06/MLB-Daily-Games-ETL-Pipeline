# Power BI — MLB Performance Intelligence report

Build guide for the Power BI report on top of the Gold layer. Measures are in
[`measures.dax`](measures.dax) and the colour theme in [`mlb_intelligence_theme.json`](mlb_intelligence_theme.json).

## 1. Connect

1. In Databricks: **SQL Warehouses** → your (serverless) warehouse → **Connection details**; copy *Server hostname* and *HTTP path*.
2. Create a personal access token: **Settings → Developer → Access tokens**.
3. Power BI Desktop → **Get data → Azure Databricks** → paste hostname and HTTP path → **Import** mode → authenticate with the token.
4. Select catalog `mlb_intelligence`, schema `gold`, and load the objects in section 2.

## 2. Model

| Object | Role | Load |
|---|---|---|
| `dim_date` | Calendar (mark as date table on `date`) | yes |
| `dim_team`, `dim_player`, `dim_venue` | Dimensions | yes |
| `fact_game`, `fact_team_game`, `fact_batting_game`, `fact_pitching_game` | Game-level facts | yes |
| `team_season_summary`, `team_game_log`, `head_to_head` | Team KPIs | yes |
| `player_season_batting`, `player_season_pitching`, `batting_game_log`, `pitching_game_log` | Player KPIs | yes |
| `country_season_summary`, `dominican_latest_games` | Dominican players | yes |
| `league_daily_summary` | League trend | yes |

**Relationships** (single direction, one-to-many from the dimension):

| From (1) | To (*) |
|---|---|
| `dim_date[date]` | `fact_game[official_date]`, `fact_team_game[official_date]`, `fact_batting_game[official_date]`, `fact_pitching_game[official_date]`, `team_game_log[official_date]`, `batting_game_log[official_date]`, `pitching_game_log[official_date]`, `league_daily_summary[game_date]` |
| `dim_team[team_id]` | `fact_team_game[team_id]`, `fact_batting_game[team_id]`, `fact_pitching_game[team_id]`, `team_season_summary[team_id]`, `team_game_log[team_id]`, `head_to_head[team_id]`, `player_season_batting[team_id]`, `player_season_pitching[team_id]` |
| `dim_player[player_id]` | `fact_batting_game[player_id]`, `fact_pitching_game[player_id]`, `player_season_batting[player_id]`, `player_season_pitching[player_id]`, `batting_game_log[player_id]`, `pitching_game_log[player_id]` |
| `dim_venue[venue_id]` | `fact_game[venue_id]` |

Add a disconnected **`Opponent`** table (`Opponent = SELECTCOLUMNS(dim_team, "opponent_id", dim_team[team_id], "opponent", dim_team[team_name])`) related to `head_to_head[opponent_id]` so the head-to-head page can select two teams.

Slicers used on every page: `season`, `season_type` (default *Regular Season*).

## 3. Pages

| # | Page | Visuals | Question answered |
|---|---|---|---|
| 1 | **League overview** | KPI cards (games, avg runs, HR, avg attendance); standings matrix by division (W, L, PCT, GB, run diff, streak, last 10); scatter *run differential vs wins*; bar *luck_wins* by team | Who is good, and who is lucky? |
| 2 | **Team** | Team slicer; cards (record, run diff, expected wins, luck, streak); line *win_pct_to_date* and *run_differential_to_date* by game number; home/away, one-run, extra-inning splits; table of last 10 games | How is this team really doing? |
| 3 | **Player** | Player search slicer; profile card (team, position, bats/throws, age, birth country); season line cards (AVG/OBP/SLG/OPS or ERA/WHIP/FIP); line *ops_last_15* vs *ops_season_to_date*; game log table; season-by-season table | Is this player hot or cold? |
| 4 | **Head-to-head** | Team and Opponent slicers; cards (games, W-L, runs); table of every meeting from `fact_game` (date, venue, score, winning pitcher) | When did they meet and who won? |
| 5 | **Leaders** | Top 10 qualified OPS, HR, SB; top 10 qualified ERA, SO, SV; filter by league | Who leads the league? |
| 6 | **Dominicans in MLB** | Cards (Dominican players, % of league, % of HR); bar *players by country*; top Dominican hitters and pitchers; table `dominican_latest_games` ("how did our players do last night") | How are Dominican players performing? |
| 7 | **Data health** | Last run status by task (`metadata.pipeline_runs`), DQ checks (`quality.dq_results`) | Can I trust today's numbers? |

## 4. Refresh

Schedule the dataset refresh in the Power BI service after the Databricks Job (daily 06:07
America/Santo_Domingo) — e.g. 07:30.
