# Data Source Assessment — MLB Stats API

| Attribute | Details |
|---|---|
| **Provider** | MLB Advanced Media — `https://statsapi.mlb.com/api/v1` |
| **Access** | Public HTTPS, JSON, no API key, no published rate limit |
| **Licence** | Data © MLB Advanced Media; used for a non-commercial portfolio project |
| **Profiling date** | October 2026 (2025 season and 2026 postseason responses) |

## 1. Endpoints used

| Endpoint | Request | Grain of the response | Volume (one season) | Used for |
|---|---|---|---|---|
| `/schedule` | `sportId=1&startDate&endDate&gameType=R,F,D,L,W&hydrate=linescore,decisions` | One entry per game per scheduled date | ~2,500 entries, ~11 MB | `fact_game`, `fact_team_game` |
| `/game/{gamePk}/boxscore` | — | One game: both rosters with batting / pitching / fielding lines, `info` block, officials | ~2,480 calls, ~170 KB each (~420 MB) | `fact_batting_game`, `fact_pitching_game`, `game_details` |
| `/people` | `personIds=…&hydrate=currentTeam` (≤ 100 ids per call) | One profile per player | ~1,500 players, ~16 calls | `dim_player` |
| `/teams` | `sportId=1&season=YYYY` | 30 teams | 1 call | `dim_team` |
| `/venues` | `venueIds=…&hydrate=location` | One venue | 1 call | `dim_venue` |
| `/standings` | `leagueId=103,104&season=YYYY&standingsTypes=regularSeason` | 6 divisions × 5 teams | 1 call | `official_standings` (reconciliation) |

## 2. Profiling findings and decisions

| # | Finding | Evidence | Decision |
|---|---|---|---|
| 1 | **Postponed games appear twice** with the same `gamePk`: once on the original date (`codedGameState = D`, "Postponed") and once on the make-up date. | 2025 schedule: 2,511 entries for 2,477 distinct games; 34 duplicated `gamePk`. | Deduplicate per `gamePk`; the completed entry wins. The Silver `MERGE` refuses to overwrite a completed game with a non-completed entry. |
| 2 | `abstractGameState = 'Final'` is also used for postponed games. | 30 entries `Final / D / Postponed` in 2025. | A game is completed only when `codedGameState = 'F'` (covers "Final" and "Completed Early"). |
| 3 | Games can end early (rain). | 5 "Completed Early" games in 2025. | Counted as completed; `innings_played < scheduled_innings` is kept for analysis. |
| 4 | Boxscore players are a **map keyed by `"ID<playerId>"`**, not an array. | `teams.home.players.ID694819`. | Parsed with `map<string, struct>` in `from_json` and `explode(map_values())`; no Python UDFs. |
| 5 | Boxscores do not contain their own `gamePk`. | Top-level keys: `teams, officials, info, pitchingNotes, topPerformers`. | `gamePk` is carried in the landing envelope (`request_key`). |
| 6 | Non-pitchers carry an empty `pitching: {}` object; pitchers who do not bat carry `batting: {}`. | Boxscore samples. | Batting rows require a `battingOrder`; pitching rows require `battersFaced` or `outs`. |
| 7 | Innings pitched is a string in baseball notation (`"6.1"` = 6⅓). | `inningsPitched: "1.1"`, `outs: 4`. | Store the exact `outs` integer; IP = outs / 3. |
| 8 | Attendance, duration and weather are free-text labels in `info`. | `{"label": "Att", "value": "43,250."}`, `{"label": "T", "value": "3:09."}`. | Parsed with regular expressions into `attendance` and `duration_minutes`. |
| 9 | Height is text (`6' 1"`). | `/people`. | Converted to inches (`height_in`). |
| 10 | Line-score totals (R/H/E/LOB per team) are in `linescore.teams` when `hydrate=linescore`. | Schedule samples. | Team-game facts come from the schedule, player facts from the boxscore; both are reconciled (DQ-009, DQ-010). |
| 11 | Official standings include `runsScored` / `runsAllowed`. | `/standings` 2025. | External reconciliation of our computed W-L and runs (DQ-013). |
| 12 | Box scores can be corrected after the game (scoring changes). | Known MLB practice. | Daily mode re-requests the last `lookback_days` boxscores; unchanged responses are skipped by SHA-256. |
| 13 | A player can appear for **both teams** in one game. | Game 746942 (Blue Jays at Red Sox, suspended 26 Jun 2024, resumed 26 Aug 2024): Danny Jansen has a TOR line and a BOS line. Found by DQ-005. | Player-game key is `(game_pk, player_id, team_id)`. |
| 14 | Rain-cancelled games are never played and keep `codedGameState = C`. | 2 cancelled games (2024-09-29, 2026-09-27). | Kept in `fact_game` with `is_completed = false`; excluded from every KPI. |
| 15 | A suspended game keeps its original `officialDate` when resumed. | Game 746942 is dated 2024-06-26. | Documented; date-based KPIs use the official date, as MLB does. |

## 3. Data-quality profile (seasons 2024–2026, regular season + postseason)

From the local end-to-end run (data through 23 Oct 2026); see `quality.dq_results` for live values.

| Check | Result |
|---|---|
| Completed games with boxscore | 7,414 / 7,414 |
| Duplicate `game_pk` / player-game rows | 0 |
| Player runs = team runs per game | 14,828 / 14,828 team-games |
| Runs allowed by pitchers = opponent runs | 100 % |
| W, L, RS, RA vs official standings | 90 / 90 team-seasons, exact match |
