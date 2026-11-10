"""Spike 0 sandbox: your stick, a puck and a net. Play, and tune everything as you go.

    uv run python sandbox.py
    uv run python sandbox.py --fresh      # start from the defaults, not your saved settings

Controls
  grip buttons (middle finger)  hold the stick: right = top hand, left = bottom hand (grab.py)
  left thumbstick               move you around the ice; forward is where you look (rig.py)
  right thumbstick left/right   turn you, about your head: smoothly, or in steps per flick (the
                                "snap turn" setting, degrees; 0 = smooth). The view's edges darken
                                while you move ("comfort vignette")
  click the left thumbstick     (a quick press) switch it to tuning, and back:
    left/right                  pick a setting (the voice says which, and its value)
    up/down                     change it (hold to keep changing)
  X                             a new puck, on your blade
  Y                             fit the stick in your hand: right thumbstick turns the blade
                                (left/right) and tilts the stick (up/down); hold B and push to
                                swing it sideways; A saves the fit (Y again leaves without saving)
  hold the left thumbstick in   (1 s) put the net straight in front of you again
  B                             say the current setting again
  A                             save the settings (sandbox_settings.json, used next time)

Settings: stick length, lie, curve depth, face open, flex, forgiveness (extra reach for catching
the puck), puck weight, ice friction, blade pop, blade grip, buzz strength, soft hands (off here; the 3v3 turns it on) and its shot
release speed, skate speed, snap turn (degrees; 0 = smooth), smooth turn speed, comfort vignette,
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

import numpy as np
import xr
from xr.utils.gl import ContextObject
from xr.utils.gl.glfw_util import GLFWOffscreenContextProvider
from xr.utils.matrix4x4f import GraphicsAPI, Matrix4x4f

import grab
import puck as pk
import recfmt
import record
import rig
import stickmath
import stickspec
import audio
from contacts import Bus, Contact
from stickspec import INCH

HERE = Path(__file__).resolve().parent
SETTINGS_PATH = HERE / "sandbox_settings.json"
SNAP_DEG = 0.0           # smooth turning (Jon's pick); 30 turns you in steps, the comfort option
VIGNETTE = 0.7           # comfort: the view's edges darken while the thumbsticks move you (0 = off)
PUSH = 6.0               # m/s^2: the skating push limit (rig.Drive.push), the research's pick. ON: with it off
                         # (the old easing, 20-47 m/s^2 jolts) Jon got sick within seconds; 6 "was solid", and
                         # 6-10 felt fine at 3 and 4 m/s (free skate 2026-11-09). 0 = the old easing
GLIDE = 1.5              # m/s^2: let go and you coast, slowing at this (rig.Drive.glide): 2 s and 3 m from 3 m/s.
STOP = 8.0               # m/s^2: the hockey stop, the left stick held against your motion (rig.Drive.stop_ms2).
                         # Both "felt good" (free skate 2026-11-09, with push 6); 0 = off
CARVE = 6.0              # m/s^2: the turn limit, the path bends at most this hard sideways (rig.Drive.carve): the
                         # stick's turn tops out at 115 deg/s at 3 m/s. 6 "felt good"; 9 (no cap at 3 m/s) left
                         # Jon "a little motion sick" after 16 min (free skate 2026-11-10); 0 = off
COMFORT_CHECK_MIN = 4.0  # a 0-10 queasiness check this often (Comfort; the "comfort check" setting, 0 = off)
JUMP_M = 0.2             # m: the blade can't move this far in one physics tick: a snap turn or a teleport
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
    Setting("hands", "hands", 0.05, 0.1, 1.0, "{:.2f}"),        # the stick's damping: higher gives a softer catch
    Setting("grip", "blade grip", 0.05, 0.0, 1.0, "{:.2f}"),
    Setting("buzz", "buzz", 0.1, 0.0, 1.0, "{:.1f}"),
    Setting("magnet", "soft hands", 0.1, 0.0, 1.0, "{:.1f}", "off"),
    Setting("release", "shot release", 0.5, 2.0, 9.0, "{:g} metres per second"),
    Setting("skate", "skate speed", 0.5, 1.0, 9.0, "{:g} metres per second"),
    # the skating model (rig.Drive): each off at 0, as it always was
    Setting("push", "push", 1, 0, 10, "{:g} metres per second squared", "off"),
    Setting("glide", "glide", 0.25, 0, 4, "slows {:g} metres per second squared", "off"),
    Setting("stop", "hockey stop", 1, 0, 12, "{:g} metres per second squared", "off"),
    Setting("carve", "turn limit", 1, 0, 12, "{:g} metres per second squared", "off"),
    Setting("back", "backward speed", 0.1, 0.3, 1.0, "{:.0%} of forward"),
    Setting("side", "sideways speed", 0.1, 0.3, 1.0, "{:.0%} of forward"),
    Setting("snap", "snap turn", 15, 0, 90, "{:.0f} degrees"),
    Setting("turn", "smooth turn speed", 15, 45, 360, "{:.0f} degrees per second"),
    Setting("vignette", "comfort vignette", 0.1, 0.0, 1.0, "{:.1f}"),
    Setting("check", "comfort check", 1, 0, 15, "every {:g} minutes", "off"),   # a 0-10 queasiness check
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
                "air": params.air_k * 1000, "boards": params.board_bounce, "hands": pk.Flex.DAMPING,
                "buzz": 0.6, "forgive_cm": params.forgiveness * 100, "puck_g": params.puck_mass * 1000,
                "skate": rig.MOVE_MS, "turn": rig.TURN_DEG_S, "magnet": params.magnet, "release": params.release,
                "push": PUSH, "glide": GLIDE, "stop": STOP, "carve": CARVE, "back": 1.0, "side": 1.0,
                "snap": SNAP_DEG, "vignette": VIGNETTE, "check": COMFORT_CHECK_MIN, "ice": pk.ICE_ASSIST * 100}

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
        self.latest_flags = {d: 0 for d in recfmt.CONTROLLERS}
        self.t_now = 0.0
        # requests to the physics thread
        self.want_puck = False
        self.want_recenter = False
        self.head = None                       # (R, p) of the headset, from the render thread
        self.haptics: queue.SimpleQueue = queue.SimpleQueue()
        self.stick_state = grab.NONE
        self.last_focus = time.time()
        self.fitting = False                   # Y: the stick held in the right hand while you fit it
        self.sounds: queue.SimpleQueue = queue.SimpleQueue()   # sounds by name (go, whistle, a hit)
        self.bus = Bus()                       # every contact, from the physics: the sound and buzz play from it
        self.rig = rig.Rig()                   # where the room sits in the world: the thumbsticks move it
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
    """events.jsonl and puck.csv, written from any thread."""

    def __init__(self, run_dir: Path):
        self.events = open(run_dir / "events.jsonl", "a", encoding="utf-8")
        self.puck = open(run_dir / "puck.csv", "w", encoding="utf-8")
        self.puck.write("t,px,py,pz,vx,vy,vz,impulse,stick,bend_mm\n")
        self.lock = threading.Lock()

    def event(self, t: float, kind: str, **data) -> None:
        with self.lock:
            self.events.write(json.dumps({"t": round(t, 4), "event": kind, **data}, default=_plain) + "\n")
            self.events.flush()

    def puck_row(self, row: str) -> None:
        with self.lock:
            self.puck.write(row)

    def close(self) -> None:
        with self.lock:
            self.events.close()
            self.puck.close()


# ----------------------------------------------------------------------------- physics (sampler thread)


HOLDERS = {grab.BOTH: ("top", "bottom"), grab.TOP: ("top",), grab.LOOSE_TOP: ("top",),
           grab.BOTTOM: ("bottom",), grab.LOOSE_BOTTOM: ("bottom",)}


class Physics:
    def __init__(self, play: Play, voice: VoiceQueue, log: Log):
        self.play, self.voice, self.log = play, voice, log
        self.grab = grab.Grab(play.spec, play.fit)
        self.version = -1
        self.last_t = None
        self.shot = None              # [t of first contact, peak speed]
        self.respawn_at = None
        self.slow_since = None
        self.last_buzz = 0.0
        self.tick = 0
        self.shots = []
        self._last_sweet = None
        self._last_yaw = 0.0
        self._refresh()

    def _refresh(self) -> None:
        pl = self.play
        spec = pl.spec
        self.grab.configure(spec, pl.fit)
        pl.sim.flex.damping = pl.tuning.values.get("hands", pk.Flex.DAMPING)   # the "hands" setting
        pl.sim.flex.set_flex(spec.flex)
        self.edge_b, self.edge_t = spec.edge(8), spec.edge(8, top=True)
        self.sweet, self.u, self.zf = spec.sweet, spec.u, spec.z_forehand
        self.version = pl.version

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
        dt_s = 0.001 if self.last_t is None else float(np.clip(t - self.last_t, 0.0002, 0.01))
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
            self._last_sweet = a
        else:
            self._last_sweet = None
        self._last_yaw = yaw
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
            imp = sim.step(dt_s, bot_e, top_e, anchor, R @ self.u, body=getattr(self.play, "body", None))
        else:
            imp = sim.step(dt_s, None, None)
        self.last_impulse = imp
        return imp

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
        """Shots: a hard contact, then call the speed once it's away."""
        pz = self.play.sim.puck
        if imp > 2.0 and pz.speed > 6.0:
            if self.shot is None:
                self.shot = [t, pz.speed]
            else:
                self.shot[1] = max(self.shot[1], pz.speed)
        if self.shot is not None and t - self.shot[0] > 0.25:
            mph = self.shot[1] * MPH
            if mph > 12:
                self.voice.say(f"{mph:.0f}", key="shot")
                self.shots.append(round(mph, 1))
                self.log.event(t, "shot", mph=round(mph, 1), ms=round(self.shot[1], 2))
            self.shot = None

    def _log_row(self, t: float, imp: float, state: int) -> None:
        sim = self.play.sim
        P, V = sim.puck.pos, sim.puck.vel
        b = np.linalg.norm(sim.bend) * 1000
        self.log.puck_row(f"{t:.4f},{P[0]:.4f},{P[1]:.4f},{P[2]:.4f},{V[0]:.3f},{V[1]:.3f},{V[2]:.3f},"
                          f"{imp:.3f},{state},{b:.1f}\n")


