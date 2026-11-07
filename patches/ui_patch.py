"""Chinese localisation + settings UI patches for BatesPosture.

The upstream app ships English text and has no autostart switch.  These patches
rewrite the dashboard and tray UI strings to Chinese, add a "quick settings"
row (autostart / reminders) to the live dashboard, and route the tray
"Settings…" item through :mod:`batesposture.ui.ui_zh` so the dialog exposes the
basic options in Chinese.

Every patch is idempotent: each file gets a marker comment once patched, and
re-running this module after a pip upgrade re-applies everything.
"""

from __future__ import annotations

import shutil
import sysconfig
from pathlib import Path

HERE = Path(__file__).resolve().parent
MARKER = "# [PostureGuard] 中文界面补丁 applied"

DASHBOARD_REPLACEMENTS = [
    ('self.setWindowTitle("Posture Dashboard")', 'self.setWindowTitle("坐姿实时监控")'),
    ('self.tr("Waiting for frames…")', 'self.tr("等待摄像头画面…")'),
    ('self.tr("Current")', 'self.tr("当前")'),
    ('self.tr("Session Avg")', 'self.tr("平均分")'),
    ('self.tr("Session Min")', 'self.tr("最低分")'),
    ('self.tr("Session Max")', 'self.tr("最高分")'),
    ('self.tr("Best Streak")', 'self.tr("最佳保持")'),
    ('self.tr("Duration")', 'self.tr("时长")'),
    (
        'self.tr("Settle into a neutral posture while we gather readings.")',
        'self.tr("请坐正，正在采集数据…")',
    ),
    (
        '"Nice alignment! Keep a relaxed breath and soft shoulders."',
        '"姿势很好！保持放松呼吸，肩膀自然下沉。"',
    ),
    (
        '"Gently draw your head back over your shoulders."',
        '"轻轻把头收回肩膀正上方。"',
    ),
    (
        '"Level your shoulders to center your posture."',
        '"双肩放平，让身体居中。"',
    ),
    ('"Lengthen through your spine and sit tall."', '"延展脊柱，坐直一点。"'),
    (
        '"Reset by rolling your shoulders back and opening your chest."',
        '"向后转动肩膀、打开胸腔，重新坐正。"',
    ),
    ('return "Excellent"', 'return "优秀"'),
    ('return "Good"', 'return "良好"'),
    ('return "Fair"', 'return "一般"'),
    ('return "Poor"', 'return "较差"'),
    ('return f"{minutes}m {secs:02d}s"', 'return f"{minutes}分{secs:02d}秒"'),
    ('return f"{secs}s"', 'return f"{secs}秒"'),
    # settings support in the dashboard constructor
    (
        "        history: Optional[List[float]] = None,\n"
        "        parent: Optional[QWidget] = None,\n"
        "    ) -> None:",
        "        history: Optional[List[float]] = None,\n"
        "        parent: Optional[QWidget] = None,\n"
        "        settings: Optional[object] = None,\n"
        "    ) -> None:",
    ),
    (
        "        self.baseline_shoulder_level = baseline_shoulder_level\n",
        "        self.baseline_shoulder_level = baseline_shoulder_level\n"
        "        self._settings = settings\n"
        "        self._quick_widget = None\n"
        "        self._autostart_check = None\n"
        "        self._notify_check = None\n",
    ),
    (
        "    QDialog,\n    QFrame,\n    QWidget,\n)",
        "    QDialog,\n    QFrame,\n    QWidget,\n    QCheckBox,\n    QPushButton,\n)",
    ),
    (
        "        card_layout.addWidget(self.feedback_label)\n",
        "        card_layout.addWidget(self.feedback_label)\n"
        "        self._build_quick_settings(card_layout)\n",
    ),
]

