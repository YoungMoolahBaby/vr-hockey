"""A hockey stick sized from the player: length from height, lie, and a curved blade.

Stick frame (metres): origin at the heel's bottom corner, x along the blade bottom toward
the toe, y up (blade flat on the ice), z = x cross y. For a LEFT shot z is the forehand face
normal and the toe curls toward +z. A right-shot blade is the mirror image.

Sizing (sources in README):
- length: heel contact to the top of the shaft (how Bauer measures it). CCM sizes 5'2"-5'10"
  on a 57" stick, so we use 0.84 x height (68" -> 57.1").
- lie: 5 is the usual starting point = 135 deg between blade and shaft = shaft 45 deg above
  the ice; each lie step stands the shaft up about 2 deg.
- blade: about 29 cm heel to toe, 7.5 cm tall, a mid-toe curve about 1/2" deep (P92-like).
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

import numpy as np

INCH = 0.0254


def parse_height(s: str) -> float:
    """5'8" / 5'8 / 68in / 173cm / 1.73 -> metres."""
    t = s.strip().lower().replace(" ", "")
    m = re.fullmatch(r"(\d+)'(\d+(?:\.\d+)?)?(?:\"|in)?", t)
    if m:
        return (int(m.group(1)) * 12 + float(m.group(2) or 0)) * INCH
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(cm|in|m)?", t)
    if not m:
        raise ValueError(f"can't read height {s!r}: try 5'8\" or 173cm")
    v, unit = float(m.group(1)), m.group(2)
    if unit == "cm" or (unit is None and v > 100):
        return v / 100
    if unit == "in" or (unit is None and 40 <= v <= 100):
        return v * INCH
    return v


@dataclass
class StickSpec:
    shoots: str               # 'left' or 'right'
    height_m: float
    length_m: float           # heel contact to the top of the shaft
    lie: float
    shaft_angle_deg: float    # shaft above the ice with the blade flat
    grip_from_top_m: float    # top hand's grip centre below the knob
    blade_len_m: float
    blade_h_m: float
    curve_depth_m: float
    curve_shape: float = 2.5      # exponent: 1 = even heel-to-toe, 2.5 = mid-toe, 4 = toe curve
    face_open_deg: float = 4.0    # how far the face opens (tilts back) by the toe; P92 is slightly open
    flex: float = 70.0            # stick flex rating: lbs to bend the shaft 1 inch (higher = stiffer)

    # ------------------------------------------------------------------ derived geometry
    @property
    def top_hand(self) -> str:
        return "r" if self.shoots == "left" else "l"

    @property
    def bottom_hand(self) -> str:
        return "l" if self.top_hand == "r" else "r"

    @property
    def u(self) -> np.ndarray:
        """Shaft direction, heel -> knob, in the stick frame."""
        a = np.radians(self.shaft_angle_deg)
        return np.array([-np.cos(a), np.sin(a), 0.0])

    @property
    def z_forehand(self) -> np.ndarray:
        return np.array([0.0, 0.0, 1.0 if self.shoots == "left" else -1.0])

    @property
    def knob(self) -> np.ndarray:
        return self.length_m * self.u

    @property
    def grip(self) -> np.ndarray:
        """Where the top hand's grip centre sits on the shaft."""
        return (self.length_m - self.grip_from_top_m) * self.u

    def blade_z(self, x):
        """Curve: the toe curls toward the forehand; curve_shape sets where the bend sits."""
        return self.z_forehand[2] * self.curve_depth_m * (np.asarray(x) / self.blade_len_m) ** self.curve_shape

    def edge(self, n: int = 12, top: bool = False, frac: float | None = None) -> np.ndarray:
        """(n, 3) points along the blade heel to toe: the bottom edge, the top edge, or a line at
        `frac` of the blade's height. The face opens (the top tilts back from the forehand) toward
        the toe."""
        f = (1.0 if top else 0.0) if frac is None else frac
        x = np.linspace(0, self.blade_len_m, n)
        open_rad = np.radians(self.face_open_deg) * (x / self.blade_len_m)
        z = self.blade_z(x) - self.z_forehand[2] * f * self.blade_h_m * np.tan(open_rad)
        return np.stack([x, np.full(n, f * self.blade_h_m), z], axis=1)

    @property
    def heel(self) -> np.ndarray:
        return np.zeros(3)

    @property
    def toe(self) -> np.ndarray:
        return np.array([self.blade_len_m, 0.0, float(self.blade_z(self.blade_len_m))])

    @property
    def sweet(self) -> np.ndarray:
        """Where the puck usually sits on the blade: a bit past the middle, on the bottom edge."""
        x = 0.55 * self.blade_len_m
        return np.array([x, 0.0, float(self.blade_z(x))])

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "StickSpec":
        names = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in d.items() if k in names})     # older files lack newer fields

    def with_(self, **changes) -> "StickSpec":
        d = self.to_dict()
        d.update(changes)
        if "lie" in changes:
            d["shaft_angle_deg"] = 45.0 + 2.0 * (d["lie"] - 5.0)
        return StickSpec(**d)


def from_height(height_m: float, shoots: str = "left", lie: float = 5.0, length_m: float | None = None,
                curve_depth_m: float = 0.5 * INCH, flex: float = 70.0) -> StickSpec:
    if shoots not in ("left", "right"):
        raise ValueError(shoots)
    length = length_m if length_m else 0.84 * height_m
    return StickSpec(shoots=shoots, height_m=height_m, length_m=float(length), lie=lie,
                     shaft_angle_deg=45.0 + 2.0 * (lie - 5.0), grip_from_top_m=0.07,
                     blade_len_m=0.29, blade_h_m=0.075, curve_depth_m=curve_depth_m, flex=flex)
