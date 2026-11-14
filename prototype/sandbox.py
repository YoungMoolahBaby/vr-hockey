"""Spike 0 sandbox: your stick, a puck and a net. Play, and tune everything as you go.

    uv run python sandbox.py
    uv run python sandbox.py --fresh      # start from the defaults, not your saved settings

Controls
  grip buttons (middle finger)  hold the stick: right = top hand, left = bottom hand (grab.py)
  left thumbstick               move you around the ice; forward is where you look (rig.py)
  left trigger (index finger)   sprint: squeeze to go faster than the stick alone, up to "sprint speed"
  right trigger (index finger)  shoot: firm hands. Released, your hands are soft and give with the puck
                                ("stickhandling hands"); squeeze and they firm up for a shot ("shooting hands")
  right thumbstick left/right   turn you, about your head: smoothly, or in steps per flick (the
                                "snap turn" setting, degrees; 0 = smooth). The view's edges darken
                                while you move ("comfort vignette")
  X                             a new puck, on your blade
  hold the left thumbstick in   (1 s) put the net straight in front of you again
  menu button (left controller) the settings menu, in and out. Nothing changes a setting outside it
                                (Jon, 2026-11-13: none changed by accident while playing). In it:
    left stick left/right       pick a setting (the voice says which, and its value)
    left stick up/down          change it (hold to keep changing); it takes effect at once
    B                           say the current setting again
    A                           save the settings (sandbox_settings.json, used next time)
    Y                           fit the stick in your hand: right thumbstick turns the blade
                                (left/right) and tilts the stick (up/down); hold B and push to
                                swing it sideways; A saves the fit (Y again leaves without saving)

Settings: stick length, lie, curve depth, face open, flex, forgiveness (extra reach for catching
the puck), puck weight, ice friction, blade pop, blade grip, buzz strength, soft hands (off here; the 3v3 turns it on) and its shot
release speed, skate speed, snap turn (degrees; 0 = smooth), skate height (the ice below your floor,
as under your feet on skates; 0 = off), smooth turn speed, comfort vignette,
ice assist (a blade within this many cm of the ice rests on it: you can't feel the ice; 0 = off).

The puck physics (puck.py) runs at 1 kHz, four substeps per controller sample, with the blade
flexing on the shaft. The ice holds the blade up: push lower and the shaft bends (and loads)
instead. Sounds: a tap when the blade lands on the ice, a clack off the puck, posts, boards.
Every puck contact buzzes the hands holding the stick; a touchdown gives a light tick.

Quit the app in the headset (or Ctrl+C) to end. Everything is recorded to data/<timestamp>/:
rec.csv (controllers), puck.csv (puck, 200 Hz), events.jsonl (settings, goals, shots), meta.json.
"""

from __future__ import annotations

import _thread
import argparse
import collections
import ctypes
import ctypes.wintypes
import datetime as dt
import json
import math
import queue
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

import glfast  # noqa: F401  (first: PyOpenGL's error checking off, read when xr loads it)
import numpy as np
import xr
from xr.utils.gl import ContextObject
from xr.utils.gl.glfw_util import GLFWOffscreenContextProvider
from xr.utils.matrix4x4f import GraphicsAPI, Matrix4x4f

import gear
import grab
import puck as pk
import recfmt
import record
import rig
import shotcall
import stickmath
import stickspec
import theme
import threes
import audio
from contacts import Bus, Contact
from stickspec import INCH

HERE = Path(__file__).resolve().parent
SETTINGS_PATH = HERE / "sandbox_settings.json"
SNAP_DEG = 0.0           # smooth turning (Jon's pick); 30 turns you in steps, the comfort option
VIGNETTE = 0.7           # comfort: the view's edges darken while the thumbsticks move you (0 = off)
GRID = 0.0               # the 2 m ice grid: off (a real rink has none; its lines sliding by under you are
                         # motion your inner ear doesn't feel). 1 = on (the "ice grid" setting)
AA = 4.0                 # anti-aliasing: 4x multisampling (record.LineRenderer), so far lines and white edges
                         # don't break into stair-steps that crawl as you move. 0 = off ("anti-aliasing")
PUSH = 6.0               # m/s^2: the skating push limit (rig.Drive.push), the research's pick. ON: with it off
                         # (the old easing, 20-47 m/s^2 jolts) Jon got sick within seconds; 6 "was solid", and
                         # 6-10 felt fine at 3 and 4 m/s (free skate 2026-11-09). 0 = the old easing
GLIDE = 1.5              # m/s^2: let go and you coast, slowing at this (rig.Drive.glide): 2 s and 3 m from 3 m/s.
STOP = 8.0               # m/s^2: the hockey stop, the left stick held against your motion (rig.Drive.stop_ms2).
                         # Both "felt good" (free skate 2026-11-09, with push 6); 0 = off
CARVE = 6.0              # m/s^2: the turn limit, the path bends at most this hard sideways (rig.Drive.carve): the
                         # stick's turn tops out at 115 deg/s at 3 m/s. 6 "felt good"; 9 (no cap at 3 m/s) left
                         # Jon "a little motion sick" after 16 min (free skate 2026-11-10); 0 = off
SPRINT = 4.5             # m/s: the left trigger's top speed (rig.Drive.sprint_ms): the stick alone cruises up to
                         # "skate speed" (3); squeezing the trigger goes faster toward this, the harder the
                         # faster (a game's speed burst, by how hard you squeeze). Modest: Jon is prone to motion
                         # sickness, and it rose from 3 to 10 m/s in So et al. 2001. 0 = off ("sprint speed")
HANDLE = 1.5             # the stick's damping (Flex.damping) while you stickhandle: soft hands that give with the
                         # puck. The right trigger (top hand's index finger) firms them up to "shooting hands"
                         # (the "hands" setting, 0.6), the harder you squeeze the firmer, for a shot. Jon asked
                         # (2026-11-10) for the puck to spring off the stick less, with a shooting mode on the
                         # trigger. Measured on a synthetic blade: a 4 m/s pass into a still blade comes back at
                         # 11% at 0.6 and 0% at 1.5; a 1.5 m/s tap sends the puck off at 98% of the blade's speed
                         # at 0.6 and 87% at 1.5; a wrist shot is ~5% slower at 1.5. Blade pop changes none of
                         # these. 0 = off: always the shooting hands, as before ("stickhandling hands")
SKATES = 0.0             # cm: skate height ("skate height"): the ice sits this far below your floor, as it does
                         # under your feet on skates (rig.Rig.lift), so a stick of your real length fits your hands
                         # and you see the ice from your height on skates. Measure it: your height in skates minus
                         # barefoot (no reliable published figure; blogs say 1-3 inches). 0 = off: the ice is your floor
FEET = 0.0               # your own skates under you ("your skates", gear.py: Jon's roller skates), placed by
                         # MyFeet from where your head is: off until tried in the headset (legs that move on
                         # their own could bother a queasy stomach)
COMFORT_CHECK_MIN = 4.0  # a 0-10 queasiness check this often (Comfort; the "comfort check" setting, 0 = off)
JUMP_M = 0.2             # m: the blade can't move this far in one physics tick: a snap turn or a teleport
# The blade's velocity at a contact (reports/Shot release.md, change 1). One sample's pose difference was
# ~10x noisier than needed (per-ms changes of 13 m/s at p99 in shots, implied accelerations of 10,000-
# 15,000 m/s^2 against pros' ~400-600): a least-squares fit over a few ms of samples, with their true
# times, cuts it 4-5x for 2 ms of delay on the contact velocity only (the stick is drawn and swept
# where the hands are). Sample gaps use their true length (they were clipped at 10 ms: the puck lost time).
VEL_WINDOW_S = 0.0       # s: the fit's window; 0 = one sample's difference. OFF: on Jon's replays (2026-11-10) a 4 ms
                         # fit made his fastest swing's shot faster (76 -> 113 mph; 8 ms: 97): it lags the virtual
                         # stick's near-instant stops, which no real stick makes, so the puck got the speed the blade
                         # had just had. Fewer launches in one session (7 -> 4), not in the other. Try 0.004 or 0.008
STALL_S = 0.020          # s: a gap between samples longer than this is a jump: no sweep, no velocity from it
JUMP_MS = 50.0           # m/s: the sweet spot moving faster than this between samples is a tracking jump, not a
                         # swing (Jon's fastest real blade: ~47 m/s, 4.7 cm a tick): no sweep, no velocity
SUBSTEP_S = 0.00025      # s: the physics' longest substep (a long gap between samples takes more of them)
MAX_DT = 0.25            # s: a longer gap (a stall) only advances the puck this far
TRACKED = recfmt.FLAG_ORI_TRACKED | recfmt.FLAG_POS_TRACKED
VALID = recfmt.FLAG_ORI_VALID | recfmt.FLAG_POS_VALID
# The physics could sample the hands at the frames' display time (record.Sampler.predict), so it moves
# the stick the headset draws (~45 ms ahead over Link). OFF: the runtime's poses that far ahead are
# steppy (free skate 2026-11-09: per-sample hand speed spiked to 3.4x its 20 ms average at p99, against
# 1.4x sampled at now; 15% of samples repeated the last pose, against 6%), and the spikes went into the
# blade: shots of 75-100 mph where they had been 40-46.
PREDICT = False
AHEAD_MAX_NS = 100e6     # ... trusting the runtime's prediction this far ahead at most
MPH = 2.23694
AWAY_LIMIT_S = 300


# ----------------------------------------------------------------------------- settings


