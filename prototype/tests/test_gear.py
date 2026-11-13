"""Your own skates (sandbox.MyFeet) and the skate models (gear)."""

import numpy as np

import gear
import rig
import sandbox


def head(x=0.0, z=0.0, yaw_deg=0.0, down_deg=40.0, h=1.6):
    """A head pose in the room looking along -z turned left by yaw_deg, tipped down."""
    a, b = np.radians(yaw_deg), np.radians(-down_deg)
    Ry = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
    return Ry @ Rx, np.array([x, h, z])


def mid(feet):
    L, R = feet
    return (L[:3, 3] + R[:3, 3]) / 2


def toes(feet):
    L, R = feet
    f = L[:3, 0] + R[:3, 0]
    return f / np.linalg.norm(f)


def test_your_skates_stand_under_you_facing_where_you_look():
    feet = sandbox.MyFeet()
    rp = rig.Rig().at(0.0)
    out = feet.update(*head(), rp, 1 / 72)
    L, R = out
    assert np.allclose([L[1, 3], R[1, 3]], 0.0)                  # on the ice
    assert np.allclose(toes(out), [0, 0, -1], atol=1e-6)         # OpenXR looks along -z
    assert L[0, 3] < -0.1 and R[0, 3] > 0.1                      # left foot on your left (-x)
    assert 0.0 < mid(out)[2] < 0.15                              # under your neck, behind your eyes


def test_your_skates_stay_put_while_you_lean_then_step_after_you():
    feet = sandbox.MyFeet()
    rp = rig.Rig().at(0.0)
    start = mid(feet.update(*head(), rp, 1 / 72))
    for _ in range(72):
        out = feet.update(*head(z=-0.15), rp, 1 / 72)            # lean 15 cm forward
    assert np.allclose(mid(out), start)
    for _ in range(144):
        out = feet.update(*head(z=-0.6), rp, 1 / 72)             # walk 60 cm
    assert abs(mid(out)[2] - (-0.6 + 0.09)) < 0.09


def test_your_skates_follow_your_head_round_only_past_35_degrees():
    feet = sandbox.MyFeet()
    rp = rig.Rig().at(0.0)
    feet.update(*head(), rp, 1 / 72)
    out = feet.update(*head(yaw_deg=20), rp, 1 / 72)
    assert np.degrees(np.arccos(toes(out) @ [0, 0, -1])) < 1.0   # a glance: they stay
    out = feet.update(*head(yaw_deg=90), rp, 1 / 72)
    assert abs(np.degrees(np.arccos(toes(out) @ [0, 0, -1])) - 55) < 1.5   # turned round with you


def test_your_skates_turn_with_the_thumbstick_and_stay_on_the_ice_on_raised_skates():
    r = rig.Rig(lift=0.09)
    r.set_lift(0.0, 0.09)
    r.drive(0.01, np.zeros(3), np.radians(90), np.array([0.0, 1.6, 0.0]))
    rp = r.at(1.01)                                              # 1 s at 90 deg/s
    out = sandbox.MyFeet().update(*head(), rp, 1 / 72)
    assert np.allclose([out[0][1, 3], out[1][1, 3]], 0.0)
    assert abs(abs(toes(out) @ [1, 0, 0]) - 1.0) < 1e-6          # turned a quarter with the rig


def test_a_left_skate_is_the_right_one_mirrored():
    v = np.zeros((3, 10), dtype=np.float32)
    v[:, :3] = [[0, 0.02, 0], [0.1, 0.03, 0], [0, 0.04, 0.1]]
    v[:, 3:6] = [0, 1, 0]
    right = gear.Model(v, np.array([[0, 1, 2]], dtype=np.uint32), 0.09)
    left = right.mirrored()
    assert np.allclose(left.vertices[:, 1], -right.vertices[:, 1])
    assert np.allclose(left.vertices[:, 4], -1.0)
    assert left.index.tolist() == [[2, 1, 0]]                    # still facing out


def test_no_custom_skate_build_no_skates(tmp_path, monkeypatch):
    monkeypatch.setattr(gear, "SOURCE", tmp_path)
    monkeypatch.setattr(gear, "_LOADED", {})
    assert gear.skates("roller") is None