DASHBOARD_METHODS = '''    # [PostureGuard] quick settings row (autostart + reminders + dialog)
    def _build_quick_settings(self, card_layout) -> None:
        if self._settings is None:
            return
        from .ui_zh import autostart_enabled, set_autostart_enabled

        quick = QWidget(self.card)
        row = QHBoxLayout(quick)
        row.setContentsMargins(0, 0, 0, 0)
        self._autostart_check = QCheckBox("开机自启", quick)
        self._autostart_check.setChecked(autostart_enabled())
        self._autostart_check.toggled.connect(set_autostart_enabled)
        self._notify_check = QCheckBox("姿势提醒", quick)
        self._notify_check.setChecked(
            bool(self._settings.runtime.notifications_enabled)
        )
        self._notify_check.toggled.connect(self._on_notify_toggled)
        settings_button = QPushButton("更多设置…", quick)
        settings_button.clicked.connect(self._open_settings)
        close_button = QPushButton("关闭", quick)
        close_button.clicked.connect(self.close)
        row.addWidget(self._autostart_check)
        row.addWidget(self._notify_check)
        row.addStretch(1)
        row.addWidget(settings_button)
        row.addWidget(close_button)
        card_layout.addWidget(quick)
        self._quick_widget = quick

    def _on_notify_toggled(self, checked: bool) -> None:
        self._settings.update_runtime(notifications_enabled=bool(checked))
        self._settings.save_all()

    def _open_settings(self) -> None:
        from .ui_zh import BasicSettingsDialog

        dialog = BasicSettingsDialog(self._settings, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_quick_settings()

    def refresh_quick_settings(self) -> None:
        if self._quick_widget is None:
            return
        from .ui_zh import autostart_enabled

        self._autostart_check.blockSignals(True)
        self._autostart_check.setChecked(autostart_enabled())
        self._autostart_check.blockSignals(False)
        self._notify_check.blockSignals(True)
        self._notify_check.setChecked(
            bool(self._settings.runtime.notifications_enabled)
        )
        self._notify_check.blockSignals(False)

'''

TRAY_REPLACEMENTS = [
    # menu labels
    ('"Start Tracking"', '"开始检测"'),
    ('"Stop Tracking"', '"停止检测"'),
    ('"Show Dashboard"', '"显示监控面板"'),
    ('"Hide Dashboard"', '"隐藏监控面板"'),
    ('menu.addSection("Session")', 'menu.addSection("检测")'),
    ('menu.addSection("Quick toggles")', 'menu.addSection("快捷开关")'),
    ('            "Notifications",', '            "姿势提醒",'),
    ('            "Database Logging",', '            "历史记录",'),
    ('            "Focus Mode",', '            "专注模式",'),
    ('            "Settings",', '            "设置…",'),
    ('"Export Data as CSV…"', '"导出历史数据 (CSV)…"'),
    ('            "Quit",', '            "退出",'),
    ('QMenu("Tracking Interval", parent_menu)', 'QMenu("检测频率", parent_menu)'),
    (
        '"Camera stays on continuously — higher CPU and battery use."',
        '"连续监测会让摄像头一直开着，比较费电。"',
    ),
    # state labels
    ('"Notifications (On)"', '"姿势提醒：开"'),
    ('"Notifications (Off)"', '"姿势提醒：关"'),
    ('"Database Logging (On)"', '"历史记录：开"'),
    ('"Database Logging (Off)"', '"历史记录：关"'),
    ('"Focus Mode (On)"', '"专注模式：开"'),
    ('"Focus Mode (Off)"', '"专注模式：关"'),
    # tooltip / status
    ('"BatesPosture — idle"', '"BatesPosture · 待机"'),
    ('"Away from desk — tracking paused"', '"离开座位 · 检测已暂停"'),
    ('f"Posture: {average_score:.0f}% ({grade})"', 'f"坐姿：{average_score:.0f}% ({grade})"'),
    ('f"🔥 {minutes}m good posture streak"', 'f"🔥 保持良好坐姿 {minutes} 分钟"'),
    ('f"Streak: {int(streak_s)}s"', 'f"连续达标：{int(streak_s)} 秒"'),
    ('f"Next scan in {mins}:{secs:02d}"', 'f"下次检测：{mins}:{secs:02d}"'),
    # export dialogs
    ('"Export",', '"导出",'),
    (
        '"Enable database logging first to collect data for export."',
        '"请先在设置里打开“历史记录”，才能导出数据。"',
    ),
    ('"Export complete",', '"导出完成",'),
    ('f"Data exported to:\\n{path}"', 'f"已导出到：\\n{path}"'),
    ('QMessageBox.warning(None, "Export failed", "Could not write CSV file.")',
     'QMessageBox.warning(None, "导出失败", "无法写入 CSV 文件。")'),
    # route the settings menu item through the Chinese dialog
    (
        "self.settings_action.triggered.connect(self.open_settings)",
        "self.settings_action.triggered.connect(self.open_settings_zh)",
    ),
    # pass settings into the dashboard so it can show quick settings
    (
        "                history=history,\n            )",
        "                history=history,\n                settings=self._settings,\n            )",
    ),
    # bring the dashboard to the front when opened
    (
        "            self.video_window.show()\n",
        "            self.video_window.show()\n"
        "            self.video_window.raise_()\n"
        "            self.video_window.activateWindow()\n",
    ),
]

