"""Spike 0 recorder: both Quest controllers in your hands as a virtual stick, sampled at ~1 kHz.

Headset on over Link, a controller in each hand (wrist straps on), then:

    uv run python record.py --notes "Quest 3, cable Link, shoots left"
    uv run python record.py --shoots left        # left shot = right hand on top (else: the higher hand)
    uv run python record.py --stick-length 1.45  # fix the stick length (top grip to heel, metres)
    uv run python record.py --no-slap            # skip the slap shots
    uv run python record.py --show-model top_hand  # which stick model the headset shows (default two_hand)
    uv run python record.py --only stance rest   # just some phases

A voice (through the default audio device, i.e. the headset on Link) walks you through
the phases. Three low beeps = get ready, high beep = go, two falling beeps = stop.
In the headset: a floor grid as the ice (green while a phase records), each hand's axes,
and, once your stance is measured, the virtual stick (white) with its blade (yellow).

Output: data/<timestamp>/rec.csv + meta.json. Then: uv run python analyze.py data/<timestamp>
"""

from __future__ import annotations

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

import numpy as np
import xr
from OpenGL import GL
from xr.utils.gl import ContextObject
from xr.utils.gl.glfw_util import GLFWOffscreenContextProvider
from xr.utils.matrix4x4f import GraphicsAPI, Matrix4x4f

import protocol
import recfmt
import stickmath

HERE = Path(__file__).resolve().parent
NEED_POSE = recfmt.FLAG_POS_VALID | recfmt.FLAG_ORI_VALID
HAND = {"l": "left", "r": "right"}


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
    def __init__(self, top_override: str | None, stick_length: float | None, show_model: str = "two_hand"):
        self.show_model = show_model
        self.phase = recfmt.GAP
        self.active = False
        self.done = False
        self.top_override = top_override
        self.stick_length = stick_length
        self.stick: stickmath.StickCal | None = None
        self.latest_flags = {d: 0 for d in recfmt.CONTROLLERS}
        self.calib_rows: dict[str, list] = {}   # phase label -> [(left 7-tuple|None, right 7-tuple|None)]
        self.phase_log: list[dict] = []
        self.calibration: dict = {}
        self.t_now = 0.0


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
            phase = sh.phase
            row = [round(t_s, 6), xt, phase]
            calib = phase.split("#")[0] == protocol.CALIBRATION
            poses = []
            for dev, space, loc, vel in zip(recfmt.CONTROLLERS, self.ctrl_spaces, self.loc, self.vel):
                if self._locate(space, loc, xt):
                    f = loc._location_flags
                    po, pp = loc.pose.orientation, loc.pose.position
                    lv, av = vel.linear_velocity, vel.angular_velocity
                    vals = (round(pp.x, 6), round(pp.y, 6), round(pp.z, 6),
                            round(po.x, 7), round(po.y, 7), round(po.z, 7), round(po.w, 7))
                    row += [f, *vals, vel._velocity_flags,
                            round(lv.x, 5), round(lv.y, 5), round(lv.z, 5),
                            round(av.x, 5), round(av.y, 5), round(av.z, 5)]
                    sh.latest_flags[dev] = f
                    poses.append(vals if (f & NEED_POSE) == NEED_POSE else None)
                else:
                    row += [0] * len(recfmt.CTRL_FIELDS)
                    sh.latest_flags[dev] = 0
                    poses.append(None)
            if calib:
                sh.calib_rows.setdefault(phase, []).append(tuple(poses))
            if self._locate(self.head_space, self.head_loc, xt):
                hl = self.head_loc
                po, pp = hl.pose.orientation, hl.pose.position
                row += [hl._location_flags, round(pp.x, 6), round(pp.y, 6), round(pp.z, 6),
                        round(po.x, 7), round(po.y, 7), round(po.z, 7), round(po.w, 7)]
            else:
                row += [0] * len(recfmt.HEAD_FIELDS)
            self.buf.append(row)
            self.n += 1
            sh.t_now = t_s
            next_t += self.period
            delay = next_t - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
            elif delay < -0.05:          # fell far behind (GC, stall): don't burst to catch up
                next_t = time.perf_counter()
        self.writer.join()


# ----------------------------------------------------------------------------- protocol


