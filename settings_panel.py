"""The slide-out settings panel: detection thresholds, potion timer, and
hotkey/behaviour toggles.

These widgets are the single source of truth for their values -- the
panel is only ever hidden/shown, never rebuilt.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from .. import __version__
from .style import SETTINGS_PANEL_STYLE

DIVIDER_COLOR = "#1c232c"


class SettingsPanel(QWidget):
    always_on_top_toggled = pyqtSignal(bool)
    change_fish_hotkey_requested = pyqtSignal()
    change_snap_hotkey_requested = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(SETTINGS_PANEL_STYLE)
        self._build()
        self.hide()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Settings")
        title.setObjectName("sp_title")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setObjectName("sp_icon_btn")
        close_btn.clicked.connect(self._on_close)
        header.addWidget(close_btn)
        layout.addLayout(header)
        self._divider(layout)

        aot_row = QHBoxLayout()
        aot_row.addWidget(QLabel("Always on top"))
        aot_row.addStretch()
        self.aot_btn = QPushButton("off")
        self.aot_btn.setObjectName("sp_aot_off")
        self.aot_btn.setCheckable(True)
        self.aot_btn.clicked.connect(self._toggle_always_on_top)
        aot_row.addWidget(self.aot_btn)
        layout.addLayout(aot_row)
        self._divider(layout)

        layout.addWidget(self._section_label("HOTKEYS"))
        fish_row = QHBoxLayout()
        fish_row.addWidget(QLabel("Toggle fishing"))
        fish_row.addStretch()
        self.fish_hk_btn = QPushButton()
        self.fish_hk_btn.setObjectName("sp_hk_btn")
        self.fish_hk_btn.clicked.connect(self.change_fish_hotkey_requested.emit)
        fish_row.addWidget(self.fish_hk_btn)
        layout.addLayout(fish_row)

        pos_row = QHBoxLayout()
        pos_row.addWidget(QLabel("Snap coordinates"))
        pos_row.addStretch()
        self.pos_hk_btn = QPushButton()
        self.pos_hk_btn.setObjectName("sp_hk_btn_blue")
        self.pos_hk_btn.clicked.connect(self.change_snap_hotkey_requested.emit)
        pos_row.addWidget(self.pos_hk_btn)
        layout.addLayout(pos_row)
        self._divider(layout)

        layout.addWidget(self._section_label("DETECTION"))
        flo = QFormLayout()
        flo.setSpacing(9)
        flo.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.threshold_input = QSpinBox()
        self.threshold_input.setMaximum(255)
        self.sensitivity_input = QSpinBox()
        self.sensitivity_input.setMaximum(999)
        flo.addRow("Threshold", self.threshold_input)
        flo.addRow("Sensitivity", self.sensitivity_input)
        layout.addLayout(flo)
        self._divider(layout)

        layout.addWidget(self._section_label("POTIONS"))
        pflo = QFormLayout()
        pflo.setSpacing(9)
        pflo.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.drink_potions_input = QCheckBox()
        self.drink_delay_input = QSpinBox()
        self.drink_delay_input.setMaximum(3600)
        self.drink_key_input = QLineEdit()
        self.drink_key_input.setMaxLength(1)
        self.drink_key_input.setFixedWidth(40)
        pflo.addRow("Enable", self.drink_potions_input)
        pflo.addRow("Interval (sec)", self.drink_delay_input)
        pflo.addRow("Key to drink", self.drink_key_input)
        layout.addLayout(pflo)

        layout.addStretch()
        ver = QLabel(f"TerraFish V2  \u2022  {__version__}")
        ver.setObjectName("sp_version")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ver)

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("sp_section")
        return lbl

    @staticmethod
    def _divider(layout: QVBoxLayout) -> None:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {DIVIDER_COLOR}; max-height: 1px; margin: 2px 0;")
        layout.addWidget(line)

    def _on_close(self) -> None:
        self.hide()
        self.closed.emit()

    def _toggle_always_on_top(self, checked: bool) -> None:
        self.aot_btn.setText("on" if checked else "off")
        self.aot_btn.setObjectName("sp_aot_on" if checked else "sp_aot_off")
        self.aot_btn.style().unpolish(self.aot_btn)
        self.aot_btn.style().polish(self.aot_btn)
        self.always_on_top_toggled.emit(checked)

    def refresh_hotkey_labels(self, fish_key: str, snap_key: str) -> None:
        self.fish_hk_btn.setText(fish_key.upper())
        self.pos_hk_btn.setText(snap_key.upper())

    def set_enabled_for_fishing(self, enabled: bool) -> None:
        for widget in (
            self.threshold_input, self.sensitivity_input,
            self.drink_potions_input, self.drink_delay_input,
            self.drink_key_input,
        ):
            widget.setEnabled(enabled)
