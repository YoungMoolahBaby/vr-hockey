"""Jon's custom skates (the custom-skate project, next door in ../../custom-skate) on the players.

The skate comes from custom-skate's 3D viewer build, the files its web page loads: a manifest (the
parts, their colours; mm, z up) and two base64 files holding each part's int16 positions (in units
of the manifest's scale, 0.01 mm) and uint32 indices, one for the boot and one for what's under it
(the roller chassis and wheels, or the ice holder and runner). It's built on custom-skate's stand-in
foot (a man of about 175 cm), a right foot: heel at x = 0, toes +x, +y the foot's inside (its left),
z up, the bottom of the foot at z = 0.

Each part is cut down to a few hundred to a few thousand triangles (fast-simplification), coloured
in Jon's colourway (custom-skate's README pictures: a black carbon boot, white laces, green eyelets,
a red heel-lock eyelet; roller: a grey truss chassis and white wheels; ice: a white holder and a
steel runner), and cached in gear_cache/ until the build changes. Parts hidden inside (footbed,
ankle pads, the stand-in leg) are left out, and so is the tongue's printed lattice: it sits under the
tongue plate, and its thousands of little holes won't cut down. The cache stays out of git: once the boot is built on
Jon's own foot scan, it carries the shape of his foot.

A model's frame is the skater's (forward, left, up) in metres, its origin on the ground under the
middle of the wheels (or runner), so it stands where it's put. Left skates are the right one
mirrored."""

from __future__ import annotations

import base64
import json
import os
import zlib
from pathlib import Path
from typing import NamedTuple

import numpy as np

import theme

SOURCE = Path(os.environ.get("VR_HOCKEY_SKATES", Path(__file__).resolve().parents[2] / "custom-skate" / "out"))
CACHE = Path(__file__).resolve().parent / "gear_cache"
KIND = "roller"                  # Jon, 2026-11-13: "let's do roller hockey skates" (or "ice")
BUILDS = {   # kind -> (build folder, manifest, the boot's mesh file, the chassis or holder's)
    "roller": ("boot_roller", "manifest_roller.json", "boot_roller.txt", "under_roller.txt"),
    "ice": ("boot", "manifest.json", "boot.txt", "under.txt"),
}
VERSION = 1                      # bump when the cache's contents change meaning (LOOK is checked itself)

# Jon's colourway, as displayed (sRGB 0-255), and how shiny each part is (0 matte - 1 gloss)
BLACK, GLOSS_BLACK, LACE = (24, 24, 27), (14, 14, 16), (238, 238, 234)
EYELET, HEEL_LOCK = (24, 112, 52), (172, 24, 32)
TRUSS, METAL, WHEEL = (168, 171, 176), (128, 132, 138), (236, 236, 233)
LOOK = {   # part -> (colour, shine, triangles to keep)
    "shell": (BLACK, 0.8, 3000),
    "heel panel (shell)": (BLACK, 0.8, 1200),
    "toe cap": (GLOSS_BLACK, 1.0, 700),
    "mount pads": ((20, 20, 22), 0.2, 150),
    "liner": ((40, 40, 44), 0.1, 800),
    "tongue plate": ((20, 20, 23), 0.3, 1500),
    "tongue tag": ((20, 20, 23), 0.3, 100),
    "tendon guard": (GLOSS_BLACK, 0.9, 400),
    "eyelets": (EYELET, 0.7, 1200),
    "heel-lock eyelets": (HEEL_LOCK, 0.7, 150),
    "laces": (LACE, 0.1, 1500),
    # roller
    "chassis upper": (TRUSS, 0.6, 3000),
    "chassis lower": (TRUSS, 0.6, 2000),
    "ties": (TRUSS, 0.6, 150),
    "axles": (METAL, 0.8, 300),
    "spacers": (METAL, 0.8, 300),
    "wheels": (WHEEL, 0.3, 1600),
    "hubs": ((150, 153, 158), 0.6, 600),
    # ice
    "holder": ((236, 238, 240), 0.6, 1500),
    "runner": ((185, 190, 198), 1.0, 300),
    "rocker insert": ((60, 62, 68), 0.3, 100),
    "pivot pin": ((140, 145, 150), 0.8, 80),
}
UNDER = ("wheels", "runner")     # what touches the ground: its lowest point is the ground, its middle the origin


class Model(NamedTuple):
    """Triangles ready to draw: vertices rows of x, y, z (forward, left, up; m), normal, colour (as
    drawn), shine; index (n, 3) uint32."""
    vertices: np.ndarray
    index: np.ndarray
    sole: float                  # m: the bottom of the foot over the ground (the skate's stand height)

    def mirrored(self) -> "Model":
        """The other foot: left and right swapped (y -> -y), triangles turned to face out again."""
        v = self.vertices.copy()
        v[:, 1] *= -1
        v[:, 4] *= -1
        return Model(v, np.ascontiguousarray(self.index[:, ::-1]), self.sole)


