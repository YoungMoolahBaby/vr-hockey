"""Geometry for a virtual hockey stick held by two tracked controllers (no physical stick).

Conventions: OpenXR stage space, metres, y up, the virtual ice at y = 0 (the boundary floor).
Quaternions are (x, y, z, w). A pose maps controller-frame points to world points:
world = R @ local + p. "Top" is the hand on the knob, "bottom" the hand down the shaft.

The stick has a fixed length (top grip to heel). In the stance its heel sits on the ice, in the
direction the hands point. Without a real shaft, the line between the grips is much flatter than
a stick (measured 2026-11-07: 24-28 degrees), so the stick is NOT the line through both grips:
it hangs at a fixed angle from it.

Stick models (how the virtual stick follows the hands); Spike 0 compares them:
  two_hand     the stick is rigid in the frame of the hand pair: the line between the grips
               steers it, the top wrist only sets the roll about that line
  top_hand     the stick is rigid in the top hand (wrist orientation steers it)
  bottom_hand  the stick is rigid in the bottom hand
  blend        the average of the two_hand and top_hand shaft directions
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np

MODELS = ("two_hand", "top_hand", "bottom_hand", "blend")
BLADE_LEN = 0.30        # heel to toe, m (display only)
DEFAULT_LENGTH = 1.40   # top grip to heel, m: a ~1.50 m senior stick held ~8 cm below the knob


def expmap(r: np.ndarray) -> np.ndarray:
    """(N, 3) rotation vectors -> (N, 3, 3) rotation matrices."""
    r = np.atleast_2d(r)
    th = np.linalg.norm(r, axis=1)
    k = np.where(th[:, None] > 1e-12, r / np.maximum(th, 1e-12)[:, None], 0.0)
    K = np.zeros((len(r), 3, 3))
    K[:, 0, 1], K[:, 0, 2] = -k[:, 2], k[:, 1]
    K[:, 1, 0], K[:, 1, 2] = k[:, 2], -k[:, 0]
    K[:, 2, 0], K[:, 2, 1] = -k[:, 1], k[:, 0]
    s, c = np.sin(th)[:, None, None], np.cos(th)[:, None, None]
    return np.eye(3) + s * K + (1 - c) * (K @ K)


def quat_to_mat(q: np.ndarray) -> np.ndarray:
    """(N, 4) xyzw quaternions -> (N, 3, 3) rotation matrices. Also takes a single (4,)."""
    q = np.asarray(q, dtype=np.float64)
    single = q.ndim == 1
    q = np.atleast_2d(q)
    q = q / np.linalg.norm(q, axis=1, keepdims=True)
    x, y, z, w = q.T
    R = np.empty((len(q), 3, 3))
    R[:, 0, 0] = 1 - 2 * (y * y + z * z)
    R[:, 0, 1] = 2 * (x * y - z * w)
    R[:, 0, 2] = 2 * (x * z + y * w)
    R[:, 1, 0] = 2 * (x * y + z * w)
    R[:, 1, 1] = 1 - 2 * (x * x + z * z)
    R[:, 1, 2] = 2 * (y * z - x * w)
    R[:, 2, 0] = 2 * (x * z - y * w)
    R[:, 2, 1] = 2 * (y * z + x * w)
    R[:, 2, 2] = 1 - 2 * (x * x + y * y)
    return R[0] if single else R


def mat_to_quat(R: np.ndarray) -> np.ndarray:
    """(N, 3, 3) -> (N, 4) xyzw. Also takes a single (3, 3)."""
    R = np.asarray(R, dtype=np.float64)
    single = R.ndim == 2
    R = R.reshape(-1, 3, 3)
    q = np.empty((len(R), 4))
    for i, m in enumerate(R):
        tr = m[0, 0] + m[1, 1] + m[2, 2]
        if tr > 0:
            s = np.sqrt(tr + 1.0) * 2
            q[i] = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, 0.25 * s]
        elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
            s = np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
            q[i] = [0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s]
        elif m[1, 1] > m[2, 2]:
            s = np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
            q[i] = [(m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s]
        else:
            s = np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
            q[i] = [(m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s, (m[1, 0] - m[0, 1]) / s]
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    return q[0] if single else q


def rot_axis_angle(axis, angle) -> np.ndarray:
    a = np.asarray(axis, dtype=np.float64)
    a = a / np.linalg.norm(a)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * (K @ K)


def mean_rotation(R: np.ndarray) -> np.ndarray:
    """Chordal mean of (N, 3, 3) rotations, projected back onto SO(3)."""
    U, _, Vt = np.linalg.svd(R.mean(axis=0))
    M = U @ Vt
    if np.linalg.det(M) < 0:
        U[:, -1] *= -1
        M = U @ Vt
    return M


def unit(v: np.ndarray) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):   # zero vectors (no pose) become NaN, masked later
        return v / np.linalg.norm(v, axis=-1, keepdims=True)


@dataclass
class StickCal:
    """The virtual stick, fitted to how the player holds their hands in their stance."""
    top: str                    # 'l' or 'r': the hand on the knob
    length_m: float             # top grip -> heel along the shaft
    d_local_top: list           # shaft direction in the top hand's frame (top_hand model)
    d_local_pair: list          # shaft direction in the hand-pair frame (two_hand model)
    pair_axis: int              # which top-hand axis sets the hand-pair frame's roll
    b_local_top: list           # blade direction heel->toe in the top hand's frame
    heel_local_bottom: list     # heel in the bottom hand's frame (bottom_hand model)
    hand_sep_m: float           # grip-to-grip distance in the stance
    grip_line_deg: float        # the line between the grips, below horizontal
    shaft_angle_deg: float      # the stick, below horizontal
    top_height_m: float         # top grip above the ice in the stance
    length_fixed: bool = False  # True when --stick-length was given (else DEFAULT_LENGTH)

    @property
    def bottom(self) -> str:
        return "r" if self.top == "l" else "l"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "StickCal":
        return cls(**d)


def pick_top(p_l: np.ndarray, p_r: np.ndarray) -> str:
    """The top hand is the higher one in the stance."""
    return "l" if np.median(p_l[:, 1]) > np.median(p_r[:, 1]) else "r"


def pair_frame(Rt, pt, pb, axis: int) -> np.ndarray:
    """Frame of the hand pair: x along the grip line (top -> bottom), roll from a top-hand axis.

    Works for one pose ((3,3), (3,), (3,)) or many ((N,3,3), (N,3), (N,3)).
    """
    a = unit(pb - pt)
    r = Rt[..., :, axis]
    b = unit(r - a * np.sum(a * r, axis=-1, keepdims=True))
    c = np.cross(a, b)
    return np.stack([a, b, c], axis=-1)


def calibrate_stance(Rt, pt, Rb, pb, top: str, ice_y: float = 0.0, length: float | None = None) -> StickCal:
    """Fit the stick to a still stance: a stick of fixed length whose heel sits on the ice,
    pointing where the hands point (the grip line's heading), hanging down at whatever angle
    puts the heel on the ice.

    Rt/pt: top hand poses (N,3,3)/(N,3); Rb/pb: bottom hand. `length` is top grip to heel
    (default DEFAULT_LENGTH).
    """
    L = float(length) if length is not None else DEFAULT_LENGTH
    line = unit(pb - pt)
    heading = np.median(line, axis=0) * np.array([1.0, 0.0, 1.0])
    if np.linalg.norm(heading) < 0.1:
        raise ValueError("the hands were straight above each other, so they point nowhere")
    heading = unit(heading)
    top_h = float(np.median(pt[:, 1]) - ice_y)
    drop = np.clip(top_h / L, 0.0, 1.0)                 # sine of the shaft angle below horizontal
    d = np.sqrt(1 - drop * drop) * heading + np.array([0.0, -drop, 0.0])
    # roll reference: the top-hand axis most across the grip line (so the frame stays well defined)
    Rt_T = np.transpose(Rt, (0, 2, 1))
    line_local = np.einsum("nij,nj->ni", Rt_T, line).mean(axis=0)
    axis = int(np.argmin(np.abs(line_local)))
    F = pair_frame(Rt, pt, pb, axis)
    d_pair = unit(np.einsum("nji,j->ni", F, d).mean(axis=0))
    d_top = unit(np.einsum("nij,j->ni", Rt_T, d).mean(axis=0))
    b_top = unit(np.einsum("nij,j->ni", Rt_T, heading).mean(axis=0))   # the blade lies flat, pointing on
    heel = pt + L * d
    heel_b = np.einsum("nij,nj->ni", np.transpose(Rb, (0, 2, 1)), heel - pb).mean(axis=0)
    sep = float(np.median(np.linalg.norm(pb - pt, axis=1)))
    grip_deg = float(np.degrees(np.arcsin(np.clip(-np.median(line[:, 1]), -1, 1))))
    return StickCal(top, L, d_top.tolist(), d_pair.tolist(), axis, b_top.tolist(), heel_b.tolist(), sep,
                    grip_deg, float(np.degrees(np.arcsin(drop))), top_h, length is not None)


def stance_problems(cal: StickCal, heel_spread_m: float) -> list[str]:
    """Plain-language reasons not to trust a stance calibration (empty if fine)."""
    out = []
    if not 0.12 <= cal.hand_sep_m <= 1.0:
        out.append(f"your hands were {cal.hand_sep_m * 100:.0f} centimetres apart")
    if cal.top_height_m >= 0.98 * cal.length_m:
        out.append(f"your top hand was {cal.top_height_m:.2f} metres up, too high for a "
                   f"{cal.length_m:.2f} metre stick to reach the ice")
    elif cal.shaft_angle_deg < 20:
        out.append("the stick would lie almost flat: is the top hand very low?")
    if heel_spread_m > 0.06:
        out.append(f"the blade moved {heel_spread_m * 100:.0f} centimetres during the stance")
    return out


def blade_heel(model: str, cal: StickCal, Rt, pt, Rb, pb) -> np.ndarray:
    """Heel position (N,3) for a stick model, from top and bottom hand poses."""
    L = cal.length_m
    if model == "two_hand":
        return pt + L * (pair_frame(Rt, pt, pb, cal.pair_axis) @ np.asarray(cal.d_local_pair))
    if model == "top_hand":
        return pt + L * (Rt @ np.asarray(cal.d_local_top))
    if model == "bottom_hand":
        return Rb @ np.asarray(cal.heel_local_bottom) + pb
    if model == "blend":
        two = pair_frame(Rt, pt, pb, cal.pair_axis) @ np.asarray(cal.d_local_pair)
        return pt + L * unit(two + Rt @ np.asarray(cal.d_local_top))
    raise ValueError(model)


def heel_velocity(model: str, cal: StickCal, Rt, pt, vt, wt, Rb, pb, vb, wb, eps: float = 1e-4) -> np.ndarray:
    """Heel velocity (N,3) from the runtime's hand velocities (world-frame linear v, angular w).

    Moves both hands a tiny step forward and back along their reported velocities and
    differences the model's heel, so it is exact for every model to O(eps^2).
    """
    def step(s):
        return (expmap(wt * s) @ Rt, pt + vt * s, expmap(wb * s) @ Rb, pb + vb * s)
    a, b = step(eps), step(-eps)
    return (blade_heel(model, cal, *a) - blade_heel(model, cal, *b)) / (2 * eps)


def rotation_angle_deg(R: np.ndarray) -> np.ndarray:
    return np.degrees(np.arccos(np.clip((np.trace(R, axis1=1, axis2=2) - 1) / 2, -1, 1)))


def blade_dir(cal: StickCal, Rt) -> np.ndarray:
    """Blade direction heel->toe (N,3), following the top hand's roll (display only)."""
    return Rt @ np.asarray(cal.b_local_top)