def calibrate_online(shared: Shared, label: str) -> tuple[stickmath.StickCal | None, list[str]]:
    """Fit the virtual stick to the stance just recorded."""
    rows = [(lv, rv) for lv, rv in shared.calib_rows.get(label, []) if lv and rv]
    n = len(shared.calib_rows.get(label, []))
    if len(rows) < 0.6 * max(n, 1) or len(rows) < 200:
        return None, ["both hands were not tracked for most of the stance"]
    a = np.asarray(rows)                       # (N, 2, 7)
    k = len(a) // 10
    a = a[k:len(a) - k]                        # drop the settling at both ends
    p = {"l": a[:, 0, :3], "r": a[:, 1, :3]}
    R = {"l": stickmath.quat_to_mat(a[:, 0, 3:]), "r": stickmath.quat_to_mat(a[:, 1, 3:])}
    top = shared.top_override or stickmath.pick_top(p["l"], p["r"])
    bot = "r" if top == "l" else "l"
    try:
        cal = stickmath.calibrate_stance(R[top], p[top], R[bot], p[bot], top, 0.0, shared.stick_length)
    except ValueError as e:
        return None, [str(e)]
    heel = stickmath.blade_heel("two_hand", cal, R[top], p[top], R[bot], p[bot])
    spread = float(np.max(np.linalg.norm(heel - np.median(heel, axis=0), axis=1)))
    return cal, stickmath.stance_problems(cal, spread)


def run_protocol(shared: Shared, voice: Voice, phases: list[protocol.Phase]) -> None:
    t_wait, ok_since = time.time(), None
    while True:  # both controllers tracked for a full second
        ok = all((shared.latest_flags[d] & NEED_POSE) == NEED_POSE for d in recfmt.CONTROLLERS)
        ok_since = (ok_since or time.time()) if ok else None
        if ok_since and time.time() - ok_since > 1.0:
            break
        if time.time() - t_wait > 15:
            missing = [HAND[d] for d in recfmt.CONTROLLERS
                       if (shared.latest_flags[d] & NEED_POSE) != NEED_POSE]
            voice.say(f"Waiting for the {' and '.join(missing)} controller. Wake it up by moving it.")
            t_wait = time.time()
        time.sleep(0.05)
    voice.say("Both controllers found. Spike zero starts now. Each step: listen, three low beeps, "
              "then a high beep means go. Two falling beeps mean stop.")

    i = 0
    attempts: dict[str, int] = {}
    while i < len(phases):
        ph = phases[i]
        attempts[ph.name] = attempts.get(ph.name, 0) + 1
        label = ph.name if attempts[ph.name] == 1 else f"{ph.name}#{attempts[ph.name]}"
        voice.say(ph.say)
        time.sleep(0.5)
        voice.get_ready()
        start = shared.t_now
        shared.phase, shared.active = label, True
        time.sleep(ph.seconds)
        shared.phase, shared.active = recfmt.GAP, False
        shared.phase_log.append({"label": label, "name": ph.name, "start_t": start, "end_t": shared.t_now})
        voice.stop()

        if ph.name == protocol.CALIBRATION:
            cal, problems = calibrate_online(shared, label)
            shared.calibration[label] = {"stick": cal.to_dict() if cal else None, "problems": problems}
            if problems and attempts[ph.name] < 3:
                voice.say(f"That stance did not work: {problems[0]}. Let's do it again.")
                continue
            if cal:
                shared.stick = cal
                msg = (f"Stick fitted. {cal.length_m:.2f} metres from your top hand to the blade, "
                       f"{HAND[cal.top]} hand on top. Hold your stance and the blade should sit on the ice.")
                if problems:
                    msg += f" It still looks off, {problems[0]}, but carrying on."
                voice.say(msg)
            else:
                voice.say("No stick could be fitted. Carrying on without one.")
        i += 1
    voice.say("All done. Thank you. You can take the headset off.")
    shared.done = True


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


def _compile(src, kind):
    s = GL.glCreateShader(kind)
    GL.glShaderSource(s, src)
    GL.glCompileShader(s)
    if not GL.glGetShaderiv(s, GL.GL_COMPILE_STATUS):
        raise RuntimeError(GL.glGetShaderInfoLog(s).decode())
    return s


