"""Line-drawn skaters: the batched drawing matches segment-by-segment, and he faces the right way;
the custom skates go on his feet when there are any."""

import numpy as np
import pytest

import figures
import gear
import sandbox
import zone as zn


@pytest.fixture(autouse=True)
def no_skates(monkeypatch):
    """Line blades, whatever is built next door (custom-skate)."""
    monkeypatch.setattr(gear, "skates", lambda *a, **k: None)


def test_batched_and_one_by_one_drawing_agree():
    zone = zn.Zone.placed((3.0, 0.15), np.array([0.3, 0.0, -0.8]), np.array([0.6, 0.0, -0.8]), (0.0, -1.0))
    batched = sandbox.Lines()
    figures.skater(batched, zone, (5.0, 9.0), (0.3, -1.0), figures.THEM, "R", stride=2.3, speed=5.0)
    segs = []
    figures.skater(lambda a, b, c: segs.append((*a, *c, *b, *c)), zone, (5.0, 9.0), (0.3, -1.0), figures.THEM,
                   "R", stride=2.3, speed=5.0)
    one = np.array(segs, dtype=np.float32).reshape(-1, 6)
    assert np.allclose(batched.array(), one, atol=1e-5)


def test_a_left_shot_facing_up_ice_has_his_blade_ahead_and_on_his_left():
    zone = zn.Zone(np.zeros(3), np.array([0.0, 0.0, 1.0]))
    lines = sandbox.Lines()
    figures.skater(lines, zone, (0.0, 0.0), (0.0, 1.0), figures.US, "L", ring=False)
    pts = lines.array()[:, :3]
    low = pts[pts[:, 1] < 0.03]                                  # skate blades and the stick blade
    blade = low[low[:, 2] > 0.8]                                 # the one well out in front
    assert len(blade) and np.all(blade[:, 0] > 0)                # zone +x is his left facing up ice
    assert pts[:, 1].max() > 1.7 and pts[:, 1].min() >= 0.0      # head up top, nothing under the ice


def test_skaters_wear_the_custom_skates_when_there_are_any(monkeypatch):
    left, right = object(), object()                             # stand-ins for gear.Model
    monkeypatch.setattr(gear, "skates", lambda *a, **k: (left, right))
    zone = zn.Zone(np.zeros(3), np.array([0.0, 0.0, 1.0]))
    for speed, stride in ((0.0, 0.0), (6.0, 0.4), (6.0, 1.25)):
        lines = sandbox.Lines()
        figures.skater(lines, zone, (2.0, 3.0), (0.0, 1.0), figures.US, "L", stride=stride, speed=speed, ring=False)
        placed = dict((id(m), Ms) for m, Ms in lines.placed.values())
        assert len(placed[id(left)]) == 1 and len(placed[id(right)]) == 1
        (L,), (R,) = placed[id(left)], placed[id(right)]
        for M in (L, R):
            assert abs(M[1, 3]) < 1e-9                           # on the ice
            assert np.isclose(np.linalg.det(M[:3, :3]), 1.0)     # turned, not mirrored (the left model is)
            assert M[1, 2] > np.cos(np.radians(16))              # upright, or tipped onto an edge a little
            assert M[:3, 0] @ [0.0, 0.0, 1.0] > 0.8              # toes up ice, the way he faces
        assert L[0, 3] - 2.0 > 0.1 and R[0, 3] - 2.0 < -0.1      # zone +x is his left facing up ice
        assert L[:3, 0] @ [1, 0, 0] >= 0 and R[:3, 0] @ [1, 0, 0] <= 0     # toes out, not in
    pts = lines.array()[:, :3]
    assert not len(pts[pts[:, 1] < 0.015])                       # no line blades (at 1 cm) under the skates
