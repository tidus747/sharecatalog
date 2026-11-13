"""Launch the real entry point and check its native window, then stop the smoke process."""

import argparse
import ctypes
import os
import subprocess
import sys
import time
from pathlib import Path


def main() -> int:
    if os.name != "nt":
        raise SystemExit("This native-window smoke check requires Windows.")
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--packaged", action="store_true")
    selection.add_argument("--executable", type=Path)
    options = parser.parse_args()
    command = (
        [str(options.executable.resolve())]
        if options.executable
        else [str(root / "dist/ShareCatalog/ShareCatalog.exe")]
        if options.packaged
        else [sys.executable, "-m", "sharecatalog"]
    )
    environment = dict(os.environ)
    environment.pop("QT_QPA_PLATFORM", None)
    windows = []
    baseline = set()
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def inspect(handle, _):
        if ctypes.windll.user32.IsWindowVisible(handle):
            title = ctypes.create_unicode_buffer(512)
            ctypes.windll.user32.GetWindowTextW(handle, title, 512)
            if "ShareCatalog" in title.value:
                windows.append((handle, title.value))
        return True

    callback = callback_type(inspect)
    ctypes.windll.user32.EnumWindows(callback, 0)
    baseline.update(handle for handle, _ in windows)
    windows.clear()
    # Windows venv launchers may create a child Python process that owns the window.
    process = subprocess.Popen(command, cwd=root, env=environment)
    window_process_id = None
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and process.poll() is None:
            ctypes.windll.user32.EnumWindows(callback, 0)
            new_windows = [(handle, title) for handle, title in windows if handle not in baseline]
            if new_windows:
                owner = ctypes.c_ulong()
                ctypes.windll.user32.GetWindowThreadProcessId(
                    new_windows[0][0], ctypes.byref(owner)
                )
                window_process_id = owner.value
                print("Native application window detected: " + new_windows[0][1])
                return 0
            time.sleep(0.1)
        raise RuntimeError(f"No native application window detected. Exit code: {process.poll()}")
    finally:
        # Do not create preferences or projects during this startup-only check.
        if window_process_id and window_process_id != process.pid:
            kernel = ctypes.windll.kernel32
            kernel.OpenProcess.restype = ctypes.c_void_p
            kernel.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint]
            kernel.CloseHandle.argtypes = [ctypes.c_void_p]
            handle = kernel.OpenProcess(1, False, window_process_id)
            if handle:
                kernel.TerminateProcess(handle, 0)
                kernel.CloseHandle(handle)
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
