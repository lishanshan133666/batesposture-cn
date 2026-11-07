"""Repair / re-apply the local patches BatesPosture needs on this machine.

BatesPosture 1.1.1 expects the *legacy* MediaPipe API (``mp.solutions.pose``),
but the MediaPipe wheels available here (0.10.3x and 1.x) only ship the Tasks
API.  This machine therefore runs with a few local fixes:

1. ``mediapipe/python`` compatibility shim inside the venv, so
   ``import mediapipe.python.solutions.pose`` works again (implemented on top of
   ``PoseLandmarker``).
2. A small patch in ``batesposture/services/camera_service.py`` that opens the
   webcam with the DirectShow backend on Windows; the default Media Foundation
   backend stalls after the first frame with this USB 2K camera.
3. A replacement for ``batesposture/util__send_notification.py`` that shows a
   local topmost reminder banner (``scripts/posture_alert.pyw``) with a system
   sound on Windows, because Windows toast notifications are suppressed on this
   machine (security suite / notification policy).
4. A patch in ``batesposture/ui/tray.py`` that starts posture tracking right
   after launch (continuous mode), so the tray app begins monitoring without a
   manual click, plus a flag-file watcher so the "坐姿实时监控" shortcut can
   pop the live dashboard window open on a running instance.

All of these live inside the venv's ``site-packages`` and are therefore lost
whenever ``mediapipe`` or ``batesposture`` is reinstalled/upgraded.  Re-run this
script after such an upgrade:

    D:\\Apps\\PostureGuard\\venv\\Scripts\\python.exe D:\\Apps\\PostureGuard\\repair.py
"""

from __future__ import annotations

import importlib.metadata
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "patches"))

ORIGINAL_OPEN = "        self._cap = cv2.VideoCapture(self._camera_id)\n"
PATCHED_OPEN = "        self._cap = self._open_capture(self._camera_id)\n"
HELPER = '''    @staticmethod
    def _open_capture(camera_id: int) -> cv2.VideoCapture:
        """Open the webcam, preferring DirectShow on Windows.

        OpenCV's default Media Foundation backend stalls after the first frame on
        some UVC cameras (observed with a 2K USB webcam), so DirectShow is tried
        first and the platform default only used as a fallback.
        """
        backends = [cv2.CAP_DSHOW, cv2.CAP_ANY] if os.name == "nt" else [cv2.CAP_ANY]
        for backend in backends:
            candidate = cv2.VideoCapture(camera_id, backend)
            if candidate.isOpened():
                try:
                    candidate.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                except Exception:  # noqa: BLE001 - optional optimisation only
                    pass
                logger.info("Camera %s opened with backend %s", camera_id, backend)
                return candidate
            candidate.release()
        logger.warning("Camera %s could not be opened with any preferred backend", camera_id)
        return cv2.VideoCapture(camera_id)

'''

AUTO_START_MARKER = "[PostureGuard] auto-start tracking on launch"
AUTO_START_SNIPPET = '''
        # [PostureGuard] auto-start tracking on launch
        try:
            from PyQt6.QtCore import QTimer as _QTimer

            def _auto_start_tracking() -> None:
                if not self.tracking_enabled:
                    self._start_tracking()

            _QTimer.singleShot(1500, _auto_start_tracking)
        except Exception:  # noqa: BLE001 - never block startup
            pass
'''
AUTO_START_OLD_SNIPPET = '''
        # [PostureGuard] auto-start tracking on launch
        try:
            from PyQt6.QtCore import QTimer as _QTimer

            _QTimer.singleShot(1500, self._start_tracking)
        except Exception:  # noqa: BLE001 - never block startup
            pass
'''
INTERVAL_ORIGINAL = "        self.tracking_interval = 30\n"
INTERVAL_PATCHED = (
    "        self.tracking_interval = 0  # [PostureGuard] continuous tracking by default\n"
)

DASHBOARD_SCHEDULE_MARKER = "[PostureGuard] dashboard request watcher"
DASHBOARD_SCHEDULE = '''
        # [PostureGuard] dashboard request watcher (shortcut can ask for the live panel)
        try:
            self._scheduler.schedule(
                "dashboard_request", 1000, self._check_dashboard_request
            )
        except Exception:  # noqa: BLE001 - never block startup
            pass
'''
DASHBOARD_METHOD_MARKER = "_check_dashboard_request(self)"
DASHBOARD_METHOD = '''    # [PostureGuard] opens the dashboard when a shortcut drops a flag file
    _DASHBOARD_FLAG = r"D:\\Apps\\PostureGuard\\open_dashboard.flag"

    def _check_dashboard_request(self) -> None:
        import os as _os

        try:
            if _os.path.exists(self._DASHBOARD_FLAG):
                _os.remove(self._DASHBOARD_FLAG)
                if not self.video_window:
                    self.toggle_dashboard()
        except Exception:  # noqa: BLE001 - watcher must never crash the app
            logger.debug("dashboard flag check failed", exc_info=True)

'''


