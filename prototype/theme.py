"""The rink's look: a white ice rink aboard a mothership.

The rink is solid: off-white ice, whiter boards with a dark top rail and two light strips, the
painted lines as real-width bands, a ring of light overhead, and a dark hull and space beyond. The
line-drawn markings, players, puck rims and stick go on top. Everything here is triangles for
sandbox.Lines.solid, built in a rink frame (origin, X, Z): (x, z) on the ice, y up.

Comfort (2026-11-10, Jon still got motion sick with no speed to blame):
- no ice grid by default (the "ice grid" setting); a real rink has none, and every line sliding past
  under you adds motion your inner ear doesn't feel;
- what's round the rink is plain, and what has detail (the light ring, the hull's light seam) is far
  away: the farther something is, the slower it slides past as you skate;
- the ice is off-white, not full white: a big bright field flickers more at 72 Hz.
"""

from __future__ import annotations

import numpy as np


def srgb(r: float, g: float, b: float) -> tuple[float, float, float]:
    """A colour as it should look in the headset (sRGB, 0-255) -> the value to draw. The runtime takes
    the RGBA8 swapchain's values as linear and encodes them for the display, so a value v shows as
    sRGB(v): the README GIFs' background, drawn as (0.05, 0.06, 0.09), shows as (63, 69, 84)."""
    def lin(c: float) -> float:
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(r), lin(g), lin(b))


SKY = srgb(10, 13, 24)           # space: the clear colour
HULL = srgb(24, 30, 44)          # the mothership's walls round the rink
SEAM = srgb(40, 120, 160)        # a dim seam of light round the hull
HALO = srgb(60, 150, 190)        # the ring of light overhead: dim, so it doesn't pull at your eye
GLOW = srgb(60, 210, 255)        # the light strips on the boards
ICE = srgb(222, 230, 238)        # white, a touch blue
ICE_EDGE = srgb(192, 202, 214)   # the ice greys toward the boards, so floor and wall read apart
BOARD = srgb(244, 245, 247)      # whiter than the ice
RAIL = srgb(70, 78, 92)          # the top rail
GRID = srgb(178, 190, 206)       # the ice grid, when it's on: faint
RED, BLUE = srgb(205, 25, 45), srgb(25, 70, 190)     # the painted lines
CREASE = srgb(120, 180, 240)
MESH = srgb(140, 145, 155)       # the nets' mesh: grey, so it shows against white boards
PUCK = srgb(12, 12, 14)
PUCK_EDGE = srgb(120, 125, 135)  # the puck's rims: a black puck still shows against the dark overhead
SHAFT, SHAFT_LOOSE = srgb(40, 44, 52), srgb(150, 156, 166)
BLADE, BLADE_LOOSE = srgb(220, 30, 170), srgb(170, 120, 165)   # magenta: shows on white ice and by a black puck
PANEL = srgb(14, 18, 30)         # behind the drills' replay map
# players (figures.py): deep enough to show against white ice and boards
US, THEM, GOALIE = srgb(25, 95, 210), srgb(235, 95, 10), srgb(205, 145, 10)
GREEN, TRAIL = srgb(20, 160, 70), srgb(40, 42, 50)  # the drills' best play and the puck's path, on the ice

ICE_Y = -0.006                   # the ice sits just under y = 0, so what's drawn at 0 shows on top
PAINT_Y = -0.003                 # painted lines: over the ice, under the 1-pixel marking lines
EDGE_FADE = 2.0                  # m: the ice darkens over this much next to the boards
WIDE, THIN = 12 * 0.0254, 2 * 0.0254    # red and blue lines 12 inches wide; goal lines and circles 2
RAIL_W = 0.10                    # m: the top rail, outward from the boards' face
STRIP = 0.04                     # m: each light strip's height
UP = np.array([0.0, 1.0, 0.0])


