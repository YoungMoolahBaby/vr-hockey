"""Hockey-sense module 1: scan, retrieve, first pass (reports/VR hockey sense training.md).

You stand behind our net, just left of it, facing the end boards with your back to the play. A
puck is dumped in down the right wall and rims around the boards to your blade. While it comes,
the forecheck commits: F1 comes down your wall, chases the puck around the net, or comes down
the middle, and F2 takes away one of your three outs:

    wall     up the left boards to your winger (W)
    reverse  back behind the net to your D partner (D)
    middle   up the slot to your center (C)

F1 only shows where he is going about a second into the rep, so the open out can only be read
with a shoulder check after that and before the puck gets to you. Then you make the pass with
your stick.

Every out is valued with a time-to-intercept model (can a forechecker get a stick on the lane, or
on the receiver, before the puck gets there?), each rep is built so that one out is clearly best
(and each out is best equally often), and your choice is scored against it at the moment you
release. F1's head start (the free time between the puck reaching you and F1 reaching you)
adapts with a weighted staircase that settles near 75% success.

Pure logic, no XR: drill.py runs it in the headset; tests/test_retrieval.py drives it with a bot.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

import puck as pk
import zone as zn

OPTIONS = ("wall", "reverse", "middle")
RECEIVER = {"wall": "W", "reverse": "D", "middle": "C"}
SAY = {"wall": "the wall", "reverse": "the reverse", "middle": "the middle", "other": "that"}

PASS_SPEED = 7.0         # m/s: the pass the value model assumes; the drill uses your own (drill.py)
DECIDE_S = 1.0           # s: from control to release; the drill uses your own
REACH = 1.2              # m: an opponent's stick covers this far from his body
BODY_R = 0.4             # m: a puck in the air gets past the stick, not the body
REACTION = 0.25          # s: before a skater reacts to a pass
VMAX, ACCEL = 7.0, 5.0   # rec forecheckers (NHL tops out near 10 m/s)
RECEIVE_R = 1.2          # m: a pass this close to a teammate is his
CONTACT_R = 1.0          # m: a forechecker this close to you has you
CONTROL_R = 0.45         # m: the puck this close to your blade, slow, is yours
READY_S = 1.2            # s: frozen before the puck is dumped in
JON_BLADE = np.array([3.0, 0.15])     # your blade: at the end boards, just left of our net (a blade
                                      # turned to the boards then covers a puck rimming along them)
AIM_MAX_Z = 1.0          # m: the rim assist steers the puck at most this far off the end boards
RESULT_S = 6.0           # s: the result shows this long before the next rep

# where everyone is (zone x, z; x positive = our left looking up ice), with how much it varies
TEAMMATES = {"W": ((zn.WIDTH / 2 - 0.75, 10.5), (0.15, 1.2)),   # left winger on the wall: rims reach him
             "D": ((-3.4, 1.7), (0.6, 0.4)),           # D partner, right of the net, behind the goal line
             "C": ((1.0, 7.5), (1.0, 1.0))}            # center, low in the slot
F1_WAYPOINTS = {"wall": [(6.8, 8.5), (5.4, 3.8)],                # down our left side
                "chase": [(-2.1, 5.0), (-2.0, 1.2)],             # after the puck, around the net
                "middle": [(1.9, 6.0)]}                          # straight down the middle
F1_FROM = {"wall": (0.8, 0.6), "chase": (-1.0, -0.15), "middle": (0.15, 1.0)}   # his side of you
F2_POSTS = {"wall": ("W", (-1.4, -1.6)), "middle": ("C", (0.9, -1.2)),
            "reverse": ("D", (0.5, 2.3)), "high": (None, (0.0, 14.0))}

NET_SOLID = (-(zn.NET_HALF_W + zn.POST_R + pk.R), zn.NET_HALF_W + zn.POST_R + pk.R,
             zn.GOAL_Z - zn.NET_DEPTH - pk.R, zn.GOAL_Z)
NET_AROUND = (NET_SOLID[0] - 0.45, NET_SOLID[1] + 0.45, NET_SOLID[2] - 0.45, NET_SOLID[3] + 0.45)


def unit(v) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-9 else np.zeros_like(v)


def angle_deg(a, b) -> float:
    a, b = unit(a), unit(b)
    return float(np.degrees(np.arccos(np.clip(a @ b, -1.0, 1.0))))


def sig(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(min(x, 40.0), -40.0)))


# ----------------------------------------------------------------------------- time to intercept


def crosses(a, b, box) -> bool:
    """Does segment a-b pass through the open box (x0, x1, z0, z1)? (Liang-Barsky)"""
    x0, x1, z0, z1 = box
    (ax, az), (bx, bz) = a, b
    dx, dz = bx - ax, bz - az
    lo, hi = 0.0, 1.0
    for p, q in ((-dx, ax - x0), (dx, x1 - ax), (-dz, az - z0), (dz, z1 - az)):
        if abs(p) < 1e-12:
            if q <= 0:
                return False
        else:
            t = q / p
            if p < 0:
                lo = max(lo, t)
            else:
                hi = min(hi, t)
            if lo >= hi:
                return False
    return hi - lo > 1e-6


def skate_dist(a, b) -> float:
    """How far a skater goes from a to b: straight, or around our net if it is in the way."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if not crosses(a, b, NET_SOLID):
        return float(np.linalg.norm(b - a))
    x0, x1, z0, z1 = NET_AROUND
    cs = [np.array(c) for c in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))]
    best = math.inf
    for i, c in enumerate(cs):
        if not crosses(a, c, NET_SOLID) and not crosses(c, b, NET_SOLID):
            best = min(best, float(np.linalg.norm(c - a) + np.linalg.norm(b - c)))
        for c2 in (cs[(i + 1) % 4], cs[(i - 1) % 4]):
            if not crosses(a, c, NET_SOLID) and not crosses(c2, b, NET_SOLID):
                best = min(best, float(np.linalg.norm(c - a) + np.linalg.norm(c2 - c) + np.linalg.norm(b - c2)))
    return best if best < math.inf else float(np.linalg.norm(b - a)) * 1.5


