"""Puck physics: sliding, blade hits (no tunnelling), soft floor, lift, goals."""

import numpy as np
import pytest

import puck as pk

RINK = pk.Rink()                    # start at the origin, net 6 m ahead along -z


def blade_at(x, z, y=0.0, face=(1.0, 0.0, 0.0), open_deg=0.0, length=0.29, height=0.075, n=8):
    """A straight blade whose face points along `face` (horizontal), bottom edge at height y.
    open_deg tilts the top of the blade back, away from the face (opens it)."""
    f = np.asarray(face, float)
    f /= np.linalg.norm(f)
    along = np.array([-f[2], 0.0, f[0]])                     # the blade runs across the face
    s = np.linspace(-length / 2, length / 2, n)
    bot = np.array([x, y, z]) + s[:, None] * along
    tilt = np.radians(open_deg)
    up = np.array([0.0, np.cos(tilt), 0.0]) - np.sin(tilt) * f
    top = bot + height * up
    return bot, top


def moved(blade, d):
    return blade[0] + d, blade[1] + d


def test_slides_and_stops():
    p = pk.Puck(pk.Params(ice_mu=0.02), RINK)
    p.spawn(np.array([0.0, 0.0]))
    p.vel = np.array([0.0, 0.0, -5.0])
    t = 0.0
    while p.speed > 0 and t < 30:
        p.step(0.001)
        t += 0.001
    # v^2 / (2 mu g) = 25 / (2 * 0.02 * 9.81) = 63.7 m, so it reaches the far boards first
    assert p.pos[1] == pytest.approx(pk.H / 2)
    q = pk.Puck(pk.Params(ice_mu=0.05), RINK)
    q.spawn(np.array([0.0, 0.0]))
    q.vel = np.array([1.0, 0.0, 0.0])
    for _ in range(3000):
        q.step(0.001)
    assert q.speed == 0.0
    assert q.pos[0] == pytest.approx(1.0 / (2 * 0.05 * 9.81), abs=0.01)


@pytest.mark.parametrize("blade_speed", [5.0, 15.0, 30.0])
def test_blade_hit_no_tunnelling(blade_speed):
    """A blade swept fast through a resting puck in one 1 ms step must still hit it."""
    p = pk.Puck(pk.Params(blade_pop=0.3, blade_grip=0.0), RINK)
    p.spawn(np.array([0.0, 0.0]))
    b0 = blade_at(-0.06, 0.0)                        # face pointing +x, just left of the puck
    dt = 0.001
    b1 = moved(b0, np.array([blade_speed * dt, 0, 0]))
    for _ in range(int(0.02 / dt)):
        p.step(dt, b0, b1)
        b0, b1 = b1, moved(b1, np.array([blade_speed * dt, 0, 0]))
    # a heavy blade: the puck leaves at (1 + pop) x the blade's speed, along the face normal
    assert p.vel[0] == pytest.approx(1.3 * blade_speed, rel=0.05)
    assert abs(p.vel[2]) < 0.05 * blade_speed


def test_blade_above_the_puck_misses_and_below_the_ice_still_hits():
    for y, hits in ((0.04, False), (-0.10, True), (-0.20, True)):
        p = pk.Puck(pk.Params(), RINK)
        p.spawn(np.array([0.0, 0.0]))
        b0 = blade_at(-0.06, 0.0, y=y)
        for _ in range(30):
            b1 = moved(b0, np.array([0.005, 0, 0]))
            p.step(0.001, b0, b1)
            b0 = b1
        assert (p.speed > 1.0) == hits, y


def test_open_face_lifts_the_puck():
    p = pk.Puck(pk.Params(blade_grip=0.0), RINK)
    p.spawn(np.array([0.0, 0.0]))
    b0 = blade_at(-0.06, 0.0, open_deg=35)
    for _ in range(20):
        b1 = moved(b0, np.array([0.015, 0, 0]))
        p.step(0.001, b0, b1)
        b0 = b1
    assert p.vel[1] > 2.0                            # airborne: a saucer or a lifted shot


def test_goal_and_posts():
    p = pk.Puck(pk.Params(ice_mu=0.0), RINK)
    p.spawn(np.array([0.0, -4.0]))
    p.vel = np.array([0.0, 0.0, -20.0])              # straight at the middle of the net
    for _ in range(500):
        p.step(0.001)
    assert p.goals == 1 and p.in_net and ("goal" in [e[0] for e in p.events])
    u, y, w = RINK.to_rink(p.pos)
    assert RINK.goal_dist <= w <= RINK.goal_dist + pk.GOAL_DEPTH
    wide = pk.Puck(pk.Params(ice_mu=0.0), RINK)
    wide.spawn(np.array([pk.GOAL_HALF_W + 0.3, -4.0]))
    wide.vel = np.array([0.0, 0.0, -20.0])
    for _ in range(500):
        wide.step(0.001)
    assert wide.goals == 0


