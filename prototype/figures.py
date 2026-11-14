"""Line-drawn skaters for the drills: legs that stride, a body that leans into speed, a head, and
a stick with its blade on the ice on his shooting side. Plus a ring on the ice in his team's
colour, so a glance tells you who is who and where. On their feet, Jon's custom skates (gear.py)
when custom-skate's build is there, turning out and onto their inside edges as they push; else a
line for each blade.

Built in the skater's own frame (forward, his left, up) and moved into the world in one numpy
step: drawing runs in the render thread, which shares Python's lock with the 1 kHz physics."""

from __future__ import annotations

import functools

import numpy as np

import gear
import theme
from threes import BLADE_AT

US, THEM, YOU = theme.US, theme.THEM, (1.0, 0.9, 0.2)     # YOU: on the drills' dark map only
_C = np.linspace(0, 2 * np.pi, 13)
_RING_A = np.stack([0.5 * np.cos(_C[:-1]), 0.5 * np.sin(_C[:-1]), np.full(12, 0.006)], axis=1)
_RING_B = np.stack([0.5 * np.cos(_C[1:]), 0.5 * np.sin(_C[1:]), np.full(12, 0.006)], axis=1)


LEGS = ((0.12, 1.0), (-0.12, -1.0))                     # (hip's offset to his left, sign): left leg, right leg


def _stride(stride: float, speed: float) -> tuple[float, float, float]:
    """How far into his top speed he is (0-1), the stride's phase (rad) and its reach (m)."""
    return min(speed / 7.0, 1.0), stride / 1.7 * 2 * np.pi, 0.32 * min(speed / 3.0, 1.0)


def _foot(side: float, sgn: float, ph: float, amp: float) -> tuple[float, float, float]:
    """A foot: how far forward it is (m), how far out (m), and how far into its push back (0-1)."""
    push = amp * np.sin(ph) * sgn
    ext = max(0.0, -push / 0.32)
    return push, side * (1.4 + 1.2 * ext), ext


