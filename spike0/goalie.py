"""A rec goalie for the drills: where he plays, what he sees, the saves he makes, and the expected
goals (xG) of a shot against him. The drill's value model and its simulated goalie are the same
model, so "this pass was worth more than that shot" and what then happens in the rep agree.

Zone frame as in zone.py: the net he guards is at the end boards (z = 0), its goal line at
GOAL_Z; shooters come from up ice (larger z).

- Positioning: on the line from the middle of the net to the puck, DEPTH out, following where the
  puck was TRACK_REACT ago, moving at most TRACK_SPEED (a shuffle or a T-push).
- Screens: he loses the puck while a skater's body is on his line of sight. A screened shot is
  picked up only SEE_DIST from him.
- A save: SAVE_REACT after he picks a shot up, he moves along his line at up to SAVE_SPEED toward
  where it will cross. He is in the butterfly: wide pads low, body and arms through the middle,
  head and shoulders up top (BANDS). A puck through his plane d metres outside that shape (after
  his move) is saved with chance sig(-d / SOFT): a reach is never quite all-or-nothing.
- Shooters miss by about SIGMA_PER_M per metre of distance (at least SIGMA_MIN) and aim where it
  pays most.
"""

from __future__ import annotations

import collections
import math

import numpy as np

import zone as zn

NET_C = np.array([0.0, zn.GOAL_Z])
DEPTH = 0.6              # m out from the goal line, on his angle
TRACK_SPEED = 2.0        # m/s: shuffling / pushing across (a rec goalie)
TRACK_REACT = 0.18       # s: he follows where the puck was this long ago
SAVE_SPEED = 2.5         # m/s: arms, pads and body reaching for a shot
SAVE_REACT = 0.20        # s
SOFT = 0.15              # m: how sharp the edge of his reach is
SEE_DIST = 9.0           # m: a screened shot is picked up only this close
SCREEN_R = 0.32          # m: a body this close to his line of sight blocks it
BANDS = ((0.0, 0.30, 0.75), (0.30, 0.95, 0.42), (0.95, 1.15, 0.25))   # (y from, y to, half width)
SIGMA_PER_M = 0.012      # m of aim error per metre of shot distance (a rec shooter)
SIGMA_MIN = 0.08         # m
MOUTH = (zn.NET_HALF_W - 0.04, zn.NET_H - 0.04)                       # where a puck counts (x, y)


def unit(v) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-9 else np.zeros_like(v)


def sig(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -40, 40)))


def home(puck_xz) -> np.ndarray:
    """Where he wants to be for a puck there: on its line to the middle of the net, DEPTH out."""
    d = np.asarray(puck_xz, dtype=float) - NET_C
    if d[1] < 0.2:                                   # behind the goal line: hug that post
        return NET_C + np.array([np.sign(d[0]) * (zn.NET_HALF_W - 0.25), 0.25])
    return NET_C + DEPTH * unit(d)


def half_width(y):
    """His butterfly's half width at height y (m); 0 above his head."""
    y = np.asarray(y, dtype=float)
    return np.select([y < BANDS[0][1], y < BANDS[1][1], y < BANDS[2][1]], [b[2] for b in BANDS], 0.0)


def blocks_sight(eye, puck, bodies) -> bool:
    """Is any body (zone x, z) on the line from his eyes to the puck, between them?"""
    e, p = np.asarray(eye, dtype=float), np.asarray(puck, dtype=float)
    d = p - e
    L = float(np.linalg.norm(d))
    if L < 1e-6:
        return False
    d /= L
    for b in bodies:
        r = np.asarray(b, dtype=float) - e
        s = float(r @ d)
        if 0.6 < s < L - 0.6 and abs(r[0] * d[1] - r[1] * d[0]) < SCREEN_R:
            return True
    return False


def sigma(origin) -> float:
    dist = float(np.hypot(origin[0], origin[1] - zn.GOAL_Z))
    return max(SIGMA_PER_M * dist, SIGMA_MIN)


