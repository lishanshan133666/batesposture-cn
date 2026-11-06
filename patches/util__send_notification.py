"""Platform-native desktop notification utilities.

Dispatch table:
- macOS   -> AppleScript via ``osascript``
- Linux   -> ``notify-send`` (libnotify)
- Windows -> local reminder banner (``scripts/posture_alert.pyw``) with a system
             sound, because Windows toast notifications are frequently suppressed
             (Focus Assist, third-party security suites, missing AppUserModelID).
- Other   -> ``plyer.notification`` (fallback platforms)

All implementations use subprocess argument lists (never shell=True) to
prevent injection from untrusted message or title strings.
"""
import os
import platform
import re
import subprocess
import sys

# Localized text for the messages the app ships with (English -> Simplified Chinese).
_TITLE_ZH = {
    "Posture Alert!": "坐姿提醒",
    "Tracking Interval Changed": "检测间隔已更改",
}
_MESSAGE_ZH = {
    "Please sit up straight!": "坐直一点！挺直背部、放松肩膀，把屏幕抬到视线高度。",
}

_ALERT_SCRIPT = r"D:\Apps\PostureGuard\scripts\posture_alert.pyw"


def _translate_message(message: str) -> str:
    """Translate the app's built-in English messages to Simplified Chinese."""
    known = _MESSAGE_ZH.get(message)
    if known:
        return known
    match = re.match(r"Scanning for (\d+) min every (\d+) min", message)
    if match:
        return f"每 {match.group(2)} 分钟检查 {match.group(1)} 分钟。"
    if message.startswith("Continuous tracking enabled"):
        return "已切换到连续监测：摄像头保持常开。"
    match = re.match(r"You've been sitting for (\d+) minutes", message)
    if match:
        return (
            f"你已经连续坐了 {match.group(1)} 分钟，站起来活动一下、"
            "伸展一下肩颈吧！"
        )
    return message


def _windows_banner(message: str, title: str) -> bool:
    """Show the local topmost reminder banner. Returns True when spawned."""
    python_exe = sys.executable
    pythonw = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
    if not os.path.isfile(pythonw):
        pythonw = python_exe
    if not os.path.isfile(_ALERT_SCRIPT):
        return False
    try:
        creationflags = 0x00000008 | 0x08000000  # DETACHED_PROCESS | CREATE_NO_WINDOW
        subprocess.Popen(
            [pythonw, _ALERT_SCRIPT, title, message],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
            close_fds=True,
        )
        return True
    except Exception:
        return False


def _show_plyer(message: str, title: str, icon_path: str) -> None:
    try:
        from plyer import notification

        notification.notify(
            title=title,
            message=message,
            app_icon=icon_path,
            timeout=10,
        )
    except Exception:
        pass


def send_notification(message: str, title: str, icon_path: str) -> None:
    """Send a desktop notification using platform-native mechanisms.

    Args:
        message: Notification body text (single quotes and backslashes are escaped
                 for AppleScript on macOS).
        title:   Notification title.
        icon_path: Path to the app icon; used by notify-send (Linux) and plyer
                   (Windows). Ignored on macOS (AppleScript does not support icons).

    Fails silently (``check=False``) if the notification daemon is unavailable.
    """
    system = platform.system()
    if system == "Darwin":
        # Escape single quotes in the strings for AppleScript
        safe_message = message.replace("\\", "\\\\").replace('"', '\\"')
        safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
        script = f'display notification "{safe_message}" with title "{safe_title}"'
        subprocess.run(["osascript", "-e", script], check=False)
    elif system == "Linux":
        subprocess.run(
            ["notify-send", title, message, "-i", icon_path],
            check=False,
        )
    elif system == "Windows":
        zh_title = _TITLE_ZH.get(title, title)
        zh_message = _translate_message(message)
        if not _windows_banner(zh_message, zh_title):
            _show_plyer(zh_message, zh_title, icon_path)
    else:
        _show_plyer(message, title, icon_path)
