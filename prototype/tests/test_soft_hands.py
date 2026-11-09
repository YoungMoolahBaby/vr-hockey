"""Soft hands (physics_core.cradle, Params.magnet): a puck on the blade rides it while you handle,
and comes off as hit when you shoot. Off by default (the sandbox, the drills)."""

import copy

import numpy as np
import pytest

import physics_core as pc
import puck as pk
import stickspec
from test_physics_core import _drive, _path, _rot_y, _stick

YAW = 0.3                    # a blade square to its sweep (+z)


def _sweep(spec, b0, t0, profile, puck_xz=(0.0, 0.0), yaw=YAW):
    """The blade on the ice, moving along +z with speed profile(t) (m/s), from 0.25 m behind the puck."""
    R = _rot_y(yaw)
    bot, top = b0 @ R.T, t0 @ R.T
    c = bot.mean(axis=0)
    base = np.array([puck_xz[0] - c[0], -bot[:, 1].min() + 0.004, puck_xz[1] - c[2] - 0.25])
    shaft = R @ spec.u
    z, out = 0.0, []
    for i in range(len(profile)):
        z += profile[i] * 0.001
        p = base + np.array([0.0, 0.0, z])
        out.append((bot + p, top + p, (bot + p).mean(axis=0), shaft))
    return out


def _run(magnet, path, release=4.0):
    spec, _, _ = _stick()
    params = pk.Params(magnet=magnet, release=release)
    sim = pk.Sim(params, pk.Rink(goal_dist=40, half_width=30, back=30), spec.flex)
    sim.puck.spawn(np.array([0.0, 0.0]))
    for e in path:
        sim.step(0.001, *e)
    blade = path[-1][0].mean(axis=0)
    return sim.puck, float(np.linalg.norm((sim.puck.pos - blade)[[0, 2]]))


def test_a_handled_puck_stays_on_the_blade_when_it_stops():
    spec, b0, t0 = _stick()
    # push it at 2.5 m/s for 0.3 s, then stop dead and hold still for 0.4 s
    path = _sweep(spec, b0, t0, [2.5] * 300 + [0.0] * 400)
    honest, d0 = _run(0.0, path)
    soft, d1 = _run(0.7, path)
    assert d0 > 0.4 and honest.speed > 1.0          # honest physics: it slides off the blade
    assert d1 < 0.12 and soft.speed < 0.2            # soft hands: it stays in the cup


def test_a_shot_comes_off_as_hard():
    spec, b0, t0 = _stick()
    # a wrist shot: the blade starts against the puck and accelerates to 15 m/s over 60 ms
    ramp = list(np.linspace(0.3, 15.0, 60))
    path = _sweep(spec, b0, t0, [0.0] * 50 + [1.2] * 160 + ramp + [15.0] * 20 + [0.0] * 50)
    honest, _ = _run(0.0, path)
    soft, _ = _run(0.7, path)
    assert honest.speed > 10.0
    assert soft.speed > 0.95 * honest.speed


def test_skating_with_it_is_handling_not_shooting():
    """The blade moving at 6 m/s because you skate (the body moves too) is handling: cradled.
    The same blade with you standing still is a shot: left alone."""
    bot = np.array([[-0.15, 0.0, 0.0], [0.0, 0.0, 0.0], [0.15, 0.0, 0.0]])
    vb = np.tile([0.0, 0.0, 6.0], (3, 1))
    pos0 = np.array([0.0, pk.H / 2, pk.R + 0.008])
    vel0 = np.array([0.0, 0.0, 7.0])                 # a little faster than the blade: leaving it
    skating = np.array([0.0, 6.0, 0.0, 0.0, 0.0])
    standing = np.zeros(5)
    for body, cradled in ((skating, True), (standing, False)):
        pos, vel = pos0.copy(), vel0.copy()
        pc.cradle.py_func(0.00025, pos, vel, bot, vb, 0.7, 4.5, 0.012, body)
        assert (vel[2] < 7.0) == cradled


def test_compiled_matches_the_reference_with_soft_hands():
    spec, b0, t0 = _stick()
    rng = np.random.default_rng(5)
    for speed, yaw in ((1.5, 0.3), (3.0, 1.2), (12.0, 0.3)):
        sim = pk.Sim(pk.Params(magnet=0.8), pk.Rink(), spec.flex)
        sim.puck.spawn(np.array([0.3, -1.0]))
        path = _path(spec, b0, t0, (0.3, -1.0), 300, speed, 0.0, yaw, rng) + [None] * 200
        worst, hits, _ = _drive(sim, path)
        # a soft blade often catches it before it strikes it (no hit): it was carried all the same
        assert np.linalg.norm(sim.puck.pos[[0, 2]] - [0.3, -1.0]) > 0.05
        assert worst < 1e-9, (speed, worst)


def test_off_by_default():
    assert pk.Params().magnet == 0.0


def test_a_retreating_blade_leaves_the_puck_where_it_is():
    """No pull: a puck resting against the face stays put when the blade goes back for another
    touch (it isn't stuck to the stick)."""
    spec, b0, t0 = _stick()
    # bring the blade gently up to the puck and stop against it, then pull back at 2 m/s
    still = _sweep(spec, b0, t0, [0.5] * 420 + [0.0] * 300)
    back = _sweep(spec, b0, t0, [0.5] * 420 + [0.0] * 100 + [-2.0] * 200)
    stayed, _ = _run(0.7, still)
    pulled, d = _run(0.7, back)
    assert pulled.speed < 0.3                                # it didn't come back with the blade
    assert np.linalg.norm(pulled.pos - stayed.pos) < 0.02    # it's where it was when the blade left it
    assert d > 0.3                                           # and the blade is well away from it