class LineRenderer:
    def __init__(self):
        self.prog = GL.glCreateProgram()
        for src, kind in ((VS, GL.GL_VERTEX_SHADER), (FS, GL.GL_FRAGMENT_SHADER)):
            GL.glAttachShader(self.prog, _compile(src, kind))
        GL.glLinkProgram(self.prog)
        if not GL.glGetProgramiv(self.prog, GL.GL_LINK_STATUS):
            raise RuntimeError(GL.glGetProgramInfoLog(self.prog).decode())
        self.mvp_loc = GL.glGetUniformLocation(self.prog, "mvp")
        self.vao = GL.glGenVertexArrays(1)
        self.vbo = GL.glGenBuffers(1)
        GL.glBindVertexArray(self.vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 24, ctypes.c_void_p(0))
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, 24, ctypes.c_void_p(12))
        GL.glBindVertexArray(0)

    def draw(self, verts: np.ndarray, mvp: np.ndarray, clear) -> None:
        GL.glClearColor(*clear, 1.0)
        GL.glClearDepth(1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glUseProgram(self.prog)
        GL.glUniformMatrix4fv(self.mvp_loc, 1, GL.GL_TRUE, np.ascontiguousarray(mvp, dtype=np.float32))
        GL.glBindVertexArray(self.vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, verts.nbytes, verts, GL.GL_DYNAMIC_DRAW)
        GL.glDrawArrays(GL.GL_LINES, 0, len(verts))
        GL.glBindVertexArray(0)
        GL.glUseProgram(0)


def scene(shared: Shared, poses: dict) -> np.ndarray:
    """Ice grid, hand axes, and the virtual stick (the chosen model; top_hand while the bottom hand is lost)."""
    v = []

    def line(a, b, c):
        v.append((*a, *c))
        v.append((*b, *c))

    grid = (0.25, 0.85, 0.35) if shared.active else (0.42, 0.44, 0.5)
    for k in range(-8, 9):
        x = k * 0.5
        line((x, 0, -4), (x, 0, 4), grid)
        line((-4, 0, x), (4, 0, x), grid)
    for dev, (R, p) in poses.items():
        for axis, col in ((0, (1, 0.2, 0.2)), (1, (0.2, 1, 0.2)), (2, (0.3, 0.5, 1))):
            line(p, p + R[:, axis] * 0.08, col)
    cal = shared.stick
    if cal is not None and cal.top in poses:
        Rt, pt = poses[cal.top]
        if cal.bottom in poses:
            Rb, pb = poses[cal.bottom]
            heel = stickmath.blade_heel(shared.show_model, cal, Rt, pt, Rb, pb)
        else:
            heel = stickmath.blade_heel("top_hand", cal, Rt, pt, Rt, pt)
        toe = heel + stickmath.BLADE_LEN * stickmath.blade_dir(cal, Rt)
        line(pt, heel, (0.9, 0.9, 0.9))
        line(heel, toe, (1, 0.85, 0.1))
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


def make_actions(ctx):
    inst = ctx.instance
    hands = [xr.string_to_path(inst, "/user/hand/left"), xr.string_to_path(inst, "/user/hand/right")]
    action = xr.create_action(
        action_set=ctx.default_action_set,
        create_info=xr.ActionCreateInfo(
            action_type=xr.ActionType.POSE_INPUT,
            action_name="grip_pose",
            localized_action_name="Grip pose",
            count_subaction_paths=len(hands),
            subaction_paths=(xr.Path * len(hands))(*hands),
        ),
    )
    for profile in ("/interaction_profiles/oculus/touch_controller",
                    "/interaction_profiles/khr/simple_controller"):
        bindings = (xr.ActionSuggestedBinding * 2)(
            xr.ActionSuggestedBinding(action, xr.string_to_path(inst, "/user/hand/left/input/grip/pose")),
            xr.ActionSuggestedBinding(action, xr.string_to_path(inst, "/user/hand/right/input/grip/pose")),
        )
        xr.suggest_interaction_profile_bindings(
            instance=inst,
            suggested_bindings=xr.InteractionProfileSuggestedBinding(
                interaction_profile=xr.string_to_path(inst, profile),
                count_suggested_bindings=len(bindings),
                suggested_bindings=bindings,
            ),
        )
    spaces = [xr.create_action_space(session=ctx.session,
                                     create_info=xr.ActionSpaceCreateInfo(action=action, subaction_path=h))
              for h in hands]
    head = xr.create_reference_space(
        session=ctx.session,
        create_info=xr.ReferenceSpaceCreateInfo(reference_space_type=xr.ReferenceSpaceType.VIEW))
    return spaces, head


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="run folder (default data/<timestamp>)")
    ap.add_argument("--rate", type=float, default=1000, help="pose queries per second (default 1000)")
    ap.add_argument("--lag-ms", type=float, default=0,
                    help="query poses this many ms in the past (0 = now; try 20 for a smoothed history)")
    ap.add_argument("--space", choices=("stage", "local"), default="stage")
    ap.add_argument("--shoots", choices=("left", "right"),
                    help="your shot side: left = right hand on top (default: the higher hand in the stance)")
    ap.add_argument("--stick-length", type=float,
                    help="fix the stick length, top grip to heel in metres (default: fitted to your stance)")
    ap.add_argument("--no-slap", action="store_true", help="skip the slap-shot phase")
    ap.add_argument("--show-model", choices=stickmath.MODELS, default="two_hand",
                    help="which stick model the headset shows (default two_hand)")
    ap.add_argument("--only", nargs="+", metavar="PHASE", help="run only these phases")
    ap.add_argument("--no-voice", action="store_true", help="print instructions instead of speaking them")
    ap.add_argument("--notes", default="", help="free text saved in meta.json (headset, Link type, shot side)")
    args = ap.parse_args()

    phases = protocol.select(args.no_slap, args.only)
    run_dir = Path(args.out) if args.out else HERE / "data" / dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    space_type = xr.ReferenceSpaceType.STAGE if args.space == "stage" else xr.ReferenceSpaceType.LOCAL
    top = {"left": "r", "right": "l"}.get(args.shoots)

    shared = Shared(top, args.stick_length, args.show_model)
    voice = Voice(not args.no_voice)
    meta = {"created": dt.datetime.now().isoformat(timespec="seconds"), "rate_hz": args.rate,
            "lag_ms": args.lag_ms, "space": args.space, "notes": args.notes, "shoots": args.shoots,
            "stick_length_arg": args.stick_length, "show_model": args.show_model,
            "protocol": [p.name for p in phases]}
    try:
        record(args, phases, run_dir, space_type, shared, voice, meta)
    except xr.FormFactorUnavailableError:
        raise SystemExit("Headset not connected: put it on, start Link, then run again (xrcheck.py tells you).")


