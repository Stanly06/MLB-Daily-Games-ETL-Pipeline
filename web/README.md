# Web platform

Single-page explorer built from the Gold layer export (`src/exports/01_Web_Platform_Export`).

```bash
python web/build.py /path/to/mlb_web_data.json   # -> web/dist/index.html (self-contained, ~10 MB)
```

| View | Content |
|---|---|
| League | KPI cards, standings by division, run differential vs wins, Pythagorean luck |
| Team | Logo, record and splits, season trajectory, top hitters and pitchers, last 10 games |
| Player | Search, headshot, current team, profile, season cards with MLB ranks, full batting/pitching line, form chart, game log, all seasons |
| Head-to-head | Two teams: season and all-time record, every meeting |
| Leaders | Qualified rate leaders and counting leaders |
| Countries | Any birth country (Dominican Republic by default): share of league, top players, latest game day, all-countries table |
| Quality | Latest data-quality results |

Filters: season, season type (regular season / postseason) and language (ES/EN).
Team logos and player headshots load from `mlbstatic.com` (© MLB); if a host blocks external
images, the page falls back to the team abbreviation or the player's initials.