def _local(shoots: str, stride: float, speed: float, ring: bool, blades: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Segment ends (A, B), each (n, 3) as (forward, left, up) in metres."""
    return _local_cached(shoots, round(stride, 2), round(speed, 1), ring, blades)


@functools.lru_cache(maxsize=512)
def _local_cached(shoots: str, stride: float, speed: float, ring: bool, blades: bool) -> tuple[np.ndarray, np.ndarray]:
    """(cached: a skater standing still, or in the same pose, costs nothing to build again)"""
    go, ph, amp = _stride(stride, speed)
    lean = 0.28 * go                                   # shoulders forward of the hips at speed
    A, B = [], []

    def seg(a, b):
        A.append(a)
        B.append(b)

    for side, sgn in LEGS:                             # legs: a skating stride pushes back and out
        push, out, _ = _foot(side, sgn, ph, amp)
        hip, knee = (0.0, side, 0.95), (0.16 + 0.4 * push + 0.15 * go, side * 1.2, 0.5 - 0.06 * go)
        foot = (push - 0.05 * go, out, 0.02)
        seg(hip, knee)
        seg(knee, foot)
        if blades:
            seg((push - 0.2, out, 0.01), (push + 0.18, out, 0.01))   # the skate blade
    sh_y = 1.45 - 0.08 * go
    seg((0.0, 0.0, 0.95), (lean, 0.0, sh_y))
    seg((0.0, 0.14, 0.95), (0.0, -0.14, 0.95))
    seg((lean, 0.23, sh_y), (lean, -0.23, sh_y))
    hx, hy = lean + 0.04, 1.66 - 0.1 * go               # head: two rings
    c, s = 0.11 * np.cos(_C), 0.11 * np.sin(_C)
    for i in range(12):
        seg((hx + c[i], 0.0, hy + s[i]), (hx + c[i + 1], 0.0, hy + s[i + 1]))
        seg((hx, c[i], hy + s[i]), (hx, c[i + 1], hy + s[i + 1]))
    k = 1.0 if shoots == "L" else -1.0                  # his blade on his shooting side
    top, bot = (lean * 0.8 + 0.2, -0.1 * k, 1.12), (lean * 0.5 + 0.45, 0.2 * k, 0.82)
    mf, ms = BLADE_AT[0], BLADE_AT[1] * k               # the blade's middle: where the game carries his puck
    heel, toe = (mf - 0.04, ms + 0.15 * k, 0.02), (mf + 0.04, ms - 0.15 * k, 0.02)
    seg((lean, -0.23 * k, 1.4), top)                    # arms
    seg((lean, 0.23 * k, 1.4), bot)
    seg(top, heel)                                      # shaft (through the bottom hand, near enough)
    seg(heel, toe)
    seg((heel[0], heel[1], 0.07), (toe[0], toe[1], 0.07))
    A, B = np.array(A), np.array(B)
    if ring:
        A, B = np.vstack([A, _RING_A]), np.vstack([B, _RING_B])
    return A, B


@functools.lru_cache(maxsize=512)
def _feet(stride: float, speed: float) -> np.ndarray:
    """(left, right) skates in his frame, 4x4 each: under each foot, toes turning out (up to about
    23 degrees) and the boot tipping onto its inside edge (about 14) as the foot pushes back."""
    go, ph, amp = _stride(stride, speed)
    out = np.empty((2, 4, 4))
    for i, (side, sgn) in enumerate(LEGS):
        push, wide, ext = _foot(side, sgn, ph, amp)
        yaw, roll = sgn * (0.1 + 0.3 * ext), sgn * 0.25 * ext
        cy, sy, cr, sr = np.cos(yaw), np.sin(yaw), np.cos(roll), np.sin(roll)
        Rz = np.array([[cy, -sy, 0.0], [sy, cy, 0.0], [0.0, 0.0, 1.0]])
        Rx = np.array([[1.0, 0.0, 0.0], [0.0, cr, -sr], [0.0, sr, cr]])
        out[i] = gear.place(Rz @ Rx, (push - 0.01, wide, 0.0))       # under the blade line's middle
    return out


def skater(line, zone, pos, facing, color, shoots: str = "L", stride: float = 0.0, speed: float = 0.0,
           ring: bool = True) -> None:
    """Draw a skater at zone (x, z) `pos`, facing zone direction `facing`. `line` is a
    sandbox.Lines (or any line(a, b, colour) callback)."""
    f = np.asarray(facing, dtype=float)
    n = float(np.linalg.norm(f))
    f = f / n if n > 1e-6 else np.array([0.0, -1.0])
    skates = gear.skates() if hasattr(line, "place") else None
    A, B = _local(shoots, stride, speed, ring, blades=skates is None)
    # (forward, left, up) -> world: zone x is our left, so the left of f is (fz, -fx)
    M = np.array([zone.dir_to_world(f[0], f[1]), zone.dir_to_world(f[1], -f[0]), [0.0, 1.0, 0.0]])
    o = zone.to_world(float(pos[0]), 0.0, float(pos[1]))
    if skates is not None:
        W = gear.place(M.T, o)
        for model, F in zip(skates, _feet(round(stride, 2), round(speed, 1))):
            line.place(model, W @ F)
    WA, WB = A @ M + o, B @ M + o
    if hasattr(line, "many"):
        line.many(WA, WB, color)
    else:
        for a, b in zip(WA, WB):
            line(a, b, color)


GOALIE = theme.GOALIE


@functools.lru_cache(maxsize=4)
def _goalie_local(down: bool) -> tuple[np.ndarray, np.ndarray]:
    """A goalie in his frame (forward, left, up): pads, body, glove (his left), blocker, mask,
    stick. down: in the butterfly (pads flat on the ice, wide); else standing."""
    A, B = [], []

    def seg(a, b):
        A.append(a)
        B.append(b)

    def rect(p0, p1, p2, p3):
        for a, b in ((p0, p1), (p1, p2), (p2, p3), (p3, p0)):
            seg(a, b)

    for k in (1.0, -1.0):                              # pads
        if down:
            knee, toe = (0.08, 0.06 * k), (-0.12, 0.75 * k)
            rect((*knee, 0.0), (*toe, 0.0), (*toe, 0.28), (*knee, 0.28))
            seg((knee[0], knee[1], 0.14), (toe[0], toe[1], 0.14))
        else:
            rect((0.05, 0.05 * k, 0.0), (0.05, 0.33 * k, 0.0), (0.05, 0.33 * k, 0.8), (0.05, 0.05 * k, 0.8))
    lo = 0.3 if down else 0.8
    rect((0.05, 0.3, lo), (0.05, -0.3, lo), (0.05, -0.28, lo + 0.62), (0.05, 0.28, lo + 0.62))   # chest
    hy = lo + 0.62
    c = np.linspace(0, 2 * np.pi, 11)
    for i in range(10):                                # glove (his left) and mask
        seg((0.18, 0.45 + 0.15 * np.cos(c[i]), hy - 0.15 + 0.15 * np.sin(c[i])),
            (0.18, 0.45 + 0.15 * np.cos(c[i + 1]), hy - 0.15 + 0.15 * np.sin(c[i + 1])))
        seg((0.05, 0.12 * np.cos(c[i]), hy + 0.16 + 0.13 * np.sin(c[i])),
            (0.05, 0.12 * np.cos(c[i + 1]), hy + 0.16 + 0.13 * np.sin(c[i + 1])))
    rect((0.18, -0.34, hy - 0.45), (0.18, -0.54, hy - 0.45), (0.18, -0.54, hy - 0.05), (0.18, -0.34, hy - 0.05))
    seg((0.18, -0.44, hy - 0.3), (0.35, -0.2, 0.05))   # stick: shaft from the blocker, paddle on the ice
    rect((0.35, -0.2, 0.0), (0.35, 0.25, 0.0), (0.35, 0.25, 0.08), (0.35, -0.2, 0.08))
    return np.array(A, dtype=float), np.array(B, dtype=float)


def goalie(line, zone, pos, facing, down: bool = False, color=GOALIE) -> None:
    """Draw the goalie at zone (x, z) `pos`, facing zone direction `facing`."""
    f = np.asarray(facing, dtype=float)
    n = float(np.linalg.norm(f))
    f = f / n if n > 1e-6 else np.array([0.0, 1.0])
    A, B = _goalie_local(bool(down))
    M = np.array([zone.dir_to_world(f[0], f[1]), zone.dir_to_world(f[1], -f[0]), [0.0, 1.0, 0.0]])
    o = zone.to_world(float(pos[0]), 0.0, float(pos[1]))
    line.many(A @ M + o, B @ M + o, color)
