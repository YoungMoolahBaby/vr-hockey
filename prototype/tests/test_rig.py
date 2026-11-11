"""Thumbstick locomotion: the room placed in the world, moving without ever jumping."""

import math

import numpy as np
import pytest

import rig
import stickmath as sm

T0 = 5000.0                  # an OpenXR time, in seconds
FRAME = 1 / 90


def head_R(yaw_deg: float) -> np.ndarray:
    """A head looking level, turned yaw_deg to the left of -z."""
    return sm.rot_axis_angle(np.array([0.0, 1.0, 0.0]), math.radians(yaw_deg))


def drive_frames(r: rig.Rig, n: int, vel, omega, pivot, t=T0) -> float:
    for k in range(n):
        r.drive(t + k * FRAME, vel, omega, pivot)
    return t + n * FRAME


def test_still_rig_is_identity():
    r = rig.Rig()
    assert not r.moved
    p = r.at(T0)
    R = head_R(30)
    R2, p2 = p.pose(R, np.array([0.3, 1.2, -0.4]))
    assert np.allclose(R2, R) and np.allclose(p2, [0.3, 1.2, -0.4])
    r.drive(T0, np.zeros(3), 0.0, np.zeros(3))          # standing still adds nothing
    assert not r.moved


def test_slide():
    r = rig.Rig()
    r.drive(T0, [1.0, 0.0, -2.0], 0.0, np.zeros(3))
    assert r.moved
    assert np.allclose(r.at(T0 + 0.5).off, [0.5, 0.0, -1.0])
    assert np.allclose(r.at(T0 - 0.5).off, 0.0)          # before it started: where the room was


def test_no_jumps_when_speeds_change():
    """The physics reads the rig at 1 kHz between frames: changing speed each frame must not jump."""
    r = rig.Rig()
    rng = np.random.default_rng(1)
    starts = T0 + FRAME * np.arange(30)
    for t in starts:                                     # a new speed, turn and pivot every frame
        r.drive(t, rng.normal(0, 1.5, 3), rng.normal(0, 1.5), rng.normal(0, 2, 3))
    eps = 1e-6
    for t in starts[2:]:                                 # across every frame's boundary
        a, b = r.at(t - eps), r.at(t + eps)
        assert np.linalg.norm(np.subtract(a.point(0.4, 1.0, -0.3), b.point(0.4, 1.0, -0.3))) < 1e-4
        assert abs(a.yaw - b.yaw) < 1e-4


def test_the_physics_reads_behind_the_frames():
    """The render thread starts each segment at a frame's display time, ahead of the physics: a
    sample just before the newest segment reads the one before it, not the newest one stretched back."""
    r = rig.Rig()
    r.drive(T0, [1.0, 0, 0], 0.0, np.zeros(3))
    r.drive(T0 + 0.1, [-3.0, 0, 0], 0.0, np.zeros(3))
    assert r.at(T0 + 0.09).off[0] == pytest.approx(0.09)
    assert r.at(T0 + 0.1).off[0] == pytest.approx(0.1)
    assert r.at(T0 + 0.11).off[0] == pytest.approx(0.07)


def test_turning_keeps_the_head_in_place():
    r = rig.Rig()
    head = np.array([0.5, 1.7, -1.0])
    drive_frames(r, 45, np.zeros(3), math.radians(90), head)    # half a second at 90 deg/s
    p = r.at(T0 + 45 * FRAME)
    assert p.yaw == pytest.approx(math.radians(45))
    assert np.allclose(p.point(*head)[::2], head[::2])           # you turn where you stand
    # what was straight ahead of you (-z) is now 45 deg to your left... in the room's frame the world
    # turned: a room point ahead of the head lands at 45 deg to the left of -z in the world
    ahead = np.array(p.point(*(head + [0, 0, -1.0]))) - head
    assert np.allclose(ahead[::2], [-math.sin(math.radians(45)), -math.cos(math.radians(45))])


def test_quat_matches_the_matrix():
    p = rig.Pose(0.7, np.array([1.0, 0.0, 2.0]), np.zeros(3), 0.0, np.zeros(3))
    q = sm.mat_to_quat(head_R(20) @ sm.rot_axis_angle(np.array([1.0, 0, 0]), 0.4))
    R_world = p.pose(sm.quat_to_mat(q), np.zeros(3))[0]
    assert np.allclose(sm.quat_to_mat(np.array(p.quat(*q))), R_world)
    assert np.allclose(p.point(0.2, 1.0, -0.5), p.pose(np.eye(3), np.array([0.2, 1.0, -0.5]))[1])


