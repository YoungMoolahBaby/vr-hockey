"""The defensive zone: placement, boards, rims, our net."""

import numpy as np
import pytest

import puck as pk
import zone as zn


@pytest.mark.parametrize("yaw_deg", [0, 37, 140, -95])
def test_placed_puts_the_spot_under_the_player_facing_the_right_way(yaw_deg):
    a = np.radians(yaw_deg)
    facing = np.array([np.cos(a), 0.0, np.sin(a)])
    spot_world = np.array([0.4, 1.7, -0.3])
    z = zn.Zone.placed((7.0, 1.6), spot_world, facing, (0.0, -1.0))
    assert np.allclose(z.to_world(7.0, 0.0, 1.6), [0.4, 0.0, -0.3])
    assert np.allclose(z.dir_to_world(0.0, -1.0), facing)
    assert np.allclose(np.cross(zn.UP, z.Z), z.X)                     # no mirror: +x is the team's left
    p = z.to_world(3.0, 0.5, 9.0)
    assert np.allclose(z.to_zone(p), [3.0, 0.5, 9.0])
    assert np.allclose(z.xz(p), [3.0, 9.0])


def _zone_puck(**kw):
    zone = zn.Zone(np.zeros(3), np.array([0.0, 0.0, 1.0]))
    return zone, zn.ZonePuck(pk.Params(**kw), zone)


def test_a_rim_hugs_the_boards_around_the_corner_and_loses_some_speed():
    zone, p = _zone_puck(ice_mu=0.0, board_bounce=0.3)
    p.place(-2.0, pk.R, 12.0, 0.0)                    # along the end boards toward the left corner
    worst, crossed = 0.0, None
    for i in range(4000):
        p.step(0.001)
        x, _, z = zone.to_zone(p.pos)
        hit = zn.boards_contact(x, z, pk.R)
        worst = max(worst, hit[0] if hit else 0.0)
        if crossed is None and z > zn.CORNER_R + 2.0:
            crossed = (x, p.speed, float(p.vel @ zone.Z))
    assert worst < 0.01                                               # never through the boards
    x, speed, vz = crossed
    assert x > zn.WIDTH / 2 - 0.5                                     # came out along the left wall
    assert vz > 0.9 * speed                                           # heading straight up the wall
    assert 6.0 < speed < 11.5                                         # the corner took some speed


def test_clearing_the_zone_is_an_event():
    zone, p = _zone_puck(ice_mu=0.0)
    p.place(0.0, 20.0, 0.0, 10.0)
    for _ in range(500):
        p.step(0.001)
    assert p.cleared and "cleared" in [e[0] for e in p.events]


def test_into_our_net_from_the_front_is_an_own_goal_and_it_stays_in():
    zone, p = _zone_puck()
    p.place(0.2, 8.0, 0.0, -10.0)
    for _ in range(2000):
        p.step(0.001)
    x, _, z = zone.to_zone(p.pos)
    assert p.in_net and p.nets == 1 and "net" in [e[0] for e in p.events]
    assert zn.GOAL_Z - zn.NET_DEPTH < z < zn.GOAL_Z and abs(x) < zn.NET_HALF_W


@pytest.mark.parametrize("start,vel", [((4.0, 2.8), (-10.0, 0.0)),     # from the side
                                       ((0.0, 0.5), (0.0, 10.0))])       # from behind (off the end boards)
def test_the_net_is_solid_from_the_side_and_back(start, vel):
    zone, p = _zone_puck()
    p.place(*start, *vel)
    for _ in range(1500):
        p.step(0.001)
        x, _, z = zone.to_zone(p.pos)
        inside = abs(x) < zn.NET_HALF_W and zn.GOAL_Z - zn.NET_DEPTH < z < zn.GOAL_Z
        assert not inside
    assert not p.in_net and p.nets == 0
