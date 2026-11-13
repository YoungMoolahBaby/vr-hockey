"""Spike 0 recorder: a virtual stick held with the controllers' grip buttons, sampled at ~1 kHz.

Headset on over Link, a controller in each hand (wrist straps on), then:

    uv run python record.py --notes "Quest 3, cable Link"
    uv run python record.py --refit              # fit the stick in your right hand again
    uv run python record.py --height 5'8 --shoots left --lie 5
    uv run python record.py --no-slap            # skip the slap shots
    uv run python record.py --only stickhandle   # just some phases

The stick is sized from your height (stickspec.py). The first time, the voice walks you
through fitting it in your right hand: right thumbstick left/right turns the blade, up/down
tilts the stick, hold B + left/right swings it sideways, A saves (stick_fit.json; reused next
time). Then the grip buttons hold the stick: right only, both, or left only with the top hand
off (grab.py). Each grab gives a short buzz.

A voice (through the default audio device, i.e. the headset on Link) walks you through the
phases. Three low beeps = get ready, high beep = go, two falling beeps = stop.
In the headset: a floor grid as the ice (green while a phase records), each hand's axes (a
green cross while that hand grips), and the stick: shaft white, blade outline yellow.

Output: data/<timestamp>/rec.csv + meta.json. Then: uv run python analyze.py data/<timestamp>
"""

from __future__ import annotations

import _thread
import argparse
import collections
import csv
import ctypes
import datetime as dt
import os
import subprocess
import threading
import time
import winsound
from ctypes import wintypes
from pathlib import Path

import glfast  # noqa: F401  (first: PyOpenGL's error checking off, read when xr loads it)
import numpy as np
import xr
from OpenGL import GL
from xr.utils.gl import ContextObject
from xr.utils.gl.glfw_util import GLFWOffscreenContextProvider
from xr.utils.matrix4x4f import GraphicsAPI, Matrix4x4f

import grab
import protocol
import recfmt
import stickmath
import stickspec

HERE = Path(__file__).resolve().parent
FIT_PATH = HERE / "stick_fit.json"
NEED_POSE = recfmt.FLAG_POS_VALID | recfmt.FLAG_ORI_VALID
HAND = {"l": "left", "r": "right"}
DEADZONE = 0.2
RATES_DEG_S = {"roll": 70.0, "pitch": 40.0, "yaw": 40.0}   # at full thumbstick


# ----------------------------------------------------------------------------- voice


class Voice:
    """Blocking text-to-speech through Windows' built-in voice, plus beeps."""

    PS = ("Add-Type -AssemblyName System.Speech; "
          "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Rate = 1; "
          "$s.Speak($env:SPIKE0_SAY)")

    def __init__(self, enabled: bool):
        self.enabled = enabled

    def say(self, text: str) -> None:
        print(f"[voice] {text}", flush=True)
        if not self.enabled:
            time.sleep(min(4.0, 0.05 * len(text)))
            return
        env = dict(os.environ, SPIKE0_SAY=text)
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", self.PS],
                       env=env, check=False, creationflags=subprocess.CREATE_NO_WINDOW)

    @staticmethod
    def get_ready() -> None:
        for _ in range(3):
            winsound.Beep(500, 120)
            time.sleep(0.88)
        winsound.Beep(1000, 300)

    @staticmethod
    def stop() -> None:
        winsound.Beep(1000, 150)
        winsound.Beep(700, 300)


# ----------------------------------------------------------------------------- shared state


class Shared:
    def __init__(self, spec: stickspec.StickSpec, fit: grab.Fit, need_fit: bool):
        self.spec = spec
        self.fit = fit
        self.need_fit = need_fit
        self.fitting = False
        self.fit_done = threading.Event()
        self.grab = grab.Grab(spec, fit)
        self.phase = recfmt.GAP
        self.active = False
        self.done = False
        self.squeeze = {d: 0.0 for d in recfmt.CONTROLLERS}
        self.latest_flags = {d: 0 for d in recfmt.CONTROLLERS}
        self.phase_log: list[dict] = []
        self.t_now = 0.0
        self.is_focused = lambda: False   # set once the session exists
        self.ended = ""                   # why the protocol stopped
        self.exited = False               # the main loop has left the frame loop


# ----------------------------------------------------------------------------- sampler


