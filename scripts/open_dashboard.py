"""Ask the running BatesPosture tray app to open its live status dashboard.

Used by the "坐姿实时监控" desktop shortcut: if the app is already running we
just drop a flag file that the tray picks up within a second; otherwise we
start the app first and then drop the flag.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

APP_DIR = Path(r"D:\Apps\PostureGuard")
FLAG = APP_DIR / "open_dashboard.flag"
CREATE_NO_WINDOW = 0x08000000


def _running() -> bool:
    try:
        import psutil
    except ImportError:  # pragma: no cover - psutil ships with the app
        return False
    for proc in psutil.process_iter(["name", "cmdline"]):
        try:
            cmdline = " ".join(proc.info.get("cmdline") or [])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if "batesposture" in cmdline and "open_dashboard" not in cmdline:
            return True
    return False


def main() -> int:
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    if not _running():
        subprocess.Popen(
            [str(pythonw), "-m", "batesposture"],
            cwd=str(APP_DIR),
            creationflags=CREATE_NO_WINDOW,
            close_fds=True,
        )
        time.sleep(4.0)
    FLAG.write_text("open", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