def time_to_cover(dist: float, v0: float = 0.0, vmax: float = VMAX, accel: float = ACCEL) -> float:
    """Seconds to skate `dist` metres starting at v0 toward it, accelerating up to vmax."""
    dist, v0 = max(dist, 0.0), min(max(v0, 0.0), vmax)
    t1 = (vmax - v0) / accel
    d1 = (v0 + vmax) / 2 * t1
    if dist <= d1:
        return (-v0 + math.sqrt(v0 * v0 + 2 * accel * dist)) / accel
    return t1 + (dist - d1) / vmax


def arrival(pos, vel, q, reach: float) -> float:
    """When a skater at pos moving at vel can get within `reach` of point q (his reaction included,
    unless he is already there)."""
    d = skate_dist(pos, q) - reach
    v0 = float(np.asarray(vel) @ unit(np.asarray(q) - np.asarray(pos)))
    return REACTION * min(max(d / 0.5, 0.0), 1.0) + time_to_cover(d, v0)


def option_value(p0, target, opps, pass_speed: float = PASS_SPEED) -> tuple[float, float, float]:
    """(value 0..1, lane margin s, receiver margin s) of a pass from p0 to a teammate at target.

    lane margin: the earliest any opponent can get a stick on the pass's line, minus when the
    puck gets there (negative = picked off). receiver margin: when an opponent can get to the
    receiver, minus when the puck does (small = he gets it and gets hit)."""
    p0, target = np.asarray(p0, dtype=float), np.asarray(target, dtype=float)
    if crosses(p0, target, NET_SOLID):
        return 0.0, -9.0, -9.0
    L = float(np.linalg.norm(target - p0))
    d = (target - p0) / max(L, 1e-9)
    lane = rcv = math.inf
    for pos, vel in opps:
        for s in np.linspace(0.0, L, 24):
            lane = min(lane, arrival(pos, vel, p0 + s * d, REACH) - s / pass_speed)
        rcv = min(rcv, arrival(pos, vel, target, CONTACT_R) - L / pass_speed)
    # the lane decides most of it (a man covering the receiver is on the lane's end too); the
    # receiver's time only shades it, or every long pass would look covered
    value = sig(lane / 0.12) * (0.4 + 0.6 * sig((rcv - 0.2) / 0.3))
    return value, lane, rcv


# ----------------------------------------------------------------------------- the dump-in


_KEEP: dict[float, float] = {}


def corner_keep(board_bounce: float) -> float:
    """The share of its speed a puck keeps rimming around a corner (board friction; no ice friction)."""
    key = round(board_bounce, 3)
    if key not in _KEEP:
        zone = zn.Zone(np.zeros(3), np.array([0.0, 0.0, 1.0]))
        p = zn.ZonePuck(pk.Params(ice_mu=0.0, board_bounce=board_bounce), zone)
        p.place(-(zn.WIDTH / 2) + pk.R, zn.CORNER_R + 0.5, 0.0, -10.0)
        for _ in range(3000):
            p.step(0.001)
            x, _, z = zone.to_zone(p.pos)
            if x > -(zn.WIDTH / 2 - zn.CORNER_R) + 0.3:
                break
        _KEEP[key] = p.speed / 10.0
    return _KEEP[key]


