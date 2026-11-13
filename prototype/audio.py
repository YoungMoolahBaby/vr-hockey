"""The sound mixer (reports/VR hockey stick and puck feel.md, build step 3): one always-open
low-latency output stream to the headset, playing every contact from the contact bus.

- Every contact gets its own voice (up to MAX_VOICES at once), placed at its own sample a
  constant delay after it happened: no jitter, and never early (people notice a sound ~25 ms
  before the hit they see, or ~42 ms after it).
- 5 variants of each sound, with a little random pitch (+-10%) and level (+-3 dB): repeated
  contacts don't sound like one sample.
- Loudness follows how hard the contact was, continuously.
- A soft limiter (tanh) keeps a pile-up from clipping.

The stream is WASAPI shared mode at 48 kHz on "Headphones (Oculus Virtual Audio Device)" (the
Quest over Link) if present, else the default output. Mixer.fill() is the whole callback and
needs no sound card, so tests drive it directly.
"""

from __future__ import annotations

import collections
import time

import numpy as np

import sounds
from contacts import Bus, Contact

RATE = 48000
BLOCK = 256              # 5.3 ms at 48 kHz
MAX_VOICES = 16
VARIANTS = 5
MASTER = 0.7
SPEECH = 1.2             # the voice's gain: over the game's sounds, short of the limiter's knee
KINDS = ("tap", "clack", "ping", "thud", "go", "whistle")


def gain_for(c: Contact) -> tuple[str, float] | None:
    """Which sound a contact makes and how loud (0-1), or None for silence."""
    if c.kind == "puck" and c.speed > 0.3:
        return "clack", 0.35 + 0.65 * min(c.speed / 8.0, 1.0)
    if c.kind == "ice" and c.speed > 0.15:
        return "tap", 0.35 + 0.65 * min(c.speed / 2.0, 1.0)
    if c.kind == "post" and c.speed > 2.0:
        return "ping", 1.0
    if c.kind == "boards" and c.speed > 1.0:
        return "thud", 0.35 + 0.65 * min(c.speed / 12.0, 1.0)
    return None


def bank(rate: int = RATE, variants: int = VARIANTS, seed: int = 7) -> dict[str, list[np.ndarray]]:
    """Each sound in a few versions: its own noise, pitch shifted by up to 10%, peak at 1."""
    rng = np.random.default_rng(seed)
    out: dict[str, list[np.ndarray]] = {}
    for kind in KINDS:
        vs = []
        for i in range(variants if kind not in ("go", "whistle") else 1):
            base = sounds.synth(kind, rng, rate)
            if i:
                f = 1.0 + rng.uniform(-0.1, 0.1)                 # a little pitch
                n = int(len(base) / f)
                base = np.interp(np.arange(n) * f, np.arange(len(base)), base)
            vs.append((base / max(np.abs(base).max(), 1e-9)).astype(np.float32))
        out[kind] = vs
    return out


