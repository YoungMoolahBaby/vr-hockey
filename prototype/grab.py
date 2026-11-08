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

SQUEEZE_ON, SQUEEZE_OFF = 0.5, 0.25       # hysteresis: press past half way to grab, release below a quarter
# a grip must stay released this long to let go (a slip mid-swing doesn't count). Jon, session 2: the
# left grip slipped and came back within 0.4 s 31 times in 9 minutes; letting go with the bottom hand
# costs nothing (the stick stays in the top hand), so it gets the longer wait; the top hand stays quick
# for taking it off the stick on D.
RELEASE_TOP_S = 0.25
RELEASE_BOTTOM_S = 0.40
RELEASE_S = RELEASE_TOP_S
BLEND_S = 0.12      # grabbing eases the stick into the hold over this long instead of jumping
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


class GripFilter:
    """One grip button: hysteresis, and a release only counts once it has lasted RELEASE_S."""

    def __init__(self, release_s: float = RELEASE_S):
        self.release_s = release_s
        self.on = False
        self.below_since = None

    def update(self, v: float, t: float) -> bool:
        if not self.on:
            if v >= SQUEEZE_ON:
                self.on, self.below_since = True, None
        elif v <= SQUEEZE_OFF:
            if self.below_since is None:
                self.below_since = t
            if t - self.below_since >= self.release_s - 1e-9:
                self.on, self.below_since = False, None
        else:
            self.below_since = None
        return self.on


def held(squeeze: np.ndarray, t: np.ndarray | None = None, release_s: float = RELEASE_S) -> np.ndarray:
    """Grip button held, per sample (t in seconds; default: 1 kHz samples)."""
    t = np.arange(len(squeeze)) / 1000.0 if t is None else np.asarray(t, dtype=float)
    f = GripFilter(release_s)
    return np.array([f.update(float(v), float(ti)) for v, ti in zip(squeeze, t)], dtype=bool)


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


def on_shaft(spec: StickSpec, q: np.ndarray) -> np.ndarray:
    """The bottom hand's grab point moved onto the shaft's axis, so the shaft runs through both
    hands (Jon: "the bottom hand grip a bit off from the shaft"). Easing in hides the move."""
    return float(q @ spec.u) * spec.u


def top_pose(R_ts, p_ts, Rt, pt):
    return Rt @ R_ts, pt + Rt @ p_ts


def both_pose(R_ts, p_ts, q_b, Rt, pt, pb):
    """Top-hand hold, then turned about the top grip so the bottom grab point follows the bottom hand."""
    R, p = top_pose(R_ts, p_ts, Rt, pt)
    pred = p + R @ q_b
    A = rot_between(pred - pt, pb - pt)
    return A @ R, pt + np.einsum("nij,nj->ni", A, p - pt)


def ease_from(Rf, pf, R, p, w):
    """Blend from pose (Rf, pf) toward (R, p) by weight w in [0, 1] (arrays of poses)."""
    qf, q = sm.mat_to_quat(Rf), sm.mat_to_quat(R)
    qf = np.where((np.sum(qf * q, axis=-1) < 0)[..., None], -qf, qf)
    w = np.asarray(w)[..., None]
    qb = (1 - w) * qf + w * q
    return sm.quat_to_mat(qb / np.linalg.norm(qb, axis=-1, keepdims=True)), (1 - w) * pf + w * p