def rim_launch(z_launch: float, x_target: float, v_arrive: float, ice_mu: float, keep: float) -> tuple[float, float]:
    """A puck sent down the right wall from z_launch rims around the right corner and along the end
    boards: the launch speed that has it pass x_target at v_arrive, and when it gets there (s)."""
    a = ice_mu * pk.G
    L1 = max(z_launch - zn.CORNER_R, 0.0)
    L2 = math.pi / 2 * (zn.CORNER_R - pk.R)
    L3 = max(x_target + (zn.WIDTH / 2 - zn.CORNER_R), 0.0)
    v3 = v_arrive
    v2 = math.sqrt(v3 * v3 + 2 * a * L3)
    v1 = math.sqrt(v2 * v2 + 2 * a * L2) / keep
    v0 = math.sqrt(v1 * v1 + 2 * a * L1)

    def leg(vi, vo, L):
        return L / max((vi + vo) / 2, 1e-6)
    return v0, leg(v0, v1, L1) + leg(v1, v2, L2) + leg(v2, v3, L3)


# ----------------------------------------------------------------------------- skaters


def chaikin(pts, n: int = 2) -> np.ndarray:
    P = np.asarray(pts, dtype=float)
    for _ in range(n):
        Q = [P[0]]
        for a, b in zip(P[:-1], P[1:]):
            Q += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]
        Q.append(P[-1])
        P = np.array(Q)
    return P


class Track:
    """A scripted skate along a smoothed polyline at constant speed, then a stop."""

    def __init__(self, pts, speed: float):
        self.pts = np.asarray(pts, dtype=float)
        self.P = chaikin(self.pts)
        self.s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(self.P, axis=0), axis=1))])
        self.speed = float(speed)
        self.length = float(self.s[-1])
        self.t_end = self.length / self.speed

    def at(self, t: float) -> np.ndarray:
        d = min(max(t * self.speed, 0.0), self.length)
        return np.array([np.interp(d, self.s, self.P[:, 0]), np.interp(d, self.s, self.P[:, 1])])

    def vel(self, t: float) -> np.ndarray:
        if t < 0 or t >= self.t_end:
            return np.zeros(2)
        return (self.at(t + 0.01) - self.at(t - 0.01)) / 0.02

    def retime(self, t_end: float) -> None:
        """Change the speed so the skate ends at t_end."""
        self.speed = self.length / max(t_end, 1e-3)
        self.t_end = self.length / self.speed

    def time_near(self, point) -> float:
        """When the skate passes closest to a point."""
        i = int(np.argmin(np.linalg.norm(self.P - np.asarray(point), axis=1)))
        return float(self.s[i] / self.speed)

    def to_dict(self) -> dict:
        return {"pts": self.pts.round(3).tolist(), "speed": round(self.speed, 3)}


@dataclass
class Skater:
    id: str
    team: str                          # "us" or "them"
    shoots: str                        # "L" or "R"
    pos: np.ndarray
    track: Track | None = None
    vel: np.ndarray = field(default_factory=lambda: np.zeros(2))
    facing: np.ndarray = field(default_factory=lambda: np.array([0.0, -1.0]))
    mode: str = "script"               # script -> react (after a pass) -> hold
    react_at: float = math.inf
    stride: float = 0.0                # metres skated (drives the legs)
    target: np.ndarray | None = None   # where he is going for the puck
    t_target: float = -1.0

    def step(self, t: float, dt: float, puck_xz, puck_v) -> None:
        if self.mode == "script" and t >= self.react_at and self.team == "them":
            self.mode = "react"
        old = self.pos.copy()
        if self.mode == "script" and self.track is not None:
            self.pos = self.track.at(t)
            self.vel = self.track.vel(t)
        elif self.mode == "react":
            if self.target is None or t - self.t_target >= 0.05:
                self.target, self.t_target = self._intercept(puck_xz, puck_v), t
            self._skate_to(dt, self.target)
        else:
            self.vel = np.zeros(2)
        self.stride += float(np.linalg.norm(self.pos - old))
        speed = float(np.linalg.norm(self.vel))
        want = unit(self.vel) if speed > 0.6 else unit(np.asarray(puck_xz) - self.pos)
        if np.any(want):
            self.facing = unit(self.facing + min(1.0, 8.0 * dt) * (want - self.facing)) if np.any(self.facing) else want

    def _intercept(self, puck_xz, puck_v) -> np.ndarray:
        """Where to go for the puck: the earliest spot on its path that he can get a stick to."""
        p, v = np.asarray(puck_xz, dtype=float), np.asarray(puck_v, dtype=float)
        if np.linalg.norm(v) <= 1.0:
            return p
        best = None
        for tau in np.arange(0.0, 1.6, 0.05):
            q = p + v * tau
            if arrival(self.pos, self.vel, q, REACH * 0.7) <= tau:
                return q
            d = float(np.linalg.norm(q - self.pos))
            if best is None or d < best[0]:
                best = (d, q)
        return best[1]

    def _skate_to(self, dt: float, target) -> None:
        to = np.asarray(target) - self.pos
        dist = float(np.linalg.norm(to))
        want = unit(to) * min(VMAX, math.sqrt(2 * ACCEL * dist))
        dv = want - self.vel
        n = float(np.linalg.norm(dv))
        if n > ACCEL * dt:
            dv *= ACCEL * dt / n
        self.vel = self.vel + dv
        self.pos = self.pos + self.vel * dt
        x, z = self.pos                                # stay on the ice
        x = float(np.clip(x, -zn.side_boards_x(max(z, 0.4)) + 0.4, zn.side_boards_x(max(z, 0.4)) - 0.4))
        z = max(z, zn.end_boards_z(x) + 0.4)
        self.pos = np.array([x, z])