@dataclass(frozen=True)
class Setting:
    key: str
    label: str
    step: float
    lo: float
    hi: float
    fmt: str
    zero: str = ""           # what 0 is called, when 0 turns it off ("off")


SETTINGS = (
    Setting("length_in", "stick length", 0.5, 44, 66, "{:.1f} inches"),
    Setting("lie", "lie", 0.5, 3, 8, "{:g}"),
    Setting("curve_in", "curve depth", 0.125, 0.0, 1.0, "{:.3g} inches"),
    Setting("face_open", "face open", 1, -10, 25, "{:.0f} degrees"),
    Setting("flex", "flex", 5, 30, 120, "{:.0f}"),
    Setting("forgive_cm", "forgiveness", 0.5, 0.0, 4.0, "{:g} centimetres"),
    Setting("puck_g", "puck weight", 10, 100, 400, "{:.0f} grams"),
    Setting("ice_mu", "ice friction", 0.005, 0.0, 0.15, "{:.3f}"),
    Setting("air", "air drag", 0.5, 0.0, 10.0, "{:g} per kilometre", "off"),            # Params.air_k x 1000
    Setting("boards", "board bounce", 0.05, 0.0, 0.9, "{:.2f}"),
    Setting("hands", "shooting hands", 0.05, 0.1, 1.0, "{:.2f}"),   # the stick's damping, right trigger held
    Setting("handle", "stickhandling hands", 0.25, 0.0, 3.0, "{:.2f}", "off"),   # ... and released (HANDLE)
    Setting("grip", "blade grip", 0.05, 0.0, 1.0, "{:.2f}"),
    Setting("buzz", "buzz", 0.1, 0.0, 1.0, "{:.1f}"),
    Setting("magnet", "soft hands", 0.1, 0.0, 1.0, "{:.1f}", "off"),
    Setting("release", "shot release", 0.5, 2.0, 9.0, "{:g} metres per second"),
    Setting("skate", "skate speed", 0.5, 1.0, 9.0, "{:g} metres per second"),
    Setting("sprint", "sprint speed", 0.5, 0.0, 9.0, "{:g} metres per second", "off"),   # the left trigger
    # the skating model (rig.Drive): each off at 0, as it always was
    Setting("push", "push", 1, 0, 10, "{:g} metres per second squared", "off"),
    Setting("glide", "glide", 0.25, 0, 4, "slows {:g} metres per second squared", "off"),
    Setting("stop", "hockey stop", 1, 0, 12, "{:g} metres per second squared", "off"),
    Setting("carve", "turn limit", 1, 0, 12, "{:g} metres per second squared", "off"),
    Setting("back", "backward speed", 0.1, 0.3, 1.0, "{:.0%} of forward"),
    Setting("side", "sideways speed", 0.1, 0.3, 1.0, "{:.0%} of forward"),
    Setting("snap", "snap turn", 15, 0, 90, "{:.0f} degrees"),
    Setting("skates", "skate height", 1, 0, 12, "{:.0f} centimetres", "off"),   # the ice below your floor (SKATES)
    Setting("turn", "smooth turn speed", 15, 45, 360, "{:.0f} degrees per second"),
    Setting("vignette", "comfort vignette", 0.1, 0.0, 1.0, "{:.1f}"),
    Setting("grid", "ice grid", 1, 0, 1, "on", "off"),
    Setting("feet", "your skates", 1, 0, 1, "on", "off"),
    Setting("aa", "anti-aliasing", 4, 0, 4, "{:.0f} times", "off"),
    Setting("check", "comfort check", 1, 0, 15, "every {:g} minutes", "off"),   # a 0-10 queasiness check
    Setting("react", "AI reaction time", 0.06, 0.0, 0.48, "{:.2f} seconds", "off"),   # the 3v3 AI (threes.REACT_S)
    Setting("steady", "steady AI skaters", 1, 0, 1, "on", "off"),   # the 3v3 AI: roles kept, jumps blended, going round people
    Setting("aiskate", "AI skating", 1, 0, 1, "like you", "old"),   # the 3v3 AI on your skating model (threes.PUSH...), or one 5 m/s^2 cap
    Setting("ice", "ice assist", 2, 0, 30, "{:.0f} centimetres"),      # last: one push left from the first
)


def tune_first(tuning: "Tuning", key: str | None) -> None:
    """--tune KEY: the tuning menu opens on that setting (for an A/B: click, change it, click back)."""
    if key:
        keys = [s.key for s in SETTINGS]
        if key not in keys:
            raise SystemExit(f"--tune {key}: one of {', '.join(keys)}")
        tuning.i = keys.index(key)


def set_values(values: dict, items) -> None:
    """--set KEY=VALUE overrides (e.g. push=6 glide=1.5), checked against the settings' keys."""
    for item in items or ():
        key, _, val = item.partition("=")
        key = key.strip()
        if key not in values or not val:
            known = ", ".join(s.key for s in SETTINGS)
            raise SystemExit(f"--set {item}: expected KEY=VALUE with KEY one of: {known}")
        values[key] = float(val)


class Tuning:
    def __init__(self, base: stickspec.StickSpec, values: dict):
        self.base = base
        self.values = values
        self.i = 0

    @classmethod
    def defaults(cls, spec: stickspec.StickSpec, fit: grab.Fit, params: pk.Params) -> dict:
        return {"length_in": spec.length_m / INCH, "lie": spec.lie, "curve_in": spec.curve_depth_m / INCH,
                "face_open": spec.face_open_deg, "flex": spec.flex, "roll": fit.roll_deg, "pitch": fit.pitch_deg,
                "yaw": fit.yaw_deg, "ice_mu": params.ice_mu, "grip": params.blade_grip,
                "air": params.air_k * 1000, "boards": params.board_bounce, "hands": pk.Flex.DAMPING, "handle": HANDLE,
                "buzz": 0.6, "forgive_cm": params.forgiveness * 100, "puck_g": params.puck_mass * 1000,
                "skate": rig.MOVE_MS, "sprint": SPRINT, "turn": rig.TURN_DEG_S, "magnet": params.magnet, "release": params.release,
                "push": PUSH, "glide": GLIDE, "skates": SKATES, "stop": STOP, "carve": CARVE, "back": 1.0, "side": 1.0,
                "snap": SNAP_DEG, "vignette": VIGNETTE, "grid": GRID, "feet": FEET, "aa": AA, "check": COMFORT_CHECK_MIN,
                "react": threes.REACT_S, "steady": float(threes.STEADY), "aiskate": float(threes.SKATE_LIKE_YOU),
                "ice": pk.ICE_ASSIST * 100}

    def spec(self) -> stickspec.StickSpec:
        v = self.values
        return self.base.with_(length_m=v["length_in"] * INCH, lie=v["lie"], curve_depth_m=v["curve_in"] * INCH,
                               face_open_deg=v["face_open"], flex=v["flex"])

    def fit(self) -> grab.Fit:
        return grab.Fit(self.values["roll"], self.values["pitch"], self.values["yaw"])

    def apply(self, params: pk.Params) -> None:
        params.ice_mu = self.values["ice_mu"]
        params.air_k = self.values["air"] / 1000
        params.board_bounce = self.values["boards"]
        params.blade_grip = self.values["grip"]
        params.forgiveness = self.values["forgive_cm"] / 100
        params.puck_mass = self.values["puck_g"] / 1000
        params.magnet = self.values["magnet"]
        params.release = self.values["release"]

    @property
    def current(self) -> Setting:
        return SETTINGS[self.i]

    def describe(self) -> str:
        s = self.current
        v = self.values[s.key]
        return f"{s.label}, {s.zero if s.zero and v == 0 else s.fmt.format(v)}"

    def drive(self, d: rig.Drive) -> None:
        """The skating settings onto the thumbstick drive."""
        v = self.values
        d.move_ms, d.turn_deg_s = v["skate"], v["turn"]
        d.push, d.glide, d.stop_ms2, d.carve = v["push"], v["glide"], v["stop"], v["carve"]
        d.back, d.side = v["back"], v["side"]
        d.sprint_ms = v.get("sprint", 0.0)

    def pick(self, d: int) -> None:
        self.i = (self.i + d) % len(SETTINGS)

    def change(self, d: int) -> bool:
        s = self.current
        old = self.values[s.key]
        new = float(np.clip(round((old + d * s.step) / s.step) * s.step, s.lo, s.hi))
        self.values[s.key] = new
        return new != old


# ----------------------------------------------------------------------------- shared state


class Play:
    """State shared by the render thread (inputs, drawing) and the sampler thread (physics)."""

    def __init__(self, tuning: Tuning):
        self.tuning = tuning
        self.spec = tuning.spec()
        self.fit = tuning.fit()
        self.params = pk.Params()
        tuning.apply(self.params)
        self.sim = pk.Sim(self.params, pk.Rink(), self.spec.flex)
        self.version = 0                       # bumped on every settings change
        # what record.Sampler expects
        self.phase = "play"
        self.squeeze = {d: 0.0 for d in recfmt.CONTROLLERS}
        self.shoot = 0.0                       # the right trigger, 0-1: firm hands for a shot (Physics._firmness)
        self.latest_flags = {d: 0 for d in recfmt.CONTROLLERS}
        self.t_now = 0.0
        # requests to the physics thread
        self.want_puck = False
        self.want_recenter = False
        self.head = None                       # (R, p) of the headset, from the render thread
        self.feet = MyFeet()                   # where your own skates go (the "your skates" setting)
        self.my_skates = None                  # their (left, right) 4x4 model -> world this frame, or None
        self.haptics: queue.SimpleQueue = queue.SimpleQueue()
        self.stick_state = grab.NONE
        self.last_focus = time.time()
        self.fitting = False                   # Y: the stick held in the right hand while you fit it
        self.sounds: queue.SimpleQueue = queue.SimpleQueue()   # sounds by name (go, whistle, a hit)
        self.bus = Bus()                       # every contact, from the physics: the sound and buzz play from it
        self.rig = rig.Rig(tuning.values.get("skates", 0.0) / 100)   # where the room sits in the world: the
                                               # thumbsticks move it; your skate height lifts it over the ice
        self.want_teleport = None              # (world point, world direction): put your head there, facing that way
        self.ahead_ns = 0.0                    # how far ahead of now the frames are displayed (the physics samples there)

    def retune(self) -> None:
        self.spec = self.tuning.spec()
        self.fit = self.tuning.fit()
        self.tuning.apply(self.params)
        self.version += 1


