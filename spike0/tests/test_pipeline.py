"""A synthetic recording with known truth: analyze.py must recover it."""

import json

import pytest

import analyze
import synth


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    out = tmp_path_factory.mktemp("synth")
    truth = synth.synthesize(out, seed=3)
    return truth, analyze.analyze(out, make_plots=False)


def test_held_as_asked(run):
    _, S = run
    for ph in ("stickhandle", "heads_up", "one_hand", "wrist_shots", "slap_shots"):
        assert S["phases"][ph]["held_as_expected_pct"] > 99, ph
    assert S["phases"]["one_hand"]["state_pct"]["bottom"] > 99


def test_blade_height(run):
    truth, S = run
    for ph in ("stickhandle", "one_hand"):
        P, T = S["phases"][ph], truth["phases"][ph]
        assert P["height_median_mm"] == pytest.approx(T["height_median_mm"], abs=4.0), ph
        assert P["near_ice_pct"] == pytest.approx(T["near_ice_pct"], abs=5.0), ph
    assert "lift_p90_mm" in S["verdict"]


def test_rates_and_tracking(run):
    truth, S = run
    for d, T in truth["controllers"].items():
        assert S["controllers"][d]["fresh_pose_hz"] == pytest.approx(T["update_hz"], rel=0.05)
        assert S["controllers"][d]["hand"] == T["hand"]
    # the synthetic bottom hand drops out heads-up and in every swing
    assert S["verdict"]["overall"] == "NO-GO"
    assert S["verdict"]["ratings"]["heads_up_tracked_pct"] == "bad"


def test_shot_speeds(run):
    truth, S = run
    for ph, peaks in truth["shots"].items():
        shots = S["shots"][ph]["shots"]
        assert len(shots) == len(peaks)
        for s, true_peak in zip(shots, peaks):
            assert s["blade_speed_ms"] == pytest.approx(true_peak, rel=0.05)
            assert s["held"] == "both"
    json.dumps(S, default=float)