TRAY_INTERVAL_LABELS = '''_INTERVAL_LABELS_ZH = {
    "Every 5 minutes": "每 5 分钟",
    "Every 15 minutes": "每 15 分钟",
    "Every 30 minutes": "每 30 分钟",
    "Every hour": "每小时",
    "Continuous (always on)": "连续监测（常开）",
}

'''

TRAY_METHOD = '''    def open_settings_zh(self) -> None:
        from .ui_zh import BasicSettingsDialog

        dialog = BasicSettingsDialog(
            self._settings, self.tracking_interval, parent=None
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_after_settings_change()
            if (
                dialog.interval_minutes is not None
                and dialog.interval_minutes != self.tracking_interval
            ):
                self.set_interval(dialog.interval_minutes)
            if isinstance(self.video_window, PostureDashboard):
                self.video_window.refresh_quick_settings()

'''


def _purelib() -> Path:
    return Path(sysconfig.get_paths()["purelib"])


def install_ui_zh() -> None:
    target = _purelib() / "batesposture" / "ui" / "ui_zh.py"
    source = HERE / "ui_zh.py"
    if not target.parent.is_dir():
        raise SystemExit("batesposture is not installed in this interpreter")
    shutil.copy2(source, target)
    print(f"[ok] Chinese settings dialog installed -> {target}")


def _apply(path: Path, replacements, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"[ok] {label} already localised")
        return
    missed = [old for old, _new in replacements if old not in text]
    if missed:
        detail = "; ".join(repr(item) for item in missed[:3])
        raise SystemExit(f"[!] {label}: upstream text changed, missing anchor(s): {detail}")
    for old, new in replacements:
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    print(f"[ok] {label} localised ({len(replacements)} strings) -> {path}")


def patch_dashboard() -> None:
    path = _purelib() / "batesposture" / "ui" / "dashboard.py"
    _apply(path, DASHBOARD_REPLACEMENTS, "dashboard")
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return
    anchor = "    def _apply_theme(self, preference: str) -> None:\n"
    if anchor not in text:
        raise SystemExit("[!] dashboard.py layout changed; re-apply the UI patch manually")
    text = text.replace(anchor, DASHBOARD_METHODS + anchor, 1)
    text = text.replace("from __future__ import annotations\n",
                        "from __future__ import annotations\n\n" + MARKER + "\n", 1)
    path.write_text(text, encoding="utf-8")


def patch_tray() -> None:
    path = _purelib() / "batesposture" / "ui" / "tray.py"
    _apply(path, TRAY_REPLACEMENTS, "tray")
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return
    if "_INTERVAL_LABELS_ZH" not in text:
        anchor = 'logger = logging.getLogger(__name__)\n'
        if anchor not in text:
            raise SystemExit("[!] tray.py layout changed; re-apply the UI patch manually")
        text = text.replace(anchor, anchor + "\n" + TRAY_INTERVAL_LABELS, 1)
        text = text.replace(
            "        for label, minutes in intervals.items():\n"
            "            action = QAction(label, interval_menu, checkable=True)",
            "        for label, minutes in intervals.items():\n"
            "            label = _INTERVAL_LABELS_ZH.get(label, label)\n"
            "            action = QAction(label, interval_menu, checkable=True)",
            1,
        )
    if "def open_settings_zh" not in text:
        anchor = "    def open_settings(self) -> None:\n"
        if anchor not in text:
            raise SystemExit("[!] tray.py layout changed; re-apply the UI patch manually")
        text = text.replace(anchor, TRAY_METHOD + anchor, 1)
    text = text.replace("from __future__ import annotations\n",
                        "from __future__ import annotations\n\n" + MARKER + "\n", 1)
    path.write_text(text, encoding="utf-8")


SINGLE_INSTANCE_MARKER = "# [PostureGuard] second launch opens the dashboard"

SINGLE_INSTANCE_OLD = '''    logger.info("Another BatesPosture instance is already running")
    if has_info:
        logger.info(
            "Active lock details: pid=%s host=%s app=%s",
            pid,
            hostname or "unknown",
            appname or "unknown",
        )
    return None'''