class VoiceQueue(threading.Thread):
    """Speaks without blocking anyone. A message with a key replaces an unspoken one with that key."""

    def __init__(self, voice: record.Voice):
        super().__init__(daemon=True, name="voice")
        self.voice = voice
        self.pending: collections.OrderedDict = collections.OrderedDict()
        self.lock = threading.Lock()
        self.wake = threading.Event()
        self.n = 0

    def say(self, text: str, key: str | None = None) -> None:
        with self.lock:
            if key is None:
                self.n += 1
                key = f"_{self.n}"
            self.pending.pop(key, None)
            self.pending[key] = text
        self.wake.set()

    def run(self) -> None:
        while True:
            self.wake.wait()
            with self.lock:
                if not self.pending:
                    self.wake.clear()
                    continue
                _, text = self.pending.popitem(last=False)
            self.voice.say(text)


def _plain(x):
    """json for numpy values."""
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.generic):
        return x.item()
    raise TypeError(type(x).__name__)


class Log:
    """events.jsonl and puck.csv, written from any thread; and any other table a mode keeps
    (row(): the 3v3 writes ai.csv)."""

    def __init__(self, run_dir: Path):
        self.dir = run_dir
        self.events = open(run_dir / "events.jsonl", "a", encoding="utf-8")
        self.puck = open(run_dir / "puck.csv", "w", encoding="utf-8")
        self.puck.write("t,px,py,pz,vx,vy,vz,impulse,stick,bend_mm,hands\n")   # hands: the damping in use
        self.tables: dict = {}
        self.lock = threading.Lock()

    def event(self, t: float, kind: str, **data) -> None:
        with self.lock:
            self.events.write(json.dumps({"t": round(t, 4), "event": kind, **data}, default=_plain) + "\n")
            self.events.flush()

    def puck_row(self, row: str) -> None:
        with self.lock:
            self.puck.write(row)

    def row(self, name: str, header: str, row: str) -> None:
        """A row of <name>.csv, opened (with its header) on the first row."""
        with self.lock:
            f = self.tables.get(name)
            if f is None:
                f = self.tables[name] = open(self.dir / f"{name}.csv", "w", encoding="utf-8")
                f.write(header)
            f.write(row)

    def close(self) -> None:
        with self.lock:
            self.events.close()
            self.puck.close()
            for f in self.tables.values():
                f.close()


# ----------------------------------------------------------------------------- physics (sampler thread)


HOLDERS = {grab.BOTH: ("top", "bottom"), grab.TOP: ("top",), grab.LOOSE_TOP: ("top",),
           grab.BOTTOM: ("bottom",), grab.LOOSE_BOTTOM: ("bottom",)}


