"""Spike 0 sandbox: your stick, a puck and a net. Play, and tune everything as you go.

    uv run python sandbox.py
    uv run python sandbox.py --fresh      # start from the defaults, not your saved settings

Controls
  grip buttons (middle finger)  hold the stick: right = top hand, left = bottom hand (grab.py)
  left thumbstick left/right    pick a setting (the voice says which, and its value)
  left thumbstick up/down       change it (hold to keep changing)
  X                             a new puck, on your blade
  hold the left thumbstick in   (1 s) put the net straight in front of you again
  B                             say the current setting again
  A                             save the settings (sandbox_settings.json, used next time)

Settings: stick length, lie, curve depth, face open, flex, blade turn / stick tilt / stick
swing (the fit in your hand), ice friction, blade pop, blade grip, buzz strength.

The puck physics (puck.py) runs at 1 kHz, four substeps per controller sample, with the blade
flexing on the shaft. Any part of the blade at or below the ice counts as on the ice. Every
puck contact buzzes the hands holding the stick.

Quit the app in the headset (or Ctrl+C) to end. Everything is recorded to data/<timestamp>/:
rec.csv (controllers), puck.csv (puck, 200 Hz), events.jsonl (settings, goals, shots), meta.json.
"""

from __future__ import annotations

import _thread
import argparse
import collections
import ctypes
import datetime as dt
import json
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
import stickmath
import stickspec
from stickspec import INCH

HERE = Path(__file__).resolve().parent
SETTINGS_PATH = HERE / "sandbox_settings.json"
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


SETTINGS = (
    Setting("length_in", "stick length", 0.5, 44, 66, "{:.1f} inches"),
    Setting("lie", "lie", 0.5, 3, 8, "{:g}"),
    Setting("curve_in", "curve depth", 0.125, 0.0, 1.0, "{:.3g} inches"),
    Setting("face_open", "face open", 1, -10, 25, "{:.0f} degrees"),
    Setting("flex", "flex", 5, 30, 120, "{:.0f}"),
    Setting("roll", "blade turn", 2, -180, 180, "{:.0f} degrees"),
    Setting("pitch", "stick tilt", 2, -150, 90, "{:.0f} degrees"),
    Setting("yaw", "stick swing", 2, -90, 90, "{:.0f} degrees"),
    Setting("ice_mu", "ice friction", 0.005, 0.0, 0.1, "{:.3f}"),
    Setting("pop", "blade pop", 0.05, 0.0, 0.9, "{:.2f}"),
    Setting("grip", "blade grip", 0.05, 0.0, 1.0, "{:.2f}"),
    Setting("buzz", "buzz", 0.1, 0.0, 1.0, "{:.1f}"),
)


class Tuning:
    def __init__(self, base: stickspec.StickSpec, values: dict):
        self.base = base
        self.values = values
        self.i = 0

    @classmethod
    def defaults(cls, spec: stickspec.StickSpec, fit: grab.Fit, params: pk.Params) -> dict:
        return {"length_in": spec.length_m / INCH, "lie": spec.lie, "curve_in": spec.curve_depth_m / INCH,
                "face_open": spec.face_open_deg, "flex": spec.flex, "roll": fit.roll_deg, "pitch": fit.pitch_deg,
                "yaw": fit.yaw_deg, "ice_mu": params.ice_mu, "pop": params.blade_pop, "grip": params.blade_grip,
                "buzz": 0.6}

    def spec(self) -> stickspec.StickSpec:
        v = self.values
        return self.base.with_(length_m=v["length_in"] * INCH, lie=v["lie"], curve_depth_m=v["curve_in"] * INCH,
                               face_open_deg=v["face_open"], flex=v["flex"])

    def fit(self) -> grab.Fit:
        return grab.Fit(self.values["roll"], self.values["pitch"], self.values["yaw"])

    def apply(self, params: pk.Params) -> None:
        params.ice_mu = self.values["ice_mu"]
        params.blade_pop = self.values["pop"]
        params.blade_grip = self.values["grip"]

    @property
    def current(self) -> Setting:
        return SETTINGS[self.i]

    def describe(self) -> str:
        s = self.current
        return f"{s.label}, {s.fmt.format(self.values[s.key])}"

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


