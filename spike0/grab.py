"""Holding the virtual stick with the grip buttons (the middle-finger squeeze on Quest controllers).

States:
  TOP          only the top hand grips: the stick is rigid in the top hand, where the fit put it
  BOTH         both grip: the top hand holds the stick and sets the blade's roll; the bottom hand
               aims the shaft (the bottom hand may slide along the shaft)
  BOTTOM       only the bottom hand grips (top hand off, e.g. angling an attacker on D): the
               stick stays rigid in the bottom hand exactly where it was when it got there
  LOOSE_TOP    no grip pressed, the top hand held it last: the stick rides in the top hand,
  LOOSE_BOTTOM or the bottom hand, exactly where it was. It is never dropped (Jon, 2026-11-07).
  NONE         never held yet (before the first grab)
Grabbing again: the top grip snaps the stick back into the fitted hold; the bottom grip alone
takes the stick where it is.

The fit is the stick's pose in the top controller's frame. It is set once by turning the stick
in the hand with the thumbstick, then saved.

Everything here works on arrays, so analyze.py replays a whole recording at 1 kHz with the same
rules the headset used live (Grab.step is the one-sample version of replay).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

import stickmath as sm
from stickspec import StickSpec

SQUEEZE_ON, SQUEEZE_OFF = 0.6, 0.35       # hysteresis: press past 0.6 to grab, release below 0.35
NONE, TOP, BOTTOM, BOTH, LOOSE_TOP, LOOSE_BOTTOM = 0, 1, 2, 3, 4, 5
STATE_NAMES = {NONE: "none", TOP: "top", BOTTOM: "bottom", BOTH: "both",
               LOOSE_TOP: "loose top", LOOSE_BOTTOM: "loose bottom"}
HELD = (TOP, BOTTOM, BOTH, LOOSE_TOP, LOOSE_BOTTOM)      # the stick is in a hand
RIDES = {LOOSE_TOP: "top", BOTTOM: "bottom", LOOSE_BOTTOM: "bottom"}   # rigid where it was, in that hand
EX, EY, EZ = np.eye(3)


# ----------------------------------------------------------------------------- the fit


@dataclass
class Fit:
    """The stick in the top hand: roll turns the blade about the shaft, pitch/yaw tilt the shaft."""
    roll_deg: float = 0.0
    pitch_deg: float = 0.0
    yaw_deg: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Fit":
        return cls(**{k: d[k] for k in ("roll_deg", "pitch_deg", "yaw_deg")})

    def save(self, path: Path, spec: StickSpec) -> None:
        Path(path).write_text(json.dumps({"fit": self.to_dict(), "spec": spec.to_dict()}, indent=2))

    @classmethod
    def load(cls, path: Path) -> "Fit | None":
        p = Path(path)
        return cls.from_dict(json.loads(p.read_text())["fit"]) if p.exists() else None


def hold(spec: StickSpec, fit: Fit) -> tuple[np.ndarray, np.ndarray]:
    """(R_ts, p_ts): stick axes and heel in the top controller's frame.

    Base hold: the shaft runs down out of the thumb side of the fist (the grip pose's -Z, the
    axis of a held cylinder), the forehand face toward the controller's +X. Then the fit: roll
    about the shaft, then pitch (about +X) and yaw (about +Y) around the grip point. The grip
    point on the shaft always stays at the controller's grip centre.
    """
    a = np.stack([-spec.u, spec.z_forehand, np.cross(-spec.u, spec.z_forehand)], axis=1)
    b = np.stack([-EZ, EX, np.cross(-EZ, EX)], axis=1)
    R0 = b @ a.T
    R_roll = sm.rot_axis_angle(spec.u, np.radians(fit.roll_deg))
    R_ts = (sm.rot_axis_angle(EY, np.radians(fit.yaw_deg)) @ sm.rot_axis_angle(EX, np.radians(fit.pitch_deg))
            @ R0 @ R_roll)
    return R_ts, -R_ts @ spec.grip


# ----------------------------------------------------------------------------- grip states


def held(squeeze: np.ndarray) -> np.ndarray:
    """Grip button pressed, with hysteresis."""
    out = np.zeros(len(squeeze), dtype=bool)
    on = False
    for i, v in enumerate(np.asarray(squeeze, dtype=float)):
        on = v >= SQUEEZE_ON if not on else v > SQUEEZE_OFF
        out[i] = on
    return out


def next_state(prev: int, top_held: bool, bottom_held: bool) -> int:
    if top_held and bottom_held:
        return BOTH
    if top_held:
        return TOP
    if bottom_held:
        return BOTTOM if prev in HELD else NONE      # the bottom hand takes the stick where it is
    if prev in (TOP, BOTH, LOOSE_TOP):
        return LOOSE_TOP                              # let go of everything: it stays in the last hand
    if prev in (BOTTOM, LOOSE_BOTTOM):
        return LOOSE_BOTTOM
    return NONE


def states(top_held: np.ndarray, bottom_held: np.ndarray, start: int = NONE) -> np.ndarray:
    out = np.empty(len(top_held), dtype=np.int8)
    s = start
    for i in range(len(top_held)):
        s = next_state(s, bool(top_held[i]), bool(bottom_held[i]))
        out[i] = s
    return out


# ----------------------------------------------------------------------------- poses


def rot_between(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """(N,3,3) smallest rotations taking directions a to b."""
    a, b = sm.unit(a), sm.unit(b)
    v = np.cross(a, b)
    c = np.sum(a * b, axis=-1)
    K = np.zeros(a.shape[:-1] + (3, 3))
    K[..., 0, 1], K[..., 0, 2] = -v[..., 2], v[..., 1]
    K[..., 1, 0], K[..., 1, 2] = v[..., 2], -v[..., 0]
    K[..., 2, 0], K[..., 2, 1] = -v[..., 1], v[..., 0]
    k = 1.0 / np.maximum(1.0 + c, 1e-9)
    return np.eye(3) + K + (K @ K) * k[..., None, None]


def top_pose(R_ts, p_ts, Rt, pt):
    return Rt @ R_ts, pt + Rt @ p_ts


def both_pose(R_ts, p_ts, q_b, Rt, pt, pb):
    """Top-hand hold, then turned about the top grip so the bottom grab point follows the bottom hand."""
    R, p = top_pose(R_ts, p_ts, Rt, pt)
    pred = p + R @ q_b
    A = rot_between(pred - pt, pb - pt)
    return A @ R, pt + np.einsum("nij,nj->ni", A, p - pt)


def replay(spec: StickSpec, fit: Fit, state, Rt, pt, Rb, pb, valid_t, valid_b):
    """Stick pose (R (N,3,3), p (N,3)) for every sample; NaN where it is unknown."""
    R_ts, p_ts = hold(spec, fit)
    N = len(state)
    R = np.full((N, 3, 3), np.nan)
    p = np.full((N, 3), np.nan)
    edges = np.flatnonzero(np.diff(state.astype(int))) + 1
    starts = np.concatenate([[0], edges])
    ends = np.concatenate([edges, [N]])
    for i0, i1 in zip(starts, ends):
        s = state[i0]
        sl = slice(i0, i1)
        if s == TOP:
            R[sl], p[sl] = top_pose(R_ts, p_ts, Rt[sl], pt[sl])
            bad = ~valid_t[sl]
        elif s == BOTH:
            R0, p0 = top_pose(R_ts, p_ts, Rt[i0], pt[i0])
            q_b = R0.T @ (pb[i0] - p0)                    # where the bottom hand took the stick
            R[sl], p[sl] = both_pose(R_ts, p_ts, q_b, Rt[sl], pt[sl], pb[sl])
            bad = ~(valid_t[sl] & valid_b[sl])
        elif s in RIDES:                                  # rigid in one hand, exactly where it was
            Rh, ph, ok = (Rt, pt, valid_t) if RIDES[s] == "top" else (Rb, pb, valid_b)
            if i0 == 0 or np.isnan(p[i0 - 1, 0]) or not ok[i0 - 1]:
                continue
            R_hs = Rh[i0 - 1].T @ R[i0 - 1]
            p_hs = Rh[i0 - 1].T @ (p[i0 - 1] - ph[i0 - 1])
            R[sl], p[sl] = Rh[sl] @ R_hs, ph[sl] + Rh[sl] @ p_hs
            bad = ~ok[sl]
        else:  # NONE: never held yet
            continue
        R[sl][bad] = np.nan
        p[sl][bad] = np.nan
    return R, p


class Grab:
    """The same rules, one sample at a time (the headset view)."""

    def __init__(self, spec: StickSpec, fit: Fit):
        self.spec = spec
        self.set_fit(fit)
        self.state = NONE
        self.on = {"t": False, "b": False}
        self.R = self.p = None
        self.q_b = None
        self.rider = None              # the stick in the hand it rides in (LOOSE_TOP, BOTTOM, LOOSE_BOTTOM)
        self.last = {"top": None, "bottom": None}   # the hands at the previous step (same instant as self.R)

    def set_fit(self, fit: Fit) -> None:
        self.fit = fit
        self.R_ts, self.p_ts = hold(self.spec, fit)

    def _held(self, key, v):
        self.on[key] = v >= SQUEEZE_ON if not self.on[key] else v > SQUEEZE_OFF
        return self.on[key]

    def step(self, top, bottom, sq_t: float, sq_b: float, force_top: bool = False):
        """top/bottom: (R, p) or None if not tracked. Returns (state, R, p) of the stick."""
        ht, hb = self._held("t", sq_t), self._held("b", sq_b)
        new = TOP if force_top else next_state(self.state, ht, hb)
        if new == TOP and top is not None:
            self.R, self.p = top_pose(self.R_ts, self.p_ts, *top)
        elif new == BOTH and top is not None and bottom is not None:
            if self.state != BOTH or self.q_b is None:
                R0, p0 = top_pose(self.R_ts, self.p_ts, *top)
                self.q_b = R0.T @ (bottom[1] - p0)
            R, p = both_pose(self.R_ts, self.p_ts, self.q_b, top[0][None], top[1][None], bottom[1][None])
            self.R, self.p = R[0], p[0]
        elif new in RIDES and self.R is not None:
            who = RIDES[new]
            hand = top if who == "top" else bottom
            if hand is not None:
                if new != self.state or self.rider is None:
                    h0 = self.last[who] if self.last[who] is not None else hand
                    self.rider = (h0[0].T @ self.R, h0[0].T @ (self.p - h0[1]))
                Rr, pr = self.rider
                self.R, self.p = hand[0] @ Rr, hand[1] + hand[0] @ pr
        self.state = new
        self.last = {"top": top, "bottom": bottom}
        return self.state, self.R, self.p