SINGLE_INSTANCE_NEW = '''    logger.info("Another BatesPosture instance is already running")
    if has_info:
        logger.info(
            "Active lock details: pid=%s host=%s app=%s",
            pid,
            hostname or "unknown",
            appname or "unknown",
        )
    # [PostureGuard] second launch opens the dashboard
    try:
        with open(
            r"D:\\Apps\\PostureGuard\\open_dashboard.flag", "w", encoding="utf-8"
        ) as flag_file:
            flag_file.write("1")
        logger.info("Requested the running instance to open its dashboard")
    except OSError:
        logger.debug("could not drop the dashboard flag", exc_info=True)
    return None'''


def patch_single_instance() -> None:
    """Second launch of the shortcut asks the running instance to show its panel."""
    path = _purelib() / "batesposture" / "main.py"
    text = path.read_text(encoding="utf-8")
    if SINGLE_INSTANCE_MARKER in text:
        print("[ok] second-launch shortcut already opens the dashboard")
        return
    if SINGLE_INSTANCE_OLD not in text:
        raise SystemExit(
            "[!] main.py lock handling changed; re-apply the single-instance patch manually"
        )
    text = text.replace(SINGLE_INSTANCE_OLD, SINGLE_INSTANCE_NEW, 1)
    path.write_text(text, encoding="utf-8")
    print(f"[ok] second launch opens the dashboard -> {path}")


RECALIBRATE_MARKER = "# [PostureGuard] recalibrate action"

RECALIBRATE_ACTION = '''        # [PostureGuard] recalibrate action
        self.recalibrate_action = QAction(
            style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload),
            "重新校准标准坐姿…",
            menu,
        )
        self.recalibrate_action.triggered.connect(self.recalibrate_posture)
        menu.addAction(self.recalibrate_action)
'''

RECALIBRATE_METHOD = '''    # [PostureGuard] recalibrate action
    def recalibrate_posture(self) -> None:
        """Stop tracking, relaunch the calibration wizard, then resume."""
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QDialog, QMessageBox

        from .onboarding import OnboardingWizard

        was_tracking = self.tracking_enabled
        was_completed = self._settings.profile.has_completed_onboarding
        if was_tracking:
            self.toggle_tracking()
        self._settings.update_profile(has_completed_onboarding=False)
        self._settings.save_all()

        def _open_wizard() -> None:
            wizard = OnboardingWizard(self._settings, None)
            accepted = wizard.exec() == QDialog.DialogCode.Accepted
            if not accepted:
                # User cancelled: keep the previous baseline / first-run state.
                self._settings.update_profile(has_completed_onboarding=was_completed)
                self._settings.save_all()
            if was_tracking:
                self.toggle_tracking()
            if accepted:
                QMessageBox.information(
                    None,
                    "重新校准完成",
                    "新的标准坐姿已经保存，之后的评分会以这次录制的基线为准。",
                )

        # Give the capture thread a moment to release the camera first.
        QTimer.singleShot(1200, _open_wizard)

'''


def patch_recalibrate() -> None:
    """Add a tray entry that re-runs the 6-second baseline calibration."""
    path = _purelib() / "batesposture" / "ui" / "tray.py"
    text = path.read_text(encoding="utf-8")
    if RECALIBRATE_MARKER in text and "def recalibrate_posture" in text:
        if "was_completed" in text:
            print("[ok] recalibration menu entry already patched")
            return
        start = text.find(RECALIBRATE_MARKER + "\n    def recalibrate_posture")
        end = text.find("    def open_settings_zh(self) -> None:\n", start)
        if start < 0 or end < 0:
            raise SystemExit("[!] could not locate the recalibrate method to upgrade")
        text = text[:start] + RECALIBRATE_METHOD + text[end:]
        path.write_text(text, encoding="utf-8")
        print(f"[ok] recalibration method upgraded (cancel keeps previous baseline) -> {path}")
        return
    anchor = "        self.settings_action.triggered.connect(self.open_settings_zh)\n"
    if anchor not in text:
        raise SystemExit(
            "[!] tray.py settings action anchor changed; re-apply recalibrate patch manually"
        )
    text = text.replace(anchor, anchor + RECALIBRATE_ACTION, 1)
    method_anchor = "    def open_settings_zh(self) -> None:\n"
    if method_anchor not in text:
        raise SystemExit("[!] tray.py open_settings_zh anchor missing")
    text = text.replace(method_anchor, RECALIBRATE_METHOD + method_anchor, 1)
    path.write_text(text, encoding="utf-8")
    print(f"[ok] recalibration menu entry added -> {path}")