# ----------------------------------------------------------------------------- scenarios


@dataclass
class Scenario:
    seed: int
    f1_route: str
    f2_post: str
    free_time: float
    v_arrive: float
    z_launch: float
    v_launch: float
    t_arrive: float                    # estimated, s after the dump-in
    t_commit: float                    # when F1 shows where he is going
    blade: np.ndarray
    head: np.ndarray
    mates: dict
    f1: Track
    f2: Track
    f1_shoots: str
    f2_shoots: str
    values: dict                       # each out's value when you should be passing
    best: str
    pass_speed: float = PASS_SPEED     # yours: what every pass is valued at
    decide_s: float = DECIDE_S         # yours: control to release

    def to_dict(self) -> dict:
        return {"seed": self.seed, "f1_route": self.f1_route, "f2_post": self.f2_post,
                "free_time": round(self.free_time, 3), "pass_speed": round(self.pass_speed, 2),
                "decide_s": round(self.decide_s, 2), "v_arrive": round(self.v_arrive, 2),
                "z_launch": round(self.z_launch, 2), "v_launch": round(self.v_launch, 2),
                "t_arrive": round(self.t_arrive, 3), "t_commit": round(self.t_commit, 3),
                "blade": self.blade.round(3).tolist(), "head": self.head.round(3).tolist(),
                "mates": {k: v.round(3).tolist() for k, v in self.mates.items()},
                "f1": self.f1.to_dict(), "f2": self.f2.to_dict(),
                "values": {k: round(v, 3) for k, v in self.values.items()}, "best": self.best}


def _length(pts) -> float:
    return float(sum(np.linalg.norm(np.asarray(b) - np.asarray(a)) for a, b in zip(pts, pts[1:])))


def _f1_track(rng, route: str, head, t_arrive: float, free_time: float) -> tuple[Track, float]:
    """F1 skates in down the middle, commits to his route `lead` s before the puck gets to you,
    and gets to you `free_time` s after it does, at a steady rec forechecker's speed."""
    contact = head + 0.75 * unit(F1_FROM[route])
    wps = [np.array(w) for w in F1_WAYPOINTS[route]]
    v, lead = rng.uniform(5.5, 7.0), rng.uniform(1.2, 1.8)
    t_c = max(t_arrive - lead, 0.5)
    want = v * (t_arrive + free_time - t_c)                  # path length from the commit to you
    x_c = rng.uniform(-1.5, 1.5)
    zs = np.arange(wps[0][1] + 1.0, 40.0, 0.25)
    lens = np.array([_length([np.array([x_c, z]), *wps, contact]) for z in zs])
    commit = np.array([x_c, zs[int(np.argmin(np.abs(lens - want)))]])
    L_after = _length([commit, *wps, contact])
    v = float(np.clip(L_after / max(t_arrive + free_time - t_c, 0.3), 4.0, 8.0))
    start = commit + unit([rng.uniform(-0.35, 0.35), 1.0]) * v * t_c
    tr = Track([start, commit, *wps, contact], v)
    tr.retime(t_arrive + free_time)                        # smoothing shortened it: arrive on time
    return tr, tr.time_near(commit)


def _f2_track(rng, post: str, mates: dict, t_commit: float) -> Track:
    who, off = F2_POSTS[post]
    spot = (mates[who] if who else np.zeros(2)) + np.array(off) + rng.uniform(-0.4, 0.4, 2)
    v = rng.uniform(4.0, 6.0)
    start = spot + unit([rng.uniform(-0.5, 0.5), 1.0]) * v * (t_commit + 0.8)
    return Track([start, spot], v)