# ----------------------------------------------------------------------------- drawing


WHITE, RED, BLUE = (0.92, 0.92, 0.92), (0.95, 0.2, 0.2), (0.3, 0.5, 1.0)


class Lines:
    """Line segments for the renderer: line(a, b, colour) one at a time, or many(A, B, colour)
    for whole arrays of them (much cheaper in Python); then .array()."""

    def __init__(self):
        self.v: list = []
        self.blocks: list[np.ndarray] = []

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


def scene(play: Play, rink: pk.Rink, poses: dict, held: dict, stick, state: int) -> np.ndarray:
    line = Lines()
    draw_rink(line, rink)
    draw_puck(line, play.sim.puck)
    draw_hands_and_stick(line, play, poses, held, stick, state)
    return line.array()


def draw_rink(line, rink: pk.Rink) -> None:
    def W(u, y, w):
        return rink.to_world(u, y, w)

    end_w = rink.goal_dist + pk.GOAL_DEPTH + rink.end
    grid = (0.32, 0.36, 0.44)
    for u in np.arange(-rink.half_width, rink.half_width + 0.01, 0.5):     # the ice
        line(W(u, 0, -rink.back), W(u, 0, end_w), grid)
    for w in np.arange(-rink.back, end_w + 0.01, 0.5):
        line(W(-rink.half_width, 0, w), W(rink.half_width, 0, w), grid)
    boards = (0.55, 0.55, 0.6)
    corners = [(-rink.half_width, -rink.back), (rink.half_width, -rink.back),
               (rink.half_width, end_w), (-rink.half_width, end_w)]
    for (u0, w0), (u1, w1) in zip(corners, corners[1:] + corners[:1]):
        line(W(u0, 1.0, w0), W(u1, 1.0, w1), boards)
    for u0, w0 in corners:
        line(W(u0, 0, w0), W(u0, 1.0, w0), boards)
    # the goal: line, crease, posts, crossbar, net
    g, hw, gh, d = rink.goal_dist, pk.GOAL_HALF_W, pk.GOAL_H, pk.GOAL_DEPTH
    line(W(-rink.half_width, 0.002, g), W(rink.half_width, 0.002, g), RED)
    a = np.linspace(0, np.pi, 17)
    crease = [W(1.83 * np.cos(x), 0.002, g - 1.83 * np.sin(x)) for x in a]
    for p0, p1 in zip(crease, crease[1:]):
        line(p0, p1, BLUE)
    for su in (-hw, hw):
        line(W(su, 0, g), W(su, gh, g), RED)
    line(W(-hw, gh, g), W(hw, gh, g), RED)
    mesh = (0.75, 0.75, 0.78)
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
    P = puck.pos
    ang = np.linspace(0, 2 * np.pi, 17)
    ring = np.stack([np.cos(ang), np.zeros_like(ang), np.sin(ang)], axis=1) * pk.R
    for y in (P[1] - pk.H / 2, P[1] + pk.H / 2):
        pts = ring + np.array([P[0], y, P[2]])
        for p0, p1 in zip(pts, pts[1:]):
            line(p0, p1, WHITE)
    for k in range(0, 16, 4):
        line(ring[k] + P - [0, pk.H / 2, 0], ring[k] + P + [0, pk.H / 2, 0], WHITE)