def _normals(P: np.ndarray, F: np.ndarray) -> np.ndarray:
    """Smooth vertex normals: each face's area-weighted normal, summed at its corners."""
    fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    N = np.zeros_like(P)
    for k in range(3):
        np.add.at(N, F[:, k], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def _build(kind: str) -> tuple[Model, dict] | None:
    import fast_simplification

    folder, man, boot, under = BUILDS[kind]
    d = SOURCE / folder / "viewer"
    if not (d / man).exists():
        return None
    m = json.loads((d / man).read_text())
    bufs = {"boot": base64.b64decode("".join((d / boot).read_text().split())),
            "under": base64.b64decode("".join((d / under).read_text().split()))}
    scale = m["scale"] / 1000.0                      # stored units -> m
    parts = []
    for p in m["parts"]:
        look = LOOK.get(p["name"])
        if look is None:
            continue
        b = bufs[p.get("buf", "boot")]
        P = np.frombuffer(b, np.int16, p["vertexCount"] * 3, p["vertexOffset"]).reshape(-1, 3) * scale
        F = np.frombuffer(b, np.uint32, p["indexCount"], p["indexOffset"]).reshape(-1, 3).astype(np.int64)
        colour, shine, keep = look
        if len(F) > keep:
            P, F = fast_simplification.simplify(P.astype(np.float32), F.astype(np.int32), 1.0 - keep / len(F))
            P, F = P.astype(np.float64), F.astype(np.int64)
        vol = np.einsum("ij,ij->i", P[F[:, 0]], np.cross(P[F[:, 1]], P[F[:, 2]])).sum()
        if vol < 0:                                  # closed and facing in: turn it out
            F = F[:, ::-1]
        parts.append((p["name"], P, F, theme.srgb(*colour), shine))
    if not parts:
        return None
    ground = [P for name, P, *_ in parts if name in UNDER]
    G = np.vstack(ground) if ground else np.vstack([P for _, P, *_ in parts])
    origin = np.array([(G[:, 0].min() + G[:, 0].max()) / 2, 0.0, G[:, 2].min()])
    V, I, n = [], [], 0
    for name, P, F, colour, shine in parts:
        P = P - origin
        rows = np.empty((len(P), 10), dtype=np.float32)
        rows[:, :3], rows[:, 3:6], rows[:, 6:9], rows[:, 9] = P, _normals(P, F), colour, shine
        V.append(rows)
        I.append(F + n)
        n += len(P)
    model = Model(np.vstack(V), np.vstack(I).astype(np.uint32), float(-origin[2]))
    info = {"kind": kind, "variant": m.get("variant", ""), "triangles": len(model.index),
            "parts": [name for name, *_ in parts]}
    return model, info


def _stamp(kind: str) -> str:
    folder, *files = BUILDS[kind]
    stats = [(SOURCE / folder / "viewer" / f).stat() for f in files]
    look = zlib.crc32(repr(sorted(LOOK.items())).encode())
    return f"v{VERSION} {look:08x} " + " ".join(f"{s.st_size}:{s.st_mtime_ns}" for s in stats)


_LOADED: dict = {}


def skates(kind: str = KIND) -> tuple[Model, Model] | None:
    """The (left, right) skate models, or None when custom-skate's viewer build isn't there."""
    if kind in _LOADED:
        return _LOADED[kind]
    out = None
    try:
        stamp = _stamp(kind)
    except OSError:
        stamp = None
    if stamp is not None:
        path = CACHE / f"skate_{kind}.npz"
        right = None
        if path.exists():
            z = np.load(path)
            if str(z["stamp"]) == stamp:
                right = Model(z["vertices"], z["index"], float(z["sole"]))
        if right is None:
            built = _build(kind)
            if built is not None:
                right, info = built
                CACHE.mkdir(exist_ok=True)
                np.savez(path, vertices=right.vertices, index=right.index, sole=right.sole, stamp=stamp)
                print(f"  skates: {info['variant']}, {info['triangles']} triangles a skate (cached)", flush=True)
        if right is not None:
            out = (right.mirrored(), right)
    _LOADED[kind] = out
    return out


def place(R: np.ndarray, o: np.ndarray) -> np.ndarray:
    """A 4x4 model -> world: columns of R are the model's forward, left and up in the world."""
    M = np.eye(4)
    M[:3, :3], M[:3, 3] = R, o
    return M