def make_scenario(rng: np.random.Generator, *, free_time: float, blade, head, ice_mu: float,
                  board_bounce: float, want: str | None = None, min_gap: float = 0.25,
                  pass_speed: float = PASS_SPEED, decide_s: float = DECIDE_S, tries: int = 400) -> Scenario:
    """A rep where `want` (or any out) is clearly the best, by at least min_gap in value, for a
    player who passes at pass_speed about decide_s after he has the puck."""
    blade, head = np.asarray(blade, dtype=float), np.asarray(head, dtype=float)
    keep = corner_keep(board_bounce)
    fallback = None
    for _ in range(tries):
        seed = int(rng.integers(1 << 31))
        r = np.random.default_rng(seed)
        mates = {k: np.array(c) + r.uniform(-1, 1, 2) * np.array(j) for k, (c, j) in TEAMMATES.items()}
        v_arrive, z_launch = r.uniform(3.5, 5.0), r.uniform(9.0, 14.0)
        v0, t_arr = rim_launch(z_launch, blade[0], v_arrive, ice_mu, keep)
        route, post = r.choice(list(F1_WAYPOINTS)), r.choice(list(F2_POSTS))
        f1, t_c = _f1_track(r, route, head, t_arr, free_time)
        f2 = _f2_track(r, post, mates, t_c)
        t_dec = t_arr + float(np.clip(decide_s, 0.3, max(0.3, 0.8 * free_time)))
        opps = [(f1.at(t_dec), f1.vel(t_dec)), (f2.at(t_dec), f2.vel(t_dec))]
        vals = {o: option_value(blade, mates[RECEIVER[o]], opps, pass_speed)[0] for o in OPTIONS}
        ranked = sorted(vals, key=vals.get, reverse=True)
        gap = vals[ranked[0]] - vals[ranked[1]]
        sc = Scenario(seed, route, post, free_time, v_arrive, z_launch, v0, t_arr, t_c, blade, head, mates,
                      f1, f2, str(r.choice(["L", "R"])), str(r.choice(["L", "R"])), vals, ranked[0],
                      pass_speed, decide_s)
        if vals[ranked[0]] > 0.5 and gap >= min_gap and (want is None or ranked[0] == want):
            return sc
        if vals[ranked[0]] > 0.5 and (fallback is None or gap > fallback[0]) and (want is None or ranked[0] == want):
            fallback = (gap, sc)
    if fallback is not None:
        return fallback[1]
    return make_scenario(rng, free_time=free_time + 0.3, blade=blade, head=head, ice_mu=ice_mu,
                         board_bounce=board_bounce, want=None, min_gap=min_gap / 2, pass_speed=pass_speed,
                         decide_s=decide_s, tries=tries)


# ----------------------------------------------------------------------------- scanning


class ScanTracker:
    """Shoulder checks from the headset: a look more than AWAY degrees off the puck for at least
    MIN_S, and who was in view (within SEE degrees of where the head points)."""

    AWAY, BACK, MIN_S, SEE = 70.0, 50.0, 0.10, 35.0

    def __init__(self):
        self.scans: list[tuple[float, float, float]] = []      # (start, end, widest angle)
        self._start = None
        self._widest = 0.0
        self.seen: dict[str, list[float]] = {}

    def update(self, t: float, head_xz, fwd_xz, puck_xz, others: dict) -> None:
        head = np.asarray(head_xz, dtype=float)
        to_puck = np.asarray(puck_xz) - head
        if np.linalg.norm(to_puck) > 0.5:
            off = angle_deg(fwd_xz, to_puck)
            if off > self.AWAY:
                if self._start is None:
                    self._start, self._widest = t, off
                self._widest = max(self._widest, off)
            elif off < self.BACK and self._start is not None:
                self._close(t)
        for k, p in others.items():
            if angle_deg(fwd_xz, np.asarray(p) - head) < self.SEE:
                self.seen.setdefault(k, []).append(t)

    def _close(self, t: float) -> None:
        if t - self._start >= self.MIN_S:
            self.scans.append((self._start, t, self._widest))
        self._start = None

    def between(self, t0: float, t1: float) -> list[tuple[float, float, float]]:
        out = [s for s in self.scans if t0 <= s[0] <= t1]
        if self._start is not None and t0 <= self._start <= t1 and t1 - self._start >= self.MIN_S:
            out.append((self._start, t1, self._widest))
        return out

    def saw(self, who: str, t0: float, t1: float) -> bool:
        return any(t0 <= t <= t1 for t in self.seen.get(who, ()))


# ----------------------------------------------------------------------------- one rep


