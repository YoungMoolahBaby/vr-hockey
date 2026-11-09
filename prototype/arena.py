"""The whole rink for the 3v3 game: both ends, both nets, regulation width and corners, and
shorter than regulation (LENGTH) so three a side isn't a marathon on a thumbstick.

Arena frame = the home end's zone frame (zone.py): x across the rink (+ = the home team's left
looking up ice), y up, z from the home end boards (z = 0) to the far end boards (z = length).
The home net is at z = GOAL_Z facing up ice; the far net at length - GOAL_Z facing back. The far
half is the home half turned 180 degrees about centre ice: arena (x, z) <-> far-end zone frame
(-x, length - z). So the far end's boards, net and goalie reuse zone.py and goalie.py as they are.
"""

from __future__ import annotations

import numpy as np

import puck as pk
import zone as zn

FT = zn.FT
LENGTH = 46.0                       # m end boards to end boards (regulation: 61)
CENTER_R = 15 * FT                  # centre-ice circle
BLUE_FRAC = 75 / 200                # blue lines: as far from the end boards as on a regulation rink, scaled


class Arena:
    def __init__(self, zone: zn.Zone, length: float = LENGTH):
        """zone: the home end's zone (its origin at the home end boards, +z up ice)."""
        self.zone = zone
        self.length = float(length)
        self.far = zn.Zone(zone.to_world(0.0, 0.0, self.length), -zone.Z)   # the far end, as its own zone
        self.blue = (self.length * BLUE_FRAC, self.length * (1 - BLUE_FRAC))

    @property
    def mid(self) -> float:
        return self.length / 2

    def mirror(self, xz) -> np.ndarray:
        """Arena (x, z) <-> the far end's zone frame (the same map both ways)."""
        p = np.asarray(xz, dtype=float)
        return np.array([-p[0], self.length - p[1]])

    def net(self, end: str) -> np.ndarray:
        """The middle of a goal line: end "home" or "far"."""
        return np.array([0.0, zn.GOAL_Z if end == "home" else self.length - zn.GOAL_Z])

    def boards_contact(self, x: float, z: float, r: float):
        """(penetration, inward normal (nx, nz)) of a disc against the boards, or None."""
        if z <= self.length / 2:
            return zn.boards_contact(x, z, r)
        hit = zn.boards_contact(-x, self.length - z, r)
        if hit is None:
            return None
        pen, (nx, nz) = hit
        return pen, (-nx, -nz)

    def keep_on_ice(self, xz, r: float) -> np.ndarray:
        """A skater (a disc of radius r) pushed back inside the boards."""
        x, z = float(xz[0]), float(xz[1])
        hit = self.boards_contact(x, z, r)
        if hit is not None:
            pen, (nx, nz) = hit
            x, z = x + nx * pen, z + nz * pen
        return np.array([x, z])

    def to_dict(self) -> dict:
        return {**self.zone.to_dict(), "length": self.length}


class ArenaPuck(zn.ZonePuck):
    """A puck on the whole rink: rounded boards at both ends, both nets. in_net: 0, 1 (the home
    net) or 2 (the far net); a puck going in posts ("net", speed) or ("net2", speed)."""

    def __init__(self, params: pk.Params, arena: Arena):
        super().__init__(params, arena.zone)
        self.arena_length = arena.length
        self.in_net = 0

    def spawn(self, pos_xz) -> None:
        super().spawn(pos_xz)
        self.in_net = 0

    def _rink(self, h: float) -> None:
        zn_, pr, L = self.zone, self.params, self.arena_length
        x, y, z = zn_.to_zone(self.pos)
        vx, vz = float(self.vel @ zn_.X), float(self.vel @ zn_.Z)
        far = z > L / 2
        if far:                                           # into the far end's own frame
            x, z, vx, vz = -x, L - z, -vx, -vz
        hit = zn.boards_contact(x, z, pk.R)
        if hit is not None:
            pen, (nx, nz) = hit
            x, z = x + nx * pen, z + nz * pen
            if -(vx * nx + vz * nz) > 0.5:
                self.events.append(("boards", float(np.hypot(vx, vz))))
            vx, vz = zn.bounce(vx, vz, nx, nz, pr.board_bounce, zn.BOARD_MU)
        was = self.in_net
        x, z, vx, vz = self._net(x, y, z, vx, vz, h)
        if self.in_net and not was:
            self.in_net = 2 if far else 1
            if far:
                self.events[-1] = ("net2", self.events[-1][1])
        if far:
            x, z, vx, vz = -x, L - z, -vx, -vz
        self.pos = zn_.to_world(x, y, z)
        self.vel = vx * zn_.X + vz * zn_.Z + np.array([0.0, self.vel[1], 0.0])


# ----------------------------------------------------------------------------- drawing


def outline(arena: Arena, n: int = 12) -> list[tuple[float, float]]:
    """The boards all the way round (arena x, z), closed."""
    half, R, L = zn.WIDTH / 2, zn.CORNER_R, arena.length
    pts = []
    for a in np.linspace(0, np.pi / 2, n):                                   # home end, left corner
        pts.append((half - R + R * np.cos(a), R - R * np.sin(a)))
    for a in np.linspace(np.pi / 2, np.pi, n):                               # home end, right corner
        pts.append((-(half - R) + R * np.cos(a), R - R * np.sin(a)))
    for a in np.linspace(np.pi, 1.5 * np.pi, n):                             # far end, right corner
        pts.append((-(half - R) + R * np.cos(a), L - R - R * np.sin(a)))
    for a in np.linspace(1.5 * np.pi, 2 * np.pi, n):                         # far end, left corner
        pts.append((half - R + R * np.cos(a), L - R - R * np.sin(a)))
    pts.append(pts[0])
    return pts