class Goalie:
    def __init__(self, puck_xz=(0.0, 20.0)):
        self.c = home(puck_xz)
        self.facing = unit(np.asarray(puck_xz, dtype=float) - self.c)
        self.seen = collections.deque()               # (t, puck xz) he has seen
        self.sees = True
        self.shot = None                              # the shot he is reacting to
        self.mode = "track"                           # track -> save -> done
        self.last_s = None

    @property
    def t_axis(self) -> np.ndarray:
        """His lateral axis (his left), along the plane he blocks."""
        return np.array([self.facing[1], -self.facing[0]])

    def step(self, t: float, dt: float, puck_xz, puck_v, bodies) -> None:
        if self.mode == "done":
            return
        p = np.asarray(puck_xz, dtype=float)
        self.sees = not blocks_sight(self.c, p, bodies)
        # he keeps his angle on the puck even behind a screen (he reads the passer, the sticks,
        # the sound); what a screen costs him is picking up the shot (see "save")
        self.seen.append((t, p.copy()))
        while len(self.seen) > 1 and self.seen[1][0] <= t - TRACK_REACT:
            self.seen.popleft()
        if self.mode == "track":
            if self.seen:
                q = self.seen[0][1]
                self._move(home(q), TRACK_SPEED, dt)
                if np.linalg.norm(q - self.c) > 0.3:
                    self.facing = unit(q - self.c)
            if shot_coming(p, puck_v):
                self.mode, self.shot = "save", {"t": t, "picked": None}
        elif self.mode == "save":
            sh = self.shot
            if sh["picked"] is None and (self.sees or float(np.linalg.norm(p - self.c)) < SEE_DIST):
                sh["picked"] = t
            if sh["picked"] is not None and t - sh["picked"] >= SAVE_REACT:
                u = self.crossing_u(p, puck_v)
                if u is not None:
                    self.c = self.c + float(np.clip(u, -SAVE_SPEED * dt, SAVE_SPEED * dt)) * self.t_axis
            if not shot_coming(p, puck_v):
                self.mode = "track"

    def _move(self, target, speed: float, dt: float) -> None:
        d = np.asarray(target) - self.c
        n = float(np.linalg.norm(d))
        if n > 1e-9:
            self.c = self.c + d * min(1.0, speed * dt / n)

    def crossing_u(self, p, v) -> float | None:
        """Where (along his lateral axis) a puck at p moving v crosses his plane, or None."""
        n = self.facing
        s = float((np.asarray(p) - self.c) @ n)
        vn = float(np.asarray(v) @ n)
        if vn >= -1e-6 or s < 0:
            return None
        q = np.asarray(p) + np.asarray(v) * (s / -vn)
        return float((q - self.c) @ self.t_axis)

    def check(self, p_xz, y: float, rng) -> str | None:
        """Every tick with the puck: "save" when it goes through his plane and he gets a piece."""
        s = float((np.asarray(p_xz) - self.c) @ self.facing)
        prev, self.last_s = self.last_s, s
        if prev is None or not (prev > 0 >= s) or y > 1.6:
            return None
        u = float((np.asarray(p_xz) - self.c) @ self.t_axis)
        d = abs(u) - float(half_width(y))
        if rng.random() < float(sig(-d / SOFT)):
            self.mode = "done"
            return "save"
        return None


def shot_coming(p, v) -> bool:
    """A puck moving fast toward the net, on a line that ends near it."""
    p, v = np.asarray(p, dtype=float), np.asarray(v, dtype=float)
    if float(np.linalg.norm(v)) < 8.0 or v[1] >= 0 or p[1] < zn.GOAL_Z:
        return False
    x_at = p[0] + v[0] * (zn.GOAL_Z - p[1]) / v[1]
    return abs(x_at) < zn.NET_HALF_W + 1.0


# ----------------------------------------------------------------------------- expected goals

_GX = np.linspace(-1.35, 1.35, 28)
_GY = np.linspace(0.02, 1.55, 16)
GX, GY = np.meshgrid(_GX, _GY)                       # where a shot can end up at the goal line
ON_NET = (np.abs(GX) <= MOUTH[0]) & (GY <= MOUTH[1])