class Rep:
    """One rep, run by update() every physics tick (rep time t, seconds, from when it was made).

    blade: zone (x, z) of your blade's sweet spot, or None while you don't hold the stick.
    head: (zone (x, z) of your head, zone direction it faces), or None.
    Things for the app (voice, sounds, buzz, log) collect in `outbox`."""

    def __init__(self, sc: Scenario, puck: zn.ZonePuck, number: int = 1):
        self.sc, self.puck, self.number = sc, puck, number
        self.skaters = [Skater("F1", "them", sc.f1_shoots, sc.f1.at(0.0), sc.f1),
                        Skater("F2", "them", sc.f2_shoots, sc.f2.at(0.0), sc.f2)]
        self.skaters += [Skater(k, "us", "L" if k == "D" else "R", p.copy(), mode="hold")
                         for k, p in sc.mates.items()]
        self.by_id = {s.id: s for s in self.skaters}
        self.paths = {s.id: [s.pos.copy()] for s in self.skaters if s.team == "them"}   # where they went
        self.state = "ready"
        self.t = 0.0
        self.go_at = READY_S
        self.scan = ScanTracker()
        self.outbox: list[tuple] = []
        self.trail: list[np.ndarray] = []
        self.t_near = self.t_control = self.t_release = self.t_done = None
        self.control_since = None
        self.slow_since = None
        self.last_blade = None
        self.release = None                     # what was open when you let it go
        self.at_control = None
        self.aimed, self.aim_z = False, None     # the rim assist
        self.result: dict | None = None
        self._last_skate = -1.0
        x0 = -(zn.WIDTH / 2) + pk.R
        puck.place(x0, sc.z_launch)

    # -- helpers
    def _xz(self):
        return self.puck.zone.xz(self.puck.pos), self.puck.zone.dir_to_zone(self.puck.vel)

    def _opps(self):
        return [(s.pos.copy(), s.vel.copy()) for s in self.skaters if s.team == "them"]

    def _values(self, p0) -> dict:
        return {o: option_value(p0, self.sc.mates[RECEIVER[o]], self._opps(), self.sc.pass_speed) for o in OPTIONS}

    @property
    def tau(self) -> float:
        """Seconds since the dump-in."""
        return self.t - self.go_at

    # -- the tick
    def update(self, t: float, blade, head) -> None:
        self.t = t
        if self.state == "done":
            return
        if self.state == "ready":
            if t >= self.go_at:
                self.state = "live"
                self.puck.place(-(zn.WIDTH / 2) + pk.R, self.sc.z_launch, 0.0, -self.sc.v_launch)
                self.outbox += [("sound", "go", 1.0), ("buzz", 0.4, 40)]
                self.outbox.append(("log", "rep_go", {"rep": self.number, **self.sc.to_dict()}))
            return
        if blade is not None:
            self.last_blade = np.asarray(blade, dtype=float)
        pxz, pv = self._xz()
        speed = float(np.linalg.norm(pv))
        if t - self._last_skate >= 0.01:
            dt = 0.01 if self._last_skate < 0 else min(t - self._last_skate, 0.05)
            self._last_skate = t
            for s in self.skaters:
                s.step(self.tau, dt, pxz, pv)
                path = self.paths.get(s.id)
                if path is not None and float(np.linalg.norm(s.pos - path[-1])) > 0.25:
                    path.append(s.pos.copy())
            if head is not None:
                self.scan.update(self.tau, head[0], head[1], pxz, {s.id: s.pos for s in self.skaters})
            if not self.trail or np.linalg.norm(pxz - self.trail[-1]) > 0.15:
                self.trail.append(pxz.copy())
        b = self.last_blade
        near = b is not None and float(np.linalg.norm(pxz - b)) < CONTROL_R
        if b is not None and self.t_near is None and float(np.linalg.norm(pxz - b)) < 1.0:
            self.t_near = self.tau
        if self.state == "live":
            self._live(pxz, speed, near, head)
        elif self.state == "control":
            self._control(pxz, pv, speed, near, head)
        elif self.state == "released":
            self._released(pxz, speed, near)

    def _hit(self, pxz, head) -> str | None:
        for s in self.skaters:
            if s.team != "them":
                continue
            if head is not None and float(np.linalg.norm(s.pos - np.asarray(head[0]))) < CONTACT_R:
                return s.id
            if self.t_near is not None and float(np.linalg.norm(s.pos - pxz)) < REACH * 0.8:
                return s.id
        return None

    def _aim(self, pxz, pv) -> None:
        """The rim assist. A puck along the boards is easy to miss in VR, where the boards have no
        feel, so as the puck comes out of the corner it is steered gently off the boards to where
        your blade is (at most AIM_MAX_Z out), as if it had kicked off the corner. Once per rep."""
        b = self.last_blade
        if self.aimed or b is None or pxz[0] < -(zn.WIDTH / 2 - zn.CORNER_R) + 0.2:
            return
        self.aimed = True
        dx = b[0] - pxz[0]
        z_to = float(np.clip(b[1], pk.R, AIM_MAX_Z))
        if dx < 1.0 or pv[0] < 0.5 or z_to <= pxz[1]:
            return
        vz = (z_to - pxz[1]) * pv[0] / dx
        zone = self.puck.zone
        self.puck.vel = zone.dir_to_world(float(pv[0]), vz) + np.array([0.0, self.puck.vel[1], 0.0])
        self.aim_z = round(z_to, 3)

    def _live(self, pxz, speed, near, head) -> None:
        self._aim(pxz, self._xz()[1])
        if near and speed < 2.5:
            self.control_since = self.control_since if self.control_since is not None else self.tau
            if self.tau - self.control_since >= 0.1:
                self.state, self.t_control = "control", self.control_since
                self.at_control = self._values(pxz)
                self.outbox.append(("log", "rep_control", {"rep": self.number, "tau": round(self.t_control, 3)}))
            return
        self.control_since = None
        who = self._hit(pxz, head)
        if who:
            return self._finish("caught", by=who)
        b = self.last_blade
        past = b is not None and pxz[0] > b[0] + 1.8
        stalled = b is not None and speed < 0.2 and float(np.linalg.norm(pxz - b)) > 1.5 and self.tau > 1.0
        if past or stalled or self.tau > self.sc.t_arrive + 3.5:
            self._finish("missed")

    def _control(self, pxz, pv, speed, near, head) -> None:
        who = self._hit(pxz, head)
        if who:
            return self._finish("caught", by=who)
        b = self.last_blade
        gone = float(np.linalg.norm(pxz - b)) if b is not None else 9.0
        if gone > 0.7 and speed > 2.0:
            vals = self._values(pxz)
            choice = self._classify(pxz, pv)
            self.t_release = self.tau
            self.release = {"at": pxz.copy(), "vel": pv.copy(), "speed": speed, "values": vals, "choice": choice}
            for s in self.skaters:
                if s.team == "them":
                    s.react_at = self.tau + REACTION
            self.state = "released"
            self.slow_since = None
        elif gone > 2.5 and speed < 0.5:
            self._finish("loose")

    def _classify(self, pxz, pv) -> str:
        best, ang = "other", 25.0
        for o in OPTIONS:
            a = angle_deg(pv, self.sc.mates[RECEIVER[o]] - pxz)
            if a < ang:
                best, ang = o, a
        return best

    def _released(self, pxz, speed, near) -> None:
        y = float(self.puck.pos[1])
        for s in self.skaters:                                  # their sticks first
            if s.team == "them":
                r = REACH if y < pk.H / 2 + 0.12 else BODY_R
                if float(np.linalg.norm(s.pos - pxz)) < r:
                    return self._finish("intercepted", by=s.id)
        for s in self.skaters:
            if s.team == "us" and y < 0.5 and float(np.linalg.norm(s.pos - pxz)) < RECEIVE_R:
                return self._finish("complete", by=s.id)
        if self.puck.in_net:
            return self._finish("own_goal")
        if self.puck.cleared:
            return self._finish("cleared")
        if near and speed < 2.5:                                # it never really left: still yours
            self.state, self.release = "control", None
            for s in self.skaters:
                if s.team == "them":
                    s.react_at, s.mode = math.inf, ("script" if s.mode == "script" else s.mode)
            return
        if speed < 0.4:
            self.slow_since = self.slow_since if self.slow_since is not None else self.tau
            if self.tau - self.slow_since > 0.8:
                return self._finish("loose")
        else:
            self.slow_since = None
        if self.tau - self.t_release > 6.0:
            self._finish("loose")

    # -- the end of a rep
    def _finish(self, outcome: str, by: str | None = None) -> None:
        self.state, self.t_done = "done", self.tau
        for s in self.skaters:
            s.mode, s.vel = "hold", np.zeros(2)
        if outcome in ("intercepted", "complete"):
            self.puck.vel = np.zeros(3)
        rel = self.release
        if outcome == "complete" and rel is not None:
            rel["choice"] = next(o for o in OPTIONS if RECEIVER[o] == by)
        t_end = self.t_control if self.t_control is not None else self.tau
        looks = self.scan.between(0.0, t_end)
        res = {"rep": self.number, "outcome": outcome, "by": by, "f1_route": self.sc.f1_route,
               "f2_post": self.sc.f2_post, "free_time": round(self.sc.free_time, 3),
               "t_arrive_est": round(self.sc.t_arrive, 3), "t_commit": round(self.sc.t_commit, 3),
               "t_near": _r(self.t_near), "t_control": _r(self.t_control), "t_release": _r(self.t_release),
               "t_done": _r(self.tau),
               "looks": len(looks), "looks_after_commit": len([s for s in looks if s[1] >= self.sc.t_commit]),
               "saw_f1_after_commit": self.scan.saw("F1", self.sc.t_commit, t_end),
               "saw_f2": self.scan.saw("F2", 0.0, t_end),
               "best_planned": self.sc.best,
               "values_planned": {k: round(v, 3) for k, v in self.sc.values.items()},
               "pass_speed": round(self.sc.pass_speed, 2), "decide_s": round(self.sc.decide_s, 2),
               "aim_z": self.aim_z}
        if self.at_control is not None:
            res["values_at_control"] = {k: round(v[0], 3) for k, v in self.at_control.items()}
            res["best_at_control"] = max(self.at_control, key=lambda k: self.at_control[k][0])
        if rel is not None:
            vals = {k: v[0] for k, v in rel["values"].items()}
            best = max(vals, key=vals.get)
            chosen = rel["choice"]
            v_ch = vals.get(chosen, 0.0)
            res.update(choice=chosen, best=best, value_chosen=round(v_ch, 3), value_best=round(vals[best], 3),
                       decision=round(v_ch / max(vals[best], 1e-6), 3),
                       lanes={k: round(v[1], 3) for k, v in rel["values"].items()},
                       release_speed=round(rel["speed"], 2), release_at=rel["at"].round(3).tolist(),
                       latency=_r(self.t_release - self.t_control) if self.t_control is not None else None)
            res["good_read"] = chosen == best or v_ch >= 0.85 * vals[best]
        else:
            res.update(choice=None, best=res.get("best_at_control", self.sc.best), good_read=False)
        res["success"] = outcome == "complete" and res["good_read"]
        res["counts"] = outcome != "missed"                      # a missed puck says nothing about the read
        self.result = res
        self.outbox.append(("say", verdict(res)))
        self.outbox.append(("sound", "whistle" if outcome != "complete" else "go", 0.6))
        self.outbox.append(("log", "rep", res))