def side_x(arena: Arena, z: float) -> float:
    """Half the ice's width at this z."""
    return zn.side_boards_x(min(z, arena.length - z))


def markings(arena: Arena, line) -> None:
    """The rink: boards (bottom and top rail), a 2 m ice grid, goal lines, blue lines, the red
    line, the circles, both creases and both nets."""
    zone, L, half = arena.zone, arena.length, zn.WIDTH / 2
    W = zone.to_world
    pts = outline(arena)
    for y in (0.0, zn.BOARDS_H):
        for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
            line(W(x0, y, z0), W(x1, y, z1), zn.BOARDS)
    for x, z in pts[::4]:
        line(W(x, 0, z), W(x, zn.BOARDS_H, z), zn.BOARDS)
    for gx in np.arange(-12, 12.1, 2.0):                                     # ice grid, every 2 m
        e = zn.end_boards_z(gx)
        line(W(gx, 0, e), W(gx, 0, L - e), zn.ICE)
    for gz in np.arange(2.0, L - 1.0, 2.0):
        k = side_x(arena, gz)
        line(W(-k, 0, gz), W(k, 0, gz), zn.ICE)
    for gz in (zn.GOAL_Z, L - zn.GOAL_Z):                                    # goal lines
        k = side_x(arena, gz)
        line(W(-k, 0.003, gz), W(k, 0.003, gz), zn.RED)
    for bz in arena.blue:                                                    # blue lines, red line
        for dz in (-0.15, 0.15):
            line(W(-half, 0.003, bz + dz), W(half, 0.003, bz + dz), zn.BLUE)
    for dz in (-0.15, 0.0, 0.15):
        line(W(-half, 0.003, L / 2 + dz), W(half, 0.003, L / 2 + dz), zn.RED)
    a = np.linspace(0, 2 * np.pi, 41)                                        # centre circle and dot
    ring = [W(CENTER_R * np.cos(t), 0.004, L / 2 + CENTER_R * np.sin(t)) for t in a]
    for p0, p1 in zip(ring, ring[1:]):
        line(p0, p1, zn.BLUE)
    dot = [W(0.3 * np.cos(t), 0.005, L / 2 + 0.3 * np.sin(t)) for t in a[::4]]
    for p0, p1 in zip(dot, dot[1:]):
        line(p0, p1, zn.BLUE)
    for end in (zone, arena.far):                                            # each end: crease, circles, net
        Z = end.to_world
        c = np.linspace(0, np.pi, 15)
        cr = [Z(zn.CREASE_R * np.cos(t), 0.003, zn.GOAL_Z + zn.CREASE_R * np.sin(t)) for t in c]
        for p0, p1 in zip(cr, cr[1:]):
            line(p0, p1, zn.BLUE)
        a = np.linspace(0, 2 * np.pi, 33)
        for sx in (-zn.CIRCLE_X, zn.CIRCLE_X):
            ring = [Z(sx + zn.CIRCLE_R * np.cos(t), 0.003, zn.CIRCLE_Z + zn.CIRCLE_R * np.sin(t)) for t in a]
            for p0, p1 in zip(ring, ring[1:]):
                line(p0, p1, zn.RED)
        zn.net(end, line)


# a seven-segment scoreboard: segments as (x0, y0, x1, y1) on a 1 x 2 digit
_SEG = {"a": (0, 2, 1, 2), "b": (1, 2, 1, 1), "c": (1, 1, 1, 0), "d": (0, 0, 1, 0), "e": (0, 0, 0, 1),
        "f": (0, 1, 0, 2), "g": (0, 1, 1, 1)}
_DIGITS = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc",
           "7": "abc", "8": "abcdefg", "9": "abcdfg", "-": "g"}


def scoreboard(arena: Arena, line, home: int, away: int, colors, at_z: float | None = None,
               height: float = 5.0, size: float = 0.5) -> None:
    """The score hanging over centre ice, readable from both ends: home (in colors[0]) - away."""
    zone = arena.zone
    z0 = arena.mid if at_z is None else at_z
    text = [(str(home), colors[0]), ("-", (0.8, 0.8, 0.8)), (str(away), colors[1])]
    chars = [(ch, col) for s, col in text for ch in s]
    width = len(chars) * 1.5 - 0.5
    for face in (1.0, -1.0):                         # one face toward each end
        for i, (ch, col) in enumerate(chars):
            x_left = -width / 2 + i * 1.5
            for s in _DIGITS.get(ch, ""):
                x0, y0, x1, y1 = _SEG[s]
                # facing the home end (face 1) the text runs to the viewer's right = arena -x
                a = zone.to_world(-face * (x_left + x0) * size, height + y0 * size, z0 - face * 0.05)
                b = zone.to_world(-face * (x_left + x1) * size, height + y1 * size, z0 - face * 0.05)
                line(a, b, col)