def record(args, phases, run_dir, space_type, shared, voice, meta) -> None:
    with GLFWOffscreenContextProvider() as provider, ContextObject(
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

        ctrl_spaces, head_space = make_actions(ctx)
        renderer = LineRenderer()
        sampler = Sampler(ctx, ctrl_spaces, head_space, args.rate, args.lag_ms, shared, run_dir / "rec.csv")
        sampler.start()
        threading.Thread(target=run_protocol, args=(shared, voice, phases), daemon=True, name="protocol").start()

        sync_info = xr.ActionsSyncInfo(active_action_sets=[xr.ActiveActionSet(action_set=ctx.default_action_set)])
        disp_vel = [xr.SpaceVelocity() for _ in ctrl_spaces]
        disp_loc = [xr.SpaceLocation(next=v) for v in disp_vel]
        last_status = 0.0
        try:
            for frame_state in ctx.frame_loop():
                if ctx.session_state == xr.SessionState.FOCUSED:
                    xr.sync_actions(ctx.session, sync_info)
                poses = {}
                for dev, space, loc in zip(recfmt.CONTROLLERS, ctrl_spaces, disp_loc):
                    r = xr.check_result(xr.raw_functions.xrLocateSpace(
                        space, ctx.space, frame_state.predicted_display_time, ctypes.byref(loc)))
                    if not r.is_exception() and (loc._location_flags & NEED_POSE) == NEED_POSE:
                        o, p = loc.pose.orientation, loc.pose.position
                        poses[dev] = (stickmath.quat_to_mat(np.array([o.x, o.y, o.z, o.w])),
                                      np.array([p.x, p.y, p.z]))
                verts = scene(shared, poses)
                for view in ctx.view_loop(frame_state):
                    proj = np.asarray(Matrix4x4f.create_projection_fov(GraphicsAPI.OPENGL, view.fov, 0.05, 100.0).m)
                    clear = (0.05, 0.12, 0.07) if shared.active else (0.06, 0.06, 0.09)
                    renderer.draw(verts, proj @ view_matrix(view.pose), clear)
                now = time.time()
                if now - last_status > 2:
                    last_status = now
                    secs = max(shared.t_now, 1e-9)
                    print(f"  t={shared.t_now:6.1f}s  phase={shared.phase:<15} samples={sampler.n} "
                          f"({sampler.n / secs:.0f}/s)  locate errors={sampler.errors}", flush=True)
                if shared.done:
                    break
        except KeyboardInterrupt:
            print("stopped with Ctrl+C; saving what was recorded")
        finally:
            sampler.stop_evt.set()
            sampler.join(timeout=5)
            meta.update(samples=sampler.n, locate_errors=sampler.errors, phases=shared.phase_log,
                        online_calibration=shared.calibration, completed=shared.done)
            recfmt.write_meta(run_dir, meta)
    print(f"saved {run_dir}\nnext: uv run python analyze.py {run_dir}")


if __name__ == "__main__":
    main()
