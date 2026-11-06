"""Chinese UI helpers for the locally patched BatesPosture build.

Contains the basic settings dialog (autostart, reminders, thresholds, camera,
tracking frequency) and small Windows helpers around the "run at login" toggle.
"""

from __future__ import annotations

import os
import winreg
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)

APP_DIR = Path(r"D:\Apps\PostureGuard")
STARTUP_DIR = (
    Path(os.environ.get("APPDATA", ""))
    / "Microsoft"
    / "Windows"
    / "Start Menu"
    / "Programs"
    / "Startup"
)
STARTUP_SHORTCUT = STARTUP_DIR / "BatesPosture 坐姿提醒.lnk"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE = "BatesPosture"
RUN_COMMAND = '"' + str(APP_DIR / "venv" / "Scripts" / "pythonw.exe") + '" -m batesposture'

INTERVAL_CHOICES = [
    ("连续监测（摄像头常开）", 0),
    ("每 5 分钟检查一次", 5),
    ("每 15 分钟检查一次", 15),
    ("每 30 分钟检查一次", 30),
    ("每小时检查一次", 60),
]


def autostart_enabled() -> bool:
    """True when the tray app is registered to start at login."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, RUN_VALUE)
        if "batesposture" in str(value).lower():
            return True
    except OSError:
        pass
    return STARTUP_SHORTCUT.exists()


def set_autostart_enabled(enabled: bool) -> None:
    """Add/remove the login autostart entry (registry Run key)."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            if enabled:
                winreg.SetValueEx(key, RUN_VALUE, 0, winreg.REG_SZ, RUN_COMMAND)
            else:
                try:
                    winreg.DeleteValue(key, RUN_VALUE)
                except FileNotFoundError:
                    pass
    except OSError:
        pass
    # A Start Menu shortcut would launch a second copy; the Run key is enough.
    try:
        if STARTUP_SHORTCUT.exists():
            STARTUP_SHORTCUT.unlink()
    except OSError:
        pass


class BasicSettingsDialog(QDialog):
    """常用设置：开机自启、提醒、阈值、摄像头、检测频率。"""

    def __init__(self, settings, current_interval: Optional[int] = None, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.interval_minutes: Optional[int] = None
        self.setWindowTitle("坐姿提醒 · 设置")
        self.setMinimumWidth(460)

        runtime = settings.runtime
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.autostart_box = QCheckBox("登录 Windows 后自动在后台运行")
        self.autostart_box.setChecked(autostart_enabled())
        form.addRow("开机自启", self.autostart_box)

        self.notify_box = QCheckBox("姿势变差时弹出提醒（提示音 + 右下角卡片）")
        self.notify_box.setChecked(runtime.notifications_enabled)
        form.addRow("姿势提醒", self.notify_box)

        self.focus_box = QCheckBox("专注模式：暂时不弹提醒")
        self.focus_box.setChecked(runtime.focus_mode_enabled)
        form.addRow("专注模式", self.focus_box)

        self.logging_box = QCheckBox("记录分数历史（可在托盘里导出 CSV）")
        self.logging_box.setChecked(runtime.enable_database_logging)
        form.addRow("历史记录", self.logging_box)

        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(30, 95)
        self.threshold_spin.setSuffix(" 分")
        self.threshold_spin.setValue(int(runtime.poor_posture_threshold))
        self.threshold_spin.setToolTip("低于这个分数就提醒你；默认 60 分。")
        form.addRow("提醒阈值", self.threshold_spin)

        self.cooldown_spin = QSpinBox()
        self.cooldown_spin.setRange(1, 60)
        self.cooldown_spin.setSuffix(" 分钟")
        self.cooldown_spin.setValue(max(1, int(runtime.notification_cooldown) // 60))
        self.cooldown_spin.setToolTip("两次提醒之间至少间隔多久，默认 5 分钟。")
        form.addRow("提醒最短间隔", self.cooldown_spin)

        self.camera_spin = QSpinBox()
        self.camera_spin.setRange(0, 3)
        self.camera_spin.setValue(int(runtime.default_camera_id))
        self.camera_spin.setToolTip("默认 0；如果有多台摄像头可改成 1、2、3。")
        form.addRow("摄像头编号", self.camera_spin)

        self.interval_combo = QComboBox()
        for label, minutes in INTERVAL_CHOICES:
            self.interval_combo.addItem(label, minutes)
        current = 0 if current_interval is None else int(current_interval)
        for index in range(self.interval_combo.count()):
            if self.interval_combo.itemData(index) == current:
                self.interval_combo.setCurrentIndex(index)
                break
        form.addRow("检测频率", self.interval_combo)

        hint = QLabel(
            "提示：摄像头编号、检测频率保存后立即生效（会重启一次检测）；"
            "开机自启会写入当前用户的启动项。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #888888; font-size: 11px;")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("保存")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(hint)
        layout.addWidget(buttons)

    def _apply(self) -> None:
        self._settings.update_runtime(
            notifications_enabled=self.notify_box.isChecked(),
            focus_mode_enabled=self.focus_box.isChecked(),
            enable_database_logging=self.logging_box.isChecked(),
            poor_posture_threshold=self.threshold_spin.value(),
            notification_cooldown=self.cooldown_spin.value() * 60,
            default_camera_id=self.camera_spin.value(),
        )
        self._settings.save_all()
        set_autostart_enabled(self.autostart_box.isChecked())
        minutes = self.interval_combo.currentData()
        self.interval_minutes = int(minutes) if minutes is not None else None
        self.accept()