def test_inverse_undoes_the_rig():
    p = rig.Pose(-1.1, np.array([0.3, 0.0, -4.0]), np.zeros(3), 0.0, np.zeros(3))
    x = np.array([0.4, 1.3, 0.9])
    w = np.append(p.point(*x), 1.0)
    assert np.allclose((p.inverse() @ w)[:3], x)


def test_velocity_is_the_rate_of_change():
    """A hand held still in the room moves through the world with the rig: slide plus turn."""
    r = rig.Rig()
    r.drive(T0, [0.8, 0, -0.5], 1.2, np.array([0.5, 0, -1.0]))
    t, h = T0 + 0.004, 1e-5
    x = (0.1, 1.0, -0.6)
    p = r.at(t)
    fd = (np.array(r.at(t + h).point(*x)) - np.array(r.at(t - h).point(*x))) / (2 * h)
    assert np.allclose(p.velocity(p.point(*x), 0.0, 0.0, 0.0), fd, atol=1e-4)
    assert p.spin(0.0, 0.0, 0.0)[1] == pytest.approx(1.2)


def test_drive_directions():
    d = rig.Drive()
    for _ in range(200):                                 # full forward while looking 90 deg left
        vel, om = d.update((0.0, 1.0), 0.0, head_R(90), FRAME)
    assert np.allclose(vel, [-rig.MOVE_MS, 0, 0], atol=1e-3)
    for _ in range(200):                                 # full right: strafe right of where you look
        vel, om = d.update((1.0, 0.0), 0.0, head_R(0), FRAME)
    assert np.allclose(vel, [rig.MOVE_MS, 0, 0], atol=1e-3)
    for _ in range(200):                                 # right stick right: turn right (yaw goes down)
        vel, om = d.update((0.0, 0.0), 1.0, head_R(0), FRAME)
    assert om == pytest.approx(-math.radians(rig.TURN_DEG_S), rel=1e-3)
    assert not vel.any()                                 # and the slide has stopped
    for _ in range(200):
        vel, om = d.update((0.1, 0.1), 0.1, head_R(0), FRAME)   # inside the deadzone: nothing
    assert om == 0.0 and not vel.any()


def test_drive_eases_in():
    d = rig.Drive()
    vel, _ = d.update((0.0, 1.0), 0.0, head_R(0), FRAME)
    assert 0 < np.linalg.norm(vel) < 0.1 * rig.MOVE_MS   # not full speed in one frame


def _run(d: rig.Drive, n: int, move, turn=0.0, yaw=0.0):
    """n frames; returns the velocities, turn rates and modes."""
    vs, oms, modes = [], [], []
    for _ in range(n):
        v, om = d.update(move, turn, head_R(yaw), FRAME)
        vs.append(v.copy())
        oms.append(om)
        modes.append(d.mode)
    return np.array(vs), np.array(oms), modes


def test_a_bounded_push_never_jolts_and_gets_there():
    d = rig.Drive(move_ms=3.0)
    d.push = 6.0
    vs, _, modes = _run(d, 120, (0.0, 1.0))
    acc = np.linalg.norm(np.diff(vs, axis=0), axis=1) / FRAME
    assert acc.max() <= 6.0 + 1e-6 and np.linalg.norm(vs[0]) / FRAME <= 6.0 + 1e-6
    t95 = np.argmax(np.linalg.norm(vs, axis=1) >= 0.95 * 3.0) * FRAME
    assert 0.45 < t95 < 0.7                                     # ~0.55 s, as a rec skater's first strides
    assert np.allclose(vs[-1], [0, 0, -3.0], atol=1e-3) and modes[-1] == "push"
    d2 = rig.Drive(move_ms=3.0)
    d2.push = 6.0
    vb, _, _ = _run(d2, 1, (0.0, -1.0))
    assert np.linalg.norm(vb[0]) / FRAME <= 3.0 + 1e-6          # backwards: half as hard