class Physics:
    def __init__(self, play: Play, voice: VoiceQueue, log: Log):
        self.play, self.voice, self.log = play, voice, log
        self.grab = grab.Grab(play.spec, play.fit)
        self.version = -1
        self.last_t = None
        self.shot = None              # shotcall.ShotCall for this puck (None: a new puck)
        self.respawn_at = None
        self.slow_since = None
        self.last_buzz = 0.0
        self.tick = 0
        self.shots = []
        self._last_sweet = None
        self._last_yaw = 0.0
        self._ring = collections.deque()      # recent (t, rigid blade points): Physics._velocity
        self._t = 0.0
        self._stalled = False
        self._refresh()

    def _refresh(self) -> None:
        pl = self.play
        spec = pl.spec
        self.grab.configure(spec, pl.fit)
        pl.sim.flex.set_flex(spec.flex)
        self._firmness()
        self.edge_b, self.edge_t = spec.edge(8), spec.edge(8, top=True)
        self.sweet, self.u, self.zf = spec.sweet, spec.u, spec.z_forehand
        self.version = pl.version

    def _firmness(self) -> None:
        """The stick's damping this tick: the stickhandling hands, firmed up toward the shooting hands
        as you squeeze the right trigger (resting fingers don't count; full by 0.95)."""
        v = self.play.tuning.values
        firm = v.get("hands", pk.Flex.DAMPING)
        soft = v.get("handle", 0.0)
        if soft > 0:
            s = min(max((self.play.shoot - rig.TRIGGER_DEAD) / (1 - 2 * rig.TRIGGER_DEAD), 0.0), 1.0)
            firm = firm * s + soft * (1 - s)          # (exactly each end at 0 and 1)
        fl = self.play.sim.flex
        if fl.damping != firm:
            fl.damping = firm
            fl.set_flex(fl.flex)                     # recomputes the damping coefficient

    def _blade_spot(self, R, p) -> np.ndarray:
        """A spot on the ice just off the forehand face."""
        n = R @ self.zf
        n_h = np.array([n[0], 0.0, n[2]])
        n_h /= max(np.linalg.norm(n_h), 1e-6)
        s = R @ self.sweet + p
        return np.array([s[0], 0.0, s[2]]) + 0.10 * n_h

    def _front_spot(self) -> np.ndarray | None:
        if self.play.head is None:
            return None
        Rh, ph = self.play.head
        f = -Rh[:, 2]
        f = np.array([f[0], 0.0, f[2]]) / max(np.hypot(f[0], f[2]), 1e-6)
        return np.array([ph[0], 0.0, ph[2]]) + 0.8 * f

    def __call__(self, t: float, tick: dict) -> None:
        try:
            self._tick(t, tick)
        except Exception as e:                       # never let a physics bug stop the recording
            self.errors = getattr(self, "errors", 0) + 1
            if self.errors <= 3:
                import traceback
                traceback.print_exc()
                self.log.event(t, "physics_error", error=repr(e))

    def _tick(self, t: float, tick: dict) -> None:
        pl = self.play
        if pl.version != self.version:
            self._refresh()
        self._firmness()
        gap = 0.001 if self.last_t is None else float(t - self.last_t)
        dt_s = min(max(gap, 0.0002), MAX_DT)
        self._stalled = gap > STALL_S
        self._t = t
        self.last_t = t
        spec = pl.spec
        top, bot = tick.get(spec.top_hand), tick.get(spec.bottom_hand)
        state, R, p = self.grab.step(top, bot, pl.squeeze[spec.top_hand], pl.squeeze[spec.bottom_hand], t,
                                     force_top=pl.fitting)
        pl.stick_state = state
        held = R is not None and state in grab.HELD
        self._world(t, R, p, held)
        imp = self._step(dt_s, R, p, held)
        self._feel(imp, state)
        self._game(t, imp)
        self.tick += 1
        if self.tick % 5 == 0:
            self._log_row(t, imp, state)

    # the steps of a tick: a drill overrides _world and _game
    def _world(self, t: float, R, p, held: bool) -> None:
        """Lay out the rink and drop pucks."""
        pl, sim = self.play, self.play.sim
        if pl.want_recenter and pl.head is not None:
            pl.want_recenter = False
            Rh, ph = pl.head
            f = -Rh[:, 2]
            sim.puck.rink = pk.Rink(origin=np.array([ph[0], 0.0, ph[2]]),
                                    fwd=np.array([f[0], 0.0, f[2]]) / max(np.hypot(f[0], f[2]), 1e-6))
            self.log.event(t, "rink", **sim.puck.rink.to_dict())
            pl.want_puck = True
        if pl.want_puck or (self.respawn_at is not None and t >= self.respawn_at):
            spot = self._blade_spot(R, p) if held else self._front_spot()
            if spot is not None:
                sim.puck.spawn(spot[[0, 2]])
                pl.want_puck, self.respawn_at, self.slow_since, self.shot = False, None, None, None
                self.log.event(t, "puck", at=spot.round(3).tolist())

    def _step(self, dt_s: float, R, p, held: bool) -> float:
        """Move the puck (and the stick's flex) one controller sample on."""
        sim = self.play.sim
        yaw = getattr(self.play, "rig_yaw", 0.0)
        if held:
            a = R @ self.sweet + p
            last = self._last_sweet
            if last is not None and float(np.linalg.norm(a - last)) > JUMP_M:
                sim._last = None                        # a snap turn or a teleport: don't sweep the blade
                self._carry(a, last, yaw - self._last_yaw)
                self._ring.clear()
            elif last is not None and (getattr(self, "_stalled", False)
                                       or float(np.linalg.norm(a - last)) > JUMP_MS * dt_s):
                sim._last = None                        # a stall or a tracking jump: no sweep, no velocity
                self._ring.clear()
            self._last_sweet = a
        else:
            self._last_sweet = None
            self._ring.clear()
        self._last_yaw = yaw
        if held and not self._tracked():                # a hand holding it only guessed: no hits this tick
            held = False
            self._last_sweet = None
            self._ring.clear()
        substeps = max(4, int(math.ceil(dt_s / SUBSTEP_S - 1e-9)))
        if held:
            bot_e = self.edge_b @ R.T + p
            top_e = self.edge_t @ R.T + p
            anchor = R @ self.sweet + p
            # the ice assist: a blade hovering just over the ice rests on it (you can't feel the ice)
            drop = pk.ice_assist(float(bot_e[:, 1].min()), self.play.tuning.values.get("ice", 0.0) / 100)
            if drop:
                bot_e[:, 1] -= drop
                top_e[:, 1] -= drop
                anchor[1] -= drop
            imp = sim.step(dt_s, bot_e, top_e, anchor, R @ self.u, substeps=substeps,
                           body=getattr(self.play, "body", None), rvel=self._velocity(bot_e, top_e, anchor))
        else:
            imp = sim.step(dt_s, None, None, substeps=substeps)
        self.last_impulse = imp
        return imp

    def _tracked(self) -> bool:
        """Whether the hands holding the stick are tracked (not only valid: guessed from the motion
        sensors). Unknown flags (0, e.g. a replay without them) count as tracked."""
        spec, flags = self.play.spec, self.play.latest_flags
        for who in HOLDERS.get(self.play.stick_state, ()):
            f = flags.get(spec.top_hand if who == "top" else spec.bottom_hand, 0)
            if f & VALID == VALID and f & TRACKED != TRACKED:
                return False
        return True

    def _velocity(self, bot_e, top_e, anchor):
        """The rigid blade's velocities (bottom edge, top edge, anchor rows) fitted over the last
        VEL_WINDOW_S of samples, or None (one sample's difference) without two samples in it."""
        if VEL_WINDOW_S <= 0:
            return None
        t = self._t
        ring = self._ring
        ring.append((t, np.vstack([bot_e, top_e, anchor[None]])))
        while ring and t - ring[0][0] > VEL_WINDOW_S + 1e-9:
            ring.popleft()
        if len(ring) < 2:
            return None
        ts = np.array([e[0] for e in ring])
        X = np.array([e[1] for e in ring])
        tm = ts - ts.mean()
        den = float(tm @ tm)
        if den <= 0:
            return None
        return np.tensordot(tm, X - X.mean(axis=0), axes=1) / den

    def _carry(self, a, last, dyaw: float) -> None:
        """A puck on the blade when you snap-turn (or are moved) goes with it."""
        pz = self.play.sim.puck
        if pz.in_net or float(np.linalg.norm((pz.pos - last)[[0, 2]])) > 0.4:
            return
        c, s = np.cos(dyaw), np.sin(dyaw)
        Ry = np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])
        d = Ry @ (pz.pos - last)
        pz.pos = np.array([a[0] + d[0], pz.pos[1], a[2] + d[2]])
        pz.vel = Ry @ pz.vel

    def _hands(self, state: int) -> list[str]:
        spec = self.play.spec
        return [spec.top_hand if h == "top" else spec.bottom_hand for h in HOLDERS.get(state, ())]

    def _feel(self, imp: float, state: int) -> None:
        """Every contact onto the contact bus (the sound plays from there), and the buzz."""
        pl, sim = self.play, self.play.sim
        hands_now = self._hands(state)
        buzz_level = pl.tuning.values["buzz"]
        now = time.perf_counter()
        for kind, speed in sim.events:                   # the blade landing on the ice
            if kind == "ice":
                pl.bus.publish(Contact(now, "ice", speed, hands=tuple(hands_now)))
                if speed > 0.15 and hands_now and buzz_level > 0:
                    pl.haptics.put((0.12 * buzz_level + 0.05, hands_now, 10))
        sim.events.clear()
        if imp > 0.15:
            c = getattr(sim, "contact", None)            # the compiled physics says where and how
            pl.bus.publish(Contact(now, "puck", imp, float(c[2]) if c is not None else 0.0,
                                   float(c[3]) if c is not None else 0.5, tuple(hands_now)))
        scr = getattr(sim, "scrape", None)
        if scr is not None:
            pl.bus.scrape = (float(scr[0]), float(scr[1]))
        # feel: every contact buzzes the hands holding the stick
        if imp > 0.15 and (self.last_t - self.last_buzz > 0.02 or imp > 3.0):
            self.last_buzz = self.last_t
            amp = float(np.clip(imp / 6.0, 0.08, 1.0)) * buzz_level
            ms = 12 + 25 * float(np.clip(imp / 6.0, 0, 1))      # a harder hit lasts longer (a heavy puck)
            if amp > 0 and hands_now:
                pl.haptics.put((amp, hands_now, ms))

    def _game(self, t: float, imp: float) -> None:
        """Free play: call shot speeds, goals, posts, the boards; bring back a puck that's gone."""
        pl, pz = self.play, self.play.sim.puck
        spec = pl.spec
        self._call_shot(t, imp)
        now = time.perf_counter()
        for kind, speed in pz.events:
            self.log.event(t, kind, ms=round(speed, 2))
            pl.bus.publish(Contact(now, kind, speed))          # posts, boards, goals: the sound plays from the bus
            if kind == "goal":
                self.voice.say(f"Goal! {pz.goals}", key="goal")
                pl.haptics.put((1.0, [spec.top_hand, spec.bottom_hand], 80))
                self.respawn_at = t + 2.0
            elif kind == "post" and speed > 2:
                self.voice.say("Post!", key="post")
        pz.events.clear()
        # a puck that's out of reach and stopped comes back
        u, _, w = pz.rink.to_rink(pz.pos)
        far = np.hypot(u, w) > 3.5 and not pz.in_net
        if far and pz.speed < 0.3:
            self.slow_since = self.slow_since or t
            if t - self.slow_since > 2.0 and self.respawn_at is None:
                self.respawn_at = t
        else:
            self.slow_since = None

    def _call_shot(self, t: float, imp: float) -> None:
        """Shots: called from the puck's free flight (shotcall.py), the same way in every replay."""
        if self.shot is None:                       # a new puck (set to None where one is dropped)
            self.shot = shotcall.ShotCall()
        call = self.shot.tick(t, imp, self.play.sim.puck.vel)
        if call is not None:
            self.voice.say(f"{call['mph']:.0f}", key="shot")
            self.shots.append(call["mph"])
            self.log.event(t, "shot", **call)

    def _log_row(self, t: float, imp: float, state: int) -> None:
        sim = self.play.sim
        P, V = sim.puck.pos, sim.puck.vel
        b = np.linalg.norm(sim.bend) * 1000
        self.log.puck_row(f"{t:.4f},{P[0]:.4f},{P[1]:.4f},{P[2]:.4f},{V[0]:.3f},{V[1]:.3f},{V[2]:.3f},"
                          f"{imp:.3f},{state},{b:.1f},{sim.flex.damping:.2f}\n")


# ----------------------------------------------------------------------------- drawing


WHITE, RED, BLUE = (0.92, 0.92, 0.92), theme.RED, theme.BLUE


class Frame(NamedTuple):
    """What a mode draws: solid triangles (drawn first) and line segments, each row x, y, z, r, g, b,
    and models placed in the world (gear.Model, instance matrices): Lines.mesh_list()."""
    tris: np.ndarray
    lines: np.ndarray
    meshes: tuple = ()


NO_TRIS = np.zeros((0, 6), dtype=np.float32)


class Lines:
    """Line segments for the renderer: line(a, b, colour) one at a time, or many(A, B, colour)
    for whole arrays of them (much cheaper in Python); then .array(). And solid triangles:
    solid(P, colour), then .tri_array()."""

    def __init__(self):
        self.v: list = []
        self.blocks: list[np.ndarray] = []
        self.tris: list[np.ndarray] = []
        self.placed: dict = {}                 # id(model) -> (model, [4x4 model -> world])

    def place(self, model, M) -> None:
        """A model (gear.Model) drawn where the 4x4 M (model -> world) puts it."""
        self.placed.setdefault(id(model), (model, []))[1].append(M)

    def mesh_list(self) -> tuple:
        """(model, instances (n, 4, 4) float32, column-major as GL reads them) for Frame.meshes."""
        return tuple((m, np.ascontiguousarray(np.asarray(Ms, dtype=np.float32).transpose(0, 2, 1)))
                     for m, Ms in self.placed.values())

    def solid(self, P, c) -> None:
        """Triangles: corners P (3n, 3), one colour (3,) or one per corner (3n, 3)."""
        P = np.asarray(P, dtype=np.float32).reshape(-1, 3)
        out = np.empty((len(P), 6), dtype=np.float32)
        out[:, :3], out[:, 3:] = P, c
        self.tris.append(out)

    def tri_array(self) -> np.ndarray:
        return np.vstack(self.tris) if self.tris else NO_TRIS

    def __call__(self, a, b, c) -> None:
        self.v.append((*a, *c))
        self.v.append((*b, *c))

    def many(self, A, B, c) -> None:
        """Segments A[i]-B[i] (each (n, 3)), all one colour."""
        A, B = np.asarray(A, dtype=np.float32), np.asarray(B, dtype=np.float32)
        out = np.empty((2 * len(A), 6), dtype=np.float32)
        out[0::2, :3], out[1::2, :3] = A, B
        out[:, 3:] = c
        self.blocks.append(out)

    def array(self) -> np.ndarray:
        parts = self.blocks + [np.asarray(self.v, dtype=np.float32).reshape(-1, 6)]
        return np.vstack(parts) if len(parts) > 1 else parts[0]


def scene(play: Play, rink: pk.Rink, poses: dict, held: dict, stick, state: int) -> Frame:
    line = Lines()
    draw_rink(line, rink, grid=play.tuning.values.get("grid", 0) > 0)
    draw_puck(line, play.sim.puck)
    draw_hands_and_stick(line, play, poses, held, stick, state)
    return Frame(line.tri_array(), line.array(), line.mesh_list())


