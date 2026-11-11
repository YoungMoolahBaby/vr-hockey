"""reports/Shot release.md: the shot call from free flight (shotcall.py, change 4) and the blade's
contact velocity from a window of samples (sandbox.Physics._velocity, change 1)."""

import numpy as np
import pytest

import grab
import puck as pk
import sandbox
import shotcall
import stickspec
from test_threes import _Quiet


def _flight(sc, t0, v, ms, dt=0.001, drag=0.0):
    """Free flight at velocity v for ms milliseconds; returns the first call made."""
    v = np.array(v, dtype=float)
    for k in range(ms):
        call = sc.tick(t0 + k * dt, 0.0, v * (1 - drag * k))
        if call is not None:
            return call
    return None


def test_a_shot_is_called_from_its_free_flight():
    sc = shotcall.ShotCall()
    for k in range(20):                                     # 20 ms on the blade, speeding up to 20 m/s
        sc.tick(k * 0.001, 3.0, [k, 0.0, 0.0])
    call = _flight(sc, 0.020, [20.0, 2.0, 0.0], 80)
    assert call is not None
    assert call["ms"] == pytest.approx(np.hypot(20, 2), abs=0.05)
    assert call["vy"] == pytest.approx(2.0, abs=0.01) and call["angle"] == pytest.approx(5.7, abs=0.1)
    assert _flight(sc, 0.2, [20.0, 2.0, 0.0], 80) is None   # one call per shot


def test_a_touch_in_flight_starts_free_flight_again():
    sc = shotcall.ShotCall()
    sc.tick(0.0, 3.0, [15.0, 0.0, 0.0])
    assert _flight(sc, 0.001, [15.0, 0.0, 0.0], 30) is None  # not yet: 50 ms of free flight first
    sc.tick(0.031, 3.0, [25.0, 0.0, 0.0])                   # the blade catches it again, harder
    call = _flight(sc, 0.032, [25.0, 0.0, 0.0], 80)
    assert call["ms"] == pytest.approx(25.0, abs=0.01)      # the speed it left with the last time


def test_no_call_when_it_hits_something_or_is_slow():
    sc = shotcall.ShotCall()
    sc.tick(0.0, 3.0, [20.0, 0.0, 0.0])
    v = [np.array([20.0, 0, 0])] * 30 + [np.array([-6.0, 0, 0])] * 40    # off the boards after 30 ms
    calls = [sc.tick(0.006 + k * 0.001, 0.0, vv) for k, vv in enumerate(v)]
    assert all(c is None for c in calls)
    sc = shotcall.ShotCall()
    sc.tick(0.0, 3.0, [6.5, 0.0, 0.0])                      # armed, but 14.5 mph...
    assert _flight(sc, 0.001, [5.0, 0.0, 0.0], 80) is None  # ... and away at 5 m/s: under 12 mph
    sc = shotcall.ShotCall()
    sc.tick(0.0, 1.0, [20.0, 0.0, 0.0])                     # a soft touch doesn't arm a call
    assert _flight(sc, 0.001, [20.0, 0.0, 0.0], 80) is None


@pytest.fixture
def window():
    was = sandbox.VEL_WINDOW_S
    sandbox.VEL_WINDOW_S = 0.004                          # off by default; the fit itself, when it's on
    yield
    sandbox.VEL_WINDOW_S = was


def _physics():
    spec = stickspec.from_height(1.73, "left")
    play = sandbox.Play(sandbox.Tuning(spec, sandbox.Tuning.defaults(spec, grab.Fit(), pk.Params())))
    return play, sandbox.Physics(play, _Quiet(), _Quiet())


def test_the_contact_velocity_is_fitted_over_a_few_ms(window):
    play, ph = _physics()
    rng = np.random.default_rng(1)
    v = np.array([12.0, 0.0, -5.0])
    p0 = np.zeros((17, 3))
    t, fits = 0.0, []
    for k in range(40):
        t += 0.001 + rng.uniform(-0.0003, 0.0003)           # irregular sample times
        if k % 7 == 3:
            continue                                        # (and a repeated pose now and then:
        ph._t = t                                           #  the fit still sees the true times)
        X = p0 + v * t
        out = ph._velocity(X[:8], X[8:16], X[16])
        if out is not None:
            fits.append(out)
    fits = np.array(fits)
    assert np.allclose(fits, v, atol=1e-6)                  # a steady motion: exactly its velocity
    sandbox_window = sandbox.VEL_WINDOW_S
    try:
        sandbox.VEL_WINDOW_S = 0.0
        assert ph._velocity(p0[:8], p0[8:16], p0[16]) is None   # 0 = one sample's difference (the sim's)
    finally:
        sandbox.VEL_WINDOW_S = sandbox_window


def test_noise_in_the_hands_reaches_the_contact_velocity_far_less(window):
    play, ph = _physics()
    rng = np.random.default_rng(2)
    v = np.array([20.0, 0.0, 0.0])
    t, fit, diff, last = 0.0, [], [], None
    for k in range(400):
        t += 0.001
        ph._t = t
        X = np.zeros((17, 3)) + v * t + rng.normal(0, 0.001, (1, 3))   # 1 mm of jitter
        out = ph._velocity(X[:8], X[8:16], X[16])
        if out is not None and k > 10:
            fit.append(out[16, 0])
            diff.append((X[16, 0] - last) / 0.001)
        last = X[16, 0]
    assert np.std(fit) < 0.25 * np.std(diff)                # 4 ms: over 4x less noise than one sample's