def ensure_versions() -> None:
    """Make sure the pinned, known-good versions are installed."""
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-q",
            "mediapipe==0.10.35",
            "pyqt6==6.9.1",
        ],
        check=False,
    )


def install_mediapipe_shim() -> None:
    import sysconfig

    source = HERE / "shim" / "python"
    target = Path(sysconfig.get_paths()["purelib"]) / "mediapipe" / "python"
    if not (Path(sysconfig.get_paths()["purelib"]) / "mediapipe").is_dir():
        raise SystemExit("mediapipe is not installed in this interpreter")
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    print(f"[ok] mediapipe shim installed -> {target}")


def patch_camera_service() -> None:
    camera = Path(sysconfig_purelib()) / "batesposture" / "services" / "camera_service.py"
    if not camera.is_file():
        raise SystemExit("batesposture is not installed in this interpreter")
    text = camera.read_text(encoding="utf-8")
    if "_open_capture" in text:
        if "\nimport os\n" not in text:
            text = text.replace("import logging\n", "import logging\nimport os\n", 1)
            camera.write_text(text, encoding="utf-8")
            print(f"[ok] camera_service os-import repaired -> {camera}")
        else:
            print("[ok] camera_service already patched")
        return
    if ORIGINAL_OPEN not in text:
        raise SystemExit("[!] camera_service.py layout changed; re-apply the patch manually")
    text = text.replace(ORIGINAL_OPEN, PATCHED_OPEN)
    if "import os\n" not in text:
        text = text.replace("import cv2\n", "import os\n\nimport cv2\n", 1)
    marker = "    def start(self, callback: Optional[FrameCallback] = None) -> bool:"
    text = text.replace(marker, HELPER + marker, 1)
    camera.write_text(text, encoding="utf-8")
    print(f"[ok] camera_service patched (DirectShow camera backend) -> {camera}")


CAMERA_WATCHDOG_MARKER = "# [PostureGuard] reopen the camera after sleep/resume"

CAMERA_WATCHDOG_OLD = '''                ret, frame = self._cap.read()
                if not ret:
                    logger.warning("Failed to read frame from camera; stopping capture")
                    self.stop()
                    break
'''

CAMERA_WATCHDOG_NEW = '''                ret, frame = self._cap.read()
                if not ret:
                    logger.warning("Failed to read frame from camera; stopping capture")
                    self.stop()
                    break
                # [PostureGuard] reopen the camera after sleep/resume
                if frame is not None and float(frame.mean()) < 1.0:
                    self._black_frames = getattr(self, "_black_frames", 0) + 1
                    if self._black_frames >= 90:
                        logger.info("Camera frames are black; reopening capture")
                        try:
                            self._cap.release()
                        except Exception:  # noqa: BLE001 - best effort
                            pass
                        self._cap = self._open_capture(self._camera_id)
                        self._black_frames = 0
                elif frame is not None:
                    self._black_frames = 0
'''


def patch_camera_watchdog() -> None:
    """Recover the camera when Windows sleep/resume leaves it returning black frames."""
    camera = Path(sysconfig_purelib()) / "batesposture" / "services" / "camera_service.py"
    text = camera.read_text(encoding="utf-8")
    if CAMERA_WATCHDOG_MARKER in text:
        print("[ok] camera black-frame recovery already patched")
        return
    if CAMERA_WATCHDOG_OLD not in text:
        raise SystemExit("[!] camera_service.py read loop changed; re-apply the watchdog manually")
    text = text.replace(CAMERA_WATCHDOG_OLD, CAMERA_WATCHDOG_NEW, 1)
    camera.write_text(text, encoding="utf-8")
    print(f"[ok] camera black-frame recovery patched -> {camera}")