ONBOARDING_CAMERA_MARKER = "# [PostureGuard] onboarding camera backend"

ONBOARDING_CAMERA_HELPER = '''# [PostureGuard] onboarding camera backend
def _open_camera(camera_id: int, backend_hint: int = 0):
    """DirectShow first on Windows (MSMF returns black/garbled frames on this machine)."""
    if sys.platform == "win32":
        capture = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
        if capture is not None and capture.isOpened():
            capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return capture
        if capture is not None:
            capture.release()
    if backend_hint:
        capture = cv2.VideoCapture(camera_id, backend_hint)
        if capture is not None and capture.isOpened():
            return capture
    return cv2.VideoCapture(camera_id)


'''


def patch_onboarding_camera() -> None:
    """Make the calibration wizard use the DirectShow backend as well."""
    path = _purelib() / "batesposture" / "ui" / "onboarding.py"
    text = path.read_text(encoding="utf-8")
    if ONBOARDING_CAMERA_MARKER in text:
        print("[ok] onboarding camera backend already patched")
        return
    anchor = "class CameraPreviewWidget(QLabel):\n"
    if anchor not in text:
        raise SystemExit("[!] onboarding.py layout changed; re-apply the camera patch manually")
    text = text.replace(anchor, ONBOARDING_CAMERA_HELPER + anchor, 1)
    text = text.replace(
        "capture = cv2.VideoCapture(self._camera_id)",
        "capture = _open_camera(self._camera_id)",
        1,
    )
    text = text.replace("capture = cv2.VideoCapture(camera_id)", "capture = _open_camera(camera_id)", 1)
    path.write_text(text, encoding="utf-8")
    print(f"[ok] onboarding camera backend patched -> {path}")


ONBOARDING_ZH_MARKER = "# [PostureGuard] onboarding Chinese"

ONBOARDING_ZH_REPLACEMENTS = [
    ("Welcome to Posture Coach", "欢迎使用坐姿提醒"),
    ("We will calibrate your experience in three quick steps.", "三步完成校准，让评分更贴合你的坐姿。"),
    (
        "Great posture starts with awareness. We'll help you dial in camera framing, "
        "learn posture cues, and capture your personal baseline so reminders feel tailored.",
        "好的坐姿从「察觉」开始。这里会帮你调好摄像头取景、认识坐姿要点，"
        "并录一段你的标准坐姿作为基线，之后的评分和提醒都会按你的基线来判断。",
    ),
    ("- Find a well-lit space", "- 找一个光线充足的位置"),
    ("- Position your camera at eye level", "- 让摄像头大致与眼睛同高"),
    ("- Sit naturally - no need to pose!", "- 自然坐好即可，不用刻意摆姿势！"),
    ("Align your camera", "调整摄像头"),
    (
        "Center yourself and ensure your upper body is in frame.",
        "让自己位于画面中央，确保上半身都在画面里。",
    ),
    (
        "Adjust your seating so your head and shoulders are visible. Use natural lighting when possible.",
        "调整座椅和摄像头，让头部、双肩清晰可见；尽量使用自然光。",
    ),
    ("Camera preview will appear here", "摄像头画面将显示在这里"),
    ("Unable to open camera", "无法打开摄像头"),
    ("Camera feed unavailable", "摄像头画面不可用"),
    ("Capture your baseline", "录制标准坐姿"),
    (
        "We'll measure a short sample so posture insights match your neutral stance.",
        "会采集约 6 秒你的自然坐姿，作为以后的评分基线。",
    ),
    (
        r"""'When you\'re ready, sit comfortably and press "Start calibration".'""",
        "'准备好后，请坐正、放松，然后点「开始录制」。'",
    ),
    ("Start calibration", "开始录制"),
    ("Collecting data... Keep still for six seconds.", "正在录制…请保持不动 6 秒。"),
    ("Baseline captured.", "标准坐姿已录制。"),
    ("- Average posture score: {score:.1f}%", "- 平均坐姿评分：{score:.1f}"),
    ("- Neck angle: {neck:.1f} deg", "- 颈部角度：{neck:.1f}°"),
    ("- Shoulder balance delta: {delta:.3f}", "- 双肩高度差：{delta:.3f}"),
    ("Calibration failed", "录制失败"),
    ('self.tr("Calibration")', 'self.tr("录制标准坐姿")'),
    ("Posture Coach Setup", "坐姿校准"),
    ("Unable to access camera", "无法访问摄像头"),
    ("Calibration cancelled", "已取消录制"),
    (
        "No posture data captured",
        "没有采集到坐姿数据，请确保上半身完整出现在画面中。",
    ),
]

