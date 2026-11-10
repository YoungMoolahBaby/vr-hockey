"""The rink's look (theme.py): no ice grid unless asked for, the solid rink under the lines, the
headset's colours, and the boards' inset."""

import numpy as np

import arena as ar
import grab
import puck as pk
import sandbox
import stickspec
import theme
import zone as zn


def test_the_ice_grid_is_off_by_default_and_a_setting():
    spec = stickspec.from_height(1.73, "left")
    values = sandbox.Tuning.defaults(spec, grab.Fit(), pk.Params())
    assert values["grid"] == sandbox.GRID == 0.0
    assert "grid" in [s.key for s in sandbox.SETTINGS]
    assert sandbox.SETTINGS[-1].key == "ice"                  # still last: one push left from the first


def test_the_rink_is_solid_and_the_grid_only_adds_lines():
    arena = ar.Arena(zn.Zone(np.zeros(3), np.array([0.0, 0.0, 1.0])))
    off, on = sandbox.Lines(), sandbox.Lines()
    ar.markings(arena, off)
    ar.markings(arena, on, grid=True)
    tris = off.tri_array()
    assert tris.shape[1] == 6 and len(tris) % 3 == 0 and len(tris) > 1000
    assert np.array_equal(tris, on.tri_array())
    assert len(on.array()) > len(off.array())
    ice = tris[np.isclose(tris[:, 1], theme.ICE_Y)]            # the ice lies flat, just under y = 0
    assert len(ice) and ice[:, 0].min() >= -zn.WIDTH / 2 - 1e-6 and ice[:, 2].max() <= arena.length + 1e-6


def test_a_bare_line_callback_still_draws_the_markings():
    segs = []
    zn.markings(zn.Zone(np.zeros(3), np.array([0.0, 0.0, 1.0])), lambda a, b, c: segs.append((a, b, c)))
    assert len(segs) > 100


def test_colours_are_given_as_the_headset_shows_them():
    # the README GIFs' background: drawn as (0.05, 0.06, 0.09), shown as (63, 69, 84)
    assert np.allclose(theme.srgb(63, 69, 84), (0.05, 0.06, 0.09), atol=0.002)
    assert theme.srgb(255, 255, 255) == (1.0, 1.0, 1.0) and theme.srgb(0, 0, 0) == (0.0, 0.0, 0.0)


def test_the_inset_stays_the_same_distance_from_every_side():
    square = np.array([[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0]])
    inner = square + theme.inward(square, closed=True) * 2.0
    assert np.allclose(inner, [[2, 2], [8, 2], [8, 8], [2, 8]])
    rim = np.array(ar.outline(ar.Arena(zn.Zone(np.zeros(3), np.array([0.0, 0.0, 1.0]))))[:-1])
    inner = rim + theme.inward(rim, closed=True) * 2.0
    assert np.all(np.abs(inner[:, 0]) <= zn.WIDTH / 2 - 2.0 + 1e-6)