def patch_notification_module() -> None:
    """Install the banner-based Windows notification module."""
    package = Path(sysconfig_purelib()) / "batesposture"
    target = package / "util__send_notification.py"
    source = HERE / "patches" / "util__send_notification.py"
    backup = HERE / "patches" / "util__send_notification.py.orig"
    if not package.is_dir():
        raise SystemExit("batesposture is not installed in this interpreter")
    if not backup.exists() and target.is_file():
        shutil.copy2(target, backup)
    shutil.copy2(source, target)
    print(f"[ok] notification module replaced (local banner + sound) -> {target}")


def patch_auto_start() -> None:
    """Make the tray start tracking automatically after launch (continuous mode)."""
    tray = Path(sysconfig_purelib()) / "batesposture" / "ui" / "tray.py"
    if not tray.is_file():
        raise SystemExit("batesposture is not installed in this interpreter")
    text = tray.read_text(encoding="utf-8")
    changed = False
    if INTERVAL_ORIGINAL in text:
        text = text.replace(INTERVAL_ORIGINAL, INTERVAL_PATCHED, 1)
        changed = True
    if AUTO_START_MARKER in text and "_auto_start_tracking" not in text:
        if AUTO_START_OLD_SNIPPET in text:
            text = text.replace(AUTO_START_OLD_SNIPPET, AUTO_START_SNIPPET, 1)
            changed = True
    elif AUTO_START_MARKER not in text:
        anchor = "        self._setup_signal_handling()\n"
        if anchor not in text:
            raise SystemExit(
                "[!] tray.py layout changed; re-apply the auto-start patch manually"
            )
        text = text.replace(anchor, anchor + AUTO_START_SNIPPET, 1)
        changed = True
    if changed:
        tray.write_text(text, encoding="utf-8")
        print(f"[ok] tray patched (auto-start tracking, continuous mode) -> {tray}")
    else:
        print("[ok] tray auto-start already patched")


def patch_dashboard_watcher() -> None:
    """Let a shortcut ask the running tray app to show its live dashboard."""
    tray = Path(sysconfig_purelib()) / "batesposture" / "ui" / "tray.py"
    if not tray.is_file():
        raise SystemExit("batesposture is not installed in this interpreter")
    text = tray.read_text(encoding="utf-8")
    changed = False
    if DASHBOARD_METHOD_MARKER not in text:
        anchor = "    def toggle_tracking(self) -> None:\n"
        if anchor not in text:
            raise SystemExit(
                "[!] tray.py layout changed; re-apply the dashboard patch manually"
            )
        text = text.replace(anchor, DASHBOARD_METHOD + anchor, 1)
        changed = True
    if DASHBOARD_SCHEDULE_MARKER not in text:
        anchor2 = (
            "            _QTimer.singleShot(1500, _auto_start_tracking)\n"
            "        except Exception:  # noqa: BLE001 - never block startup\n"
            "            pass\n"
        )
        if anchor2 not in text:
            raise SystemExit(
                "[!] tray.py layout changed; re-apply the dashboard patch manually"
            )
        text = text.replace(anchor2, anchor2 + DASHBOARD_SCHEDULE, 1)
        changed = True
    if changed:
        tray.write_text(text, encoding="utf-8")
        print(f"[ok] tray patched (open dashboard from shortcut) -> {tray}")
    else:
        print("[ok] tray dashboard shortcut already patched")


def patch_ui() -> None:
    """Install the Chinese UI, quick settings row and basic settings dialog."""
    import ui_patch

    ui_patch.patch_all()


def sysconfig_purelib() -> str:
    import sysconfig

    return sysconfig.get_paths()["purelib"]


def verify() -> None:
    import cv2
    import mediapipe as mp
    from mediapipe.python.solutions import pose as legacy_pose
    import batesposture

    print(f"[ok] mediapipe {mp.__version__} + legacy solutions shim "
          f"({len(legacy_pose.POSE_CONNECTIONS)} connections)")
    print(f"[ok] batesposture {importlib.metadata.version('batesposture')}")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY)
    ok = cap.isOpened() and cap.read()[0]
    cap.release()
    print(f"[{'ok' if ok else '!!'}] camera frame capture works: {ok}")


def main() -> int:
    ensure_versions()
    install_mediapipe_shim()
    patch_camera_service()
    patch_camera_watchdog()
    patch_notification_module()
    patch_ui()
    patch_auto_start()
    patch_dashboard_watcher()
    verify()
    print("\nAll patches applied. Launch with: "
          r"D:\Apps\PostureGuard\venv\Scripts\pythonw.exe -m batesposture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