class Surf:
    """Triangles in a rink frame: world = origin + x X + y up + z Z. solid(P, colour) takes the
    triangles' corners (3n, 3) with one colour (3,) or a colour per corner (3n, 3)."""

    def __init__(self, solid, origin, X, Z):
        self.solid = solid
        self.o = np.array([origin[0], 0.0, origin[2]], dtype=float)
        self.X, self.Z = np.asarray(X, dtype=float), np.asarray(Z, dtype=float)

    def w(self, xz, y) -> np.ndarray:
        """(x, z) points (n, 2) at height y (a number or one per point) -> world (n, 3)."""
        xz = np.asarray(xz, dtype=float).reshape(-1, 2)
        y = np.broadcast_to(np.asarray(y, dtype=float), (len(xz),))
        return self.o + xz[:, :1] * self.X + xz[:, 1:] * self.Z + y[:, None] * UP

    def quads(self, a, b, c, d, ca, cb=None, cc=None, cd=None) -> None:
        """Quads a-b-c-d (each (n, 3) world points), one colour or one per corner."""
        P = np.stack([a, b, c, a, c, d], axis=1).reshape(-1, 3)
        if cb is None:
            self.solid(P, ca)
            return
        n = len(a)
        C = [np.broadcast_to(np.asarray(k, dtype=float), (n, 3)) for k in (ca, cb, cc, cd)]
        self.solid(P, np.stack([C[0], C[1], C[2], C[0], C[2], C[3]], axis=1).reshape(-1, 3))

    def fan(self, ring, y, col) -> None:
        """A convex polygon (n, 2), filled from its middle."""
        ring = np.asarray(ring, dtype=float)
        c = np.repeat(ring.mean(axis=0)[None], len(ring), axis=0)
        P = np.stack([self.w(c, y), self.w(ring, y), self.w(np.roll(ring, -1, axis=0), y)], axis=1)
        self.solid(P.reshape(-1, 3), col)

    def band(self, a, b, width, y, col) -> None:
        """A painted line from a to b (x, z), width across."""
        a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        t = (b - a) / max(float(np.linalg.norm(b - a)), 1e-9)
        n = np.array([-t[1], t[0]]) * width / 2
        self.quads(self.w(a - n, y), self.w(b - n, y), self.w(b + n, y), self.w(a + n, y), col)

    def arc(self, c, r, width, y, col, a0=0.0, a1=2 * np.pi, n=40) -> None:
        """A painted circle (or part of one) of radius r, width across."""
        a = np.linspace(a0, a1, n + 1)
        u = np.stack([np.cos(a), np.sin(a)], axis=1)
        c = np.asarray(c, dtype=float)
        lo, hi = c + u * (r - width / 2), c + u * (r + width / 2)
        self.quads(self.w(lo[:-1], y), self.w(lo[1:], y), self.w(hi[1:], y), self.w(hi[:-1], y), col)

    def disc(self, c, r, y, col, a0=0.0, a1=2 * np.pi, n=24) -> None:
        a = np.linspace(a0, a1, n + 1)
        ring = np.asarray(c, dtype=float) + r * np.stack([np.cos(a), np.sin(a)], axis=1)
        mid = np.repeat(np.asarray(c, dtype=float)[None], n, axis=0)
        P = np.stack([self.w(mid, y), self.w(ring[:-1], y), self.w(ring[1:], y)], axis=1)
        self.solid(P.reshape(-1, 3), col)


def inward(pts, closed: bool) -> np.ndarray:
    """Each point's inward offset direction (mitred, so an inset of d stays d from every side) along
    a polyline (n, 2) round a convex region. Closed: the last point joins the first."""
    p = np.asarray(pts, dtype=float)
    mid = p.mean(axis=0)
    e = (np.roll(p, -1, axis=0) - p) if closed else np.diff(p, axis=0)
    nrm = np.stack([-e[:, 1], e[:, 0]], axis=1) / np.maximum(np.linalg.norm(e, axis=1), 1e-9)[:, None]
    centre = (p + np.roll(p, -1, axis=0)) / 2 if closed else (p[:-1] + p[1:]) / 2
    nrm *= np.where(np.sum(nrm * (mid - centre), axis=1) < 0, -1.0, 1.0)[:, None]
    before = np.roll(nrm, 1, axis=0) if closed else np.vstack([nrm[:1], nrm])
    after = nrm if closed else np.vstack([nrm, nrm[-1:]])
    m = before + after
    m /= np.maximum(np.linalg.norm(m, axis=1), 1e-9)[:, None]
    return m / np.maximum(np.sum(m * after, axis=1), 0.5)[:, None]


