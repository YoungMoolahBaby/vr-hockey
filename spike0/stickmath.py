"""Rotation and vector helpers. Quaternions are (x, y, z, w); poses map local to world:
world = R @ local + p."""

from __future__ import annotations

import numpy as np


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


def unit(v: np.ndarray) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):   # zero vectors (no pose) become NaN, masked later
        return v / np.linalg.norm(v, axis=-1, keepdims=True)