def test_letting_go_glides():
    d = rig.Drive(move_ms=3.0)
    d.push, d.glide = 6.0, 1.5
    _run(d, 120, (0.0, 1.0))
    vs, _, modes = _run(d, 400, (0.0, 0.0))
    speed = np.linalg.norm(vs, axis=1)
    dec = -np.diff(speed)[speed[1:] > 0] / FRAME
    assert np.allclose(dec, 1.5, atol=1e-6)                     # a steady coast
    moving = int((speed > 0).sum())
    assert abs(moving * FRAME - 2.0) < 0.05                     # 2 s to a stop from 3 m/s
    assert modes[0] == "coast" and modes[-1] == "still"
    # without the glide, letting go eases you to a stop as it always did
    d0 = rig.Drive(move_ms=3.0)
    _run(d0, 120, (0.0, 1.0))
    vs0, _, _ = _run(d0, 100, (0.0, 0.0))
    assert not vs0[-1].any() and np.linalg.norm(vs0[40]) < 0.3  # mostly stopped in under half a second


def test_a_hockey_stop_then_the_other_way():
    d = rig.Drive(move_ms=3.0)
    d.push, d.stop_ms2 = 6.0, 8.0
    _run(d, 120, (0.0, 1.0))
    vs, _, modes = _run(d, 120, (0.0, -1.0))                    # stick full back
    speed = np.linalg.norm(vs, axis=1)
    i = modes.index("push")
    assert set(modes[:i]) == {"stop"}
    assert abs(i * FRAME - (3.0 - rig.STOP_DONE) / 8.0) < 2 * FRAME    # about 0.34 s of stopping
    assert np.all(vs[:i, 2] <= 1e-9)                            # still going forwards (-z) while it stops
    assert vs[-1][2] > 0                                        # then backwards
    assert np.max(np.abs(np.diff(speed[:i])) / FRAME) <= 8.0 + 1e-6


def test_the_carve_limit_bends_the_path_at_most_so_hard():
    d = rig.Drive(move_ms=3.0)
    d.push, d.carve = 6.0, 6.0
    _run(d, 120, (0.0, 1.0))
    vs, _, _ = _run(d, 60, (0.0, 1.0), yaw=90.0)                # look 90 degrees left, stick forward
    a = np.linalg.norm(np.diff(vs, axis=0), axis=1) / FRAME
    assert a.max() <= 6.0 + 1e-3                                # the glance doesn't whip the path round
    vt, oms, _ = _run(d, 60, (0.0, 1.0), turn=1.0, yaw=90.0)    # right stick full right at ~3 m/s
    speed = float(np.linalg.norm(vt[-2]))
    assert abs(oms[-1]) == pytest.approx(6.0 / speed, rel=1e-2)  # capped: about 115 deg/s, not 150
    assert abs(oms[-1]) < math.radians(rig.TURN_DEG_S)


def test_backwards_and_sideways_are_slower_when_asked():
    d = rig.Drive(move_ms=3.0)
    d.back, d.side = 0.8, 0.5
    vb, _, _ = _run(d, 200, (0.0, -1.0))
    assert np.linalg.norm(vb[-1]) == pytest.approx(2.4, abs=1e-3)
    vs, _, _ = _run(d, 200, (1.0, 0.0))
    assert np.linalg.norm(vs[-1]) == pytest.approx(1.5, abs=1e-3)


def test_place_head_puts_you_there_facing_that_way():
    R_room, p_room = head_R(40), np.array([0.7, 1.6, -0.2])     # where you stand in your room
    at, facing = np.array([12.0, 0.0, -30.0]), np.array([1.0, 0.0, 0.0])
    yaw, off = rig.place_head(R_room, p_room, at, facing)
    r = rig.Rig()
    r.teleport(T0, yaw, off)
    R_w, p_w = r.at(T0 + 0.1).pose(R_room, p_room)
    assert np.allclose(p_w[[0, 2]], at[[0, 2]])
    f = -R_w[:, 2]
    assert np.allclose(f / np.linalg.norm(f), facing, atol=1e-9)


def test_teleport_is_a_jump_and_then_still():
    r = rig.Rig()
    r.drive(T0, [2.0, 0, 0], 0.5, np.zeros(3))
    r.teleport(T0 + 0.1, 1.0, [5.0, 3.0, 5.0])
    before, after = r.at(T0 + 0.099), r.at(T0 + 0.101)
    assert np.linalg.norm(after.off - before.off) > 5               # jumped (y stays on the floor)
    assert after.off[1] == 0.0
    assert np.allclose(r.at(T0 + 1.0).off, after.off) and r.at(T0 + 1.0).yaw == pytest.approx(1.0)