def _r(x):
    return None if x is None else round(float(x), 3)


def verdict(res: dict) -> str:
    """What the voice says after a rep: the result, the open out, and the check."""
    out, best, choice = res["outcome"], res.get("best"), res.get("choice")
    best_s = SAY.get(best, "")
    if out == "missed":
        return "Missed the puck."
    if out == "complete" and res["good_read"]:
        head = f"Good. {best_s.capitalize()}."
    elif out == "complete":
        head = f"Complete, but {best_s} was the better play."
    elif out == "intercepted" and res["good_read"]:
        soft = res.get("release_speed", 99) < 0.7 * res.get("pass_speed", PASS_SPEED)
        head = "Right read. Picked off: pass it harder." if soft else "Right read, but picked off."
    elif out == "intercepted":
        head = f"Picked off. {best_s.capitalize()} was open."
    elif out == "caught":
        head = f"Hit. {best_s.capitalize()} was open."
    elif out == "own_goal":
        head = "In our net."
    elif out == "cleared":
        head = f"Cleared it. {best_s.capitalize()} was open."
    else:
        head = f"Loose puck. {best_s.capitalize()} was open."
    if res["looks"] == 0:
        return head + " No shoulder check."
    if res["looks_after_commit"] == 0:
        return head + " You looked too early."
    return head


