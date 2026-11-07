"""Stick-model maths, then a synthetic recording with known truth that analyze.py must recover."""

import json

import numpy as np
import pytest

import analyze
import stickmath as sm
import synth


def _hands_on_stick(n=2000, seed=0):
    """Two hands rigidly on a moving stick, heel at the stick origin. Returns poses + true heel."""
    rng = np.random.default_rng(seed)
    t = np.arange(n) / 1000
    R_ws = synth.rot([0, 1, 0], 0.5 * np.sin(2 * np.pi * 1.3 * t)) @ synth.rot([1, 0, 0], 0.3 * np.sin(2 * np.pi * 0.7 * t))
    p_ws = np.stack([0.2 * np.sin(2 * np.pi * t), 0.02 * np.sin(5 * t) ** 2, 0.3 * np.cos(2 * np.pi * 0.5 * t)], axis=1)
    gt, gb = synth.expmap(rng.normal(size=(2, 3)))
    Rt, pt = R_ws @ gt, p_ws + R_ws @ (1.4 * synth.U)
    Rb, pb = R_ws @ gb, p_ws + R_ws @ (0.8 * synth.U)
    return t, Rt, pt, Rb, pb, p_ws


def test_quat_roundtrip():
    R = synth.expmap(np.random.default_rng(1).normal(size=(50, 3)))
    assert np.allclose(sm.quat_to_mat(sm.mat_to_quat(R)), R, atol=1e-12)


def test_stance_fit_and_models_exact():
    """Hands exactly on the shaft: every model must put the heel exactly where it is."""
    t, Rt, pt, Rb, pb, heel = _hands_on_stick()
    still = slice(0, 1)
    # a stance with the heel on the ice: shift everything so the first heel sits at y = 0
    off = np.array([0, heel[0, 1], 0])
    pt, pb, heel = pt - off, pb - off, heel - off
    cal = sm.calibrate_stance(Rt[still].repeat(50, 0), pt[still].repeat(50, 0),
                              Rb[still].repeat(50, 0), pb[still].repeat(50, 0), "r")
    assert cal.length_m == pytest.approx(1.4, abs=1e-9)
    assert cal.hand_sep_m == pytest.approx(0.6, abs=1e-9)
    for model in sm.MODELS:
        assert np.allclose(sm.blade_heel(model, cal, Rt, pt, Rb, pb), heel, atol=1e-9), model


def test_heel_velocity_matches_numerical_derivative():
    t, Rt, pt, Rb, pb, _ = _hands_on_stick()
    # make the hands not rigid so the models disagree and every term matters
    Rb = Rb @ synth.rot([0, 0, 1], 0.2 * np.sin(2 * np.pi * 2 * t))
    pb = pb + np.stack([0.05 * np.sin(2 * np.pi * 3 * t), 0 * t, 0 * t], axis=1)
    vt, vb = np.gradient(pt, t, axis=0), np.gradient(pb, t, axis=0)
    wt, wb = synth.angular_velocity(Rt, t), synth.angular_velocity(Rb, t)
    cal = sm.calibrate_stance(Rt[:50], pt[:50] - [0, pt[0, 1] - 1.0, 0], Rb[:50], pb[:50] - [0, pt[0, 1] - 1.0, 0], "r")
    for model in sm.MODELS:
        h = sm.blade_heel(model, cal, Rt, pt, Rb, pb)
        num = np.gradient(h, t, axis=0)
        ana = sm.heel_velocity(model, cal, Rt, pt, vt, wt, Rb, pb, vb, wb)
        err = np.linalg.norm((num - ana)[5:-5], axis=1).max()
        assert err < 0.01, f"{model}: {err:.4f} m/s"


def test_move_noise_without_noise_is_identity():
    R = np.repeat(synth.expmap(np.array([[0.3, -0.2, 0.9]])), 20, axis=0)
    p = np.tile([0.4, 0.75, -0.6], (20, 1))
    to_R, to_p = synth.expmap(np.array([[1.0, 0.5, -0.2]]))[0], np.array([-0.5, 1.1, 0.2])
    Rn, pn = sm.move_noise(R, p, to_R, to_p)
    assert np.allclose(Rn, to_R) and np.allclose(pn, to_p)


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    out = tmp_path_factory.mktemp("synth")
    truth = synth.synthesize(out, seed=3)
    S = analyze.analyze(out, make_plots=False)
    return truth, S


def test_stick_fit(run):
    truth, S = run
    st = S["stick"]
    assert st["top"] == truth["top"] and not st["problems"]
    assert st["length_m"] == pytest.approx(truth["length_m"], abs=0.01)
    assert st["hand_sep_m"] == pytest.approx(truth["hand_sep_m"], abs=0.01)


def test_noise_rate_and_height(run):
    truth, S = run
    for d, T in truth["controllers"].items():
        assert S["controllers"][d]["fresh_pose_hz"] == pytest.approx(T["update_hz"], rel=0.05)
        assert S["controllers"][d]["hand"] == T["hand"]
    for model, T in truth["models"].items():
        M = S["models"][model]
        assert M["rest_heel_std_mm"] == pytest.approx(T["rest_heel_std_mm"], rel=0.15), model
        assert M["stickhandle"]["height_median_mm"] == pytest.approx(T["stickhandle_height_median_mm"], abs=3.0), model


def test_shot_speeds(run):
    truth, S = run
    for ph, peaks in truth["shots"].items():
        shots = S["shots"][ph]["shots"]
        assert len(shots) == len(peaks)
        for s, true_peak in zip(shots, peaks):
            for model in ("two_hand", "top_hand", "blend"):
                assert s["speed"][model]["runtime"] == pytest.approx(true_peak, rel=0.03), model
                assert s["speed"][model]["positions"] == pytest.approx(true_peak, rel=0.05), model


def test_verdicts(run):
    truth, S = run
    V = S["verdict"]
    # the synthetic bottom hand drops out heads-up and in every swing; its wobble and slide break bottom_hand
    assert V["tracking"]["overall"] == "NO-GO"
    assert V["tracking"]["ratings"]["heads_up_tracked_pct"] == "bad"
    assert V["bottom_hand"]["ratings"]["on_ice_pct"] == "bad"
    assert V["recommended_model"] in ("top_hand", "blend", "two_hand")
    json.dumps(S, default=float)
