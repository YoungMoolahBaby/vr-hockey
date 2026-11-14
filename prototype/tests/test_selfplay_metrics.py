"""selfplay_metrics.py: a self-play game recorded the way game.py records one, read back and scored."""

import json

import selfplay_metrics as sm


def test_a_short_self_play_game_is_recorded_and_scored(tmp_path):
    meta = sm.play_one((1, 40.0, str(tmp_path / "s1"), 3.0, []))
    assert (tmp_path / "s1" / "ai.csv").exists() and (tmp_path / "s1" / "events.jsonl").exists()
    assert meta["ai_tick_ms"][0] > 0
    kinds = {json.loads(line)["event"] for line in (tmp_path / "s1" / "events.jsonl").read_text().splitlines()}
    assert {"rink", "drop", "take", "pass"} <= kinds
    assert sm.runs_in(tmp_path) == [tmp_path / "s1"]
    R = sm.score(sm.runs_in(tmp_path))
    assert R["games"] == 1 and abs(R["vmax"] - 0.95 * 3.0) < 1e-6
    assert R["counts"]["passes"] > 3 and R["counts"]["touches"] > 5
    assert 0.0 <= R["completion"] <= 1.0 and 0.0 < R["mean_speed"] <= 1.0
    assert 0.9 < R["carry_p90"] <= 0.96                     # a carrier skates at 0.95 of the top
    assert R["to_you"] is None                              # no you in self-play
    text = sm.table(R)
    assert "Pass completion" in text and "baseline" in text


def test_a_constant_can_be_set_for_an_ab(tmp_path):
    carry = sm.th.CARRY
    meta = sm.play_one((2, 25.0, str(tmp_path / "s2"), 3.0, [("CARRY", 0.8)]))
    assert sm.th.CARRY == carry and meta["set"] == {"CARRY": 0.8}     # only for that game
    R = sm.score([tmp_path / "s2"])
    assert 0.75 < R["carry_p90"] < 0.85                     # (just after a take he can still be going faster)
