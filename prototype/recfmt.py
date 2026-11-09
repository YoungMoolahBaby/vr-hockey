"""The recording format shared by record.py, synth.py and analyze.py.

A run is a folder with:
  rec.csv    one row per sample (target 1 kHz)
  meta.json  run info: query rate, lag, reference space, phase list, notes

Devices: l = left controller, r = right controller, h = head (the VIEW space).
Flags are the raw OpenXR bits (see FLAG_* below).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from stickmath import quat_to_mat

CONTROLLERS = ("l", "r")
CTRL_FIELDS = ("flags", "px", "py", "pz", "qx", "qy", "qz", "qw",
               "vflags", "vx", "vy", "vz", "wx", "wy", "wz", "grip")   # grip = squeeze button 0..1
HEAD_FIELDS = ("flags", "px", "py", "pz", "qx", "qy", "qz", "qw")

COLUMNS = (["t", "xr_ns", "phase"]
           + [f"{d}_{f}" for d in CONTROLLERS for f in CTRL_FIELDS]
           + [f"h_{f}" for f in HEAD_FIELDS])

FLAG_ORI_VALID = 0x1
FLAG_POS_VALID = 0x2
FLAG_ORI_TRACKED = 0x4
FLAG_POS_TRACKED = 0x8
VFLAG_LINEAR = 0x1
VFLAG_ANGULAR = 0x2

GAP = "-"  # phase label between protocol phases


def write_meta(run_dir: Path, meta: dict) -> None:
    (Path(run_dir) / "meta.json").write_text(json.dumps(meta, indent=2))


def load(run_dir) -> tuple[pd.DataFrame, dict]:
    run_dir = Path(run_dir)
    df = pd.read_csv(run_dir / "rec.csv", dtype={"phase": str})
    meta_path = run_dir / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    return df, meta


class Track:
    """One device's samples as arrays (rows in the same order as the frame)."""

    def __init__(self, df: pd.DataFrame, dev: str):
        self.dev = dev
        self.t = df["t"].to_numpy(dtype=np.float64)
        self.flags = df[f"{dev}_flags"].to_numpy(dtype=np.int64)
        self.p = df[[f"{dev}_px", f"{dev}_py", f"{dev}_pz"]].to_numpy(dtype=np.float64)
        q = df[[f"{dev}_qx", f"{dev}_qy", f"{dev}_qz", f"{dev}_qw"]].to_numpy(dtype=np.float64, copy=True)  # written below
        # an all-zero quaternion means "no pose"; make it identity so the maths stays finite
        bad = np.linalg.norm(q, axis=1) < 1e-6
        q[bad] = [0, 0, 0, 1]
        self.q = q
        self.R = quat_to_mat(q)
        if f"{dev}_vflags" in df:
            self.vflags = df[f"{dev}_vflags"].to_numpy(dtype=np.int64)
            self.v = df[[f"{dev}_vx", f"{dev}_vy", f"{dev}_vz"]].to_numpy(dtype=np.float64)
            self.w = df[[f"{dev}_wx", f"{dev}_wy", f"{dev}_wz"]].to_numpy(dtype=np.float64)
        col = f"{dev}_grip"
        self.grip = df[col].to_numpy(dtype=np.float64) if col in df else np.zeros(len(df))

    @property
    def valid(self) -> np.ndarray:
        need = FLAG_POS_VALID | FLAG_ORI_VALID
        return (self.flags & need) == need

    @property
    def tracked(self) -> np.ndarray:
        need = FLAG_POS_TRACKED | FLAG_ORI_TRACKED
        return self.valid & ((self.flags & need) == need)

    def changed(self) -> np.ndarray:
        """True where the pose differs from the previous sample (a fresh pose from the runtime)."""
        pq = np.hstack([self.p, self.q])
        ch = np.any(pq[1:] != pq[:-1], axis=1)
        return np.concatenate([[True], ch])