class Mixer:
    def __init__(self, bus: Bus | None, enabled: bool = True, device: str | None = "Oculus",
                 rate: int = RATE, block: int = BLOCK):
        self.enabled, self.rate, self.block = enabled, rate, block
        self.clips = bank(rate)
        self.rng = np.random.default_rng()
        self.q = bus.subscribe() if bus is not None else collections.deque()
        self.ui: collections.deque = collections.deque()             # (name, strength, perf time)
        self.speech: collections.deque = collections.deque()         # spoken lines (record.Voice)
        self.pending: list = []                                       # (stream time, clip, gain)
        self.voices: list = []                                        # [clip, position, gain]
        self.delay = 0.0                                              # contact -> DAC, kept constant
        self._leads: collections.deque = collections.deque(maxlen=400)
        self.stats = {"played": 0, "late": 0, "dropped": 0, "underruns": 0, "callbacks": 0}
        self.stream = None
        self.device_name = None
        self.want_device = device

    # ---- the stream
    def start(self) -> bool:
        """Open the output stream. False (and a message) if there is no usable device."""
        if not self.enabled:
            return False
        try:
            import sounddevice as sd
            dev = None
            if self.want_device:
                for i, d in enumerate(sd.query_devices()):
                    host = sd.query_hostapis(d["hostapi"])["name"]
                    if d["max_output_channels"] > 0 and "WASAPI" in host and self.want_device.lower() in d["name"].lower():
                        dev = i
                        break
            info = sd.query_devices(dev, "output")
            self.device_name = info["name"]
            rate = self.rate if dev is None else int(info["default_samplerate"])
            if rate != self.rate:
                self.rate = rate
                self.clips = bank(rate)
            self.stream = sd.OutputStream(samplerate=self.rate, blocksize=self.block, channels=2, dtype="float32",
                                          latency="low", device=dev, callback=self._callback)
            self.stream.start()
            return True
        except Exception as e:                                         # no device, busy, ...
            print(f"  audio: no mixer ({e!r}); falling back to winsound", flush=True)
            self.stream = None
            return False

    def close(self) -> None:
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    @property
    def latency_ms(self) -> float:
        return self.delay * 1000

    # ---- playing
    def play(self, name: str, strength: float = 1.0, t: float | None = None) -> None:
        """A sound by name (the drills' go and whistle, a hit), now or at perf time t."""
        self.ui.append((name, float(strength), time.perf_counter() if t is None else t))

    def speak(self, clip: np.ndarray) -> None:
        """A spoken line (float32 samples at our rate, from record.Voice): played from the next
        block, on the headset with the game's sounds."""
        self.speech.append(np.asarray(clip, dtype=np.float32))

    def _callback(self, outdata, frames, time_info, status) -> None:
        if status.output_underflow:
            self.stats["underruns"] += 1
        now_perf = time.perf_counter()
        cur = time_info.currentTime
        dac = time_info.outputBufferDacTime
        if dac <= 0 or cur <= 0:                                       # no timing from this host API
            cur, dac = now_perf, now_perf + (self.stream.latency if self.stream is not None else 0.02)
        mono = self.fill(frames, cur, dac, now_perf)
        outdata[:, 0] = mono
        outdata[:, 1] = mono

    def fill(self, frames: int, cur: float, dac: float, now_perf: float) -> np.ndarray:
        """One block: schedule what has happened since the last block, mix the voices.
        cur: the stream clock now; dac: when this block's first sample is heard (stream clock);
        now_perf: time.perf_counter() now (maps contacts' perf times onto the stream clock)."""
        self.stats["callbacks"] += 1
        to_stream = cur - now_perf
        self._leads.append(dac - cur)
        self.delay = max(self._leads) + frames / self.rate + 0.001    # the most the stream needs, constant
        while self.q:                                                  # contacts
            c = self.q.popleft()
            g = gain_for(c)
            if g is not None:
                self._schedule(c.t + to_stream + self.delay, g[0], g[1])
        while self.ui:                                                 # by name
            name, strength, t = self.ui.popleft()
            self._schedule(t + to_stream + self.delay, name, 0.35 + 0.65 * min(max(strength, 0.0), 1.0))
        while self.speech:                                             # the voice: now, never dropped
            self.voices.append([self.speech.popleft(), 0, SPEECH])
        out = np.zeros(frames, dtype=np.float32)
        keep = []
        for item in sorted(self.pending, key=lambda x: x[0]):
            ts, clip, gain = item
            start = int(round((ts - dac) * self.rate))
            if start >= frames:
                keep.append(item)
                continue
            if start < 0:                                              # late: play now (never early)
                self.stats["late"] += 1
                start = 0
            self._voice(clip, gain, -start)                            # negative position: starts later
        self.pending = keep
        alive = []
        for v in self.voices:
            clip, pos, gain = v
            a = max(0, -pos)                                           # where in this block it starts
            src = max(pos, 0)
            n = min(frames - a, len(clip) - src)
            if n > 0:
                out[a:a + n] += clip[src:src + n] * gain
            v[1] = pos + frames
            if v[1] < len(clip):
                alive.append(v)
        self.voices = alive
        return np.tanh(out * MASTER).astype(np.float32)

    def _schedule(self, ts: float, name: str, gain: float) -> None:
        vs = self.clips.get(name)
        if not vs:
            return
        clip = vs[int(self.rng.integers(len(vs)))]
        gain *= 10 ** (self.rng.uniform(-3, 3) / 20)                   # +-3 dB
        self.pending.append((ts, clip, gain))
        self.stats["played"] += 1

    def _voice(self, clip, gain, pos) -> None:
        if len(self.voices) >= MAX_VOICES:                             # drop the quietest (never speech)
            i = min(range(len(self.voices)), key=lambda k: self.voices[k][2] + 9 * (len(self.voices[k][0]) > self.rate))
            if self.voices[i][2] >= gain:
                self.stats["dropped"] += 1
                return
            self.voices.pop(i)
            self.stats["dropped"] += 1
        self.voices.append([clip, pos, gain])


class WinsoundSink:
    """The old player, when there is no mixer: the loudest-ranked sound of each frame, one at a time."""

    def __init__(self, bus: Bus | None, enabled: bool = True):
        self.s = sounds.Sounds(enabled)
        self.q = bus.subscribe() if bus is not None else collections.deque()
        self.ui: list = []
        self.device_name, self.stats, self.latency_ms = "winsound", {}, float("nan")

    def play(self, name: str, strength: float = 1.0, t: float | None = None) -> None:
        self.ui.append((name, strength))

    def frame(self) -> None:
        evs = list(self.ui)
        self.ui.clear()
        while self.q:
            g = gain_for(self.q.popleft())
            if g is not None:
                evs.append((g[0], (g[1] - 0.35) / 0.65))
        self.s.play_most_important(evs)

    def close(self) -> None:
        pass