class Log:
    """events.jsonl and puck.csv, written from any thread."""

    def __init__(self, run_dir: Path):
        self.events = open(run_dir / "events.jsonl", "a", encoding="utf-8")
        self.puck = open(run_dir / "puck.csv", "w", encoding="utf-8")
        self.puck.write("t,px,py,pz,vx,vy,vz,impulse,stick,bend_mm\n")
        self.lock = threading.Lock()

    def event(self, t: float, kind: str, **data) -> None:
        with self.lock:
            self.events.write(json.dumps({"t": round(t, 4), "event": kind, **data}) + "\n")
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
        self._refresh()

    def _refresh(self) -> None:
        pl = self.play
        spec = pl.spec
        self.grab.configure(spec, pl.fit)
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
        state, R, p = self.grab.step(top, bot, pl.squeeze[spec.top_hand], pl.squeeze[spec.bottom_hand])
        pl.stick_state = state
        sim = pl.sim

        if pl.want_recenter and pl.head is not None:
            pl.want_recenter = False
            Rh, ph = pl.head
            f = -Rh[:, 2]
            sim.puck.rink = pk.Rink(origin=np.array([ph[0], 0.0, ph[2]]),
                                    fwd=np.array([f[0], 0.0, f[2]]) / max(np.hypot(f[0], f[2]), 1e-6))
            self.log.event(t, "rink", **sim.puck.rink.to_dict())
            pl.want_puck = True
        held = R is not None and state in grab.HELD
        if pl.want_puck or (self.respawn_at is not None and t >= self.respawn_at):
            spot = self._blade_spot(R, p) if held else self._front_spot()
            if spot is not None:
                sim.puck.spawn(spot[[0, 2]])
                pl.want_puck, self.respawn_at, self.slow_since, self.shot = False, None, None, None
                self.log.event(t, "puck", at=spot.round(3).tolist())

        if held:
            bot_e = self.edge_b @ R.T + p
            top_e = self.edge_t @ R.T + p
            imp = sim.step(dt_s, bot_e, top_e, R @ self.sweet + p, R @ self.u)
        else:
            imp = sim.step(dt_s, None, None)
        pz = sim.puck

        # feel: every contact buzzes the hands holding the stick
        if imp > 0.15 and (t - self.last_buzz > 0.02 or imp > 3.0):
            self.last_buzz = t
            amp = float(np.clip(imp / 6.0, 0.08, 1.0)) * self.play.tuning.values["buzz"]
            hands = [spec.top_hand if h == "top" else spec.bottom_hand for h in HOLDERS.get(state, ())]
            if amp > 0 and hands:
                pl.haptics.put((amp, hands))
        # shots: a hard contact, then call the speed once it's away
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
        for kind, speed in pz.events:
            self.log.event(t, kind, ms=round(speed, 2))
            if kind == "goal":
                self.voice.say(f"Goal! {pz.goals}", key="goal")
                pl.haptics.put((1.0, [spec.top_hand, spec.bottom_hand]))
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
        self.tick += 1
        if self.tick % 5 == 0:
            P, V = pz.pos, pz.vel
            b = np.linalg.norm(sim.bend) * 1000
            self.log.puck_row(f"{t:.4f},{P[0]:.4f},{P[1]:.4f},{P[2]:.4f},{V[0]:.3f},{V[1]:.3f},{V[2]:.3f},"
                              f"{imp:.3f},{state},{b:.1f}\n")


# ----------------------------------------------------------------------------- drawing


WHITE, RED, BLUE = (0.92, 0.92, 0.92), (0.95, 0.2, 0.2), (0.3, 0.5, 1.0)


