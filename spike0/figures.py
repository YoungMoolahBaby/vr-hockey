"""Line-drawn skaters for the drills: legs that stride, a body that leans into speed, a head, and
a stick with its blade on the ice on his shooting side. Plus a ring on the ice in his team's
colour, so a glance tells you who is who and where.

Built in the skater's own frame (forward, his left, up) and moved into the world in one numpy
step: drawing runs in the render thread, which shares Python's lock with the 1 kHz physics."""

from __future__ import annotations

import functools

import numpy as np

US, THEM, YOU = (0.25, 0.85, 1.0), (1.0, 0.5, 0.15), (1.0, 0.9, 0.2)
_C = np.linspace(0, 2 * np.pi, 13)
_RING_A = np.stack([0.5 * np.cos(_C[:-1]), 0.5 * np.sin(_C[:-1]), np.full(12, 0.006)], axis=1)
_RING_B = np.stack([0.5 * np.cos(_C[1:]), 0.5 * np.sin(_C[1:]), np.full(12, 0.006)], axis=1)


def _local(shoots: str, stride: float, speed: float, ring: bool) -> tuple[np.ndarray, np.ndarray]:
    """Segment ends (A, B), each (n, 3) as (forward, left, up) in metres."""
    return _local_cached(shoots, round(stride, 2), round(speed, 1), ring)


@functools.lru_cache(maxsize=512)
def _local_cached(shoots: str, stride: float, speed: float, ring: bool) -> tuple[np.ndarray, np.ndarray]:
    """(cached: a skater standing still, or in the same pose, costs nothing to build again)"""
    go = min(speed / 7.0, 1.0)
    lean = 0.28 * go                                   # shoulders forward of the hips at speed
    ph = stride / 1.7 * 2 * np.pi
    amp = 0.32 * min(speed / 3.0, 1.0)
    A, B = [], []

    def seg(a, b):
        A.append(a)
        B.append(b)

    for side, sgn in ((0.12, 1.0), (-0.12, -1.0)):     # legs: a skating stride pushes back and out
        push = amp * np.sin(ph) * sgn
        out = side * (1.4 + 1.2 * max(0.0, -push / 0.32))
        hip, knee = (0.0, side, 0.95), (0.16 + 0.4 * push + 0.15 * go, side * 1.2, 0.5 - 0.06 * go)
        foot = (push - 0.05 * go, out, 0.02)
        seg(hip, knee)
        seg(knee, foot)
        seg((push - 0.2, out, 0.01), (push + 0.18, out, 0.01))       # the skate blade
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
    heel, toe = (1.05, 0.42 * k, 0.02), (1.12, 0.12 * k, 0.02)
    seg((lean, -0.23 * k, 1.4), top)                    # arms
    seg((lean, 0.23 * k, 1.4), bot)
    seg(top, heel)                                      # shaft (through the bottom hand, near enough)
    seg(heel, toe)
    seg((1.05, 0.42 * k, 0.07), (1.12, 0.12 * k, 0.07))
    A, B = np.array(A), np.array(B)
    if ring:
        A, B = np.vstack([A, _RING_A]), np.vstack([B, _RING_B])
    return A, B


def skater(line, zone, pos, facing, color, shoots: str = "L", stride: float = 0.0, speed: float = 0.0,
           ring: bool = True) -> None:
    """Draw a skater at zone (x, z) `pos`, facing zone direction `facing`. `line` is a
    sandbox.Lines (or any line(a, b, colour) callback)."""
    f = np.asarray(facing, dtype=float)
    n = float(np.linalg.norm(f))
    f = f / n if n > 1e-6 else np.array([0.0, -1.0])
    A, B = _local(shoots, stride, speed, ring)
    # (forward, left, up) -> world: zone x is our left, so the left of f is (fz, -fx)
    M = np.array([zone.dir_to_world(f[0], f[1]), zone.dir_to_world(f[1], -f[0]), [0.0, 1.0, 0.0]])
    o = zone.to_world(float(pos[0]), 0.0, float(pos[1]))
    WA, WB = A @ M + o, B @ M + o
    if hasattr(line, "many"):
        line.many(WA, WB, color)
    else:
        for a, b in zip(WA, WB):
            line(a, b, color)