class Sampler(threading.Thread):
    """Locates both controllers and the head at a fixed rate, at the current time (minus a lag)."""

    def __init__(self, ctx, ctrl_spaces, head_space, rate_hz, lag_ms, shared, csv_path):
        super().__init__(daemon=True, name="sampler")
        self.inst = ctx.instance
        self.base = ctx.space
        self.ctrl_spaces = ctrl_spaces
        self.head_space = head_space
        self.period = 1.0 / rate_hz
        self.lag_ns = int(lag_ms * 1e6)
        self.shared = shared
        self.stop_evt = threading.Event()
        self.buf: collections.deque = collections.deque()
        self.n = 0
        self.errors = 0
        self.writer = threading.Thread(target=self._write_loop, args=(csv_path,), daemon=True, name="writer")
        self.on_tick = None      # optional: on_tick(t_s, {dev: (R, p) or None}) after each sample (the sandbox physics)
        self.rig = None          # optional rig.Rig (thumbstick locomotion): poses are recorded and ticked in the world
        # sample where the hands will be when the frame is on the display (shared.ahead_ns, kept by the
        # render loop), not where they are now: the physics then moves the stick the headset draws,
        # not one ~40 ms behind it (a puck that followed a blade you'd seen leave it)
        self.predict = False
        self.qpc_freq = wintypes.LARGE_INTEGER()
        ctypes.windll.kernel32.QueryPerformanceFrequency(ctypes.byref(self.qpc_freq))
        # reusable output structs: location -> velocity chain for controllers, plain for the head
        self.vel = [xr.SpaceVelocity() for _ in ctrl_spaces]
        self.loc = [xr.SpaceLocation(next=v) for v in self.vel]
        self.head_loc = xr.SpaceLocation()

    def _write_loop(self, csv_path):
        with open(csv_path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(recfmt.COLUMNS)
            while not (self.stop_evt.is_set() and not self.buf):
                time.sleep(0.25)
                rows = [self.buf.popleft() for _ in range(len(self.buf))]
                if rows:
                    w.writerows(rows)
                    fh.flush()

    def _locate(self, space, loc, t):
        res = xr.check_result(xr.raw_functions.xrLocateSpace(space, self.base, t, ctypes.byref(loc)))
        if res.is_exception():
            self.errors += 1
            return False
        return True

    def run(self):
        self.writer.start()
        qpc = wintypes.LARGE_INTEGER()
        kernel = ctypes.windll.kernel32
        freq = self.qpc_freq.value
        kernel.QueryPerformanceCounter(ctypes.byref(qpc))
        qpc0 = qpc.value
        next_t = time.perf_counter()
        sh = self.shared
        while not self.stop_evt.is_set():
            kernel.QueryPerformanceCounter(ctypes.byref(qpc))
            t_s = (qpc.value - qpc0) / freq
            xt = xr.convert_win32_performance_counter_to_time_khr(self.inst, qpc).value - self.lag_ns
            if self.predict:
                xt += int(sh.ahead_ns)
            row = [round(t_s, 6), xt, sh.phase]
            tick = {}
            rp = self.rig.at(xt * 1e-9) if self.rig is not None and self.rig.moved else None
            if rp is not None:                   # your body's motion, for the physics' soft hands
                sh.body = (rp.vel[0], rp.vel[2], rp.omega, rp.pivot[0], rp.pivot[2])
                sh.rig_yaw = rp.yaw              # and your turn (a snap turn carries the puck on your blade)
            for dev, space, loc, vel in zip(recfmt.CONTROLLERS, self.ctrl_spaces, self.loc, self.vel):
                squeeze = round(sh.squeeze[dev], 3)
                if self._locate(space, loc, xt):
                    f = loc._location_flags
                    po, pp = loc.pose.orientation, loc.pose.position
                    lv, av = vel.linear_velocity, vel.angular_velocity
                    P, Q = (pp.x, pp.y, pp.z), (po.x, po.y, po.z, po.w)
                    LV, AV = (lv.x, lv.y, lv.z), (av.x, av.y, av.z)
                    if rp is not None:                 # the room, moved by the thumbsticks, into the world
                        P, Q = rp.point(*P), rp.quat(*Q)
                        LV, AV = rp.velocity(P, *LV), rp.spin(*AV)
                    row += [f, round(P[0], 6), round(P[1], 6), round(P[2], 6),
                            round(Q[0], 7), round(Q[1], 7), round(Q[2], 7), round(Q[3], 7),
                            vel._velocity_flags, round(LV[0], 5), round(LV[1], 5), round(LV[2], 5),
                            round(AV[0], 5), round(AV[1], 5), round(AV[2], 5), squeeze]
                    sh.latest_flags[dev] = f
                    if self.on_tick is not None and (f & NEED_POSE) == NEED_POSE:
                        tick[dev] = (stickmath.quat_to_mat(np.array(Q)), np.array(P))
                else:
                    row += [0] * (len(recfmt.CTRL_FIELDS) - 1) + [squeeze]
                    sh.latest_flags[dev] = 0
            if self._locate(self.head_space, self.head_loc, xt):
                hl = self.head_loc
                po, pp = hl.pose.orientation, hl.pose.position
                P, Q = (pp.x, pp.y, pp.z), (po.x, po.y, po.z, po.w)
                if rp is not None:
                    P, Q = rp.point(*P), rp.quat(*Q)
                row += [hl._location_flags, round(P[0], 6), round(P[1], 6), round(P[2], 6),
                        round(Q[0], 7), round(Q[1], 7), round(Q[2], 7), round(Q[3], 7)]
            else:
                row += [0] * len(recfmt.HEAD_FIELDS)
            self.buf.append(row)
            self.n += 1
            sh.t_now = t_s
            if self.on_tick is not None:
                self.on_tick(t_s, tick)
            next_t += self.period
            delay = next_t - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
            elif delay < -0.05:          # fell far behind (GC, stall): don't burst to catch up
                next_t = time.perf_counter()
        self.writer.join()


# ----------------------------------------------------------------------------- protocol


AWAY_LIMIT_S = 120   # out of the app (headset off, quit to home) this long ends the session


class SessionEnded(Exception):
    pass


def wait_focus(shared: Shared, voice: Voice) -> None:
    """Block while the app is not in front in the headset; give up after AWAY_LIMIT_S."""
    if shared.is_focused():
        return
    print("  paused: the app is not in focus in the headset", flush=True)
    t0 = time.time()
    while not shared.is_focused():
        if time.time() - t0 > AWAY_LIMIT_S:
            raise SessionEnded(f"away from the app for {AWAY_LIMIT_S} s")
        time.sleep(0.1)
    voice.say("Welcome back. Continuing.")


def run_protocol(shared: Shared, voice: Voice, phases: list[protocol.Phase]) -> None:
    try:
        _run_protocol(shared, voice, phases)
        voice.say("All done. Thank you. You can take the headset off.")
        shared.ended = "completed"
    except SessionEnded as e:
        print(f"  ending: {e}", flush=True)
        shared.ended = str(e)
    shared.done = True
    time.sleep(2.0)
    if not shared.exited:            # the frame loop only notices `done` while the app is in focus
        _thread.interrupt_main()


def _run_protocol(shared: Shared, voice: Voice, phases: list[protocol.Phase]) -> None:
    t_wait, t_start, ok_since = time.time(), time.time(), None
    while True:  # both controllers tracked for a full second
        ok = all((shared.latest_flags[d] & NEED_POSE) == NEED_POSE for d in recfmt.CONTROLLERS)
        ok_since = (ok_since or time.time()) if ok else None
        if ok_since and time.time() - ok_since > 1.0:
            break
        if time.time() - t_start > AWAY_LIMIT_S:
            raise SessionEnded(f"no controllers for {AWAY_LIMIT_S} s")
        if time.time() - t_wait > 15:
            missing = [HAND[d] for d in recfmt.CONTROLLERS
                       if (shared.latest_flags[d] & NEED_POSE) != NEED_POSE]
            voice.say(f"Waiting for the {' and '.join(missing)} controller. Wake it up by moving it.")
            t_wait = time.time()
        time.sleep(0.05)
    spec = shared.spec
    voice.say(f"Both controllers found. Your stick: {spec.length_m / stickspec.INCH:.0f} inches, lie "
              f"{spec.lie:g}, {spec.shoots} shot.")

    if shared.need_fit:
        shared.phase, shared.fitting = "fit", True
        voice.say(protocol.FIT_SAY)
        while not shared.fit_done.wait(0.2):
            wait_focus(shared, voice)
        shared.fitting, shared.phase = False, recfmt.GAP
        shared.fit.save(FIT_PATH, spec)
        f = shared.fit
        voice.say(f"Saved. Blade turned {f.roll_deg:.0f}, tilted {f.pitch_deg:.0f}, swung {f.yaw_deg:.0f} degrees.")
    else:
        voice.say("Using your saved stick fit. Run with refit to change it.")
    voice.say("Each step: listen, three low beeps, then a high beep means go. Two falling beeps mean stop.")

    for ph in phases:
        attempt = 0
        while True:                  # an interrupted step is done again
            attempt += 1
            label = ph.name if attempt == 1 else f"{ph.name}#{attempt}"
            wait_focus(shared, voice)
            voice.say(ph.say)
            time.sleep(0.5)
            voice.get_ready()
            start = shared.t_now
            shared.phase, shared.active = label, True
            t_end, interrupted = time.time() + ph.seconds, False
            while time.time() < t_end:
                if not shared.is_focused():
                    interrupted = True
                    break
                time.sleep(0.05)
            shared.phase, shared.active = recfmt.GAP, False
            shared.phase_log.append({"label": label, "name": ph.name, "start_t": start, "end_t": shared.t_now,
                                     "interrupted": interrupted})
            if not interrupted:
                voice.stop()
                break
            print(f"  {label} interrupted; it will be redone", flush=True)


# ----------------------------------------------------------------------------- input


class Inputs:
    """Grip poses, squeeze (grip button), both thumbsticks, A/B/X/Y, both triggers, and haptics."""

    PROFILE = "/interaction_profiles/oculus/touch_controller"

    def __init__(self, ctx):
        self.ctx = ctx
        inst = ctx.instance
        self.hand = {"l": xr.string_to_path(inst, "/user/hand/left"),
                     "r": xr.string_to_path(inst, "/user/hand/right")}
        both = [self.hand["l"], self.hand["r"]]
        right = [self.hand["r"]]

        def make(name, kind, subs):
            return xr.create_action(
                action_set=ctx.default_action_set,
                create_info=xr.ActionCreateInfo(action_type=kind, action_name=name, localized_action_name=name,
                                                count_subaction_paths=len(subs),
                                                subaction_paths=(xr.Path * len(subs))(*subs)))

        A = xr.ActionType
        self.pose = make("grip_pose", A.POSE_INPUT, both)
        self.squeeze = make("squeeze", A.FLOAT_INPUT, both)
        self.thumb = make("thumbstick", A.VECTOR2F_INPUT, right)
        self.a = make("a_button", A.BOOLEAN_INPUT, right)
        self.b = make("b_button", A.BOOLEAN_INPUT, right)
        left = [self.hand["l"]]
        self.x = make("x_button", A.BOOLEAN_INPUT, left)
        self.y = make("y_button", A.BOOLEAN_INPUT, left)
        self.lthumb = make("left_thumbstick", A.VECTOR2F_INPUT, left)
        self.lclick = make("left_thumbstick_click", A.BOOLEAN_INPUT, left)
        self.ltrigger = make("left_trigger", A.FLOAT_INPUT, left)
        self.rtrigger = make("right_trigger", A.FLOAT_INPUT, right)
        self.haptic = make("haptic", A.VIBRATION_OUTPUT, both)
        pairs = [(self.pose, "/user/hand/left/input/grip/pose"), (self.pose, "/user/hand/right/input/grip/pose"),
                 (self.squeeze, "/user/hand/left/input/squeeze/value"),
                 (self.squeeze, "/user/hand/right/input/squeeze/value"),
                 (self.thumb, "/user/hand/right/input/thumbstick"),
                 (self.a, "/user/hand/right/input/a/click"), (self.b, "/user/hand/right/input/b/click"),
                 (self.x, "/user/hand/left/input/x/click"), (self.y, "/user/hand/left/input/y/click"),
                 (self.lthumb, "/user/hand/left/input/thumbstick"),
                 (self.lclick, "/user/hand/left/input/thumbstick/click"),
                 (self.ltrigger, "/user/hand/left/input/trigger/value"),
                 (self.rtrigger, "/user/hand/right/input/trigger/value"),
                 (self.haptic, "/user/hand/left/output/haptic"), (self.haptic, "/user/hand/right/output/haptic")]
        bindings = (xr.ActionSuggestedBinding * len(pairs))(
            *[xr.ActionSuggestedBinding(act, xr.string_to_path(inst, path)) for act, path in pairs])
        xr.suggest_interaction_profile_bindings(
            instance=inst,
            suggested_bindings=xr.InteractionProfileSuggestedBinding(
                interaction_profile=xr.string_to_path(inst, self.PROFILE),
                count_suggested_bindings=len(pairs), suggested_bindings=bindings))
        self.spaces = [xr.create_action_space(session=ctx.session,
                                              create_info=xr.ActionSpaceCreateInfo(action=self.pose, subaction_path=h))
                       for h in both]
        self.head = xr.create_reference_space(
            session=ctx.session,
            create_info=xr.ReferenceSpaceCreateInfo(reference_space_type=xr.ReferenceSpaceType.VIEW))

    def _info(self, action, dev):
        return xr.ActionStateGetInfo(action=action, subaction_path=self.hand[dev])

    def read(self) -> dict:
        s = self.ctx.session
        out = {"squeeze": {}, "thumb": (0.0, 0.0), "a": False, "b": False,
               "x": False, "y": False, "lthumb": (0.0, 0.0), "lclick": False, "ltrigger": 0.0, "rtrigger": 0.0}
        try:
            for d in ("l", "r"):
                st = xr.get_action_state_float(s, self._info(self.squeeze, d))
                out["squeeze"][d] = float(st.current_state) if st.is_active else 0.0
            v = xr.get_action_state_vector2f(s, self._info(self.thumb, "r"))
            out["thumb"] = (v.current_state.x, v.current_state.y) if v.is_active else (0.0, 0.0)
            out["a"] = bool(xr.get_action_state_boolean(s, self._info(self.a, "r")).current_state)
            out["b"] = bool(xr.get_action_state_boolean(s, self._info(self.b, "r")).current_state)
            out["x"] = bool(xr.get_action_state_boolean(s, self._info(self.x, "l")).current_state)
            out["y"] = bool(xr.get_action_state_boolean(s, self._info(self.y, "l")).current_state)
            v = xr.get_action_state_vector2f(s, self._info(self.lthumb, "l"))
            out["lthumb"] = (v.current_state.x, v.current_state.y) if v.is_active else (0.0, 0.0)
            out["lclick"] = bool(xr.get_action_state_boolean(s, self._info(self.lclick, "l")).current_state)
            st = xr.get_action_state_float(s, self._info(self.ltrigger, "l"))
            out["ltrigger"] = float(st.current_state) if st.is_active else 0.0
            st = xr.get_action_state_float(s, self._info(self.rtrigger, "r"))
            out["rtrigger"] = float(st.current_state) if st.is_active else 0.0
        except xr.XrException:
            pass
        return out

    def buzz(self, dev: str, amplitude: float = 0.6, ms: float = 25) -> None:
        try:
            xr.apply_haptic_feedback(self.ctx.session, xr.HapticActionInfo(action=self.haptic,
                                                                           subaction_path=self.hand[dev]),
                                     xr.HapticVibration(duration=int(ms * 1e6), frequency=xr.FREQUENCY_UNSPECIFIED,
                                                        amplitude=amplitude))
        except xr.XrException:
            pass


def apply_thumbstick(fit: grab.Fit, thumb, b_held: bool, dt: float) -> grab.Fit:
    def shaped(v):
        m = abs(v)
        return 0.0 if m < DEADZONE else np.sign(v) * (m - DEADZONE) / (1 - DEADZONE)
    x, y = shaped(thumb[0]), shaped(thumb[1])
    if b_held:
        return grab.Fit(fit.roll_deg, fit.pitch_deg, fit.yaw_deg + x * RATES_DEG_S["yaw"] * dt)
    return grab.Fit(fit.roll_deg + x * RATES_DEG_S["roll"] * dt, fit.pitch_deg + y * RATES_DEG_S["pitch"] * dt,
                    fit.yaw_deg)


# ----------------------------------------------------------------------------- rendering

VS = """#version 410
layout(location = 0) in vec3 pos;
layout(location = 1) in vec3 col;
uniform mat4 mvp;
out vec3 vcol;
void main() { gl_Position = mvp * vec4(pos, 1.0); vcol = col; }
"""
FS = """#version 410
in vec3 vcol;
out vec4 frag;
void main() { frag = vec4(vcol, 1.0); }
"""


TUNNEL_VS = """#version 410
layout(location = 0) in vec3 pa;
out float va;
void main() { gl_Position = vec4(pa.xy, 0.0, 1.0); va = pa.z; }
"""
TUNNEL_FS = """#version 410
in float va;
out vec4 frag;
void main() { frag = vec4(0.0, 0.0, 0.0, va); }
"""

# Models (gear.Model: the skates), drawn many times each: one copy per instance matrix. Lit from a
# light overhead (the rink's ring of light) and from below by the white ice, with a highlight that
# shows the shape of black carbon. Colours are linear, like everything drawn (theme.srgb).
MESH_VS = """#version 410
layout(location = 0) in vec3 pos;
layout(location = 1) in vec3 nrm;
layout(location = 2) in vec3 col;
layout(location = 3) in float shine;
layout(location = 4) in mat4 model;
uniform mat4 mvp;
out vec3 wpos;
out vec3 wn;
out vec3 vcol;
out float vshine;
void main() {
    vec4 w = model * vec4(pos, 1.0);
    wpos = w.xyz;
    wn = mat3(model) * nrm;
    vcol = col;
    vshine = shine;
    gl_Position = mvp * w;
}
"""
MESH_FS = """#version 410
in vec3 wpos;
in vec3 wn;
in vec3 vcol;
in float vshine;
uniform vec3 eye;
out vec4 frag;
void main() {
    vec3 n = normalize(wn);
    if (!gl_FrontFacing) n = -n;                  // inside a part, seen through an opening
    vec3 v = normalize(eye - wpos);
    vec3 l = normalize(vec3(0.3, 1.0, 0.25));
    float sky = 0.5 + 0.5 * n.y;
    vec3 amb = vcol * mix(0.55, 0.8, sky);        // the white ice lights things from below too
    float d = max(dot(n, l), 0.0);
    float spec = pow(max(dot(n, normalize(l + v)), 0.0), 40.0) * vshine;
    float rim = pow(1.0 - max(dot(n, v), 0.0), 3.0) * 0.12 * vshine;
    frag = vec4(amb * 0.6 + vcol * 0.6 * d + vec3(0.45 * spec + rim), 1.0);
}
"""


def tunnel_mesh(strength: float, n: int = 48) -> np.ndarray:
    """The comfort vignette in clip space: triangles (x, y, alpha), clear in the middle, fading to
    black toward the edges; stronger closes it in. strength 0-1."""
    s = float(np.clip(strength, 0.0, 1.0))
    r1 = 1.45 - 0.8 * s                    # fully dark from here out
    r0 = r1 - 0.35                         # clear inside this
    a = np.linspace(0, 2 * np.pi, n + 1)
    c, si = np.cos(a), np.sin(a)
    rings = [(r0, 0.0), (r1, 1.0), (3.0, 1.0)]
    tris = []
    for (ra, aa), (rb, ab) in zip(rings, rings[1:]):
        for k in range(n):
            p00 = (ra * c[k], ra * si[k], aa)
            p01 = (ra * c[k + 1], ra * si[k + 1], aa)
            p10 = (rb * c[k], rb * si[k], ab)
            p11 = (rb * c[k + 1], rb * si[k + 1], ab)
            tris += [p00, p10, p11, p00, p11, p01]
    return np.asarray(tris, dtype=np.float32)


def _compile(src, kind):
    s = GL.glCreateShader(kind)
    GL.glShaderSource(s, src)
    GL.glCompileShader(s)
    if not GL.glGetShaderiv(s, GL.GL_COMPILE_STATUS):
        raise RuntimeError(GL.glGetShaderInfoLog(s).decode())
    return s


class LineRenderer:
    """Solid triangles, then lines over them, into a 4x multisampled buffer that's resolved into the
    target (anti-aliased: thin lines and white edges against the dark shimmer less as you move)."""

    def __init__(self, samples: int = 4):
        self.samples = samples
        self._msaa = None                                # (width, height, framebuffer, renderbuffers)
        self.prog = GL.glCreateProgram()
        for src, kind in ((VS, GL.GL_VERTEX_SHADER), (FS, GL.GL_FRAGMENT_SHADER)):
            GL.glAttachShader(self.prog, _compile(src, kind))
        GL.glLinkProgram(self.prog)
        if not GL.glGetProgramiv(self.prog, GL.GL_LINK_STATUS):
            raise RuntimeError(GL.glGetProgramInfoLog(self.prog).decode())
        self.mvp_loc = GL.glGetUniformLocation(self.prog, "mvp")
        self.vao, self.vbo = self._buffers()
        self.tri_vao, self.tri_vbo = self._buffers()
        self._uploaded = None
        self._tris = None
        # the comfort vignette: its own little program, drawn over each eye's view
        self.tprog = GL.glCreateProgram()
        for src, kind in ((TUNNEL_VS, GL.GL_VERTEX_SHADER), (TUNNEL_FS, GL.GL_FRAGMENT_SHADER)):
            GL.glAttachShader(self.tprog, _compile(src, kind))
        GL.glLinkProgram(self.tprog)
        if not GL.glGetProgramiv(self.tprog, GL.GL_LINK_STATUS):
            raise RuntimeError(GL.glGetProgramInfoLog(self.tprog).decode())
        self.tvao = GL.glGenVertexArrays(1)
        self.tvbo = GL.glGenBuffers(1)
        GL.glBindVertexArray(self.tvao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.tvbo)
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 12, ctypes.c_void_p(0))
        GL.glBindVertexArray(0)
        self._tunnel = None
        # models (the skates): uploaded once each, then only their instance matrices every frame
        self.mprog = GL.glCreateProgram()
        for src, kind in ((MESH_VS, GL.GL_VERTEX_SHADER), (MESH_FS, GL.GL_FRAGMENT_SHADER)):
            GL.glAttachShader(self.mprog, _compile(src, kind))
        GL.glLinkProgram(self.mprog)
        if not GL.glGetProgramiv(self.mprog, GL.GL_LINK_STATUS):
            raise RuntimeError(GL.glGetProgramInfoLog(self.mprog).decode())
        self.m_mvp = GL.glGetUniformLocation(self.mprog, "mvp")
        self.m_eye = GL.glGetUniformLocation(self.mprog, "eye")
        self._models: dict = {}                          # id(model) -> (model, vao, index count, instance vbo)
        self._inst: dict = {}                            # id(model) -> the instances uploaded last

    def _model(self, model):
        """A gear.Model's buffers on the GPU (made on first use; models live as long as the program)."""
        got = self._models.get(id(model))
        if got is not None and got[0] is model:
            return got
        vao = GL.glGenVertexArrays(1)
        vbo, ibo, ivbo = GL.glGenBuffers(3)
        GL.glBindVertexArray(vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
        v = np.ascontiguousarray(model.vertices, dtype=np.float32)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, v.nbytes, v, GL.GL_STATIC_DRAW)
        for loc, n, off in ((0, 3, 0), (1, 3, 12), (2, 3, 24), (3, 1, 36)):     # pos, normal, colour, shine
            GL.glEnableVertexAttribArray(loc)
            GL.glVertexAttribPointer(loc, n, GL.GL_FLOAT, GL.GL_FALSE, 40, ctypes.c_void_p(off))
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, ibo)
        idx = np.ascontiguousarray(model.index, dtype=np.uint32)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, idx.nbytes, idx, GL.GL_STATIC_DRAW)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, ivbo)
        for k in range(4):                               # the instance matrix, a column per slot
            GL.glEnableVertexAttribArray(4 + k)
            GL.glVertexAttribPointer(4 + k, 4, GL.GL_FLOAT, GL.GL_FALSE, 64, ctypes.c_void_p(16 * k))
            GL.glVertexAttribDivisor(4 + k, 1)
        GL.glBindVertexArray(0)
        got = (model, vao, idx.size, ivbo)
        self._models[id(model)] = got
        return got

    def _draw_models(self, meshes, mvp32, eye) -> None:
        """meshes: (model, instances) pairs, instances (n, 4, 4) float32 model -> world, column-major."""
        GL.glUseProgram(self.mprog)
        GL.glUniformMatrix4fv(self.m_mvp, 1, GL.GL_TRUE, mvp32)
        GL.glUniform3f(self.m_eye, *(float(c) for c in (eye if eye is not None else (0.0, 10.0, 0.0))))
        for model, inst in meshes:
            if not len(inst):
                continue
            _, vao, count, ivbo = self._model(model)
            GL.glBindVertexArray(vao)
            if self._inst.get(id(model)) is not inst:     # the same frame's second eye: already there
                GL.glBindBuffer(GL.GL_ARRAY_BUFFER, ivbo)
                GL.glBufferData(GL.GL_ARRAY_BUFFER, inst.nbytes, inst, GL.GL_DYNAMIC_DRAW)
                self._inst[id(model)] = inst
            GL.glDrawElementsInstanced(GL.GL_TRIANGLES, count, GL.GL_UNSIGNED_INT, ctypes.c_void_p(0), len(inst))
        GL.glBindVertexArray(0)
        GL.glUseProgram(self.prog)

    @staticmethod
    def _buffers():
        """A vertex array and its buffer: rows of x, y, z, r, g, b."""
        vao, vbo = GL.glGenVertexArrays(1), GL.glGenBuffers(1)
        GL.glBindVertexArray(vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 24, ctypes.c_void_p(0))
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, 24, ctypes.c_void_p(12))
        GL.glBindVertexArray(0)
        return vao, vbo

    def _multisampled(self, w: int, h: int):
        """Our multisampled framebuffer at this size, or None (then draw straight into the target)."""
        if self.samples < 2:
            return None
        if self._msaa is not None and self._msaa[:2] == (w, h):
            return self._msaa[2]
        if self._msaa is not None:
            GL.glDeleteFramebuffers(1, [self._msaa[2]])
            GL.glDeleteRenderbuffers(2, list(self._msaa[3]))
            self._msaa = None
        n = min(self.samples, int(GL.glGetIntegerv(GL.GL_MAX_SAMPLES)))
        fbo = GL.glGenFramebuffers(1)
        rbs = GL.glGenRenderbuffers(2)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fbo)
        for rb, fmt, at in zip(rbs, (GL.GL_RGBA8, GL.GL_DEPTH_COMPONENT24),
                               (GL.GL_COLOR_ATTACHMENT0, GL.GL_DEPTH_ATTACHMENT)):
            GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, rb)
            GL.glRenderbufferStorageMultisample(GL.GL_RENDERBUFFER, n, fmt, w, h)
            GL.glFramebufferRenderbuffer(GL.GL_FRAMEBUFFER, at, GL.GL_RENDERBUFFER, rb)
        GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, 0)
        if GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER) != GL.GL_FRAMEBUFFER_COMPLETE:
            print(f"  multisampling unavailable ({n}x at {w}x{h}): drawing without it", flush=True)
            GL.glDeleteFramebuffers(1, [fbo])
            GL.glDeleteRenderbuffers(2, list(rbs))
            self.samples = 0
            return None
        self._msaa = (w, h, fbo, tuple(rbs))
        return fbo

    def tunnel(self, mesh: np.ndarray) -> None:
        """Draw the vignette over what's drawn (after draw(), in the same view)."""
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glUseProgram(self.tprog)
        GL.glBindVertexArray(self.tvao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.tvbo)
        if mesh is not self._tunnel:                     # once per frame, not per eye
            GL.glBufferData(GL.GL_ARRAY_BUFFER, mesh.nbytes, mesh, GL.GL_DYNAMIC_DRAW)
            self._tunnel = mesh
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, len(mesh))
        GL.glBindVertexArray(0)
        GL.glUseProgram(0)
        GL.glDisable(GL.GL_BLEND)
        GL.glEnable(GL.GL_DEPTH_TEST)

    def draw(self, verts: np.ndarray, mvp: np.ndarray, clear, tris: np.ndarray | None = None,
             target: int | None = None, viewport: tuple[int, int, int, int] | None = None,
             meshes=(), eye=None) -> None:
        """Clear, then the triangles (solid surfaces) and models (meshes: (gear.Model, instances)
        pairs, lit as seen from eye, a world point), then the lines, into the target framebuffer's
        viewport (by way of the multisampled one, resolved into it at the end). Pass target and
        viewport when they're known (the headset's): asking GL for them makes the CPU wait for the
        driver; left out, they're the bound framebuffer and the current viewport."""
        if target is None:
            target = int(GL.glGetIntegerv(GL.GL_DRAW_FRAMEBUFFER_BINDING))
        if viewport is None:
            viewport = tuple(int(v) for v in GL.glGetIntegerv(GL.GL_VIEWPORT))
        x, y, w, h = viewport
        ms = self._multisampled(w, h)
        if ms is not None:
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, ms)
            GL.glViewport(0, 0, w, h)
        GL.glClearColor(*clear, 1.0)
        GL.glClearDepth(1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glUseProgram(self.prog)
        mvp32 = np.ascontiguousarray(mvp, dtype=np.float32)
        GL.glUniformMatrix4fv(self.mvp_loc, 1, GL.GL_TRUE, mvp32)
        if tris is not None and len(tris):
            GL.glBindVertexArray(self.tri_vao)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.tri_vbo)
            if tris is not self._tris:                   # the same frame's second eye: already there
                GL.glBufferData(GL.GL_ARRAY_BUFFER, tris.nbytes, tris, GL.GL_DYNAMIC_DRAW)
                self._tris = tris
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, len(tris))
        if meshes:
            self._draw_models(meshes, mvp32, eye)
        GL.glBindVertexArray(self.vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        if verts is not self._uploaded:
            GL.glBufferData(GL.GL_ARRAY_BUFFER, verts.nbytes, verts, GL.GL_DYNAMIC_DRAW)
            self._uploaded = verts
        GL.glDrawArrays(GL.GL_LINES, 0, len(verts))
        GL.glBindVertexArray(0)
        GL.glUseProgram(0)
        if ms is not None:                               # resolve into the target, and draw on there again
            GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, ms)
            GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, target)
            GL.glBlitFramebuffer(0, 0, w, h, x, y, x + w, y + h, GL.GL_COLOR_BUFFER_BIT, GL.GL_NEAREST)
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, target)
            GL.glViewport(x, y, w, h)