def test_snap_turn_turns_about_your_head():
    r = rig.Rig()
    head = np.array([1.0, 1.7, -2.0])
    r.drive(T0, [0.5, 0, 0], 0.0, np.zeros(3))
    r.snap(T0 + 0.1, math.radians(30), head)
    before, after = r.at(T0 + 0.1 - 1e-6), r.at(T0 + 0.1 + 1e-6)
    assert after.yaw - before.yaw == pytest.approx(math.radians(30), abs=1e-6)
    h_room = np.linalg.solve(before.Ry, head - before.off)  # where that head is in the room
    assert np.allclose(np.array(after.point(*h_room))[[0, 2]], head[[0, 2]], atol=1e-5)   # you turned in place


def test_the_left_trigger_sprints_the_harder_the_faster():
    """The stick alone cruises at skate speed; the trigger raises it toward sprint speed, at the push
    limit; easing off coasts back down at the glide."""
    d = rig.Drive(move_ms=3.0)
    d.push, d.glide, d.sprint_ms = 6.0, 1.5, 4.5

    def go(n, boost):
        vs = []
        for _ in range(n):
            v, _ = d.update((0.0, 1.0), 0.0, head_R(0), FRAME, boost=boost)
            vs.append(np.linalg.norm(v))
        return np.array(vs)

    assert go(200, 0.0)[-1] == pytest.approx(3.0, abs=1e-3)        # cruising
    assert go(10, 0.03)[-1] == pytest.approx(3.0, abs=1e-3)        # a resting finger: nothing
    up = go(200, 1.0)
    assert up[-1] == pytest.approx(4.5, abs=1e-3)                  # full squeeze: sprinting
    assert np.diff(up).max() / FRAME <= 6.0 + 1e-6                 # got there at the push limit
    assert go(300, 0.5)[-1] == pytest.approx(3.75, abs=1e-3)       # half: halfway
    down = go(300, 0.0)
    assert down[-1] == pytest.approx(3.0, abs=1e-3)
    assert -np.diff(down).max() / FRAME <= 6.0 and np.diff(down).min() / FRAME >= -1.5 - 1e-6   # coasting back
    assert d.top(1.0) == 4.5 and d.top(0.0) == 3.0
    d.sprint_ms = 0.0                                              # off
    assert d.top(1.0) == 3.0


def test_skate_height_lifts_the_room_over_the_ice():
    """Skate height: the room's floor sits that far over the ice, hands and head alike."""
    r = rig.Rig(0.06)
    assert r.moved                                         # the sampler must transform even standing still
    R, p = r.at(T0).pose(np.eye(3), np.array([0.2, 1.0, -0.3]))
    assert np.allclose(p, [0.2, 1.06, -0.3])
    assert np.allclose(r.at(T0).point(0.2, 1.0, -0.3), (0.2, 1.06, -0.3))
    # skating and turning don't lose it, nor does a teleport
    t = drive_frames(r, 30, np.array([2.0, 0.0, 0.0]), 0.5, np.array([0.0, 1.5, 0.0]))
    assert r.at(t).off[1] == pytest.approx(0.06)
    r.teleport(t, 0.3, np.array([5.0, 0.0, 2.0]))
    assert r.at(t + 0.1).off[1] == pytest.approx(0.06)
    m = r.at(t + 0.1)                                      # and the view undoes it
    assert np.allclose(m.inverse() @ np.r_[m.point(0.1, 1.2, 0.4), 1.0], [0.1, 1.2, 0.4, 1.0])


def test_changing_skate_height_eases_in_without_a_jump():
    r = rig.Rig()
    assert not r.moved and r.at(T0).off[1] == 0.0
    r.set_lift(T0, 0.06)
    assert r.moved
    ts = T0 + np.arange(0, 0.7, 0.001)
    ys = np.array([r.at(t).off[1] for t in ts])
    assert ys[0] == pytest.approx(0.0) and ys[-1] == pytest.approx(0.06)
    assert np.max(np.abs(np.diff(ys))) < 0.0003             # < 0.3 mm a ms: the physics sees no jump
    assert np.all(np.diff(ys) >= -1e-12)
    # the reported velocity is the rate of change (the physics' soft hands read it)
    k = 250
    rate = (ys[k + 1] - ys[k - 1]) / 0.002
    assert r.at(ts[k]).vel[1] == pytest.approx(rate, rel=0.02)
    # a sample from before the change (the physics reads behind the frames) is still the old height
    assert r.at(T0 - 0.05).off[1] == 0.0
    # changing again mid-way starts from where it is
    r.set_lift(T0 + 0.25, 0.0)
    assert r.at(T0 + 0.25).off[1] == pytest.approx(ys[250], abs=1e-9)
