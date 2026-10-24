"""MLB Stats API client and extraction helpers.

* `MlbApiClient` wraps `requests` with retries, exponential backoff and a thread-local session,
  so hundreds of boxscores can be downloaded concurrently without hammering the API.
* The pure functions below plan what to extract (date windows, completed games, player ids)
  and land each response as a self-describing JSON envelope in the raw archive.

Source: https://statsapi.mlb.com (public, no key). Data copyright MLB Advanced Media;
used here for a non-commercial portfolio project.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from typing import Iterable, Iterator

import requests

BASE_URL = "https://statsapi.mlb.com/api/v1"
RETRY_STATUS = {429, 500, 502, 503, 504}


class MlbApiClient:
    """Small, polite HTTP client for the MLB Stats API."""

    def __init__(self, timeout: int = 30, max_retries: int = 4, backoff_seconds: float = 2.0):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self._local = threading.local()

    def _session(self) -> requests.Session:
        if not hasattr(self._local, "session"):
            s = requests.Session()
            s.headers.update({"User-Agent": "mlb-performance-intelligence/2.0 (portfolio project)"})
            self._local.session = s
        return self._local.session

    def get(self, path: str, params: dict | None = None) -> dict:
        """GET one endpoint. Returns url, status_code, payload (dict or None) and error (str or None)."""
        url = f"{BASE_URL}/{path.lstrip('/')}"
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                r = self._session().get(url, params=params, timeout=self.timeout)
                if r.status_code == 200:
                    return {"url": r.url, "status_code": 200, "payload": r.json(), "error": None}
                last_error = f"HTTP {r.status_code}"
                if r.status_code not in RETRY_STATUS:
                    return {"url": r.url, "status_code": r.status_code, "payload": None, "error": last_error}
            except (requests.ConnectionError, requests.Timeout, ValueError) as e:
                last_error = f"{type(e).__name__}: {e}"
            if attempt < self.max_retries:
                time.sleep(self.backoff_seconds * (2 ** attempt))
        return {"url": url, "status_code": -1, "payload": None, "error": last_error}

    def get_many(self, calls: list[dict], max_workers: int = 8) -> Iterator[dict]:
        """Run many GETs concurrently. Each call is {"key", "path", "params"}; yields call + result."""
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(self.get, c["path"], c.get("params")): c for c in calls}
            for f in as_completed(futures):
                yield {**futures[f], **f.result()}


# ---------------------------------------------------------------------------
# Request builders
# ---------------------------------------------------------------------------

def schedule_call(start: date, end: date, game_types: Iterable[str]) -> dict:
    return {
        "key": f"{start:%Y-%m-%d}_{end:%Y-%m-%d}",
        "path": "schedule",
        "params": {
            "sportId": 1,
            "startDate": f"{start:%Y-%m-%d}",
            "endDate": f"{end:%Y-%m-%d}",
            "gameType": ",".join(game_types),
            "hydrate": "linescore,decisions",
        },
    }


def boxscore_call(game_pk: int) -> dict:
    return {"key": str(game_pk), "path": f"game/{game_pk}/boxscore", "params": None}


def people_call(player_ids: list[int], batch_label: str) -> dict:
    return {"key": batch_label, "path": "people",
            "params": {"personIds": ",".join(str(i) for i in player_ids), "hydrate": "currentTeam"}}


def teams_call(season: int) -> dict:
    return {"key": str(season), "path": "teams", "params": {"sportId": 1, "season": season}}


def venues_call(venue_ids: list[int], batch_label: str) -> dict:
    return {"key": batch_label, "path": "venues",
            "params": {"venueIds": ",".join(str(i) for i in venue_ids), "hydrate": "location"}}


def standings_call(season: int) -> dict:
    return {"key": str(season), "path": "standings",
            "params": {"leagueId": "103,104", "season": season, "standingsTypes": "regularSeason"}}


# ---------------------------------------------------------------------------
# Planning helpers
# ---------------------------------------------------------------------------

def date_chunks(start: date, end: date, days: int = 31) -> list[tuple[date, date]]:
    """Split [start, end] into consecutive windows of at most `days` days."""
    chunks, cur = [], start
    while cur <= end:
        stop = min(cur + timedelta(days=days - 1), end)
        chunks.append((cur, stop))
        cur = stop + timedelta(days=1)
    return chunks


def season_window(season: int, latest: date) -> tuple[date, date] | None:
    """MLB games (regular season + postseason) fall between March and mid-November."""
    start, end = date(season, 3, 1), min(date(season, 11, 30), latest)
    return (start, end) if start <= end else None


def games_from_schedule(payload: dict) -> list[dict]:
    """Flatten a schedule payload into one dict per game entry (a game can appear twice
    when it was postponed or suspended; callers decide which entry wins)."""
    games = []
    for d in payload.get("dates", []):
        for g in d.get("games", []):
            status = g.get("status", {})
            teams = g.get("teams", {})
            games.append({
                "game_pk": g.get("gamePk"),
                "game_type": g.get("gameType"),
                "season": int(g.get("season")) if g.get("season") else None,
                "official_date": g.get("officialDate"),
                "is_completed": status.get("codedGameState") == "F",
                "venue_id": (g.get("venue") or {}).get("id"),
                "home_team_id": ((teams.get("home") or {}).get("team") or {}).get("id"),
                "away_team_id": ((teams.get("away") or {}).get("team") or {}).get("id"),
            })
    return games


def player_ids_from_boxscore(payload: dict) -> set[int]:
    ids = set()
    for side in ("home", "away"):
        players = ((payload.get("teams") or {}).get(side) or {}).get("players") or {}
        for p in players.values():
            pid = (p.get("person") or {}).get("id")
            if pid:
                ids.add(int(pid))
    return ids


def chunked(seq: list, size: int) -> list[list]:
    return [seq[i:i + size] for i in range(0, len(seq), size)]


# ---------------------------------------------------------------------------
# Landing (append-only raw archive)
# ---------------------------------------------------------------------------

def canonical_json(payload: dict) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def land_response(raw_root: str, endpoint: str, request_key: str, url: str, status_code: int,
                  payload_text: str, extracted_at: datetime, run_id: str) -> tuple[str, int]:
    """Write one API response as a JSON envelope:
    <raw_root>/<endpoint>/<yyyy>/<mm>/<request_key>__<yyyymmddThhmmss>.json
    Files are never overwritten; each extraction is a new file. Returns (path, bytes)."""
    folder = os.path.join(raw_root, endpoint, f"{extracted_at:%Y}", f"{extracted_at:%m}")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{request_key}__{extracted_at:%Y%m%dT%H%M%S%f}.json")
    # The payload is embedded as canonical JSON text (sorted keys) so identical content always
    # produces the same SHA-256 and unchanged re-extractions can be skipped.
    envelope = (
        '{"endpoint":' + json.dumps(endpoint)
        + ',"request_key":' + json.dumps(request_key)
        + ',"request_url":' + json.dumps(url)
        + ',"status_code":' + str(int(status_code))
        + ',"extracted_at":' + json.dumps(extracted_at.isoformat())
        + ',"run_id":' + json.dumps(run_id)
        + ',"payload_sha256":' + json.dumps(sha256(payload_text))
        + ',"payload":' + payload_text + "}"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(envelope)
    return path, len(envelope.encode("utf-8"))