def scene(active: bool, spec: stickspec.StickSpec, poses: dict, held: dict, stick, state: int) -> np.ndarray:
    """Ice grid, hand axes (+ a green cross while gripping), and the stick with its blade outline."""
    v = []

    def line(a, b, c):
        v.append((*a, *c))
        v.append((*b, *c))

    grid = (0.25, 0.85, 0.35) if active else (0.42, 0.44, 0.5)
    for k in range(-8, 9):
        x = k * 0.5
        line((x, 0, -4), (x, 0, 4), grid)
        line((-4, 0, x), (4, 0, x), grid)
    for dev, (R, p) in poses.items():
        for axis, col in ((0, (1, 0.2, 0.2)), (1, (0.2, 1, 0.2)), (2, (0.3, 0.5, 1))):
            line(p, p + R[:, axis] * 0.06, col)
        if held.get(dev):
            for axis in range(3):
                e = np.eye(3)[axis] * 0.035
                line(p - e, p + e, (0.2, 1.0, 0.3))
    R, p = stick
    if R is not None:
        loose = state in (grab.LOOSE_TOP, grab.LOOSE_BOTTOM)     # in a hand, no grip pressed
        shaft = (0.6, 0.66, 0.75) if loose else (0.92, 0.92, 0.92)
        blade = (0.8, 0.65, 0.2) if loose else (1.0, 0.85, 0.1)
        line(R @ spec.knob + p, p, shaft)
        bottom = spec.edge(10) @ R.T + p
        top = spec.edge(10, top=True) @ R.T + p
        for i in range(len(bottom) - 1):
            line(bottom[i], bottom[i + 1], blade)
            line(top[i], top[i + 1], blade)
        line(bottom[0], top[0], blade)
        line(bottom[-1], top[-1], blade)
    return np.asarray(v, dtype=np.float32)