def draw_rink(line, rink: pk.Rink, grid: bool = False) -> None:
    def W(u, y, w):
        return rink.to_world(u, y, w)

    end_w = rink.goal_dist + pk.GOAL_DEPTH + rink.end
    hw_ice = rink.half_width
    corners = [(-hw_ice, -rink.back), (hw_ice, -rink.back), (hw_ice, end_w), (-hw_ice, end_w)]
    g, hw, gh, d = rink.goal_dist, pk.GOAL_HALF_W, pk.GOAL_H, pk.GOAL_DEPTH
    s = theme.Surf(line.solid, rink.origin, rink.right, rink.fwd)    # the ice, the boards, the paint
    theme.ice(s, corners)
    theme.boards(s, corners, 1.0)
    theme.board_lines(line, W, corners + corners[:1], 1.0)
    s.band((-hw_ice, g), (hw_ice, g), theme.THIN, theme.PAINT_Y, RED)
    s.disc((0.0, g), 1.83, theme.PAINT_Y, theme.CREASE, np.pi, 2 * np.pi)
    if grid:
        for u in np.arange(-hw_ice, hw_ice + 0.01, 0.5):
            line(W(u, 0.001, -rink.back), W(u, 0.001, end_w), theme.GRID)
        for w in np.arange(-rink.back, end_w + 0.01, 0.5):
            line(W(-hw_ice, 0.001, w), W(hw_ice, 0.001, w), theme.GRID)
    # the goal: line, crease, posts, crossbar, net
    line(W(-hw_ice, 0.002, g), W(hw_ice, 0.002, g), RED)
    a = np.linspace(0, np.pi, 17)
    crease = [W(1.83 * np.cos(x), 0.002, g - 1.83 * np.sin(x)) for x in a]
    for p0, p1 in zip(crease, crease[1:]):
        line(p0, p1, RED)
    for su in (-hw, hw):
        line(W(su, 0, g), W(su, gh, g), RED)
    line(W(-hw, gh, g), W(hw, gh, g), RED)
    mesh = theme.MESH
    for su in (-hw, hw):
        line(W(su, 0, g + d), W(su, gh * 0.6, g + d), mesh)
        line(W(su, gh, g), W(su, gh * 0.6, g + d), mesh)
        line(W(su, 0, g), W(su, 0, g + d), mesh)
    line(W(-hw, 0, g + d), W(hw, 0, g + d), mesh)
    line(W(-hw, gh * 0.6, g + d), W(hw, gh * 0.6, g + d), mesh)
    for u in np.linspace(-hw, hw, 9)[1:-1]:
        line(W(u, 0, g + d), W(u, gh * 0.6, g + d), mesh)
        line(W(u, gh, g), W(u, gh * 0.6, g + d), mesh)


def draw_puck(line, puck) -> None:
    """A black puck (solid, a touch inside its rims) with grey rims."""
    P = puck.pos
    solid = getattr(line, "solid", None)
    if solid is not None:
        solid(theme.puck(P, pk.R * 0.97, pk.H * 0.94), theme.PUCK)
    ang = np.linspace(0, 2 * np.pi, 17)
    ring = np.stack([np.cos(ang), np.zeros_like(ang), np.sin(ang)], axis=1) * pk.R
    for y in (P[1] - pk.H / 2, P[1] + pk.H / 2):
        pts = ring + np.array([P[0], y, P[2]])
        for p0, p1 in zip(pts, pts[1:]):
            line(p0, p1, theme.PUCK_EDGE)
    for k in range(0, 16, 4):
        line(ring[k] + P - [0, pk.H / 2, 0], ring[k] + P + [0, pk.H / 2, 0], theme.PUCK_EDGE)


def save_settings(play: Play, voice, log, t_sim: float) -> None:
    """A in the settings menu: every setting and the stick's fit, used next time (and by the game)."""
    tu = play.tuning
    SETTINGS_PATH.write_text(json.dumps({"values": tu.values, "spec": play.spec.to_dict()}, indent=2))
    play.fit.save(record.FIT_PATH, play.spec)
    voice.say("Saved.", key="saved")
    log.event(t_sim, "saved", values=dict(tu.values))


class MyFeet:
    """Where your own skates go, from your head alone (nothing tracks your feet): under your neck,
    about hip width apart, toes turned out a little. Your feet stay put while your head leans and
    turns; they step after it once it's 25 cm away, and turn with it once it's turned 35 degrees
    from them (and slowly settle toward where it looks). Kept in the room, so they turn and slide
    with the thumbsticks exactly, then put on the ice."""

    NECK = 0.09          # m: the neck behind your eyes
    STANCE = 0.16        # m: each skate out from your middle
    TOE_OUT = 0.12       # rad: each toe turned out
    STEP_FROM, STEP_TO, STEP_MS = 0.25, 0.08, 1.5      # m, m, m/s
    TURN_FREE, SETTLE_S = np.radians(35), 2.0

    def __init__(self):
        self.c = None                          # room (x, z) between your feet
        self.yaw = 0.0                         # room heading: forward is (sin yaw, 0, cos yaw)
        self.stepping = False

    def update(self, R: np.ndarray, p: np.ndarray, rp, dt: float) -> tuple[np.ndarray, np.ndarray]:
        """Head pose in the room -> the (left, right) skates' 4x4 model -> world."""
        f = -R[:, 2]                           # where you look (OpenXR: -z forward)
        h = np.array([f[0], f[2]])
        n = float(np.linalg.norm(h))
        neck = np.array([p[0], p[2]])
        if n > 0.2:                            # not looking straight down or up
            head_yaw = np.arctan2(h[0], h[1])
            neck = neck - self.NECK * h / n
            d = (head_yaw - self.yaw + np.pi) % (2 * np.pi) - np.pi
            if self.c is None:
                self.yaw, d = head_yaw, 0.0
            if abs(d) > self.TURN_FREE:        # turned too far from your feet: they come round
                self.yaw += d - np.sign(d) * self.TURN_FREE
                d = np.sign(d) * self.TURN_FREE
            self.yaw += d * (1 - np.exp(-dt / self.SETTLE_S))
        if self.c is None:
            self.c = neck.copy()
        gap = neck - self.c
        dist = float(np.linalg.norm(gap))
        if dist > self.STEP_FROM:
            self.stepping = True
        if self.stepping:
            self.c = self.c + gap * min(1.0, self.STEP_MS * dt / max(dist, 1e-9))
            self.stepping = dist > self.STEP_TO
        sy, cy = np.sin(self.yaw), np.cos(self.yaw)
        fwd, left = np.array([sy, 0.0, cy]), np.array([cy, 0.0, -sy])
        out = []
        for k in (1.0, -1.0):                  # left foot, right foot
            a = k * self.TOE_OUT
            ff, ll = np.cos(a) * fwd + np.sin(a) * left, np.cos(a) * left - np.sin(a) * fwd
            Rw, ow = rp.pose(np.stack([ff, ll, [0.0, 1.0, 0.0]], axis=1),
                             np.array([self.c[0], 0.0, self.c[1]]) + k * self.STANCE * left)
            ow = ow.copy()
            ow[1] = 0.0                        # on the ice, whatever the skate height
            out.append(gear.place(Rw, ow))
        return out[0], out[1]


def draw_hands_and_stick(line, play: Play, poses: dict, held: dict, stick, state: int) -> None:
    my = play.my_skates
    skates = gear.skates() if my is not None else None
    if skates is not None:                     # your own skates (the "your skates" setting)
        for model, M in zip(skates, my):
            line.place(model, M)
    # hands
    for dev, (R, p) in poses.items():
        for axis, col in ((0, (1, 0.2, 0.2)), (1, (0.2, 1, 0.2)), (2, (0.3, 0.5, 1))):
            line(p, p + R[:, axis] * 0.05, col)
        if held.get(dev):
            for axis in range(3):
                e = np.eye(3)[axis] * 0.03
                line(p - e, p + e, (0.2, 1.0, 0.3))
    # the stick, bent by the flex
    R, p = stick
    if R is not None:
        spec = play.spec
        loose = state in (grab.LOOSE_TOP, grab.LOOSE_BOTTOM)
        shaft_c = theme.SHAFT_LOOSE if loose else theme.SHAFT
        blade_c = theme.BLADE_LOOSE if loose else theme.BLADE
        bend = play.sim.bend
        # the ice assist, as the physics does it: the stick tilts down onto the ice (the shaft stays
        # straight: the drop grows along it from the top hand)
        down = np.array([0.0, -pk.ice_assist(float((spec.edge(9) @ R.T + p)[:, 1].min()),
                                             play.tuning.values.get("ice", 0.0) / 100), 0.0])
        # the headset draws where the hands will be (~45 ms ahead of the physics, unless PREDICT): rest
        # this stick on the ice itself so it is never drawn through it (more bend, then a slide)
        bend, slide = pk.ice_rest(bend, float((spec.edge(9) @ R.T + p + bend + down)[:, 1].min()), R @ spec.u,
                                  pk.ICE_BEND)
        slide = slide + down
        grip_s = spec.length_m - spec.grip_from_top_m
        s = np.linspace(spec.length_m, 0, 12)
        xi = np.clip((grip_s - s) / grip_s, 0, 1)
        pts = (s[:, None] * spec.u) @ R.T + p + (xi ** 2)[:, None] * bend + slide - (1 - xi)[:, None] * down
        for p0, p1 in zip(pts, pts[1:]):
            line(p0, p1, shaft_c)
        for frac in (0.0, 0.33, 0.66, 1.0):
            e = spec.edge(9, frac=frac) @ R.T + p + bend + slide
            for p0, p1 in zip(e, e[1:]):
                line(p0, p1, blade_c)
        bot = spec.edge(5) @ R.T + p + bend + slide
        top = spec.edge(5, top=True) @ R.T + p + bend + slide
        for b0, t0 in zip(bot, top):
            line(b0, t0, blade_c)


