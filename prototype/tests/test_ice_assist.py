"""The ice assist (puck.ice_assist, the "ice assist" setting): you can't feel the ice in VR, so a
blade hovering just over it rests on it."""

import numpy as np

import grab
import puck as pk
import sandbox
import stickspec
from test_threes import _Quiet


def test_the_blade_rests_on_the_ice_and_never_jumps():
    band = 0.12
    lows = np.linspace(-0.05, 0.4, 4501)                     # the hands' blade height, 0.1 mm apart
    h = np.array([low - pk.ice_assist(low, band) for low in lows])
    assert np.max(np.abs(np.diff(h))) < 1e-3                 # continuous: the physics sees no jump
    on = (lows > 0) & (lows <= band)
    assert np.allclose(h[on], -pk.ICE_PRESS)                 # on the ice (just pressed in)
    free = lows >= 2 * band
    assert np.allclose(h[free], lows[free])                  # lifted well up: where your hands hold it
    pressed = lows <= -pk.ICE_PRESS
    assert np.allclose(h[pressed], lows[pressed])            # pressed in: ice_rest's business
    assert np.all(np.diff(h[lows > band]) >= 0)              # lifting your hands lifts it
    assert pk.ice_assist(0.05, 0.0) == 0.0                   # 0 = off


def _hovering(ice_cm: float, height: float = 0.05):
    """The sandbox's physics with the stick held still, its blade `height` m over the ice."""
    spec = stickspec.from_height(1.73, "left")
    values = sandbox.Tuning.defaults(spec, grab.Fit(), pk.Params())
    values["ice"] = ice_cm
    play = sandbox.Play(sandbox.Tuning(spec, values))
    physics = sandbox.Physics(play, _Quiet(), _Quiet())
    play.squeeze["r"] = 1.0
    hand = (np.eye(3), np.array([0.25, 1.0, -0.3]))
    physics(0.0, {"r": hand})
    low = float((physics.edge_b @ physics.grab.R.T + physics.grab.p)[:, 1].min())
    hand = (hand[0], hand[1] + np.array([0.0, height - low, 0.0]))
    for i in range(1, 300):
        physics(i * 0.001, {"r": hand})
    return spec, play, physics, hand


def test_a_puck_slides_under_a_hovering_blade_unless_the_assist_rests_it_on_the_ice():
    for ice_cm, met in ((0, False), (12, True)):
        spec, play, physics, hand = _hovering(ice_cm)
        R, p = physics.grab.R, physics.grab.p
        mid = (physics.edge_b @ R.T + p).mean(axis=0)
        n = R @ spec.z_forehand
        n = np.array([n[0], 0.0, n[2]]) / np.hypot(n[0], n[2])
        pz = play.sim.puck
        pz.spawn((mid + 0.4 * n)[[0, 2]])                    # 40 cm off the forehand, sliding at it
        pz.vel = -2.0 * n
        for i in range(300, 800):
            physics(i * 0.001, {"r": hand})
        side = float((pz.pos - mid) @ n)
        if met:
            assert side > 0, ice_cm                          # it met the blade
        else:
            assert side < -0.2 and pz.speed > 1.5, ice_cm    # under it and on its way


def test_a_blade_lifted_well_up_is_where_your_hands_hold_it():
    _, play, physics, hand = _hovering(12, height=0.30)
    low = float((physics.edge_b @ physics.grab.R.T + physics.grab.p)[:, 1].min())
    assert abs(low - 0.30) < 1e-6
    assert not play.sim.on_ice