def view_matrix(pose) -> np.ndarray:
    R = stickmath.quat_to_mat(np.array([pose.orientation.x, pose.orientation.y,
                                        pose.orientation.z, pose.orientation.w]))
    p = np.array([pose.position.x, pose.position.y, pose.position.z])
    m = np.eye(4)
    m[:3, :3] = R.T
    m[:3, 3] = -R.T @ p
    return m


# ----------------------------------------------------------------------------- main


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="run folder (default data/<timestamp>)")
    ap.add_argument("--rate", type=float, default=1000, help="pose queries per second (default 1000)")
    ap.add_argument("--lag-ms", type=float, default=0,
                    help="query poses this many ms in the past (0 = now; try 20 for a smoothed history)")
    ap.add_argument("--space", choices=("stage", "local"), default="stage")
    ap.add_argument("--height", default="5'8\"", help="your height: 5'8\", 68in, 173cm (default 5'8\")")
    ap.add_argument("--shoots", choices=("left", "right"), default="left",
                    help="shot side; left = right hand on top (default left)")
    ap.add_argument("--lie", type=float, default=5.0, help="stick lie (default 5 = shaft at 45 degrees)")
    ap.add_argument("--stick-length", type=float, help="stick length in metres, heel to top (default 0.84 x height)")
    ap.add_argument("--refit", action="store_true", help="fit the stick in your right hand again")
    ap.add_argument("--no-slap", action="store_true", help="skip the slap-shot phase")
    ap.add_argument("--only", nargs="+", metavar="PHASE", help="run only these phases")
    ap.add_argument("--no-voice", action="store_true", help="print instructions instead of speaking them")
    ap.add_argument("--notes", default="", help="free text saved in meta.json (headset, Link type)")
    args = ap.parse_args()

    phases = protocol.select(args.no_slap, args.only)
    run_dir = Path(args.out) if args.out else HERE / "data" / dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    space_type = xr.ReferenceSpaceType.STAGE if args.space == "stage" else xr.ReferenceSpaceType.LOCAL
    spec = stickspec.from_height(stickspec.parse_height(args.height), args.shoots, args.lie, args.stick_length)
    saved = None if args.refit else grab.Fit.load(FIT_PATH)
    shared = Shared(spec, saved or grab.Fit(), need_fit=saved is None)
    voice = Voice(not args.no_voice)
    meta = {"created": dt.datetime.now().isoformat(timespec="seconds"), "rate_hz": args.rate,
            "lag_ms": args.lag_ms, "space": args.space, "notes": args.notes, "spec": spec.to_dict(),
            "fit_source": "saved" if saved else "fitted this run", "protocol": [p.name for p in phases]}
    print(f"stick: {spec.length_m / stickspec.INCH:.1f} in, lie {spec.lie:g} ({spec.shaft_angle_deg:.0f} deg), "
          f"{spec.shoots} shot; fit: {'saved ' + str(FIT_PATH) if saved else 'will be fitted'}")
    lock = take_lock()
    try:
        record(args, phases, run_dir, space_type, shared, voice, meta)
    except xr.FormFactorUnavailableError:
        raise SystemExit("Headset not connected: put it on, start Link, then run again (xrcheck.py tells you).")
    finally:
        lock.unlink(missing_ok=True)


