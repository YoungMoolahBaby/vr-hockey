"""Calling a shot's speed from the puck's free flight (reports/Shot release.md, change 4).

The game and every replay tool use this, so the numbers they report mean the same thing. Radar and
lab trackers measure a puck in flight; the old call took the peak puck speed over 0.25 s after a
hard contact, re-contacts and all.

A hard contact (impulse over 2 m/s, the puck over 6 m/s) arms a call. Free flight starts once the
blade hasn't touched the puck for 5 ms; any touch starts it again. The call is the puck's mean speed
over the first 15 ms of free flight, made once 50 ms of free flight have passed. No call if the speed
changed by more than 4.5 m/s within those 50 ms (it hit something: Manning 2020 excluded shots the
same way) or if it is slower than 12 mph.
"""

from __future__ import annotations

import math

import numpy as np

MPH = 2.23694
ARM_IMPULSE = 2.0        # m/s: a contact at least this hard...
ARM_SPEED = 6.0          # m/s: ... that leaves the puck at least this fast arms a call
QUIET_S = 0.005          # s: free flight starts once the blade hasn't touched the puck for this long
WINDOW_S = 0.015         # s: the call is the mean speed over this much free flight
CHECK_S = 0.050          # s: ... made after this much free flight, if
JUMP_MS = 4.5            # m/s: ... the speed changed by no more than this meanwhile
MIN_MPH = 12.0


class ShotCall:
    def __init__(self):
        self.reset()

    def reset(self) -> None:
        """A new puck: forget any shot in progress."""
        self.armed = False
        self.last_touch = -1e9
        self.flight: list[tuple[float, np.ndarray]] = []

    def tick(self, t: float, impulse: float, vel) -> dict | None:
        """One physics tick: t (s), the biggest blade-puck impulse this tick (m/s, 0 if none), and the
        puck's velocity. Returns the call when one is made: speed (m/s and mph), horizontal and
        vertical speed (m/s) and launch angle (degrees up)."""
        vel = np.asarray(vel, dtype=float)
        if impulse > 0:
            self.last_touch = t
            self.flight = []
            if impulse > ARM_IMPULSE and float(np.linalg.norm(vel)) > ARM_SPEED:
                self.armed = True
            return None
        if not self.armed or t - self.last_touch < QUIET_S:
            return None
        self.flight.append((t, vel.copy()))
        if t - self.flight[0][0] < CHECK_S:
            return None
        flight, self.flight, self.armed = self.flight, [], False
        speeds = np.array([np.linalg.norm(v) for _, v in flight])
        if speeds.max() - speeds.min() > JUMP_MS:
            return None
        t0 = flight[0][0]
        win = np.array([v for tt, v in flight if tt - t0 <= WINDOW_S])
        s = float(np.mean(np.linalg.norm(win, axis=1)))
        vh = float(np.mean(np.hypot(win[:, 0], win[:, 2])))
        vy = float(np.mean(win[:, 1]))
        if s * MPH < MIN_MPH:
            return None
        return {"ms": round(s, 2), "mph": round(s * MPH, 1), "vh": round(vh, 2), "vy": round(vy, 2),
                "angle": round(math.degrees(math.atan2(vy, vh)), 1)}