def test_flex_stiffness_and_whip():
    f = pk.Flex(70)
    assert 8 < f.hz < 30                                 # a hand-held stick bends at roughly 10-30 Hz
    assert pk.Flex(100).k > f.k > pk.Flex(50).k          # higher flex rating = stiffer
    shaft, x, h, peak = np.array([0.0, 1.0, 0.0]), np.zeros(3), 0.00025, 0.0
    for i in range(int(0.3 / h)):
        v = np.array([10.0, 0, 0]) if i * h < 0.05 else np.zeros(3)
        x = x + v * h
        f.step(h, x, v, shaft)
        if i * h >= 0.05:
            peak = max(peak, f.bend(x)[0])
        assert abs(f.bend(x)[1]) < 1e-12                 # it bends across the shaft, never along it
    assert 0.04 < peak < 0.09                            # the whip: the blade swings on past the stop


@pytest.mark.parametrize("flex", [50, 70, 100])
def test_slap_with_flex(flex):
    sim = pk.Sim(pk.Params(blade_pop=0.3, blade_grip=0.0, ice_mu=0.0), RINK, flex)
    sim.puck.spawn(np.array([0.0, 0.0]))
    b = blade_at(-0.5, 0.0)
    for _ in range(60):
        b = moved(b, np.array([0.020, 0, 0]))           # 20 m/s
        sim.step(0.001, b[0], b[1], shaft=np.array([0.0, 1.0, 0.0]))
    assert 18 < sim.puck.speed < 32


def test_the_ice_holds_the_blade_and_the_shaft_bends():
    """Hands 5 cm too low: the blade stays on the ice and the shaft takes the bend."""
    sim = pk.Sim(pk.Params(), RINK, 70)
    shaft = np.array([-np.cos(np.radians(45)), np.sin(np.radians(45)), 0.0])
    b = blade_at(0.0, 0.0, y=0.05)                          # start 5 cm above the ice
    for k in range(400):
        y = 0.05 - 0.10 * min(k / 200, 1.0)                 # lower the hands until the rigid blade is 5 cm under
        bot, top = blade_at(0.0, 0.0, y=y)
        sim.step(0.001, bot, top, bot.mean(axis=0), shaft)
    low = (bot + sim.bend + sim.slide)[:, 1].min()
    assert low == pytest.approx(0.0, abs=0.003)             # on the ice, not through it
    assert np.linalg.norm(sim.bend) <= pk.ICE_BEND + 1e-6   # the shaft bows a little...
    assert np.linalg.norm(sim.slide) > 0.02                 # ...and the stick slides up for the rest
    assert [e[0] for e in sim.events].count("ice") == 1     # one touchdown


def test_a_stick_pressed_into_the_ice_does_not_fire_a_resting_puck():
    """Session 2: hands held low loaded the shaft, then let go and fired a resting puck at 6 m/s."""
    sim = pk.Sim(pk.Params(), RINK, 70)
    shaft = np.array([0.0, np.sin(np.radians(45)), np.cos(np.radians(45))])   # leaning back, face +x
    sim.puck.spawn(np.array([0.06, 0.0]))                    # resting against the face
    for k in range(3000):
        tt = k * 0.001
        y = -0.12 * min(tt / 2.0, 1.0)                       # 2 s pressing 12 cm into the ice...
        if tt > 2.5:
            y = -0.12 + 0.12 * min((tt - 2.5) / 0.05, 1.0)   # ...then the hands come up in 50 ms
        bot, top = blade_at(0.0, 0.0, y=y)
        sim.step(0.001, bot, top, bot.mean(axis=0), shaft)
    assert sim.puck.speed < 1.0


def test_forgiveness_reaches_further():
    hits = []
    for forgive in (0.0, 0.03):
        p = pk.Puck(pk.Params(forgiveness=forgive), RINK)
        p.spawn(np.array([0.0, 0.0]))
        b0 = blade_at(-0.08, 0.0)                           # 8 cm away, moving 1.5 cm closer: no touch
        b1 = moved(b0, np.array([0.015, 0, 0]))
        p.step(0.001, b0, b1)
        hits.append(p.speed > 0)
    assert hits == [False, True]


@pytest.mark.parametrize("depth", [0.02, 0.08, 0.30])
def test_ice_rest_never_leaves_the_blade_in_the_ice(depth):
    shaft = np.array([-np.cos(np.radians(45)), np.sin(np.radians(45)), 0.0])
    bend, slide = pk.ice_rest(np.zeros(3), -depth, shaft)
    lift = bend[1] + slide[1]
    assert lift == pytest.approx(depth, abs=1e-9)                  # back on the ice exactly
    assert np.linalg.norm(bend) <= pk.Flex.MAX_BEND + 1e-9         # the shaft bends only so far
    assert abs(bend @ shaft) < 1e-9                                # and only across the shaft
    if depth < 0.015:
        assert np.allclose(slide, 0)                               # a little: the flex takes it all
