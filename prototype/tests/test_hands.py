"""The hands: the ice's hold moves the blade with a matching velocity (no launches from a pinned
blade), and the right trigger firms soft stickhandling hands up for a shot (sandbox.Physics._firmness)."""

import numpy as np
import pytest

import grab
import puck as pk
import sandbox
import stickspec
from test_puck import RINK, blade_at
from test_threes import _Quiet

SHAFT = np.array([0.0, np.sin(np.radians(45)), np.cos(np.radians(45))])   # leaning back, face +x


def _pinned_then_lifted(fast: bool) -> float:
    """A square blade pressed 20 cm into the ice (bowed to the limit and sliding up the hands) sweeps
    into a resting puck at 6 m/s while the hands lift 18 cm at 10 m/s; the blade stays on the ice
    throughout. Returns the puck's fastest upward speed (m/s)."""
    was = pk.FAST
    pk.FAST = fast
    try:
        sim = pk.Sim(pk.Params(), RINK, 70)
        sim.puck.spawn(np.array([0.3, 0.0]))
        top_vy, highest = 0.0, -1.0
        for k in range(1300):
            tt = k * 0.001
            y = -0.20 * min(tt / 1.0, 1.0)                      # 1 s pressing 20 cm into the ice
            x = 6.0 * max(tt - 1.15, 0.0)                        # a sweep at 6 m/s from 1.15 s...
            if tt > 1.18:
                y = -0.20 + 0.18 * min((tt - 1.18) / 0.018, 1.0)   # ... the hands rising 10 m/s as it hits
            bot, top = blade_at(x, 0.0, y=y)
            sim.step(0.001, bot, top, bot.mean(axis=0), SHAFT)
            top_vy = max(top_vy, float(sim.puck.vel[1]))
            if tt > 1.15:
                highest = max(highest, float((bot + sim.bend + sim.slide)[:, 1].min()))
        assert sim.puck.speed > 5.0                               # the blade hit it
        assert abs(highest) < 0.003                               # on the ice all along
        return top_vy
    finally:
        pk.FAST = was


@pytest.mark.parametrize("fast", [True, False])
def test_hands_lifting_out_of_the_ice_do_not_launch_the_puck(fast):
    """Free skates 2026-11-09/10: pucks went up at 14-20 m/s. The ice held the blade still while the
    contact used the hands' velocity: their lift went into the puck (through the face's friction)."""
    assert _pinned_then_lifted(fast) < 0.3                       # a square face on the ice: no lift


def test_the_fix_is_what_stops_it():
    """The same sweep with the hold's velocity left out (the old physics) lifts the puck."""
    was = pk.HOLD_JUMP
    pk.HOLD_JUMP = -1.0                                         # every hold rate counts as a reset: none
    try:
        assert _pinned_then_lifted(False) > 1.0
    finally:
        pk.HOLD_JUMP = was


def _physics(**values):
    spec = stickspec.from_height(1.73, "left")
    v = sandbox.Tuning.defaults(spec, grab.Fit(), pk.Params())
    v.update(values)
    play = sandbox.Play(sandbox.Tuning(spec, v))
    return play, sandbox.Physics(play, _Quiet(), _Quiet())


def test_soft_hands_until_you_squeeze_the_right_trigger():
    play, physics = _physics()
    fl = play.sim.flex
    assert fl.damping == pytest.approx(sandbox.HANDLE)        # released: stickhandling hands
    play.shoot = 1.0
    physics(0.0, {})
    assert fl.damping == pytest.approx(pk.Flex.DAMPING)       # squeezed: shooting hands
    play.shoot = 0.5
    physics(0.001, {})
    assert pk.Flex.DAMPING < fl.damping < sandbox.HANDLE      # in between, the harder the firmer
    play.shoot = 0.03                                           # a resting finger doesn't count
    physics(0.002, {})
    assert fl.damping == pytest.approx(sandbox.HANDLE)
    assert fl.c == pytest.approx(2 * fl.damping * np.sqrt(fl.k * fl.mass))


def test_stickhandling_hands_off_is_always_the_shooting_hands():
    play, physics = _physics(handle=0.0, hands=0.45)
    for s in (0.0, 1.0):
        play.shoot = s
        physics(s, {})
        assert play.sim.flex.damping == pytest.approx(0.45)


def _rebound(damping: float, v_in: float = 4.0) -> float:
    """A puck sent square at a still blade on the ice: how fast it comes back, over how fast it came."""
    sim = pk.Sim(pk.Params(), RINK, 75)
    sim.flex.damping = damping
    sim.flex.set_flex(75)
    sim.puck.spawn(np.array([0.5, 0.0]))
    sim.puck.vel = np.array([-v_in, 0.0, 0.0])
    bot, top = blade_at(0.0, 0.0)
    back = 0.0
    for _ in range(250):
        sim.step(0.001, bot, top, bot.mean(axis=0), np.array([-np.cos(np.radians(45)), np.sin(np.radians(45)), 0.0]))
        back = max(back, float(sim.puck.vel[0]))
    return back / v_in


def test_soft_hands_catch_a_pass_that_firm_hands_send_back():
    assert _rebound(pk.Flex.DAMPING) > 0.02                    # firm: it comes back off the blade
    assert _rebound(sandbox.HANDLE) < 0.5 * _rebound(pk.Flex.DAMPING)   # soft: far less