def scene(play: Play, rink: pk.Rink, poses: dict, held: dict, stick, state: int) -> np.ndarray:
    v = []

    def line(a, b, c):
        v.append((*a, *c))
        v.append((*b, *c))

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
    # the puck
    P = play.sim.puck.pos
    ang = np.linspace(0, 2 * np.pi, 17)
    ring = np.stack([np.cos(ang), np.zeros_like(ang), np.sin(ang)], axis=1) * pk.R
    for y in (P[1] - pk.H / 2, P[1] + pk.H / 2):
        pts = ring + np.array([P[0], y, P[2]])
        for p0, p1 in zip(pts, pts[1:]):
            line(p0, p1, WHITE)
    for k in range(0, 16, 4):
        line(ring[k] + P - [0, pk.H / 2, 0], ring[k] + P + [0, pk.H / 2, 0], WHITE)
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
        grip_s = spec.length_m - spec.grip_from_top_m
        s = np.linspace(spec.length_m, 0, 12)
        xi = np.clip((grip_s - s) / grip_s, 0, 1)
        pts = (s[:, None] * spec.u) @ R.T + p + (xi ** 2)[:, None] * bend
        for p0, p1 in zip(pts, pts[1:]):
            line(p0, p1, shaft_c)
        for frac in (0.0, 0.33, 0.66, 1.0):
            e = spec.edge(9, frac=frac) @ R.T + p + bend
            for p0, p1 in zip(e, e[1:]):
                line(p0, p1, blade_c)
        bot = spec.edge(5) @ R.T + p + bend
        top = spec.edge(5, top=True) @ R.T + p + bend
        for b0, t0 in zip(bot, top):
            line(b0, t0, blade_c)
    return np.asarray(v, dtype=np.float32)


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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--height", default="5'8\"")
    ap.add_argument("--shoots", choices=("left", "right"), default="left")
    ap.add_argument("--fresh", action="store_true", help="ignore sandbox_settings.json and start from defaults")
    ap.add_argument("--no-voice", action="store_true")
    ap.add_argument("--notes", default="")
    args = ap.parse_args()

    base = stickspec.from_height(stickspec.parse_height(args.height), args.shoots)
    fit = grab.Fit.load(record.FIT_PATH) or grab.Fit()
    values = Tuning.defaults(base, fit, pk.Params())
    if SETTINGS_PATH.exists() and not args.fresh:
        values.update(json.loads(SETTINGS_PATH.read_text())["values"])
    play = Play(Tuning(base, values))
    run_dir = HERE / "data" / ("sandbox-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
    lock = record.take_lock()
    try:
        run(args, play, run_dir)
    except xr.FormFactorUnavailableError:
        raise SystemExit("Headset not connected: put it on, start Link, then run again (xrcheck.py tells you).")
    finally:
        lock.unlink(missing_ok=True)


def run(args, play: Play, run_dir: Path) -> None:
    voice = VoiceQueue(record.Voice(not args.no_voice))
    voice.start()
    provider = GLFWOffscreenContextProvider()
    with ContextObject(
        context_provider=provider,
        instance_create_info=xr.InstanceCreateInfo(
            application_info=xr.ApplicationInfo(application_name="vr-hockey-sandbox", engine_name="none"),
            enabled_extension_names=[xr.KHR_OPENGL_ENABLE_EXTENSION_NAME,
                                     xr.KHR_WIN32_CONVERT_PERFORMANCE_COUNTER_TIME_EXTENSION_NAME],
        ),
        reference_space_create_info=xr.ReferenceSpaceCreateInfo(reference_space_type=xr.ReferenceSpaceType.STAGE),
    ) as ctx:
        run_dir.mkdir(parents=True, exist_ok=False)
        log = Log(run_dir)
        meta = {"created": dt.datetime.now().isoformat(timespec="seconds"), "kind": "sandbox", "notes": args.notes,
                "runtime": xr.get_instance_properties(ctx.instance).runtime_name.decode(),
                "system": xr.get_system_properties(ctx.instance, ctx.system_id).system_name.decode(),
                "settings_start": dict(play.tuning.values), "rate_hz": 1000, "lag_ms": 0, "space": "stage"}
        print(f"sandbox: {meta['system']} | recording to {run_dir}")
        inputs = record.Inputs(ctx)
        renderer = record.LineRenderer()
        sampler = record.Sampler(ctx, inputs.spaces, inputs.head, 1000, 0, play, run_dir / "rec.csv")
        physics = Physics(play, voice, log)
        sampler.on_tick = physics
        sampler.start()

        def watchdog():                              # the frame loop stalls while the headset sleeps
            while True:
                time.sleep(5)
                if time.time() - play.last_focus > AWAY_LIMIT_S:
                    print(f"  away for {AWAY_LIMIT_S} s: ending", flush=True)
                    _thread.interrupt_main()
                    return
        threading.Thread(target=watchdog, daemon=True, name="watchdog").start()
        voice.say("Sandbox. Squeeze the grips to hold the stick. Left stick left and right picks a setting, "
                  "up and down changes it. X gives you a new puck.")

        sync_info = xr.ActionsSyncInfo(active_action_sets=[xr.ActiveActionSet(action_set=ctx.default_action_set)])
        disp_loc = [xr.SpaceLocation() for _ in inputs.spaces]   # no velocity chain: a temporary one dangles
        head_loc = xr.SpaceLocation()
        dgrab = grab.Grab(play.spec, play.fit)
        version = play.version
        pick, change = Stick(), Stick()
        prev = {"x": False, "a": False, "b": False, "lclick": False}
        last_change, announced = 0.0, True
        click_since, click_done = None, False
        last_status, away_since = 0.0, None
        rink_set = False
        try:
            for frame_state in ctx.frame_loop():
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
                poses = {}
                for dev, space, loc in zip(recfmt.CONTROLLERS, inputs.spaces, disp_loc):
                    r = xr.check_result(xr.raw_functions.xrLocateSpace(space, ctx.space, t_disp, ctypes.byref(loc)))
                    if not r.is_exception() and (loc._location_flags & record.NEED_POSE) == record.NEED_POSE:
                        o, q = loc.pose.orientation, loc.pose.position
                        poses[dev] = (stickmath.quat_to_mat(np.array([o.x, o.y, o.z, o.w])), np.array([q.x, q.y, q.z]))
                r = xr.check_result(xr.raw_functions.xrLocateSpace(inputs.head, ctx.space, t_disp, ctypes.byref(head_loc)))
                if not r.is_exception() and (head_loc._location_flags & record.NEED_POSE) == record.NEED_POSE:
                    o, q = head_loc.pose.orientation, head_loc.pose.position
                    play.head = (stickmath.quat_to_mat(np.array([o.x, o.y, o.z, o.w])), np.array([q.x, q.y, q.z]))
                    if not rink_set:
                        play.want_recenter, rink_set = True, True

                # ---- tuning and buttons
                tu = play.tuning
                lx, ly = inp["lthumb"]
                horiz = abs(lx) > abs(ly) + 0.25          # only a clearly sideways push picks a setting,
                vert = abs(ly) > abs(lx) + 0.25           # only a clearly up/down push changes it
                d = pick.update(lx if horiz else 0.0, now)
                if d:
                    tu.pick(d)
                    voice.say(tu.describe(), key="setting")
                    announced = True
                d = change.update(ly if vert else 0.0, now)
                if d and tu.change(d):
                    play.retune()
                    last_change, announced = now, False
                    log.event(sampler.shared.t_now, "setting", key=tu.current.key, value=tu.values[tu.current.key])
                if not announced and now - last_change > 0.5:
                    voice.say(tu.describe(), key="setting")
                    announced = True
                if inp["x"] and not prev["x"]:
                    play.want_puck = True
                # the net moves only on a deliberate 1 s press of the stick (pushing it hard clicks it)
                if inp["lclick"]:
                    click_since = click_since or now
                    if now - click_since > 1.0 and not click_done:
                        play.want_recenter, click_done = True, True
                        voice.say("Net in front of you.", key="rink")
                else:
                    click_since, click_done = None, False
                if inp["b"] and not prev["b"]:
                    voice.say(tu.describe(), key="setting")
                if inp["a"] and not prev["a"]:
                    SETTINGS_PATH.write_text(json.dumps({"values": tu.values, "spec": play.spec.to_dict()}, indent=2))
                    play.fit.save(record.FIT_PATH, play.spec)
                    voice.say("Saved.", key="saved")
                    log.event(sampler.shared.t_now, "saved", values=dict(tu.values))
                for k in prev:
                    prev[k] = inp[k]

                # ---- the stick for display, and the buzz
                if play.version != version:
                    dgrab.configure(play.spec, play.fit)
                    version = play.version
                top, bot = play.spec.top_hand, play.spec.bottom_hand
                state, R, p = dgrab.step(poses.get(top), poses.get(bot), play.squeeze[top], play.squeeze[bot])
                buzz: dict = {}
                while not play.haptics.empty():
                    amp, hands = play.haptics.get_nowait()
                    for h in hands:
                        buzz[h] = max(buzz.get(h, 0.0), amp)
                for h, amp in buzz.items():
                    inputs.buzz(h, amp, 15)

                held = {top: dgrab.on["t"], bot: dgrab.on["b"]}
                verts = scene(play, play.sim.puck.rink, poses, held, (R, p), state)
                for view in ctx.view_loop(frame_state):
                    proj = np.asarray(Matrix4x4f.create_projection_fov(GraphicsAPI.OPENGL, view.fov, 0.05, 100.0).m)
                    renderer.draw(verts, proj @ record.view_matrix(view.pose), (0.05, 0.06, 0.09))
                if now - last_status > 2:
                    last_status = now
                    pz = play.sim.puck
                    print(f"  t={play.t_now:6.1f}s  samples/s={sampler.n / max(play.t_now, 1e-9):.0f}  "
                          f"stick={grab.STATE_NAMES[play.stick_state]:<12} puck {pz.speed:5.1f} m/s  "
                          f"goals={pz.goals}  setting: {tu.describe()}", flush=True)
        except KeyboardInterrupt:
            print("stopped with Ctrl+C")
        finally:
            sampler.stop_evt.set()
            sampler.join(timeout=5)
            pz = play.sim.puck
            meta.update(samples=sampler.n, settings_end=dict(play.tuning.values), spec=play.spec.to_dict(),
                        fit=play.fit.to_dict(), params=play.params.to_dict(), rink=pz.rink.to_dict(),
                        goals=pz.goals, shots_mph=physics.shots, phases=[], completed=True, ended="quit")
            recfmt.write_meta(run_dir, meta)
            log.close()
    print(f"saved {run_dir}")


if __name__ == "__main__":
    main()
