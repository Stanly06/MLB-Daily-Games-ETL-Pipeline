# Business Requirements Document

## MLB Performance Intelligence Platform

| Attribute | Details |
|---|---|
| **Project** | MLB Performance Intelligence Platform (v2 of *MLB Daily Games ETL Pipeline*) |
| **Document** | Business Requirements Document (BRD) |
| **Version** | 1.0 |
| **Status** | Implemented in development |
| **Owner** | Stanly Fernández |
| **Platform** | Databricks (Free Edition) · Unity Catalog · Delta Lake · Power BI |
| **Source** | MLB Stats API (`statsapi.mlb.com`), public, no key |

---

## 1. Business problem

Baseball decisions (lineups, scouting reports, fantasy rosters, betting research, media coverage)
depend on answering performance questions quickly: *How is this player trending? Is this team
really as good as its record? How have these two teams done against each other this year?*

The official data exists but is hard to use:

- It is spread across **separate API endpoints** (schedule, one boxscore per game, player profiles, teams, standings) returned as deeply nested JSON.
- Player statistics are only available **game by game** inside each boxscore; season lines, rolling form and rankings have to be computed.
- The API has **operational quirks**: postponed and suspended games appear twice, games can end early, box scores receive scoring corrections days later.
- There is **no history** in one place: comparing seasons or rebuilding a head-to-head record requires thousands of calls.

The v1 pipeline loaded only yesterday's schedule into a daily summary (games and total runs). It
had no players, no team history and no business questions behind it.

## 2. Objective

Build an automated Lakehouse that consolidates every regular-season and postseason game since 2024
at **game, team and player level**, computes the standard and advanced metrics analysts use, proves
its numbers against official MLB standings, and serves a Power BI model that answers the questions
below in seconds.

## 3. Stakeholders and personas

| Persona | Need | Example question |
|---|---|---|
| Team / front-office analyst | Evaluate team strength beyond the record | Which teams over- or under-performed their run differential? |
| Scout / player-development analyst | Track a player's season and current form | Is this hitter's OPS over the last 15 games above his season line? |
| Sports journalist / content creator | Fast, reliable facts for daily coverage | How did the Dominican players do last night? |
| Fantasy / betting researcher | Matchups and trends | What is the head-to-head record between these teams this season? |
| Data platform owner | Trustworthy, automated data | Did last night's load complete, and do the totals reconcile? |

## 4. Business questions (summary)

The full list, with formulas and target tables, is in the [KPI Catalog](02_KPI_Catalog.md).

**Teams**
1. What is each team's record, run differential and home/away split by season?
2. Which teams won more (or fewer) games than their runs scored and allowed predict (Pythagorean expectation)?
3. How does a team perform in close games (one-run, extra innings) and what is its current streak and last-10 record?
4. How did the record and run differential evolve game by game during the season?

**Matchups**
5. When did two teams meet, who won, and what is the season and all-time (since 2024) head-to-head record?

**Players**
6. What is a player's season line (AVG, OBP, SLG, OPS, HR, RBI; ERA, WHIP, K/9, FIP) and league rank?
7. Is the player hot or cold (rolling last-15-games OPS, last-5-appearances ERA vs season-to-date)?
8. Who leads the league among qualified players?

**Dominican players in MLB**
9. How many MLB players were born in the Dominican Republic and what share of league production (home runs, strikeouts) do they represent each season?
10. Who are the top Dominican hitters and pitchers, and how did they do on the latest game day?

**League and operations**
11. How many games were completed or postponed per day, with average runs, attendance and duration?
12. Did every pipeline step succeed, and do our totals match the official standings?

## 5. Scope

| In scope | Out of scope (future) |
|---|---|
| Regular season (R) and postseason (F, D, L, W), 2024 → today | Spring training, exhibitions, All-Star Game |
| Game, team-game, batting and pitching lines per game | Pitch-by-pitch / Statcast data (exit velocity, spin) |
| Player profile incl. birth country, team, league, division, venue | Salaries, contracts, injuries, transactions |
| Daily incremental load + on-demand historical backfill | Real-time (in-game) updates |
| Data-quality checks and reconciliation with official standings | Predictive models (win probability, projections) |

## 6. Functional requirements

| ID | Requirement |
|---|---|
| FR-01 | Extract schedule, boxscores, players, teams, venues and standings from the MLB Stats API. |
| FR-02 | Keep every raw response (append-only archive) with request URL, HTTP status, extraction time and SHA-256. |
| FR-03 | Load incrementally: only new or changed responses are landed and processed; re-runs never duplicate data. |
| FR-04 | Support a parameterized historical backfill by season and a custom date range. |
| FR-05 | Handle postponed, suspended and early-ended games correctly (one row per game; a completed game is never overwritten). |
| FR-06 | Produce team, head-to-head, player season, player form, Dominican-player and league KPIs as defined in the KPI catalog. |
| FR-07 | Expose a star schema (dimensions + facts) for Power BI in the Gold schema. |
| FR-08 | Log every task (status, records, duration, error) and run data-quality checks after each load. |
| FR-09 | Fail the run when a critical check fails, including any mismatch with official standings. |
| FR-10 | Run automatically every day without manual steps. |

## 7. Non-functional requirements

- **Reliability:** HTTP retries with exponential backoff; a run fails if more than 2 % of boxscores cannot be downloaded; tasks have retries in the Job.
- **Auditability:** every Bronze row carries its source file, size, modification time, ingestion time and batch id.
- **Performance:** a full season backfill (~2,500 boxscores) completes in minutes with concurrent requests; the daily run touches ~50 games.
- **Maintainability:** shared code (API client, logging, MERGE, watermarks, schemas) lives in `src/shared/`, not copied across notebooks.
- **Cost:** runs on Databricks Free Edition serverless compute.

## 8. Success criteria

| Criterion | Target |
|---|---|
| Regular-season W, L, runs scored and runs allowed vs official MLB standings | 100 % match for every fully loaded team-season |
| Sum of player runs per game vs team runs (line score) | 100 % match |
| Completed games with a boxscore | 100 % |
| Duplicate games or player-game rows | 0 |
| Daily run | Completes unattended; failures alert by e-mail |

## 9. Assumptions, constraints and risks

| Type | Description | Mitigation |
|---|---|---|
| Constraint | The MLB Stats API is public but undocumented and may change fields. | `from_json` with declared fields only; raw payload kept in Bronze so Silver can be rebuilt (`full_refresh`). |
| Risk | Rate limiting or transient errors. | Retries with backoff, 8 concurrent requests, failure threshold. |
| Risk | Scoring corrections after a game ends. | Daily mode re-checks the last `lookback_days` boxscores; unchanged responses are skipped by hash. |
| Assumption | Birth country in the player profile identifies Dominican-born players. | Documented in the KPI catalog (DR-001). |
| Legal | Data © MLB Advanced Media. | Non-commercial portfolio use; attribution in the README. |