def draw_hands_and_stick(line, play: Play, poses: dict, held: dict, stick, state: int) -> None:
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
        shaft_c = (0.6, 0.66, 0.75) if loose else WHITE
        blade_c = (0.8, 0.65, 0.2) if loose else (1.0, 0.85, 0.1)
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

    - rig.csv: every frame, the sticks, the drive's velocity, turn rate and mode, and the vignette.
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
            self.fh.write("t,lx,ly,rx,moving,mode,vx,vz,speed,omega,accel,vignette\n")
        self.asking_since: float | None = None
        self.play_s = 0.0
        self.next_check: float | None = None
        self.ratings: list[dict] = []
        self.prev_v: np.ndarray | None = None
        self.stats = {"frames": 0, "moving_s": 0.0, "accel_events": 0, "over6_s": 0.0, "peak_accel": 0.0,
                      "peak_turn_deg_s": 0.0, "vignette_s": 0.0}
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
        if self.fh is not None:
            lx, ly, rx = sticks
            self.fh.write(f"{t_sim:.3f},{lx:.3f},{ly:.3f},{rx:.3f},{int(moving)},{drive.mode},{vel[0]:.3f},"
                          f"{vel[2]:.3f},{speed:.3f},{omega:.4f},{a:.2f},{vignette:.2f}\n")
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
                "vignette_min": round(s["vignette_s"] / 60, 2), "ratings": self.ratings}

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
                "Click the left stick to tune the settings instead. X gives you a new puck. "
                "Y fits the stick in your hand.")

    def first_head(self) -> None:
        self.play.want_recenter = True

    def recenter(self) -> None:
        self.play.want_recenter = True
        self.voice.say("Net in front of you.", key="rink")

    def button(self, name: str, t_sim: float) -> None:
        """X, A or B pressed (A and B only while not fitting the stick)."""
        pl, tu = self.play, self.play.tuning
        if name == "x":
            pl.want_puck = True
        elif name == "b":
            self.voice.say(tu.describe(), key="setting")
        elif name == "a":
            SETTINGS_PATH.write_text(json.dumps({"values": tu.values, "spec": pl.spec.to_dict()}, indent=2))
            pl.fit.save(record.FIT_PATH, pl.spec)
            self.voice.say("Saved.", key="saved")
            self.log.event(t_sim, "saved", values=dict(tu.values))

    def frame(self, now: float) -> None:
        """Once a frame, in the render thread."""

    def confine(self, head_world, vel: np.ndarray, dt: float) -> np.ndarray:
        """The thumbsticks' velocity, allowed where you are (the sandbox: anywhere)."""
        return vel

    def draw(self, poses: dict, held: dict, stick, state: int) -> np.ndarray:
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
        moving = True                                # the left stick moves you (else it tunes the settings)
        prev = {"x": False, "a": False, "b": False, "y": False, "lclick": False}
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
                       "lthumb": (0.0, 0.0), "lclick": False}
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
                    if not head_seen:
                        head_seen = True
                        mode.first_head()

                # ---- moving: the left stick slides you (where you look is forward), the right stick
                # turns you about your head (not while fitting: it fits the stick then)
                lx, ly = inp["lthumb"]
                tv = play.tuning.values
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
                vel, omega = drive.update((lx, ly) if moving else (0.0, 0.0), rx,
                                          play.head[0] if play.head is not None else None, dt_frame)
                vel = drive.vel = mode.confine(play.head[1] if play.head is not None else None, vel, dt_frame)
                play.rig.drive(t_disp * 1e-9, vel, omega, pivot)
                # the comfort vignette closes in with the thumbsticks' motion (not your own)
                want = min(1.0, float(np.linalg.norm(vel)) / max(drive.move_ms, 0.5) * 1.3
                           + abs(omega) / np.radians(max(drive.turn_deg_s, 1.0)))
                if drive.mode == "stop":                        # held closed through a hockey stop
                    want = 1.0
                tunnel += (want - tunnel) * (1 - np.exp(-dt_frame / (0.08 if want > tunnel else 0.25)))
                if focused:                                     # play time only (not while the headset sleeps)
                    comfort.frame(now, sampler.shared.t_now, dt_frame, (lx, ly, rx), moving, drive, vel, omega,
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
                if inp["y"] and not prev["y"] and not answered:
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
                # the left stick's click, only with the stick centred (pushing it hard clicks it too):
                # a quick press switches it between moving you and tuning; a 1 s press recenters
                if inp["lclick"]:
                    if click_since is None:
                        click_since, click_centred = now, True
                    click_centred = click_centred and max(abs(lx), abs(ly)) < 0.35
                    if now - click_since > 1.0 and click_centred and not click_done:
                        click_done = True
                        mode.recenter()
                else:
                    if click_since is not None and click_centred and not click_done and now - click_since < 0.5:
                        moving = not moving
                        voice.say("Moving. Left stick moves you, right stick turns you." if moving else
                                  f"Tuning. {tu.describe()}", key="setting")
                        announced = True
                        log.event(sampler.shared.t_now, "left_stick", mode="move" if moving else "tune")
                    click_since, click_done = None, False
                if inp["b"] and not prev["b"] and not play.fitting and not answered:
                    mode.button("b", sampler.shared.t_now)
                if inp["a"] and not prev["a"] and play.fitting and not answered:
                    play.fitting = False
                    play.fit.save(record.FIT_PATH, play.spec)
                    SETTINGS_PATH.write_text(json.dumps({"values": tu.values, "spec": play.spec.to_dict()}, indent=2))
                    f = play.fit
                    voice.say(f"Fit saved. Turned {f.roll_deg:.0f}, tilted {f.pitch_deg:.0f}, "
                              f"swung {f.yaw_deg:.0f} degrees.", key="fit")
                    log.event(sampler.shared.t_now, "fit_saved", **f.to_dict())
                    inputs.buzz(top_hand_dev, 0.8, 60)
                elif inp["a"] and not prev["a"] and not answered:
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
                verts = mode.draw(poses, held, (R, p), state)
                world_to_room = rp.inverse()
                strength = tunnel * play.tuning.values["vignette"]
                mesh = record.tunnel_mesh(strength) if strength > 0.02 else None
                for view in ctx.view_loop(frame_state):
                    proj = np.asarray(Matrix4x4f.create_projection_fov(GraphicsAPI.OPENGL, view.fov, 0.05, 100.0).m)
                    renderer.draw(verts, proj @ record.view_matrix(view.pose) @ world_to_room, (0.05, 0.06, 0.09))
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