# ----------------------------------------------------------------------------- difficulty


@dataclass
class Staircase:
    """F1's head start (the free time, s), weighted up/down so it settles near 75% success.

    The first `warmup` counted reps of each session don't move it: getting used to the stick and
    the room again says nothing about the reads."""
    level: float = 2.0
    down: float = 0.15
    up: float = 0.45
    lo: float = 0.6
    hi: float = 3.0
    reps: int = 0
    wins: int = 0
    warmup: int = 5

    def __post_init__(self):
        self.session = 0                        # counted reps this session (not saved)

    @property
    def warming_up(self) -> bool:
        return self.session < self.warmup

    def update(self, success: bool) -> bool:
        """Count a rep; False while warming up (the level stays)."""
        self.session += 1
        if self.session <= self.warmup:
            return False
        self.reps += 1
        self.wins += int(success)
        self.level = float(np.clip(self.level - self.down if success else self.level + self.up, self.lo, self.hi))
        return True

    @classmethod
    def load(cls, path: Path) -> "Staircase":
        try:
            saved = json.loads(Path(path).read_text())["staircase"]
            return cls(**{k: saved[k] for k in ("level", "reps", "wins") if k in saved})   # steps: from the code
        except (OSError, ValueError, KeyError, TypeError):
            return cls()

    def save(self, path: Path, **extra) -> None:
        Path(path).write_text(json.dumps({"staircase": asdict(self), **extra}, indent=2))


class You:
    """How you pass, learned as you play: your pass speed and your time from control to release
    (medians of the last `keep` passes, clamped), so every rep is valued for the passer you are."""

    def __init__(self, speeds=(), decides=(), keep: int = 20):
        self.speeds, self.decides, self.keep = list(speeds)[-keep:], list(decides)[-keep:], keep

    def add(self, res: dict) -> None:
        v, d = res.get("release_speed"), res.get("latency")
        if v is None or not 1.5 <= v <= 25.0:                  # not a pass: a fan, or a physics glitch
            return
        self.speeds = (self.speeds + [float(v)])[-self.keep:]
        if d is not None and 0.0 <= d <= 4.0:
            self.decides = (self.decides + [float(d)])[-self.keep:]

    @property
    def pass_speed(self) -> float:
        return float(np.clip(np.median(self.speeds), 5.0, 12.0)) if len(self.speeds) >= 3 else PASS_SPEED

    @property
    def decide_s(self) -> float:
        return float(np.clip(np.median(self.decides), 0.3, 2.5)) if len(self.decides) >= 3 else DECIDE_S

    def to_dict(self) -> dict:
        return {"speeds": [round(v, 2) for v in self.speeds], "decides": [round(d, 3) for d in self.decides]}

    @classmethod
    def load(cls, path: Path) -> "You":
        try:
            d = json.loads(Path(path).read_text())["you"]
            return cls(d.get("speeds", ()), d.get("decides", ()))
        except (OSError, ValueError, KeyError, TypeError):
            return cls()


class Picker:
    """Which out should be best next: each equally often, shuffled in blocks (no long runs)."""

    def __init__(self, rng: np.random.Generator):
        self.rng, self.bag = rng, []

    def next(self) -> str:
        if not self.bag:
            self.bag = list(self.rng.permutation(OPTIONS))
        return str(self.bag.pop())