def _smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def replay(spec: StickSpec, fit: Fit, state, Rt, pt, Rb, pb, valid_t, valid_b, t=None):
    """Stick pose (R (N,3,3), p (N,3)) for every sample; NaN where it is unknown."""
    R_ts, p_ts = hold(spec, fit)
    t = np.arange(len(state)) / 1000.0 if t is None else np.asarray(t, dtype=float)
    N = len(state)
    R = np.full((N, 3, 3), np.nan)
    p = np.full((N, 3), np.nan)
    edges = np.flatnonzero(np.diff(state.astype(int))) + 1
    starts = np.concatenate([[0], edges])
    ends = np.concatenate([edges, [N]])
    for i0, i1 in zip(starts, ends):
        s = state[i0]
        sl = slice(i0, i1)
        if s in (TOP, BOTH):
            if s == TOP:
                R[sl], p[sl] = top_pose(R_ts, p_ts, Rt[sl], pt[sl])
                bad = ~valid_t[sl]
            else:
                R0, p0 = top_pose(R_ts, p_ts, Rt[i0], pt[i0])
                q_b = on_shaft(spec, R0.T @ (pb[i0] - p0))   # where the bottom hand took the stick
                R[sl], p[sl] = both_pose(R_ts, p_ts, q_b, Rt[sl], pt[sl], pb[sl])
                bad = ~(valid_t[sl] & valid_b[sl])
            # ease in: start from where the stick was (carried by the top hand), not a jump
            if i0 > 0 and not np.isnan(p[i0 - 1, 0]) and valid_t[i0 - 1]:
                k = np.flatnonzero(t[sl] - t[i0] < BLEND_S)
                if len(k):
                    ks = i0 + k
                    rel_R = Rt[i0 - 1].T @ R[i0 - 1]
                    rel_p = Rt[i0 - 1].T @ (p[i0 - 1] - pt[i0 - 1])
                    Rf, pf = Rt[ks] @ rel_R, pt[ks] + Rt[ks] @ rel_p
                    R[ks], p[ks] = ease_from(Rf, pf, R[ks], p[ks], _smooth((t[ks] - t[i0]) / BLEND_S))
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
        self.filters = {"t": GripFilter(RELEASE_TOP_S), "b": GripFilter(RELEASE_BOTTOM_S)}
        self.ease = None               # (R rel to the top hand, p rel to the top hand, t0) while easing in
        self.R = self.p = None
        self.q_b = None
        self.rider = None              # the stick in the hand it rides in (LOOSE_TOP, BOTTOM, LOOSE_BOTTOM)
        self.last = {"top": None, "bottom": None}   # the hands at the previous step (same instant as self.R)

    def set_fit(self, fit: Fit) -> None:
        self.fit = fit
        self.R_ts, self.p_ts = hold(self.spec, fit)

    def configure(self, spec: StickSpec, fit: Fit) -> None:
        """A new stick or fit (live tuning): a gripped stick takes it at the next step, a loose one
        at the next grab."""
        self.spec = spec
        self.set_fit(fit)

    def _held(self, key, v, t):
        self.on[key] = self.filters[key].update(v, t)
        return self.on[key]

    def step(self, top, bottom, sq_t: float, sq_b: float, t: float, force_top: bool = False):
        """top/bottom: (R, p) or None if not tracked; t in seconds. Returns (state, R, p) of the stick."""
        ht, hb = self._held("t", sq_t, t), self._held("b", sq_b, t)
        new = TOP if force_top else next_state(self.state, ht, hb)
        if new in (TOP, BOTH) and new != self.state and self.R is not None:
            lt = self.last["top"]
            if lt is not None:                      # ease in from where the stick was
                self.ease = (lt[0].T @ self.R, lt[0].T @ (self.p - lt[1]), t)
        elif new not in (TOP, BOTH):
            self.ease = None
        if new == TOP and top is not None:
            self.R, self.p = top_pose(self.R_ts, self.p_ts, *top)
        elif new == BOTH and top is not None and bottom is not None:
            if self.state != BOTH or self.q_b is None:
                R0, p0 = top_pose(self.R_ts, self.p_ts, *top)
                self.q_b = on_shaft(self.spec, R0.T @ (bottom[1] - p0))
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
        if self.ease is not None and new in (TOP, BOTH) and top is not None:
            rel_R, rel_p, t0 = self.ease
            if t - t0 < BLEND_S:
                Rf, pf = top[0] @ rel_R, top[1] + top[0] @ rel_p
                R, p = ease_from(Rf[None], pf[None], self.R[None], self.p[None], [_smooth((t - t0) / BLEND_S)])
                self.R, self.p = R[0], p[0]
            else:
                self.ease = None
        self.state = new
        self.last = {"top": top, "bottom": bottom}
        return self.state, self.R, self.p
