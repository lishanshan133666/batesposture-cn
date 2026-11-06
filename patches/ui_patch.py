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
    patch_pose_overlay()