# ----------------------------------------------------------------------------- main


class Stick:
    """Thumbstick flicks: one step per flick, repeating while held."""

    def __init__(self):
        self.dir = 0
        self.next_t = 0.0

    def update(self, value: float, now: float) -> int:
        d = 1 if value > 0.6 else -1 if value < -0.6 else 0
        if d == 0 or abs(value) < 0.3:
            self.dir = 0
            return 0
        if d != self.dir:
            self.dir, self.next_t = d, now + 0.45
            return d
        if now >= self.next_t:
            self.next_t = now + 0.09
            return d
        return 0


class Comfort:
    """How the thumbsticks move you, and how you feel about it.

    - rig.csv: every frame, the sticks, the drive's velocity, turn rate and mode, the vignette, and
      the sprint trigger.
    - A queasiness check every `check` minutes of play (the "comfort check" setting; 0 = off): the
      voice asks, and you press A (fine), B (a bit queasy) or Y (I need a break). Logged as 0, 2
      and 5 on the usual 0-10 scale, where 4 is about where nausea becomes notable (Farmani &
      Teather 2020): Y says to take the headset off. Not X: X is a new puck, pressed all the time
      (a puck grabbed while it was asking counted as a break). (A 0-10 count on the left stick was too fiddly
      in the headset: Jon couldn't tell how to answer.) Tune skating one change at a time against
      these answers.
    - summary(): for meta.json (time moving, hard accelerations, turn rates, the ratings)."""

    TIMEOUT = 30.0
    ANSWERS = {"a": ("fine", 0), "b": ("a bit queasy", 2), "y": ("need a break", 5)}
    HARD = (2.0, 6.0)                 # m/s^2: accelerations counted (events above 2, time above 6)

    def __init__(self, path: Path | None, voice, log):
        self.voice, self.log = voice, log
        self.fh = open(path, "w", newline="") if path is not None else None
        if self.fh is not None:
            self.fh.write("t,lx,ly,rx,moving,mode,vx,vz,speed,omega,accel,vignette,trigger\n")
        self.asking_since: float | None = None
        self.play_s = 0.0
        self.next_check: float | None = None
        self.ratings: list[dict] = []
        self.prev_v: np.ndarray | None = None
        self.stats = {"frames": 0, "moving_s": 0.0, "accel_events": 0, "over6_s": 0.0, "peak_accel": 0.0,
                      "peak_turn_deg_s": 0.0, "vignette_s": 0.0, "sprint_s": 0.0, "peak_speed": 0.0}
        self._over2 = False

    @property
    def asking(self) -> bool:
        return self.asking_since is not None

    def frame(self, now: float, t_sim: float, dt: float, sticks, moving: bool, drive, vel, omega: float,
              vignette: float, every_min: float) -> None:
        """Once a frame, after the drive: the log row and the stats; and whether to ask."""
        a = 0.0 if self.prev_v is None or dt <= 0 else float(np.linalg.norm(vel - self.prev_v)) / dt
        self.prev_v = np.array(vel, dtype=float)
        speed = float(np.linalg.norm(vel))
        s = self.stats
        s["frames"] += 1
        s["moving_s"] += dt if speed > 0.1 or omega else 0.0
        if a > self.HARD[0] and not self._over2:
            s["accel_events"] += 1
        self._over2 = a > self.HARD[0]
        s["over6_s"] += dt if a > self.HARD[1] else 0.0
        s["peak_accel"] = max(s["peak_accel"], a)
        s["peak_turn_deg_s"] = max(s["peak_turn_deg_s"], abs(math.degrees(omega)))
        s["vignette_s"] += dt if vignette > 0.1 else 0.0
        lx, ly, rx, *rest = sticks
        lt = rest[0] if rest else 0.0
        s["sprint_s"] += dt if speed > drive.move_ms + 0.05 else 0.0
        s["peak_speed"] = max(s["peak_speed"], speed)
        if self.fh is not None:
            self.fh.write(f"{t_sim:.3f},{lx:.3f},{ly:.3f},{rx:.3f},{int(moving)},{drive.mode},{vel[0]:.3f},"
                          f"{vel[2]:.3f},{speed:.3f},{omega:.4f},{a:.2f},{vignette:.2f},{lt:.2f}\n")
        self.play_s += dt
        if every_min <= 0:
            self.next_check = None
            return
        if self.next_check is None:
            self.next_check = self.play_s + every_min * 60
        if not self.asking and self.play_s >= self.next_check:
            self.asking_since = now
            self.voice.say("Comfort check. Press A if you feel fine, B if you're a bit queasy, Y if you need a break.",
                           key="comfort")
        if self.asking and now - self.asking_since > self.TIMEOUT:
            self.asking_since = None
            self.next_check = self.play_s + every_min * 60
            self.log.event(t_sim, "comfort", answer=None, rating=None)

    def answer(self, button: str, t_sim: float, every_min: float) -> bool:
        """A, B or Y while asking: the answer (True: the button was the answer, not its usual job)."""
        if not self.asking or button not in self.ANSWERS:
            return False
        word, r = self.ANSWERS[button]
        self.asking_since = None
        self.next_check = self.play_s + every_min * 60 if every_min > 0 else None
        self.ratings.append({"t": round(t_sim, 1), "play_min": round(self.play_s / 60, 1), "answer": word,
                             "rating": r})
        self.log.event(t_sim, "comfort", answer=word, rating=r)
        print(f"  comfort: {word} ({r}/10) after {self.play_s / 60:.1f} min", flush=True)
        self.voice.say("Take a break: take the headset off." if button == "y" else
                       "Thanks. Tell Claude what feels off." if button == "b" else "Thanks.", key="comfort")
        return True

    def summary(self) -> dict:
        s = dict(self.stats)
        mins = max(self.play_s / 60, 1e-9)
        return {"play_min": round(self.play_s / 60, 2), "moving_min": round(s["moving_s"] / 60, 2),
                "accel_events_per_min": round(s["accel_events"] / mins, 1), "over6_s": round(s["over6_s"], 2),
                "peak_accel": round(s["peak_accel"], 1), "peak_turn_deg_s": round(s["peak_turn_deg_s"]),
                "vignette_min": round(s["vignette_s"] / 60, 2), "sprint_min": round(s["sprint_s"] / 60, 2),
                "peak_speed": round(s["peak_speed"], 2), "ratings": self.ratings}

    def close(self) -> None:
        if self.fh is not None:
            self.fh.close()
            self.fh = None


