"""Thumbstick locomotion: where your room sits in the game world.

You stand in a room (the OpenXR STAGE space); the rink, the puck and the drills live in the world.
The rig places the room in the world: world = yaw(a) * room + offset. The left thumbstick slides the
room across the ice (where you look is forward), the right one turns it about your head.

The 1 kHz physics locates the hands between frames, so the rig must never jump: a jump of a few cm
in one tick would be a blade moving at tens of m/s. So it moves continuously in time, as a chain of
segments, each with a constant velocity and turn rate. The render thread starts a new segment every
frame (at that frame's display time) from where the last one had got to; the physics thread reads
the segment that covers its own sample time. Times are OpenXR times, in seconds.
"""

from __future__ import annotations

import math

import numpy as np

MOVE_MS = 3.0                 # m/s at full stick (Jon's pick; 6, then 4 felt too fast in the 3v3: "skate speed")
TURN_DEG_S = 150.0            # deg/s at full stick (90 felt too slow; tunable: "turn speed")
DEAD = 0.15                   # stick deadzone
MOVE_TAU, TURN_TAU = 0.15, 0.08   # s: how quickly you get up to (and down from) speed


class Pose:
    """The rig at one instant: maps room poses into the world."""

    __slots__ = ("yaw", "c", "s", "off", "vel", "omega", "pivot", "Ry")

    def __init__(self, yaw: float, off: np.ndarray, vel: np.ndarray, omega: float, pivot: np.ndarray):
        self.yaw, self.off, self.vel, self.omega, self.pivot = yaw, off, vel, omega, pivot
        self.c, self.s = math.cos(yaw), math.sin(yaw)
        self.Ry = np.array([[self.c, 0.0, self.s], [0.0, 1.0, 0.0], [-self.s, 0.0, self.c]])

    def pose(self, R: np.ndarray, p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """A room pose (rotation, position) in the world."""
        return self.Ry @ R, self.Ry @ p + self.off

    # plain floats, for the sampler's hot loop
    def point(self, x: float, y: float, z: float) -> tuple[float, float, float]:
        c, s, o = self.c, self.s, self.off
        return c * x + s * z + o[0], y + o[1], -s * x + c * z + o[2]

    def quat(self, x: float, y: float, z: float, w: float) -> tuple[float, float, float, float]:
        """(x, y, z, w) of yaw(a) * q."""
        cy, sy = math.cos(self.yaw / 2), math.sin(self.yaw / 2)
        return cy * x + sy * z, cy * y + sy * w, cy * z - sy * x, cy * w - sy * y

    def velocity(self, world_p, vx: float, vy: float, vz: float) -> tuple[float, float, float]:
        """A room velocity at world point world_p, in the world: turned, plus the rig's own motion."""
        c, s, v = self.c, self.s, self.vel
        rx, rz = world_p[0] - self.pivot[0], world_p[2] - self.pivot[2]
        return c * vx + s * vz + v[0] + self.omega * rz, vy + v[1], -s * vx + c * vz + v[2] - self.omega * rx

    def spin(self, wx: float, wy: float, wz: float) -> tuple[float, float, float]:
        c, s = self.c, self.s
        return c * wx + s * wz, wy + self.omega, -s * wx + c * wz

    def inverse(self) -> np.ndarray:
        """4x4 world -> room (for the view matrix)."""
        m = np.eye(4)
        m[:3, :3] = self.Ry.T
        m[:3, 3] = -self.Ry.T @ self.off
        return m


class Rig:
    KEEP = 32                     # segments kept: about 0.4 s at 90 Hz, far more than the physics lags

    def __init__(self):
        zero = np.zeros(3)
        # (t0, yaw0, offset0, velocity, turn rate, pivot): replaced whole, so a reader needs no lock
        self._segs: tuple = ((0.0, 0.0, zero, zero, 0.0, zero),)
        self.moved = False        # still where the room is: nothing to transform

    @staticmethod
    def _at(seg, t: float) -> tuple[float, np.ndarray]:
        t0, yaw0, off0, vel, om, piv = seg
        tau = t - t0
        a = om * tau
        if a:                     # turn about the pivot, then slide
            c, s = math.cos(a), math.sin(a)
            d = off0 - piv
            off = piv + np.array([c * d[0] + s * d[2], d[1], -s * d[0] + c * d[2]]) + vel * tau
        else:
            off = off0 + vel * tau
        return yaw0 + a, off

    def _seg(self, t: float):
        segs = self._segs
        for seg in reversed(segs):
            if seg[0] <= t:
                return seg
        return segs[0]

    def at(self, t: float) -> Pose:
        seg = self._seg(t)
        yaw, off = self._at(seg, t)
        return Pose(yaw, off, seg[3], seg[4], seg[5] + seg[3] * (t - seg[0]))   # the pivot slides along

    def drive(self, t: float, vel, omega: float, pivot) -> None:
        """From time t on, slide at vel (world m/s) and turn at omega (rad/s, + = left) about pivot."""
        segs = self._segs
        last = segs[-1]
        vel = np.array([vel[0], 0.0, vel[2]], dtype=float)
        if t <= last[0]:
            return
        if not omega and not vel.any() and not last[4] and not last[3].any():
            return                # standing still, and was: the last segment holds
        yaw, off = self._at(last, t)
        pivot = np.array([pivot[0], 0.0, pivot[2]], dtype=float)
        self._segs = segs[-(self.KEEP - 1):] + ((t, yaw, off, vel, float(omega), pivot),)
        self.moved = True

    def snap(self, t: float, angle: float, pivot) -> None:
        """From time t on, turned by `angle` (rad, + = left) about `pivot` (your head): a snap turn.
        A deliberate jump, like teleport; the slide carries on."""
        segs = self._segs
        last = segs[-1]
        t = max(t, last[0] + 1e-6)
        yaw, off = self._at(last, t)
        c, s = math.cos(angle), math.sin(angle)
        piv = np.array([pivot[0], 0.0, pivot[2]], dtype=float)
        d = off - piv
        off = piv + np.array([c * d[0] + s * d[2], d[1], -s * d[0] + c * d[2]])
        self._segs = segs[-(self.KEEP - 1):] + ((t, yaw + angle, off, last[3], 0.0, piv),)
        self.moved = True

    def teleport(self, t: float, yaw: float, off) -> None:
        """From time t on, put the room at (yaw, offset), standing still: a deliberate jump (after
        a goal, back to centre ice). The physics sees the stick jump and doesn't sweep it."""
        segs = self._segs
        t = max(t, segs[-1][0] + 1e-6)
        zero = np.zeros(3)
        off = np.array([off[0], 0.0, off[2]], dtype=float)
        self._segs = segs[-(self.KEEP - 1):] + ((t, float(yaw), off, zero, 0.0, zero),)
        self.moved = True


def yaw_of(d) -> float:
    """The yaw (+ = left of -z) of a horizontal direction (x, _, z)."""
    return math.atan2(-d[0], -d[2])


def place_head(head_R_room: np.ndarray, head_p_room: np.ndarray, at_world, facing_world) -> tuple[float, np.ndarray]:
    """The rig (yaw, offset) that puts your head (a room pose) over world point `at_world`, looking
    along world direction `facing_world`."""
    yaw = yaw_of(facing_world) - yaw_of(-head_R_room[:, 2])
    c, s = math.cos(yaw), math.sin(yaw)
    x, z = head_p_room[0], head_p_room[2]
    return yaw, np.array([at_world[0] - (c * x + s * z), 0.0, at_world[2] - (-s * x + c * z)])


def _shape(v: float, power: float = 2.0) -> float:
    """Deadzone, then a curve: fine control near the middle, full speed at the edge."""
    m = abs(v)
    if m < DEAD:
        return 0.0
    return math.copysign(min((m - DEAD) / (1 - DEAD), 1.0) ** power, v)


EASE = 0.1                    # s: a bounded push eases into its target speed over about this
STOP_ANGLE = 120.0            # deg: the left stick held this far against your motion is a hockey stop
STOP_DONE = 0.3               # m/s: ... until you're this slow; then it pushes you the new way
CARVE_MIN = 0.5               # m/s: below this the turn limit doesn't apply (you can pivot standing)


def _rotate(v: np.ndarray, a: float) -> np.ndarray:
    """A world vector turned by yaw a (+ = left), as the rig turns the room."""
    c, s = math.cos(a), math.sin(a)
    return np.array([c * v[0] + s * v[2], 0.0, -s * v[0] + c * v[2]])


class Drive:
    """Thumbsticks to rig velocities.

    By default as it always was: eased in and out (MOVE_TAU, TURN_TAU), so letting go of the stick
    stops you within about half a second. Each hockey limit is its own setting, off at 0, to try one
    at a time (reports/Hockey physics feel.md):
    - push (m/s^2): speed up (and turn your path) at most this hard, easing in over EASE at the top,
      half as hard pushing backwards, instead of the exponential easing (a 2 g onset).
    - glide (m/s^2): let go of the stick, or ease off it, and you coast, slowing at this rate.
    - stop (m/s^2): the stick held more than STOP_ANGLE against your motion is a hockey stop at
      this rate, down to STOP_DONE; then you push the new way.
    - carve (m/s^2): your path can't bend harder than this sideways (a glance doesn't whip it round),
      the right stick's turn is capped to it at speed, and turning carves your path with you.
    - back, side: top speed backwards and sideways, as a share of forwards (1 = the same).
    `mode` says what it did last: "still", "push", "coast", "stop" or "ease" (the old let-go)."""

    def __init__(self, move_ms: float = MOVE_MS, turn_deg_s: float = TURN_DEG_S):
        self.move_ms = move_ms
        self.turn_deg_s = turn_deg_s
        self.push = self.glide = self.stop_ms2 = self.carve = 0.0
        self.back = self.side = 1.0
        self.vel = np.zeros(3)
        self.omega = 0.0
        self.mode = "still"

    def stop(self) -> None:
        self.vel = np.zeros(3)
        self.omega = 0.0
        self.mode = "still"

    def _want(self, move_xy, head_R) -> tuple[np.ndarray, float]:
        """The velocity the left stick asks for (world), and how far it points backwards (0-1)."""
        x, y = move_xy
        m = math.hypot(x, y)
        if m <= DEAD or head_R is None:
            return np.zeros(3), 0.0
        f = -head_R[:, 2]
        n = math.hypot(f[0], f[2])
        if n <= 1e-6:
            return np.zeros(3), 0.0
        fwd = np.array([f[0] / n, 0.0, f[2] / n])
        right = np.array([-fwd[2], 0.0, fwd[0]])
        speed = self.move_ms * _shape(min(m, 1.0))
        ux, uy = x / m, y / m
        sx, sy = ux * self.side, uy * (1.0 if uy >= 0 else self.back)    # backwards, sideways: slower
        return speed * (sy * fwd + sx * right), max(0.0, -uy)

    def update(self, move_xy, turn_x: float, head_R: np.ndarray | None, dt: float) -> tuple[np.ndarray, float]:
        """move_xy: the left stick (x right, y forward); turn_x: the right stick's x (right = turn right);
        head_R: the head's world rotation (forward = where you look). Returns (velocity, turn rate)."""
        want, backward = self._want(move_xy, head_R)
        v = self.vel
        speed = float(np.linalg.norm(v))
        want_s = float(np.linalg.norm(want))
        # turning: the right stick, capped at speed by the carve limit
        want_om = -math.radians(self.turn_deg_s) * _shape(turn_x, 1.3)     # turning: closer to linear
        if self.carve > 0 and speed > CARVE_MIN:
            cap = self.carve / speed
            want_om = max(-cap, min(cap, want_om))
        k_w = 1 - math.exp(-dt / TURN_TAU)
        self.omega += (want_om - self.omega) * k_w
        if not want_om and abs(self.omega) < math.radians(0.5):
            self.omega = 0.0
        if self.carve > 0 and speed > CARVE_MIN:
            v = _rotate(v, self.omega * dt)                 # a turn carves your path with you
        # sliding: coast, stop, or push toward what the stick asks for
        against = (speed > STOP_DONE and want_s > 0
                   and float(want @ v) < math.cos(math.radians(STOP_ANGLE)) * want_s * speed)
        if want_s == 0 and self.glide > 0:
            self.mode = "coast"
            new = v * (max(speed - self.glide * dt, 0.0) / speed) if speed > 0 else v
        elif against and self.stop_ms2 > 0:
            self.mode = "stop"
            new = v * (max(speed - self.stop_ms2 * dt, 0.0) / speed)
        elif self.push > 0:
            new = self._push(v, speed, want, want_s, backward, dt)
        else:                                               # as it always was: eased in and out
            self.mode = "push" if want_s > 0 else "ease"
            new = v + (want - v) * (1 - math.exp(-dt / MOVE_TAU))
        if self.carve > 0 and speed > CARVE_MIN and float(np.linalg.norm(new)) > 1e-9:
            new = self._bend_limit(v, new, speed, dt)
        if want_s == 0 and float(np.linalg.norm(new)) < 0.01:
            new = np.zeros(3)
        if not new.any() and want_s == 0:
            self.mode = "still"
        self.vel = new
        return self.vel, self.omega

    def _push(self, v, speed, want, want_s, backward, dt) -> np.ndarray:
        """Toward `want` at bounded rates: speeding up at push (half pushing backwards), easing in over
        EASE; easing off the stick coasts (glide) if there is one, else slows at push."""
        push = self.push * (1 - 0.5 * backward)
        dv = want - v
        if speed < STOP_DONE:                               # from (nearly) still: straight at it
            n = float(np.linalg.norm(dv))
            self.mode = "push" if want_s > 0 else "still"
            a = min(push, n / EASE)
            return v + (dv / n) * min(a * dt, n) if n > 1e-9 else v
        u = v / speed
        along = float(dv @ u)
        across = dv - along * u
        if along >= 0:
            a_al = min(push, along / EASE)
            self.mode = "push"
        elif float(want @ v) > 0 and self.glide > 0:        # eased off, still this way: coasting
            a_al = -min(self.glide, -along / EASE)
            self.mode = "coast"
        else:                                               # pushing against it
            a_al = -min(push, -along / EASE)
            self.mode = "push"
        n_x = float(np.linalg.norm(across))
        a_x = min(self.carve if self.carve > 0 else push, n_x / EASE)
        grip = max(push, self.carve)                        # the edges' grip: turning first, then the rest
        a_al = math.copysign(min(abs(a_al), math.sqrt(max(grip * grip - a_x * a_x, 0.0))), a_al)
        out = v + u * (a_al * dt)
        if n_x > 1e-9:
            out = out + across / n_x * min(a_x * dt, n_x)
        return out

    def _bend_limit(self, v, new, speed, dt) -> np.ndarray:
        """The path's direction turns at most carve/speed (rad/s): sideways acceleration <= carve."""
        if float(new @ v) <= 0:                             # through zero: a stop, not a turn
            return new
        a0 = math.atan2(v[0], v[2])
        a1 = math.atan2(new[0], new[2])
        d = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        lim = self.carve / speed * dt
        if abs(d) <= lim:
            return new
        a = a0 + math.copysign(lim, d)
        s = float(np.linalg.norm(new))
        return np.array([math.sin(a) * s, 0.0, math.cos(a) * s])
