"""Stick sizing and the grab rules."""

import numpy as np
import pytest

import grab
import stickmath as sm
import stickspec

SPEC = stickspec.from_height(stickspec.parse_height("5'8\""), "left")
EZ = np.array([0.0, 0.0, 1.0])


def test_parse_height():
    assert stickspec.parse_height("5'8\"") == pytest.approx(68 * 0.0254)
    assert stickspec.parse_height("5'8") == pytest.approx(68 * 0.0254)
    assert stickspec.parse_height("68in") == pytest.approx(68 * 0.0254)
    assert stickspec.parse_height("173cm") == pytest.approx(1.73)
    assert stickspec.parse_height("1.73") == pytest.approx(1.73)


def test_sizing():
    assert SPEC.length_m / stickspec.INCH == pytest.approx(57.1, abs=0.1)     # CCM: 5'2"-5'10" -> 57"
    assert SPEC.shaft_angle_deg == 45.0
    assert stickspec.from_height(1.73, lie=6).shaft_angle_deg == 47.0
    assert SPEC.top_hand == "r" and stickspec.from_height(1.73, "right").top_hand == "l"
    # left and right blades are mirror images: the toe curls toward the forehand
    right = stickspec.from_height(1.73, "right")
    assert SPEC.toe[2] > 0 and right.toe[2] < 0 and SPEC.toe[2] == pytest.approx(-right.toe[2])


def test_hold_keeps_the_grip_in_the_hand():
    for fit in (grab.Fit(), grab.Fit(35, -20, 10)):
        R_ts, p_ts = grab.hold(SPEC, fit)
        assert np.allclose(R_ts @ SPEC.grip + p_ts, 0, atol=1e-12)
        assert np.allclose(R_ts @ R_ts.T, np.eye(3), atol=1e-12)
    R_ts, _ = grab.hold(SPEC, grab.Fit())
    assert np.allclose(R_ts @ -SPEC.u, -EZ)                    # down the shaft = out of the thumb side
    R_roll, _ = grab.hold(SPEC, grab.Fit(roll_deg=40))
    assert np.allclose(R_roll @ SPEC.u, R_ts @ SPEC.u)         # roll turns the blade, not the shaft


def test_held_hysteresis():
    assert grab.held(np.array([0, 0.4, 0.55, 0.3, 0.4, 0.3])).tolist() == [False, False, True, True, True, True]


def test_a_slip_is_not_a_release():
    t = np.arange(1000) / 1000
    sq = np.ones(1000)
    sq[100:250] = 0.0                                   # a 150 ms slip: still holding
    sq[500:800] = 0.0                                   # a 300 ms release: let go after 200 ms
    h = grab.held(sq, t, release_s=0.2)
    assert h[100:250].all() and h[250:500].all()
    assert h[500:700].all() and not h[700:800].any()
    assert h[800:].all()


def test_states():
    T, F = True, False
    top = [F, T, T, F, F, T, F, F]
    bot = [T, F, T, T, F, F, F, T]
    # nothing to grab before the first hold; after that, letting go keeps the stick in the last
    # hand, and the bottom hand alone takes it from wherever it is
    assert grab.states(np.array(top), np.array(bot)).tolist() == [
        grab.NONE, grab.TOP, grab.BOTH, grab.BOTTOM, grab.LOOSE_BOTTOM, grab.TOP, grab.LOOSE_TOP, grab.BOTTOM]


def test_letting_go_keeps_the_stick_in_the_last_hand():
    fit, R_s, p_s, Rt, pt, Rb, pb = _session(600)
    n = len(R_s)
    top, bot = np.ones(n, bool), np.ones(n, bool)
    top[200:], bot[200:] = False, False                         # both grips released at 200
    state = grab.states(top, bot)
    assert set(state[200:]) == {grab.LOOSE_TOP}
    ok = np.ones(n, bool)
    R, p = grab.replay(SPEC, fit, state, Rt, pt, Rb, pb, ok, ok)
    # no jump at the release, then rigid in the top hand where it was
    assert np.allclose(p[200], p[199], atol=5e-3)
    rel_R = np.einsum("nji,njk->nik", Rt[200:], R[200:])
    rel_p = np.einsum("nji,nj->ni", Rt[200:], p[200:] - pt[200:])
    assert np.allclose(rel_R, rel_R[0], atol=1e-9) and np.allclose(rel_p, rel_p[0], atol=1e-9)


