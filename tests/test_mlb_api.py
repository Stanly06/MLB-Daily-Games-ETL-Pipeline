"""Unit tests for the pure extraction helpers (no network, no Spark).  Run: pytest tests/"""
import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "shared"))
import mlb_api as API  # noqa: E402


def test_date_chunks_cover_range_without_gaps():
    chunks = API.date_chunks(date(2025, 3, 1), date(2025, 5, 15), days=31)
    assert chunks[0][0] == date(2025, 3, 1) and chunks[-1][1] == date(2025, 5, 15)
    for (_, end), (start, _) in zip(chunks, chunks[1:]):
        assert (start - end).days == 1
    assert all((b - a).days <= 30 for a, b in chunks)


def test_season_window_is_capped_and_skips_future_seasons():
    assert API.season_window(2026, date(2026, 10, 23)) == (date(2026, 3, 1), date(2026, 10, 23))
    assert API.season_window(2027, date(2026, 10, 23)) is None


def test_games_from_schedule_flags_completed_and_keeps_duplicates():
    payload = {"dates": [
        {"date": "2025-04-05", "games": [{"gamePk": 1, "gameType": "R", "season": "2025", "officialDate": "2025-04-06",
                                          "status": {"codedGameState": "D"}, "venue": {"id": 5},
                                          "teams": {"home": {"team": {"id": 10}}, "away": {"team": {"id": 20}}}}]},
        {"date": "2025-04-06", "games": [{"gamePk": 1, "gameType": "R", "season": "2025", "officialDate": "2025-04-06",
                                          "status": {"codedGameState": "F"}, "venue": {"id": 5},
                                          "teams": {"home": {"team": {"id": 10}}, "away": {"team": {"id": 20}}}}]},
    ]}
    games = API.games_from_schedule(payload)
    assert [g["is_completed"] for g in games] == [False, True]
    assert games[1] == {"game_pk": 1, "game_type": "R", "season": 2025, "official_date": "2025-04-06",
                        "is_completed": True, "venue_id": 5, "home_team_id": 10, "away_team_id": 20}


def test_player_ids_from_boxscore():
    box = {"teams": {"home": {"players": {"ID1": {"person": {"id": 1}}, "ID2": {"person": {"id": 2}}}},
                     "away": {"players": {"ID3": {"person": {"id": 3}}}}}}
    assert API.player_ids_from_boxscore(box) == {1, 2, 3}


def test_canonical_json_hash_is_order_independent():
    assert API.sha256(API.canonical_json({"a": 1, "b": 2})) == API.sha256(API.canonical_json({"b": 2, "a": 1}))


def test_land_response_writes_parseable_envelope(tmp_path):
    payload = {"dates": [], "copyright": "MLB"}
    text = API.canonical_json(payload)
    path, size = API.land_response(str(tmp_path), "schedule", "2025-04-01_2025-04-02", "https://x", 200,
                                   text, datetime(2025, 4, 3, 5, 0, 0), "run-1")
    env = json.loads(Path(path).read_text())
    assert env["payload"] == payload and env["payload_sha256"] == API.sha256(text)
    assert "/schedule/2025/04/" in path and size == Path(path).stat().st_size


def test_chunked():
    assert API.chunked(list(range(5)), 2) == [[0, 1], [2, 3], [4]]
