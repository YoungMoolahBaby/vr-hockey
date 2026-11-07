"""Geometry for a virtual hockey stick held by two tracked controllers (no physical stick).

Conventions: OpenXR stage space, metres, y up, the virtual ice at y = 0 (the boundary floor).
Quaternions are (x, y, z, w). A pose maps controller-frame points to world points:
world = R @ local + p. "Top" is the hand on the knob, "bottom" the hand down the shaft.

Stick models (how the virtual stick follows the hands); Spike 0 compares them:
  two_hand     the shaft runs through both grips; length fixed from the top grip
  top_hand     the stick is rigid in the top hand (wrist orientation steers it)
  bottom_hand  the stick is rigid in the bottom hand
  blend        the average of the two_hand and top_hand shaft directions
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np

MODELS = ("two_hand", "top_hand", "bottom_hand", "blend")
BLADE_LEN = 0.30   # heel to toe, m (display only)


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
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


@dataclass
class StickCal:
    """The virtual stick, fitted to how the player holds their hands in their stance."""
    top: str                    # 'l' or 'r': the hand on the knob
    length_m: float             # top grip -> heel along the shaft
    d_local_top: list           # shaft direction in the top hand's frame (top_hand model)
    b_local_top: list           # blade direction heel->toe in the top hand's frame
    heel_local_bottom: list     # heel in the bottom hand's frame (bottom_hand model)
    hand_sep_m: float           # grip-to-grip distance in the stance
    shaft_angle_deg: float      # shaft below horizontal in the stance
    length_fixed: bool = False  # True when --stick-length was given

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


def calibrate_stance(Rt, pt, Rb, pb, top: str, ice_y: float = 0.0, length: float | None = None) -> StickCal:
    """Fit the stick to a still stance: the blade sits on the ice where the hands point.

    Rt/pt: top hand poses (N,3,3)/(N,3); Rb/pb: bottom hand. If `length` is given the
    stick keeps that length instead of being sized from the stance.
    """
    d = unit(pb - pt)                                  # shaft direction, top -> bottom -> blade
    if length is None:
        down = d[:, 1] < -0.2
        if down.sum() < 10:
            raise ValueError("the hands were not one above the other (the shaft never pointed down)")
        L = float(np.median((pt[down, 1] - ice_y) / -d[down, 1]))
    else:
        L = float(length)
    heel = pt + L * d
    Rt_T = np.transpose(Rt, (0, 2, 1))
    d_local = unit(np.einsum("nij,nj->ni", Rt_T, d).mean(axis=0))
    flat = d.copy()
    flat[:, 1] = 0                                     # the blade lies flat, pointing away along the shaft
    b_local = unit(np.einsum("nij,nj->ni", Rt_T, unit(flat)).mean(axis=0))
    heel_b = np.einsum("nij,nj->ni", np.transpose(Rb, (0, 2, 1)), heel - pb).mean(axis=0)
    sep = float(np.median(np.linalg.norm(pb - pt, axis=1)))
    ang = float(np.degrees(np.arcsin(np.clip(-np.median(d[:, 1]), -1, 1))))
    return StickCal(top, L, d_local.tolist(), b_local.tolist(), heel_b.tolist(), sep, ang, length is not None)


def stance_problems(cal: StickCal, heel_spread_m: float) -> list[str]:
    """Plain-language reasons not to trust a stance calibration (empty if fine)."""
    out = []
    if not 0.9 <= cal.length_m <= 2.0:
        out.append(f"the stick came out {cal.length_m:.2f} metres long")
    if not 0.12 <= cal.hand_sep_m <= 1.0:
        out.append(f"your hands were {cal.hand_sep_m * 100:.0f} centimetres apart")
    if cal.shaft_angle_deg < 20:
        out.append("the stick was almost flat")
    if heel_spread_m > 0.06:
        out.append(f"the blade moved {heel_spread_m * 100:.0f} centimetres during the stance")
    return out


def blade_heel(model: str, cal: StickCal, Rt, pt, Rb, pb) -> np.ndarray:
    """Heel position (N,3) for a stick model, from top and bottom hand poses."""
    L = cal.length_m
    if model == "two_hand":
        return pt + L * unit(pb - pt)
    if model == "top_hand":
        return pt + L * (Rt @ np.asarray(cal.d_local_top))
    if model == "bottom_hand":
        return Rb @ np.asarray(cal.heel_local_bottom) + pb
    if model == "blend":
        return pt + L * unit(unit(pb - pt) + Rt @ np.asarray(cal.d_local_top))
    raise ValueError(model)


def heel_velocity(model: str, cal: StickCal, Rt, pt, vt, wt, Rb, pb, vb, wb) -> np.ndarray:
    """Heel velocity (N,3) from the runtime's hand velocities (world-frame linear v, angular w)."""
    L = cal.length_m
    if model in ("two_hand", "blend"):
        sep = pb - pt
        s = np.linalg.norm(sep, axis=1, keepdims=True)
        d = sep / s
        dd_two = (vb - vt - d * np.sum(d * (vb - vt), axis=1, keepdims=True)) / s
        if model == "two_hand":
            return vt + L * dd_two
        # blend: differentiate the normalised sum numerically-safe via the same projection rule
        e = Rt @ np.asarray(cal.d_local_top)
        de = np.cross(wt, e)
        m = d + e
        mn = np.linalg.norm(m, axis=1, keepdims=True)
        u = m / mn
        dm = dd_two + de
        return vt + L * (dm - u * np.sum(u * dm, axis=1, keepdims=True)) / mn
    if model == "top_hand":
        r = L * (Rt @ np.asarray(cal.d_local_top))
        return vt + np.cross(wt, r)
    if model == "bottom_hand":
        r = Rb @ np.asarray(cal.heel_local_bottom)
        return vb + np.cross(wb, r)
    raise ValueError(model)


def move_noise(R_rest, p_rest, R_to, p_to):
    """Carry a resting controller's tracking noise onto another pose.

    Each rest sample's deviation from the rest mean, expressed in the controller's own frame,
    is applied to the pose (R_to, p_to). Gives (N,3,3), (N,3): that pose as the tracker would
    report it, jitter and all.
    """
    Rm = mean_rotation(R_rest)
    pm = p_rest.mean(axis=0)
    dR = Rm.T @ R_rest
    dp = (p_rest - pm) @ Rm
    return R_to @ dR, p_to + dp @ R_to.T


def rotation_angle_deg(R: np.ndarray) -> np.ndarray:
    return np.degrees(np.arccos(np.clip((np.trace(R, axis1=1, axis2=2) - 1) / 2, -1, 1)))


def blade_dir(cal: StickCal, Rt) -> np.ndarray:
    """Blade direction heel->toe (N,3), following the top hand's roll (display only)."""
    return Rt @ np.asarray(cal.b_local_top)
