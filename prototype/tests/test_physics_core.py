"""The compiled physics (physics_core.py) against the Python reference (puck.Sim.step_ref)."""

import copy

import numpy as np
import pytest

import puck as pk
import stickspec
import zone as zn


def _stick():
    spec = stickspec.from_height(stickspec.parse_height("5'8\""), "left")
    return spec, spec.edge(8), spec.edge(8, top=True)


def _rot_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def _state(sim):
    p, f = sim.puck, sim.flex
    out = [p.pos, p.vel, p._normal, sim.bend, sim.slide, f.v, f.x if f.x is not None else np.zeros(3)]
    flags = [p.in_net, p.goals, sim.on_ice, getattr(p, "cleared", False), getattr(p, "nets", 0), f.x is None]
    return np.concatenate([np.asarray(a, dtype=float).ravel() for a in out]), flags


def _drive(sim, path, check_every=1):
    """Step the reference along `path` [(rigid_bot, rigid_top, anchor, shaft) or None]; at each step,
    also step a copy with the compiled path and compare."""
    worst = 0.0
    hits = ice = 0
    for i, edges in enumerate(path):
        fast = copy.deepcopy(sim)
        args = (None, None) if edges is None else edges
        pk.FAST = False
        imp_ref = sim.step_ref(0.001, *args)
        pk.FAST = True
        imp_fast = fast._step_fast(0.001, *(args if edges is not None else (None, None, None, None)), 4)
        a, fa = _state(sim)
        b, fb = _state(fast)
        worst = max(worst, float(np.max(np.abs(a - b))), abs(imp_ref - imp_fast))
        assert fa == fb, (i, fa, fb)
        assert [e[0] for e in sim.puck.events] == [e[0] for e in fast.puck.events], i
        assert [e[0] for e in sim.events] == [e[0] for e in fast.events], i
        hits += imp_ref > 0
        ice += sum(e[0] == "ice" for e in sim.events)
        sim.puck.events.clear()
        sim.events.clear()
    return worst, hits, ice


def _path(spec, bot0, top0, puck_xz, n, speed, dip, yaw, rng):
    """The whole stick sweeping its blade through the puck at `speed`, dipping `dip` m into the ice."""
    R = _rot_y(yaw)
    bot, top = bot0 @ R.T, top0 @ R.T
    c = bot.mean(axis=0)
    base = np.array([puck_xz[0] - c[0], -bot[:, 1].min() + 0.004, puck_xz[1] - c[2]])
    out = []
    shaft = R @ spec.u
    for i in range(n):
        t = i * 0.001
        p = base + np.array([0.0, -dip * np.sin(np.pi * min(t / (n * 0.001), 1.0)),
                             -0.25 + speed * t]) + rng.normal(0, 0.0003, 3)
        out.append((bot + p, top + p, (bot + p).mean(axis=0) + np.array([0.0, 0.0, 0.0]), shaft))
    return out


@pytest.mark.parametrize("speed,dip,yaw", [(1.5, 0.0, 0.3), (4.0, 0.06, 1.2), (12.0, 0.15, 2.0), (25.0, 0.02, -0.7)])
def test_compiled_matches_the_reference_in_the_sandbox(speed, dip, yaw):
    spec, b0, t0 = _stick()
    rng = np.random.default_rng(int(speed * 10))
    params = pk.Params()
    sim = pk.Sim(params, pk.Rink(origin=np.array([0.2, 0.0, -0.1]), fwd=np.array([0.0, 0.0, -1.0])), spec.flex)
    sim.puck.spawn(np.array([0.3, -1.0]))
    path = _path(spec, b0, t0, (0.3, -1.0), 260, speed, dip, yaw, rng) + [None] * 400
    worst, hits, ice = _drive(sim, path)
    assert hits > 0, "the blade never hit the puck: the test is not testing contact"
    assert worst < 1e-9, worst


def test_compiled_matches_the_reference_in_the_zone_with_boards_and_net():
    spec, b0, t0 = _stick()
    rng = np.random.default_rng(3)
    params = pk.Params()
    zone = zn.Zone(np.array([1.0, 0.0, 2.0]), np.array([0.6, 0.0, 0.8]))
    sim = pk.Sim(params, pk.Rink(), spec.flex)
    sim.puck = zn.ZonePuck(params, zone)
    start = zone.to_world(-3.0, 0.0, 0.6)[[0, 2]]
    sim.puck.spawn(start)
    path = _path(spec, b0, t0, start, 200, 9.0, 0.05, 0.9, rng) + [None] * 2500
    worst, hits, _ = _drive(sim, path)
    assert hits > 0
    assert worst < 1e-9, worst


@pytest.mark.parametrize("start,vel", [((-2.0, pk.R), (12.0, 0.0)),        # rimmed around the corner
                                       ((0.2, 8.0), (0.0, -10.0)),          # into our net
                                       ((4.0, 2.8), (-10.0, 0.0)),          # into the side of the net
                                       ((0.0, 20.0), (0.0, 10.0))])         # out past the blue line
def test_compiled_puck_alone_follows_the_reference(start, vel):
    params = pk.Params(ice_mu=0.05, board_bounce=0.55)
    zone = zn.Zone(np.zeros(3), np.array([0.0, 0.0, 1.0]))
    sims = []
    for fast in (False, True):
        sim = pk.Sim(params, pk.Rink(), 70)
        sim.puck = zn.ZonePuck(params, zone)
        sim.puck.place(*start, *vel)
        sims.append(sim)
    for _ in range(3000):
        pk.FAST = False
        sims[0].step(0.001, None, None)
        pk.FAST = True
        sims[1].step(0.001, None, None)
    a, b = sims
    pk.FAST = True
    assert np.allclose(a.puck.pos, b.puck.pos, atol=1e-9) and np.allclose(a.puck.vel, b.puck.vel, atol=1e-9)
    assert [e[0] for e in a.puck.events] == [e[0] for e in b.puck.events]
    assert (a.puck.in_net, a.puck.nets, a.puck.cleared) == (b.puck.in_net, b.puck.nets, b.puck.cleared)


def test_the_compiled_step_is_fast():
    import time
    spec, b0, t0 = _stick()
    sim = pk.Sim(pk.Params(), pk.Rink(), spec.flex)
    sim.puck.spawn(np.array([0.3, -1.0]))
    path = _path(spec, b0, t0, (0.3, -1.0), 400, 3.0, 0.05, 0.4, np.random.default_rng(0))
    sim.step(0.001, *path[0])                                       # compile / load the cache
    t = time.perf_counter()
    for e in path:
        sim.step(0.001, *e)
    per = (time.perf_counter() - t) / len(path)
    assert per < 150e-6, f"{per * 1e6:.0f} us per step"
