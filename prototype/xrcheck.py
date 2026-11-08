"""Quick OpenXR check before a recording: runtime, extensions, time conversion, headset.

    uv run python xrcheck.py
"""

import ctypes
from ctypes import wintypes

import xr

NEEDED = (xr.KHR_OPENGL_ENABLE_EXTENSION_NAME, xr.KHR_WIN32_CONVERT_PERFORMANCE_COUNTER_TIME_EXTENSION_NAME)


def main() -> None:
    exts = xr.enumerate_instance_extension_properties()
    names = {e.extension_name.decode() if isinstance(e.extension_name, bytes) else e.extension_name for e in exts}
    for n in NEEDED:
        print(f"extension {n}: {'yes' if n in names else 'MISSING'}")
    inst = xr.create_instance(xr.InstanceCreateInfo(
        application_info=xr.ApplicationInfo(application_name="vr-hockey-xrcheck", engine_name="none"),
        enabled_extension_names=list(NEEDED)))
    try:
        props = xr.get_instance_properties(inst)
        print(f"runtime: {props.runtime_name.decode()} {xr.Version(props.runtime_version)}")
        qpc = wintypes.LARGE_INTEGER()
        ctypes.windll.kernel32.QueryPerformanceCounter(ctypes.byref(qpc))
        t = xr.convert_win32_performance_counter_to_time_khr(inst, qpc)
        print(f"time conversion: QPC {qpc.value} -> XrTime {t.value} ns")
        try:
            sys_id = xr.get_system(inst, xr.SystemGetInfo(form_factor=xr.FormFactor.HEAD_MOUNTED_DISPLAY))
        except xr.FormFactorUnavailableError:
            print("headset: NOT CONNECTED (start Link in the headset and run this again)")
            return
        sp = xr.get_system_properties(inst, sys_id)
        tp = sp.tracking_properties
        print(f"headset: {sp.system_name.decode()} | position tracking: {bool(tp.position_tracking)}")
    finally:
        xr.destroy_instance(inst)


if __name__ == "__main__":
    main()
