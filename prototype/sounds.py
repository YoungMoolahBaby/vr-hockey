"""Short synthesized sounds for the sandbox: the blade touching the ice, the puck off the blade,
a post, the boards. Made once as WAV files (no extra packages) and played with winsound.

winsound plays one sound at a time (a new one cuts the last) with some tens of ms of latency;
fine for a first feel test, and the controller buzz carries the instant feedback.
"""

from __future__ import annotations

import tempfile
import wave
import winsound
from pathlib import Path

import numpy as np

RATE = 22050
LEVELS = (0.35, 0.65, 1.0)          # soft / medium / hard
PRIORITY = {"go": 5, "whistle": 4, "clack": 3, "ping": 2, "thud": 1, "tap": 0}


def _env(n: int, decay_s: float) -> np.ndarray:
    return np.exp(-np.arange(n) / (decay_s * RATE))


def _lowpass(x: np.ndarray, a: float) -> np.ndarray:
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc)
        y[i] = acc
    return y


def synth(kind: str, rng: np.random.Generator) -> np.ndarray:
    if kind == "tap":                 # blade on ice: a short, dull scrape
        n = int(0.05 * RATE)
        return _lowpass(rng.normal(size=n), 0.35) * _env(n, 0.008) * 1.6
    if kind == "clack":               # puck off the blade: a heavy, dull rubber "thock" (was a light clack)
        n = int(0.09 * RATE)
        t = np.arange(n) / RATE
        body = 0.7 * np.sin(2 * np.pi * 380 * t) + 0.45 * np.sin(2 * np.pi * 690 * t) + 0.2 * np.sin(2 * np.pi * 1150 * t)
        knock = _lowpass(rng.normal(size=n), 0.25) * _env(n, 0.004)
        return (body * _env(n, 0.018) + 0.9 * knock) * 0.9
    if kind == "ping":                # off the post
        n = int(0.4 * RATE)
        t = np.arange(n) / RATE
        return (0.6 * np.sin(2 * np.pi * 3400 * t) + 0.3 * np.sin(2 * np.pi * 5150 * t)) * _env(n, 0.12)
    if kind == "thud":                # into the boards
        n = int(0.15 * RATE)
        t = np.arange(n) / RATE
        return (0.8 * np.sin(2 * np.pi * 110 * t) + 0.5 * _lowpass(rng.normal(size=n), 0.1)) * _env(n, 0.05)
    if kind == "go":                  # a rep starts: two quick rising beeps
        n = int(0.09 * RATE)
        t = np.arange(n) / RATE
        beep = lambda f: np.sin(2 * np.pi * f * t) * np.minimum(1, (n - np.arange(n)) / (0.01 * RATE))
        return np.concatenate([beep(880), np.zeros(int(0.04 * RATE)), beep(1320)])
    if kind == "whistle":             # a rep ends: a short referee's trill
        n = int(0.35 * RATE)
        t = np.arange(n) / RATE
        f = 2900 + 180 * np.sin(2 * np.pi * 28 * t)
        return np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.minimum(1, (n - np.arange(n)) / (0.05 * RATE))
    raise ValueError(kind)


class Sounds:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.dir = Path(tempfile.gettempdir()) / "vr-hockey-sounds"
        self.dir.mkdir(exist_ok=True)
        rng = np.random.default_rng(7)
        self.files: dict[tuple[str, int], str] = {}
        for kind in PRIORITY:
            base = synth(kind, rng)
            base = base / max(np.abs(base).max(), 1e-9)
            for i, level in enumerate(LEVELS):
                path = self.dir / f"{kind}_{i}.wav"
                with wave.open(str(path), "wb") as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(RATE)
                    w.writeframes((base * level * 0.9 * 32767).astype(np.int16).tobytes())
                self.files[(kind, i)] = str(path)

    def play(self, kind: str, strength: float) -> None:
        if not self.enabled:
            return
        i = 0 if strength < 0.33 else 1 if strength < 0.66 else 2
        winsound.PlaySound(self.files[(kind, i)], winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)

    def play_most_important(self, events: list[tuple[str, float]]) -> None:
        """Several sounds in one frame: play the one that matters most (winsound plays one at a time)."""
        if events:
            kind, strength = max(events, key=lambda e: (PRIORITY[e[0]], e[1]))
            self.play(kind, strength)