def ice(s: Surf, ring) -> None:
    """The ice inside a convex outline (n, 2, not repeating its first point): darker by the boards."""
    out = np.asarray(ring, dtype=float)
    inn = out + inward(out, closed=True) * EDGE_FADE
    s.quads(s.w(out, ICE_Y), s.w(np.roll(out, -1, axis=0), ICE_Y), s.w(np.roll(inn, -1, axis=0), ICE_Y),
            s.w(inn, ICE_Y), ICE_EDGE, ICE_EDGE, ICE, ICE)
    s.fan(inn, ICE_Y, ICE)


def boards(s: Surf, pts, height: float, closed: bool = True) -> None:
    """The boards along a polyline (n, 2) round the ice: a white face, a dark rail on top, a light
    strip under the rail and one along the ice."""
    p = np.asarray(pts, dtype=float)
    m = inward(p, closed)
    if closed:
        p, m = np.vstack([p, p[:1]]), np.vstack([m, m[:1]])
    a, b, ma, mb = p[:-1], p[1:], m[:-1], m[1:]
    h = height
    s.quads(s.w(a, ICE_Y), s.w(b, ICE_Y), s.w(b, h), s.w(a, h), BOARD)
    s.quads(s.w(a, h), s.w(b, h), s.w(b - mb * RAIL_W, h), s.w(a - ma * RAIL_W, h), RAIL)
    a_in, b_in = a + ma * 0.004, b + mb * 0.004                     # just off the face
    for y0 in (h - 0.06 - STRIP, ICE_Y):
        s.quads(s.w(a_in, y0), s.w(b_in, y0), s.w(b_in, y0 + STRIP), s.w(a_in, y0 + STRIP), GLOW)


def board_lines(line, W, pts, height: float) -> None:
    """The boards' edges as 1-pixel lines too, so they stay unbroken far off: the rail and the strip
    along the ice. W(x, y, z) -> world."""
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        line(W(x0, height, z0), W(x1, height, z1), RAIL)
        line(W(x0, 0.012, z0), W(x1, 0.012, z1), GLOW)


def mothership(s: Surf, ring, top: float = 20.0) -> None:
    """Round the rink: the hull's walls, well back, with a dim seam of light; a ring of light
    overhead, 18 m up. ring: the boards' outline (n, 2, not repeating its first point)."""
    ring = np.asarray(ring, dtype=float)
    into = inward(ring, closed=True)
    wall = ring - into * 9.0                                        # 9 m behind the boards
    a, b = wall, np.roll(wall, -1, axis=0)
    s.quads(s.w(a, -0.5), s.w(b, -0.5), s.w(b, top), s.w(a, top), HULL)
    face = wall + inward(wall, closed=True) * 0.02                  # the seam, just off the wall
    fa, fb = face, np.roll(face, -1, axis=0)
    s.quads(s.w(fa, 3.0), s.w(fb, 3.0), s.w(fb, 3.1), s.w(fa, 3.1), SEAM)
    halo = ring + into * 5.0                                        # the ring of light, 18 m up
    inner = halo + into * 0.5
    s.quads(s.w(halo, 18.0), s.w(np.roll(halo, -1, axis=0), 18.0), s.w(np.roll(inner, -1, axis=0), 18.0),
            s.w(inner, 18.0), HALO)


def puck(P, r: float, h: float, n: int = 16) -> np.ndarray:
    """A solid puck at P (its middle): triangles (k, 3) in the world."""
    a = np.linspace(0, 2 * np.pi, n + 1)
    rim = np.stack([np.cos(a) * r, np.zeros_like(a), np.sin(a) * r], axis=1) + np.asarray(P, dtype=float)
    lo, hi = rim - [0, h / 2, 0], rim + [0, h / 2, 0]
    top = np.asarray(P, dtype=float) + [0, h / 2, 0]
    side = np.stack([lo[:-1], lo[1:], hi[1:], lo[:-1], hi[1:], hi[:-1]], axis=1).reshape(-1, 3)
    cap = np.stack([np.repeat(top[None], n, axis=0), hi[:-1], hi[1:]], axis=1).reshape(-1, 3)
    return np.vstack([side, cap])