ONBOARDING_BUTTONS = '''        self.setButtonText(QWizard.WizardButton.BackButton, "上一步")
        self.setButtonText(QWizard.WizardButton.NextButton, "下一步")
        self.setButtonText(QWizard.WizardButton.FinishButton, "完成")
        self.setButtonText(QWizard.WizardButton.CancelButton, "取消")
'''


def patch_onboarding_zh() -> None:
    """Localise the calibration wizard (welcome / camera / calibration pages)."""
    path = _purelib() / "batesposture" / "ui" / "onboarding.py"
    text = path.read_text(encoding="utf-8")
    if ONBOARDING_ZH_MARKER in text:
        print("[ok] onboarding wizard already localised")
        return
    for old, new in ONBOARDING_ZH_REPLACEMENTS:
        if old not in text:
            raise SystemExit(f"[!] onboarding.py missing string: {old!r}")
        text = text.replace(old, new, 1)
    anchor = "        self.setMinimumWidth(500)\n"
    if anchor not in text:
        raise SystemExit("[!] onboarding.py wizard init changed; add button labels manually")
    text = text.replace(anchor, anchor + ONBOARDING_BUTTONS, 1)
    text = text.replace(
        "from __future__ import annotations\n",
        "from __future__ import annotations\n\n" + ONBOARDING_ZH_MARKER + "\n",
        1,
    )
    path.write_text(text, encoding="utf-8")
    print(f"[ok] onboarding wizard localised -> {path}")


POSE_OVERLAY_MARKER = "# [PostureGuard] CJK overlay"

POSE_OVERLAY_METHOD = '''    # [PostureGuard] CJK overlay
    def _draw_posture_feedback(self, frame: np.ndarray, score: float) -> None:
        runtime = self._settings.runtime
        score_color = (
            0,
            int(min(255, score * 2.55)),
            int(min(255, (100 - score) * 2.55)),
        )
        self._draw_cjk_text(
            frame, f"坐姿评分：{score:.0f} 分", (10, 8), 30, score_color
        )
        if score < runtime.poor_posture_threshold:
            self._draw_cjk_text(
                frame, runtime.default_posture_message, (10, 52), 22, (60, 60, 255)
            )

    @staticmethod
    def _draw_cjk_text(frame: np.ndarray, text: str, origin, size: int, color) -> None:
        from PIL import Image, ImageDraw, ImageFont

        try:
            font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", size)
        except Exception:  # noqa: BLE001 - fall back to the bitmap font
            font = ImageFont.load_default()
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        ImageDraw.Draw(image).text(
            origin,
            text,
            font=font,
            fill=(int(color[2]), int(color[1]), int(color[0])),
        )
        frame[:] = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

'''


def patch_pose_overlay() -> None:
    path = _purelib() / "batesposture" / "ml" / "pose_detector.py"
    text = path.read_text(encoding="utf-8")
    if POSE_OVERLAY_MARKER in text:
        print("[ok] camera score overlay already localised")
        return
    start = text.find(
        "    def _draw_posture_feedback(self, frame: np.ndarray, score: float) -> None:"
    )
    if start < 0:
        raise SystemExit(
            "[!] pose_detector.py layout changed; re-apply the overlay patch manually"
        )
    end = text.find("    @staticmethod\n", start)
    if end < 0:
        raise SystemExit(
            "[!] pose_detector.py layout changed (no @staticmethod anchor)"
        )
    text = text[:start] + POSE_OVERLAY_METHOD + text[end:]
    path.write_text(text, encoding="utf-8")
    print(f"[ok] camera score overlay localised -> {path}")


def patch_all() -> None:
    install_ui_zh()
    patch_dashboard()
    patch_tray()
    patch_recalibrate()
    patch_onboarding_camera()
    patch_onboarding_zh()
    patch_pose_overlay()
    patch_single_instance()