class SandboxMode:
    """Free play: what X, A, B and the left-stick click do, what is drawn, what is said first.
    A drill (drill.py) is another mode with the same methods."""

    kind = "sandbox"
    app_name = "vr-hockey-sandbox"

    def __init__(self, play: Play, voice: VoiceQueue, log: Log):
        self.play, self.voice, self.log = play, voice, log
        self.physics: Physics | None = None

    def make_physics(self) -> Physics:
        self.physics = Physics(self.play, self.voice, self.log)
        return self.physics

    def intro(self) -> str:
        return ("Sandbox. Squeeze the grips to hold the stick. Left stick moves you, right stick turns you. "
                "X gives you a new puck. The menu button on your left controller opens the settings.")

    def first_head(self) -> None:
        self.play.want_recenter = True

    def recenter(self) -> None:
        self.play.want_recenter = True
        self.voice.say("Net in front of you.", key="rink")

    def button(self, name: str, t_sim: float) -> None:
        """X pressed, or A or B outside the settings menu: X a new puck; A and B nothing here."""
        if name == "x":
            self.play.want_puck = True

    def frame(self, now: float) -> None:
        """Once a frame, in the render thread."""

    def confine(self, head_world, vel: np.ndarray, dt: float) -> np.ndarray:
        """The thumbsticks' velocity, allowed where you are (the sandbox: anywhere)."""
        return vel

    def draw(self, poses: dict, held: dict, stick, state: int) -> Frame:
        return scene(self.play, self.play.sim.puck.rink, poses, held, stick, state)

    def status(self) -> str:
        pz = self.play.sim.puck
        return f"puck {pz.speed:5.1f} m/s  goals={pz.goals}"

    def meta(self) -> dict:
        pz = self.play.sim.puck
        return {"rink": pz.rink.to_dict(), "goals": pz.goals, "shots_mph": self.physics.shots}

    def close(self) -> None:
        pass


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--height", default="5'8\"")
    ap.add_argument("--shoots", choices=("left", "right"), default="left")
    ap.add_argument("--fresh", action="store_true", help="ignore sandbox_settings.json and start from defaults")
    ap.add_argument("--no-voice", action="store_true")
    ap.add_argument("--no-sound", action="store_true", help="no ice / puck sounds")
    ap.add_argument("--audio-device", default="Oculus", help="part of the output device's name (default: the Quest over Link)")
    ap.add_argument("--notes", default="")
    ap.add_argument("--set", action="append", metavar="KEY=VALUE",
                    help="a setting for this run, e.g. --set push=6 --set glide=1.5 (keys as in sandbox_settings.json)")
    ap.add_argument("--tune", metavar="KEY", help="open the tuning menu on this setting (e.g. push), for an A/B")
    args = ap.parse_args()

    base = stickspec.from_height(stickspec.parse_height(args.height), args.shoots)
    fit = grab.Fit.load(record.FIT_PATH) or grab.Fit()
    values = Tuning.defaults(base, fit, pk.Params())
    if SETTINGS_PATH.exists() and not args.fresh:
        values.update(json.loads(SETTINGS_PATH.read_text())["values"])
    set_values(values, args.set)
    play = Play(Tuning(base, values))
    tune_first(play.tuning, args.tune)
    run_dir = HERE / "data" / ("sandbox-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
    lock = record.take_lock()
    try:
        run(args, play, run_dir)
    except xr.FormFactorUnavailableError:
        raise SystemExit("Headset not connected: put it on, start Link, then run again (xrcheck.py tells you).")
    finally:
        lock.unlink(missing_ok=True)


def run(args, play: Play, run_dir: Path, mode_cls=SandboxMode) -> None:
    # Leave Python's GIL switch interval at its default (5 ms). A short one (0.5 ms) was tried and
    # was worse: a busy background thread then gets the lock in the middle of each physics tick
    # (drill 2026-11-07: 752 samples/s; off the headset: 590-850/s while a rep was prepared).
    voice = VoiceQueue(record.Voice(not args.no_voice))
    voice.start()
    sounds = audio.Mixer(play.bus, enabled=not args.no_sound, device=getattr(args, "audio_device", "Oculus"))
    if sounds.start():
        print(f"  audio: mixer on {sounds.device_name} at {sounds.rate} Hz, block {sounds.block}", flush=True)
        voice.voice.sink, voice.voice.rate = sounds.speak, sounds.rate   # the voice there too, not Windows' default
    else:
        sounds = audio.WinsoundSink(play.bus, not args.no_sound)
    provider = GLFWOffscreenContextProvider()
    with ContextObject(
        context_provider=provider,
        instance_create_info=xr.InstanceCreateInfo(
            application_info=xr.ApplicationInfo(application_name=mode_cls.app_name, engine_name="none"),
            enabled_extension_names=[xr.KHR_OPENGL_ENABLE_EXTENSION_NAME,
                                     xr.KHR_WIN32_CONVERT_PERFORMANCE_COUNTER_TIME_EXTENSION_NAME],
        ),
        reference_space_create_info=xr.ReferenceSpaceCreateInfo(reference_space_type=xr.ReferenceSpaceType.STAGE),
    ) as ctx:
        run_dir.mkdir(parents=True, exist_ok=False)
        log = Log(run_dir)
        meta = {"created": dt.datetime.now().isoformat(timespec="seconds"), "kind": mode_cls.kind, "notes": args.notes,
                "runtime": xr.get_instance_properties(ctx.instance).runtime_name.decode(),
                "system": xr.get_system_properties(ctx.instance, ctx.system_id).system_name.decode(),
                "settings_start": dict(play.tuning.values), "rate_hz": 1000, "lag_ms": 0, "space": "stage",
                "predict": PREDICT}
        print(f"{mode_cls.kind}: {meta['system']} | recording to {run_dir}")
        inputs = record.Inputs(ctx)
        renderer = record.LineRenderer()
        sampler = record.Sampler(ctx, inputs.spaces, inputs.head, 1000, 0, play, run_dir / "rec.csv")
        mode = mode_cls(play, voice, log)
        physics = mode.make_physics()
        if pk.FAST:                                  # compile (first run) or load the physics before the loop
            import physics_core
            print(f"  physics compiled/loaded in {physics_core.warm():.1f} s", flush=True)
        sampler.on_tick = physics
        sampler.rig = play.rig
        sampler.predict = PREDICT
        sampler.start()
        qpc_now = ctypes.wintypes.LARGE_INTEGER()

        def watchdog():                              # the frame loop stalls while the headset sleeps
            while True:
                time.sleep(5)
                if time.time() - play.last_focus > AWAY_LIMIT_S:
                    print(f"  away for {AWAY_LIMIT_S} s: ending", flush=True)
                    _thread.interrupt_main()
                    return
        threading.Thread(target=watchdog, daemon=True, name="watchdog").start()
        voice.say(mode.intro())

        sync_info = xr.ActionsSyncInfo(active_action_sets=[xr.ActiveActionSet(action_set=ctx.default_action_set)])
        disp_loc = [xr.SpaceLocation() for _ in inputs.spaces]   # no velocity chain: a temporary one dangles
        head_loc = xr.SpaceLocation()
        dgrab = grab.Grab(play.spec, play.fit)
        version = play.version
        top_hand_dev = play.spec.top_hand
        pick, change = Stick(), Stick()
        drive = rig.Drive()
        comfort = Comfort(run_dir / "rig.csv", voice, log)
        snap_ready, tunnel = True, 0.0
        menu = False                                 # the settings menu: only the menu button opens it (Jon,
                                                     # 2026-11-13: no settings changed by accident while playing)
        moving = True                                # the left stick moves you (in the menu it tunes the settings)
        prev = {"x": False, "a": False, "b": False, "y": False, "lclick": False, "menu": False}
        last_change, announced = 0.0, True
        click_since, click_done, click_centred = None, False, True
        last_status, away_since = 0.0, None
        head_seen = False
        fr = {"n": 0, "work": 0.0, "max": 0.0, "moved": 0, "t0": time.perf_counter(), "samples": 0}
        try:
            for frame_state in ctx.frame_loop():
                t_work = time.perf_counter()
                now = time.time()
                focused = ctx.session_state == xr.SessionState.FOCUSED
                inp = {"squeeze": {}, "thumb": (0.0, 0.0), "a": False, "b": False, "x": False, "y": False,
                       "lthumb": (0.0, 0.0), "lclick": False, "ltrigger": 0.0, "rtrigger": 0.0}
                if focused:
                    xr.sync_actions(ctx.session, sync_info)
                    inp = inputs.read()
                    away_since = None
                    play.last_focus = now
                else:
                    away_since = away_since or now
                    if now - away_since > AWAY_LIMIT_S:
                        break
                for d in recfmt.CONTROLLERS:
                    play.squeeze[d] = inp["squeeze"].get(d, 0.0)
                play.shoot = inp.get("rtrigger", 0.0)          # firm hands for a shot (Physics._firmness)
                t_disp = frame_state.predicted_display_time
                dt_frame = frame_state.predicted_display_period / 1e9 if frame_state.predicted_display_period else 1 / 72
                # how far ahead this frame will be on the display: the physics samples the hands there
                ctypes.windll.kernel32.QueryPerformanceCounter(ctypes.byref(qpc_now))
                lead = t_disp - xr.convert_win32_performance_counter_to_time_khr(ctx.instance, qpc_now).value
                if 0 < lead < AHEAD_MAX_NS:
                    play.ahead_ns += (lead - play.ahead_ns) * (1.0 if play.ahead_ns == 0 else 0.05)
                room = {}                                    # poses in the room, then in the world
                for dev, space, loc in zip(recfmt.CONTROLLERS, inputs.spaces, disp_loc):
                    r = xr.check_result(xr.raw_functions.xrLocateSpace(space, ctx.space, t_disp, ctypes.byref(loc)))
                    if not r.is_exception() and (loc._location_flags & record.NEED_POSE) == record.NEED_POSE:
                        o, q = loc.pose.orientation, loc.pose.position
                        room[dev] = (stickmath.quat_to_mat(np.array([o.x, o.y, o.z, o.w])), np.array([q.x, q.y, q.z]))
                head_room = None
                r = xr.check_result(xr.raw_functions.xrLocateSpace(inputs.head, ctx.space, t_disp, ctypes.byref(head_loc)))
                if not r.is_exception() and (head_loc._location_flags & record.NEED_POSE) == record.NEED_POSE:
                    o, q = head_loc.pose.orientation, head_loc.pose.position
                    head_room = (stickmath.quat_to_mat(np.array([o.x, o.y, o.z, o.w])), np.array([q.x, q.y, q.z]))
                tp = play.want_teleport
                if tp is not None and head_room is not None:  # e.g. back to centre ice after a goal
                    play.want_teleport = None
                    play.rig.teleport(t_disp * 1e-9, *rig.place_head(*head_room, *tp))
                    drive.stop()
                rp = play.rig.at(t_disp * 1e-9)              # the room in the world at this frame
                poses = {dev: rp.pose(*pose) for dev, pose in room.items()}
                if head_room is not None:
                    play.head = rp.pose(*head_room)
                    play.my_skates = (play.feet.update(*head_room, rp, dt_frame)
                                      if play.tuning.values.get("feet", 0) > 0 else None)
                    if not head_seen:
                        head_seen = True
                        mode.first_head()

                # ---- moving: the left stick slides you (where you look is forward), the right stick
                # turns you about your head (not while fitting: it fits the stick then)
                lx, ly = inp["lthumb"]
                tv = play.tuning.values
                play.rig.set_lift(t_disp * 1e-9, tv.get("skates", 0.0) / 100)   # skate height, eased in when changed
                play.tuning.drive(drive)
                rx = 0.0 if play.fitting else inp["thumb"][0]
                pivot = play.head[1] if play.head is not None else rp.off
                if tv["snap"] > 0:                          # snap turns: one step per flick of the stick
                    if snap_ready and abs(rx) > 0.7:
                        play.rig.snap(t_disp * 1e-9, -np.sign(rx) * np.radians(tv["snap"]), pivot)
                        snap_ready = False
                    elif abs(rx) < 0.35:
                        snap_ready = True
                    rx = 0.0
                lt = inp.get("ltrigger", 0.0) if moving else 0.0          # the sprint trigger
                vel, omega = drive.update((lx, ly) if moving else (0.0, 0.0), rx,
                                          play.head[0] if play.head is not None else None, dt_frame, boost=lt)
                vel = drive.vel = mode.confine(play.head[1] if play.head is not None else None, vel, dt_frame)
                play.rig.drive(t_disp * 1e-9, vel, omega, pivot)
                # the comfort vignette closes in with the thumbsticks' motion (not your own)
                want = min(1.0, float(np.linalg.norm(vel)) / max(drive.move_ms, 0.5) * 1.3
                           + abs(omega) / np.radians(max(drive.turn_deg_s, 1.0)))
                if drive.mode == "stop":                        # held closed through a hockey stop
                    want = 1.0
                tunnel += (want - tunnel) * (1 - np.exp(-dt_frame / (0.08 if want > tunnel else 0.25)))
                if focused:                                     # play time only (not while the headset sleeps)
                    comfort.frame(now, sampler.shared.t_now, dt_frame, (lx, ly, rx, lt), moving, drive, vel, omega,
                                  tunnel * tv["vignette"], tv["check"])

                # ---- tuning and buttons
                tu = play.tuning
                horiz = abs(lx) > abs(ly) + 0.25          # only a clearly sideways push picks a setting,
                vert = abs(ly) > abs(lx) + 0.25           # only a clearly up/down push changes it
                d = pick.update(lx if horiz and not moving else 0.0, now)
                if d:
                    tu.pick(d)
                    voice.say(tu.describe(), key="setting")
                    announced = True
                d = change.update(ly if vert and not moving else 0.0, now)
                if d and tu.change(d):
                    play.retune()
                    last_change, announced = now, False
                    log.event(sampler.shared.t_now, "setting", key=tu.current.key, value=tu.values[tu.current.key])
                if not announced and now - last_change > 0.5:
                    voice.say(tu.describe(), key="setting")
                    announced = True
                answered = False
                for b in ("a", "b", "y"):                      # the comfort check's answer, if it's asking
                    if inp[b] and not prev[b] and comfort.answer(b, sampler.shared.t_now, tv["check"]):
                        answered = True
                if inp["menu"] and not prev["menu"]:          # the settings menu, in and out
                    menu = not menu
                    moving = not menu
                    if menu:
                        voice.say(f"Settings. {tu.describe()}. Left stick picks and changes, A saves, "
                                  "Y fits the stick. The menu button closes.", key="setting")
                    else:
                        msg = "Menu closed."
                        if play.fitting:
                            play.fitting = False
                            msg = "Fitting off, not saved. Menu closed."
                        voice.say(msg, key="setting")
                    announced = True
                    log.event(sampler.shared.t_now, "menu", open=menu)
                if menu and inp["y"] and not prev["y"] and not answered:
                    play.fitting = not play.fitting
                    voice.say("Stick fitting. Right stick turns and tilts it. Hold B and push to swing it. "
                              "A saves." if play.fitting else "Fitting off, not saved.", key="fit")
                if play.fitting:
                    new_fit = record.apply_thumbstick(play.fit, inp["thumb"], inp["b"], dt_frame)
                    if new_fit != play.fit:
                        tu.values.update(roll=new_fit.roll_deg, pitch=new_fit.pitch_deg, yaw=new_fit.yaw_deg)
                        play.retune()
                if inp["x"] and not prev["x"]:
                    mode.button("x", sampler.shared.t_now)
                # holding the left stick in (1 s, centred: pushing it hard clicks it too) recenters
                if inp["lclick"]:
                    if click_since is None:
                        click_since, click_centred = now, True
                    click_centred = click_centred and max(abs(lx), abs(ly)) < 0.35
                    if now - click_since > 1.0 and click_centred and not click_done:
                        click_done = True
                        mode.recenter()
                else:
                    click_since, click_done = None, False
                b_down = inp["b"] and not prev["b"] and not answered
                a_down = inp["a"] and not prev["a"] and not answered
                if menu:                                       # in the menu: B says the setting, A saves
                    if b_down and not play.fitting:
                        voice.say(tu.describe(), key="setting")
                    if a_down and play.fitting:
                        play.fitting = False
                        play.fit.save(record.FIT_PATH, play.spec)
                        SETTINGS_PATH.write_text(json.dumps({"values": tu.values, "spec": play.spec.to_dict()}, indent=2))
                        f = play.fit
                        voice.say(f"Fit saved. Turned {f.roll_deg:.0f}, tilted {f.pitch_deg:.0f}, "
                                  f"swung {f.yaw_deg:.0f} degrees.", key="fit")
                        log.event(sampler.shared.t_now, "fit_saved", **f.to_dict())
                        inputs.buzz(top_hand_dev, 0.8, 60)
                    elif a_down:
                        save_settings(play, voice, log, sampler.shared.t_now)
                else:                                          # playing: the mode's own (start, score, next rep)
                    if b_down:
                        mode.button("b", sampler.shared.t_now)
                    if a_down:
                        mode.button("a", sampler.shared.t_now)
                mode.frame(now)
                for k in prev:
                    prev[k] = inp[k]

                # ---- the stick for display, and the buzz
                if play.version != version:
                    dgrab.configure(play.spec, play.fit)
                    version = play.version
                top, bot = play.spec.top_hand, play.spec.bottom_hand
                state, R, p = dgrab.step(poses.get(top), poses.get(bot), play.squeeze[top], play.squeeze[bot], now,
                                         force_top=play.fitting)
                while not play.sounds.empty():                # by name; contacts play straight off the bus
                    name, strength = play.sounds.get_nowait()
                    sounds.play(name, strength)
                if isinstance(sounds, audio.WinsoundSink):
                    sounds.frame()
                buzz: dict = {}
                while not play.haptics.empty():
                    amp, hands, ms = play.haptics.get_nowait()
                    for h in hands:
                        a0, m0 = buzz.get(h, (0.0, 0.0))
                        buzz[h] = (max(a0, amp), max(m0, ms))
                for h, (amp, ms) in buzz.items():
                    inputs.buzz(h, amp, ms)

                held = {top: dgrab.on["t"], bot: dgrab.on["b"]}
                drawn = mode.draw(poses, held, (R, p), state)
                world_to_room = rp.inverse()
                strength = tunnel * play.tuning.values["vignette"]
                mesh = record.tunnel_mesh(strength) if strength > 0.02 else None
                renderer.samples = int(play.tuning.values.get("aa", AA))
                for i, view in enumerate(ctx.view_loop(frame_state)):
                    proj = np.asarray(Matrix4x4f.create_projection_fov(GraphicsAPI.OPENGL, view.fov, 0.05, 100.0).m)
                    sc = ctx.swapchains[i]
                    ep = view.pose.position
                    renderer.draw(drawn.lines, proj @ record.view_matrix(view.pose) @ world_to_room, theme.SKY,
                                  tris=drawn.tris, target=ctx.graphics.swapchain_framebuffer,
                                  viewport=(0, 0, sc.width, sc.height),
                                  meshes=drawn.meshes, eye=rp.point(ep.x, ep.y, ep.z))
                    if mesh is not None:
                        renderer.tunnel(mesh)
                w = time.perf_counter() - t_work               # this frame's work, not the wait for the headset
                fr["n"] += 1
                fr["work"] += w
                fr["max"] = max(fr["max"], w)
                fr["moved"] += bool(omega or vel.any())
                if now - last_status > 2:
                    last_status = now
                    st = sounds.stats
                    au = (f"audio {sounds.latency_ms:.0f} ms late {st.get('late', 0)} under {st.get('underruns', 0)}"
                          if st else "audio winsound")
                    el = time.perf_counter() - fr["t0"]
                    hz = 1e9 / frame_state.predicted_display_period if frame_state.predicted_display_period else 0
                    fps = (f"fps {fr['n'] / el:.0f}/{hz:.0f} frame {fr['work'] / max(fr['n'], 1) * 1000:.1f} ms "
                           f"max {fr['max'] * 1000:.0f}{' moving' if fr['moved'] else ''}  "
                           f"physics {(sampler.n - fr['samples']) / el:.0f}/s"
                           f"{f' ahead {play.ahead_ns / 1e6:.0f} ms' if sampler.predict else ''}")
                    fr.update(n=0, work=0.0, max=0.0, moved=0, t0=time.perf_counter(), samples=sampler.n)
                    print(f"  t={play.t_now:6.1f}s  {fps}  "
                          f"stick={grab.STATE_NAMES[play.stick_state]:<12} {mode.status()}  {au}  "
                          f"setting: {tu.describe()}", flush=True)
        except KeyboardInterrupt:
            print("stopped with Ctrl+C")
        finally:
            sampler.stop_evt.set()
            sampler.join(timeout=5)
            comfort.close()
            meta.update(samples=sampler.n, ahead_ms=round(play.ahead_ns / 1e6, 1), comfort=comfort.summary(),
                        settings_end=dict(play.tuning.values), spec=play.spec.to_dict(),
                        fit=play.fit.to_dict(), params=play.params.to_dict(), phases=[], completed=True,
                        ended="quit", **mode.meta())
            if play.rig.moved:                      # rec.csv holds world poses: the room as the thumbsticks moved it
                meta["space"] = "stage, moved by the thumbsticks (world)"
            meta["audio"] = {"device": sounds.device_name, "latency_ms": round(sounds.latency_ms, 1)
                             if sounds.latency_ms == sounds.latency_ms else None, **sounds.stats}
            recfmt.write_meta(run_dir, meta)
            mode.close()
            sounds.close()
            log.close()
    print(f"saved {run_dir}")


if __name__ == "__main__":
    main()