def goal_chance(origin, speed: float, goalie_c, sees: bool, y0: float = 0.02) -> np.ndarray:
    """For every grid point on the goal line: the chance a shot there from `origin` (zone x, z)
    at `speed` beats a goalie centred at goalie_c facing the shooter (who saw it or not)."""
    o, c = np.asarray(origin, dtype=float), np.asarray(goalie_c, dtype=float)
    n = unit(o - c)
    tax = np.array([n[1], -n[0]])
    dx, dz = GX - o[0], zn.GOAL_Z - o[1]
    L = np.hypot(dx, dz)
    denom = dx * n[0] + dz * n[1]                    # where each path crosses his plane
    ok = np.abs(denom) > 1e-9
    f = np.clip(np.where(ok, -((o - c) @ n) / np.where(ok, denom, 1.0), 1.0), 0.0, 1.0)
    u = (o[0] + f * dx - c[0]) * tax[0] + (o[1] + f * dz - c[1]) * tax[1]
    y = y0 + f * (GY - y0)                           # rising roughly straight to its height
    t_fly = f * L / speed
    t_seen = t_fly if sees else np.minimum(t_fly, SEE_DIST / speed)
    reach = SAVE_SPEED * np.maximum(t_seen - SAVE_REACT, 0.0)
    d = np.abs(u) - half_width(y) - reach
    return np.where(ON_NET, 1.0 - sig(-d / SOFT), 0.0)


def shot_xg(origin, speed: float, goalie_c, sees: bool, clean: float = 1.0):
    """(chance of a goal, the aim point (x, y)). The shooter aims where it pays most and misses by
    about sigma(origin); clean = the chance he gets it off cleanly (a one-timer can be fanned)."""
    o = np.asarray(origin, dtype=float)
    g = goal_chance(o, speed, goalie_c, sees)
    if g.max() < 1e-4:
        return 0.0, (0.0, 0.5)
    s = sigma(o)
    # the payoff of aiming at each grid point = the goal chance blurred by the aim error
    kx = np.exp(-((_GX[:, None] - _GX[None, :]) ** 2) / (2 * s * s))
    ky = np.exp(-((_GY[:, None] - _GY[None, :]) ** 2) / (2 * s * s))
    kx /= kx.sum(axis=0, keepdims=True)
    ky /= ky.sum(axis=0, keepdims=True)
    pay = ky.T @ g @ kx                              # [aim y, aim x]
    pay = np.where(ON_NET, pay, 0.0)
    i, j = np.unravel_index(int(np.argmax(pay)), pay.shape)
    return float(pay[i, j]) * clean, (float(GX[i, j]), float(GY[i, j]))


def after_tracking(goalie_c, to_puck_xz, seconds: float) -> np.ndarray:
    """Where a tracking goalie gets to, `seconds` after the puck moved to `to_puck_xz`."""
    target = home(to_puck_xz)
    d = target - np.asarray(goalie_c, dtype=float)
    n = float(np.linalg.norm(d))
    step = TRACK_SPEED * max(seconds - TRACK_REACT, 0.0)
    return target if n <= step else np.asarray(goalie_c) + d * step / n


def launch(origin, aim, speed: float, y0: float = 0.02, g: float = 9.81) -> np.ndarray:
    """Zone velocity (vx, vy, vz) that sends a puck from origin (x, z) to the goal line at aim (x, y)."""
    o = np.asarray(origin, dtype=float)
    d = np.array([aim[0] - o[0], zn.GOAL_Z - o[1]])
    T = float(np.linalg.norm(d)) / speed
    vy = (aim[1] - y0) / T + g * T / 2
    return np.array([d[0] / T, vy, d[1] / T])


def aimed(rng, aim, origin, wild: float = 1.0):
    """Where a shot aimed at `aim` actually goes."""
    s = sigma(origin) * wild
    return (aim[0] + rng.normal(0, s), max(0.03, aim[1] + rng.normal(0, s)))


__all__ = ["Goalie", "home", "shot_xg", "goal_chance", "after_tracking", "launch", "aimed", "blocks_sight",
           "half_width", "shot_coming", "sigma", "math"]