def _session(n=3000, seed=0):
    """A stick moving smoothly; the top hand holds it per the fit, the bottom hand rides the shaft."""
    rng = np.random.default_rng(seed)
    t = np.arange(n) / 1000
    R_s = sm.expmap(np.stack([0.3 * np.sin(2 * t), 0.5 * np.sin(1.3 * t), 0.2 * np.cos(0.7 * t)], axis=1))
    p_s = np.stack([0.2 * np.sin(3 * t), 0.01 * np.sin(5 * t), 0.3 * np.cos(2 * t)], axis=1)
    fit = grab.Fit(25, -10, 8)
    R_ts, p_ts = grab.hold(SPEC, fit)
    Rt = R_s @ R_ts.T
    pt = p_s - np.einsum("nij,j->ni", Rt, p_ts)
    Gb = sm.expmap(rng.normal(size=(1, 3)))[0]
    Rb = R_s @ Gb
    s = 0.8 + 0.05 * np.sin(4 * t)                              # sliding along the shaft
    pb = p_s + np.einsum("nij,nj->ni", R_s, s[:, None] * SPEC.u)
    return fit, R_s, p_s, Rt, pt, Rb, pb


def test_replay_is_exact_when_the_hands_hold_the_stick():
    fit, R_s, p_s, Rt, pt, Rb, pb = _session()
    n = len(R_s)
    top = np.ones(n, bool)
    top[1000:2000] = False                                      # top hand off in the middle
    # while the top hand is off, the true stick rides rigidly in the bottom hand (no sliding)
    Rb[1000:2000] = R_s[1000:2000] @ (Rb[999].T @ R_s[999]).T
    pb[1000:2000] = p_s[1000:2000] + np.einsum("nij,j->ni", R_s[1000:2000], R_s[999].T @ (pb[999] - p_s[999]))
    state = grab.states(top, np.ones(n, bool))
    assert set(state[:1000]) == {grab.BOTH} and set(state[1000:2000]) == {grab.BOTTOM}
    ok = np.ones(n, bool)
    R, p = grab.replay(SPEC, fit, state, Rt, pt, Rb, pb, ok, ok)
    assert np.allclose(R, R_s, atol=1e-9) and np.allclose(p, p_s, atol=1e-9)


def test_live_step_matches_replay():
    fit, R_s, p_s, Rt, pt, Rb, pb = _session(3600)
    n = len(R_s)
    i = np.arange(n)                                    # releases last > 0.2 s, so each one counts
    sq_t = (((0 <= i) & (i < 600)) | ((1200 <= i) & (i < 1800)) | ((2400 <= i) & (i < 2700))).astype(float)
    sq_b = (((300 <= i) & (i < 900)) | ((1500 <= i) & (i < 1800)) | (3300 <= i)).astype(float)
    state = grab.states(grab.held(sq_t, release_s=grab.RELEASE_TOP_S), grab.held(sq_b, release_s=grab.RELEASE_BOTTOM_S))
    # every state shows up: top, both, bottom, loose bottom, loose top
    assert {grab.TOP, grab.BOTH, grab.BOTTOM, grab.LOOSE_BOTTOM, grab.LOOSE_TOP} <= set(state.tolist())
    ok = np.ones(n, bool)
    R, p = grab.replay(SPEC, fit, state, Rt, pt, Rb, pb, ok, ok)
    g = grab.Grab(SPEC, fit)
    for i in range(n):
        s, Ri, pi = g.step((Rt[i], pt[i]), (Rb[i], pb[i]), sq_t[i], sq_b[i], i / 1000)
        assert s == state[i]
        if not np.isnan(p[i, 0]):
            assert np.allclose(Ri, R[i], atol=1e-9) and np.allclose(pi, p[i], atol=1e-9), i


def test_curve_depth_is_the_gap_to_a_straight_edge():
    """A 1/2" curve: the biggest gap between the blade and a straight edge from heel to toe."""
    for depth_in, shape in ((0.5, 2.5), (0.75, 2.0), (0.25, 4.0)):
        spec = SPEC.with_(curve_depth_m=depth_in * stickspec.INCH, curve_shape=shape)
        e = spec.edge(400)[:, [0, 2]]
        chord = e[-1] - e[0]
        n = np.array([-chord[1], chord[0]]) / np.linalg.norm(chord)
        gap = np.max(np.abs((e - e[0]) @ n))
        assert gap == pytest.approx(depth_in * stickspec.INCH, rel=0.01)


def test_the_shaft_runs_through_both_hands():
    """Grab with the bottom hand 6 cm off the shaft: the stick turns so its axis passes through it."""
    fit, R_s, p_s, Rt, pt, Rb, pb = _session(400)
    off = np.cross(SPEC.u, [0.0, 0.0, 1.0])
    off /= np.linalg.norm(off)
    pb = pb + np.einsum("nij,j->ni", R_s, 0.06 * off)       # the bottom hand beside the shaft
    n = len(R_s)
    state = grab.states(np.ones(n, bool), np.ones(n, bool))
    ok = np.ones(n, bool)
    R, p = grab.replay(SPEC, fit, state, Rt, pt, Rb, pb, ok, ok)
    for i in (200, 399):                                    # after the ease-in
        axis = R[i] @ SPEC.u
        to_b = pb[i] - (p[i] + R[i] @ SPEC.grip)
        miss = np.linalg.norm(to_b - (to_b @ axis) * axis)
        assert miss < 1e-6, i
