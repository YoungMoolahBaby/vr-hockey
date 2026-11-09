"""Air drag on the puck (Params.air_k) and the closed forms the AI and the drills predict with
(puck.slide, slide_stop, speed_after, launch_speed, slide_time)."""

import math

import numpy as np
import pytest

import puck as pk


def _engine_slide(v0: float, seconds: float, **kw):
    """The engine (compiled when FAST) sliding a puck along open ice: times, distances, speeds."""
    params = pk.Params(**kw)
    sim = pk.Sim(params, pk.Rink(goal_dist=300, half_width=300, back=300), 70)
    sim.puck.spawn(np.array([0.0, 0.0]))
    sim.puck.vel = np.array([v0, 0.0, 0.0])
    ts, xs, vs = [], [], []
    for i in range(int(seconds * 1000)):
        sim.step(0.001, None, None)
        ts.append((i + 1) * 0.001)
        xs.append(float(sim.puck.pos[0]))
        vs.append(float(sim.puck.speed))
    return np.array(ts), np.array(xs), np.array(vs)


@pytest.mark.parametrize("v0", [3.0, 10.0, 20.0])
def test_the_engine_slides_as_the_closed_forms_say(v0):
    mu, k = 0.085, 0.0043
    a = mu * pk.G
    t_stop = math.atan(v0 * math.sqrt(k / a)) / math.sqrt(a * k)
    t, x, v = _engine_slide(v0, t_stop + 0.5, ice_mu=mu, air_k=k)
    assert v[-1] == 0.0
    assert abs(x[-1] - pk.slide_stop(v0, mu, k)) < 0.01 * pk.slide_stop(v0, mu, k) + 0.01
    for tt in (0.5, 1.0, 2.0):
        i = int(tt * 1000) - 1
        assert abs(x[i] - float(pk.slide(v0, tt, mu, k))) < 0.01
        assert abs(v[i] - pk.speed_after(v0, x[i], mu, k)) < 0.02
        assert abs(pk.slide_time(v0, x[i], mu, k) - tt) < 0.005


def test_drag_matters_for_hard_pucks_not_for_stickhandling():
    mu, k = 0.085, 0.0043
    assert abs(math.sqrt(mu * pk.G / k) - 14.0) < 0.2           # drag equals the ice's friction at ~14 m/s
    # a 15 m pass at 10 m/s: 8.7 m/s without the air, about 8.0 with it
    assert abs(pk.speed_after(10.0, 15.0, mu, 0.0) - 8.7) < 0.1
    assert abs(pk.speed_after(10.0, 15.0, mu, k) - 8.0) < 0.1
    # a stickhandled puck at 1.5 m/s over 0.5 m: under 1% different
    a, b = pk.speed_after(1.5, 0.5, mu, 0.0), pk.speed_after(1.5, 0.5, mu, k)
    assert abs(a - b) / a < 0.01


def test_the_closed_forms_invert_and_reduce_to_coulomb_without_drag():
    for mu, k in ((0.085, 0.0043), (0.085, 0.0), (0.0, 0.0043)):
        for v1, x in ((4.0, 12.0), (0.5, 3.0)):
            v0 = pk.launch_speed(v1, x, mu, k)
            assert abs(pk.speed_after(v0, x, mu, k) - v1) < 1e-9
            assert pk.slide_time(v0, x, mu, k) < math.inf
    # no drag: the Coulomb formulas
    assert abs(pk.slide_stop(10.0, 0.085, 0.0) - 100 / (2 * 0.085 * pk.G)) < 1e-9
    assert abs(float(pk.slide(10.0, 1.0, 0.085, 0.0)) - (10.0 - 0.5 * 0.085 * pk.G)) < 1e-9
    assert pk.slide_time(1.0, 50.0, 0.085, 0.0) == math.inf    # it stops short
    assert pk.slide_time(1.0, 50.0, 0.085, 0.0043) == math.inf


def test_a_puck_in_the_air_slows_too():
    params = pk.Params()
    sim = pk.Sim(params, pk.Rink(goal_dist=300, half_width=300, back=300), 70)
    sim.puck.spawn(np.array([0.0, 0.0]))
    sim.puck.pos = np.array([0.0, 1.0, 0.0])
    sim.puck.vel = np.array([30.0, 0.0, 0.0])
    for _ in range(100):                                        # 0.1 s of flight
        sim.step(0.001, None, None)
    vx = float(sim.puck.vel[0])
    assert abs(vx - 30.0 / (1 + params.air_k * 30.0 * 0.1)) < 0.05      # dv/dt = -k v^2