LOCK = HERE / "data" / ".recording.lock"


def _alive(pid: int) -> bool:
    k = ctypes.windll.kernel32
    h = k.OpenProcess(0x1000, False, pid)            # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    code = wintypes.DWORD()
    ok = k.GetExitCodeProcess(h, ctypes.byref(code))
    k.CloseHandle(h)
    return bool(ok) and code.value == 259            # STILL_ACTIVE


def take_lock() -> Path:
    """One recorder at a time: two OpenXR apps fight over the headset."""
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        try:
            pid = int(LOCK.read_text().strip())
        except ValueError:
            pid = 0
        if pid and pid != os.getpid() and _alive(pid):
            raise SystemExit(f"Another recorder is running (pid {pid}). Stop it first.")
    LOCK.write_text(str(os.getpid()))
    return LOCK


def record(args, phases, run_dir, space_type, shared, voice, meta) -> None:
    provider = GLFWOffscreenContextProvider()   # ContextObject's teardown destroys it
    with ContextObject(
        context_provider=provider,
        instance_create_info=xr.InstanceCreateInfo(
            application_info=xr.ApplicationInfo(application_name="vr-hockey-spike0", engine_name="none"),
            enabled_extension_names=[xr.KHR_OPENGL_ENABLE_EXTENSION_NAME,
                                     xr.KHR_WIN32_CONVERT_PERFORMANCE_COUNTER_TIME_EXTENSION_NAME],
        ),
        reference_space_create_info=xr.ReferenceSpaceCreateInfo(reference_space_type=space_type),
    ) as ctx:
        meta["runtime"] = xr.get_instance_properties(ctx.instance).runtime_name.decode()
        meta["system"] = xr.get_system_properties(ctx.instance, ctx.system_id).system_name.decode()
        run_dir.mkdir(parents=True, exist_ok=False)
        print(f"runtime: {meta['runtime']} | system: {meta['system']} | recording to {run_dir}")

        shared.is_focused = lambda: ctx.session_state == xr.SessionState.FOCUSED
        inputs = Inputs(ctx)
        renderer = LineRenderer()
        sampler = Sampler(ctx, inputs.spaces, inputs.head, args.rate, args.lag_ms, shared, run_dir / "rec.csv")
        sampler.start()
        threading.Thread(target=run_protocol, args=(shared, voice, phases), daemon=True, name="protocol").start()

        sync_info = xr.ActionsSyncInfo(active_action_sets=[xr.ActiveActionSet(action_set=ctx.default_action_set)])
        disp_vel = [xr.SpaceVelocity() for _ in inputs.spaces]
        disp_loc = [xr.SpaceLocation(next=v) for v in disp_vel]
        spec, g = shared.spec, shared.grab
        top, bot = spec.top_hand, spec.bottom_hand
        last_status, a_was = 0.0, False
        try:
            for frame_state in ctx.frame_loop():
                inp = {"squeeze": {}, "thumb": (0.0, 0.0), "a": False, "b": False}
                if ctx.session_state == xr.SessionState.FOCUSED:
                    xr.sync_actions(ctx.session, sync_info)
                    inp = inputs.read()
                for d in recfmt.CONTROLLERS:
                    shared.squeeze[d] = inp["squeeze"].get(d, 0.0)
                poses = {}
                for dev, space, loc in zip(recfmt.CONTROLLERS, inputs.spaces, disp_loc):
                    r = xr.check_result(xr.raw_functions.xrLocateSpace(
                        space, ctx.space, frame_state.predicted_display_time, ctypes.byref(loc)))
                    if not r.is_exception() and (loc._location_flags & NEED_POSE) == NEED_POSE:
                        o, p = loc.pose.orientation, loc.pose.position
                        poses[dev] = (stickmath.quat_to_mat(np.array([o.x, o.y, o.z, o.w])),
                                      np.array([p.x, p.y, p.z]))
                if shared.fitting:
                    dt_s = frame_state.predicted_display_period / 1e9 if frame_state.predicted_display_period else 1 / 72
                    shared.fit = apply_thumbstick(shared.fit, inp["thumb"], inp["b"], dt_s)
                    g.set_fit(shared.fit)
                    if inp["a"] and not a_was:
                        inputs.buzz("r", 0.8, 60)
                        shared.fit_done.set()
                a_was = inp["a"]
                was = dict(g.on)
                state, R, p = g.step(poses.get(top), poses.get(bot), shared.squeeze[top], shared.squeeze[bot],
                                     time.perf_counter(),
                                     force_top=shared.fitting)
                for key, dev in (("t", top), ("b", bot)):
                    if g.on[key] and not was[key]:
                        inputs.buzz(dev)
                held = {top: g.on["t"], bot: g.on["b"]}
                verts = scene(shared.active, spec, poses, held, (R, p), state)
                for view in ctx.view_loop(frame_state):
                    proj = np.asarray(Matrix4x4f.create_projection_fov(GraphicsAPI.OPENGL, view.fov, 0.05, 100.0).m)
                    clear = (0.05, 0.12, 0.07) if shared.active else (0.06, 0.06, 0.09)
                    renderer.draw(verts, proj @ view_matrix(view.pose), clear)
                now = time.time()
                if now - last_status > 2:
                    last_status = now
                    secs = max(shared.t_now, 1e-9)
                    print(f"  t={shared.t_now:6.1f}s  phase={shared.phase:<12} stick={grab.STATE_NAMES[state]:<6} "
                          f"samples={sampler.n} ({sampler.n / secs:.0f}/s)  locate errors={sampler.errors}", flush=True)
                if shared.done:
                    break
        except KeyboardInterrupt:
            if not shared.done:
                print("stopped with Ctrl+C; saving what was recorded")
        finally:
            shared.exited = True
            sampler.stop_evt.set()
            sampler.join(timeout=5)
            meta.update(samples=sampler.n, locate_errors=sampler.errors, phases=shared.phase_log,
                        fit=shared.fit.to_dict(), completed=shared.ended == "completed",
                        ended=shared.ended or "stopped")
            recfmt.write_meta(run_dir, meta)
    print(f"saved {run_dir}\nnext: uv run python analyze.py {run_dir}")


if __name__ == "__main__":
    main()
