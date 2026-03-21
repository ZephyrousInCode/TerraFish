#!/usr/bin/env python3
 
from PyQt6.QtGui import QPixmap, QCursor, QImage, QColor, QPalette, QFont
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtWidgets import (
    QLabel, QCheckBox, QFrame, QFormLayout, QHBoxLayout,
    QLineEdit, QPushButton, QVBoxLayout, QApplication,
    QMainWindow, QWidget, QSpinBox, QInputDialog,
    QMessageBox, QProgressBar, QListWidget, QDialog,
    QGridLayout, QSizePolicy, QToolButton, QScrollArea,
    QStackedWidget, QGraphicsDropShadowEffect
)
 
from PIL import Image, ImageGrab
from PIL.ImageQt import ImageQt
 
from pynput.keyboard import Listener
 
import sys
import cv2
import time
import numpy
import pyautogui
import subprocess
import configparser
 
 
__version__ = '1.0 beta'
__author__ = 'ZephyrousInCode'
 
STYLE = """
QMainWindow, QWidget {
    background-color: #0f0f0f;
    color: #e0e0e0;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
}
QLabel {
    color: #a0a0a0;
}
QLabel#title {
    color: #ffffff;
    font-size: 15px;
    font-weight: bold;
    letter-spacing: 3px;
}
QLabel#version_label {
    color: #3a3a3a;
    font-size: 10px;
}
 
/* ── Base button ── */
QPushButton {
    background-color: #161616;
    color: #888888;
    border: 1px solid #242424;
    padding: 6px 14px;
    border-radius: 4px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 11px;
    letter-spacing: 0.5px;
    text-align: left;
}
QPushButton:hover {
    background-color: #1e1e1e;
    border: 1px solid #383838;
    color: #cccccc;
}
QPushButton:pressed {
    background-color: #111111;
    color: #aaaaaa;
}
QPushButton:disabled {
    color: #2a2a2a;
    border-color: #1a1a1a;
    background-color: #111111;
}
 
/* ── Start button ── */
QPushButton#start_btn {
    background-color: #111f11;
    color: #4ade80;
    border: 1px solid #1f3d1f;
    font-size: 12px;
    padding: 10px 14px;
    letter-spacing: 1px;
    text-align: center;
}
QPushButton#start_btn:hover {
    background-color: #162816;
    border: 1px solid #3a7a3a;
    color: #6eeea0;
}
QPushButton#start_btn[active="true"] {
    background-color: #1f1111;
    color: #f87171;
    border: 1px solid #3d1f1f;
}
QPushButton#start_btn[active="true"]:hover {
    border: 1px solid #7a3a3a;
    color: #ff9090;
}
 
/* ── Icon-only buttons (⚙ ✕ ＋ ✎ 🗑) ── */
QPushButton#icon_btn {
    background-color: transparent;
    border: none;
    color: #3a3a3a;
    font-size: 15px;
    padding: 4px 6px;
    text-align: center;
}
QPushButton#icon_btn:hover {
    color: #888888;
    background-color: #1a1a1a;
    border-radius: 4px;
}
QPushButton#icon_btn[active="true"] {
    color: #4ade80;
}
 
/* ── Inputs ── */
QSpinBox {
    background-color: #141414;
    color: #cccccc;
    border: 1px solid #242424;
    border-radius: 3px;
    padding: 4px 6px;
    font-family: 'Consolas', monospace;
}
QSpinBox:focus {
    border: 1px solid #383838;
    color: #e0e0e0;
}
QCheckBox {
    color: #888888;
    spacing: 8px;
    font-size: 11px;
}
QCheckBox::indicator {
    width: 13px; height: 13px;
    border-radius: 2px;
    border: 1px solid #2a2a2a;
    background: #141414;
}
QCheckBox::indicator:checked {
    background: #4ade80;
    border-color: #4ade80;
}
 
/* ── List ── */
QListWidget {
    background-color: #0d0d0d;
    border: 1px solid #1e1e1e;
    border-radius: 4px;
    color: #666666;
    outline: none;
    font-size: 11px;
}
QListWidget::item {
    padding: 4px 8px;
}
QListWidget::item:selected {
    background-color: #111f11;
    color: #4ade80;
    border-left: 2px solid #4ade80;
}
QListWidget::item:hover:!selected {
    background-color: #141414;
    color: #888888;
}
 
/* ── Progress bar ── */
QProgressBar {
    background-color: #0d0d0d;
    border: none;
    border-radius: 2px;
    height: 4px;
}
QProgressBar::chunk {
    background-color: #4ade80;
    border-radius: 2px;
}
 
QScrollArea { border: none; }
"""
 
def mouse_click():
    if sys.platform == 'linux':
        subprocess.call(['xdotool', 'mousedown', '1'])
        time.sleep(0.02)
        subprocess.call(['xdotool', 'mouseup', '1'])
    elif sys.platform == 'win32':
        pyautogui.mouseDown()
        time.sleep(0.02)
        pyautogui.mouseUp()
    else:
        raise RuntimeError("Unsupported platform: {0}".format(sys.platform))
 
 
 
class InitializationFisherState():
    def __init__(self):
        self.code = "INIT"
        self.description = "Waiting to start..."
 
    def update(self, sense):
        if sense > 1:
            return CastingFisherState(cast=False)
        return None
 
class CastingFisherState():
    def __init__(self, cast=True):
        self.code = "CAST"
        self.description = "Casting the line"
        self.created_at = time.time()
        if cast: mouse_click()
 
    def update(self, sense):
        if (time.time() - self.created_at) > 1 and sense < 1:
            return WaitingFisherState()
        return None
 
class WaitingFisherState():
    def __init__(self):
        self.code = "WAIT"
        self.description = "Waiting for bite..."
        self.created_at = time.time()
 
    def update(self, sense):
        if (time.time() - self.created_at) > 1 and sense > 1:
            return ReelingInFisherState()
        return None
 
class ReelingInFisherState():
    def __init__(self):
        self.code = "REEL"
        self.description = "Hooked! Reeling in"
        self.created_at = time.time()
        mouse_click()
 
    def update(self, sense):
        if (time.time() - self.created_at) > 0.5 and sense < 1:
            return CastingFisherState()
        return None
 
class FisherStateMachine():
    def __init__(self):
        self.state = InitializationFisherState()
 
    def update(self, sense):
        result = self.state.update(sense)
        if result:
            self.state = result
 
 
class MovementTracker():
    def __init__(self, n):
        self.change_buffer = None
        self.size = n
        self.counter = 0
 
    def get_diff(self, img, trsh):
        if not self.change_buffer:
            self.change_buffer = [img for _ in range(self.size)]
        self.change_buffer[self.counter] = img
        self.counter = (self.counter + 1) % self.size
        buff = self.change_buffer[self.counter:] + self.change_buffer[:self.counter]
        return self.diff_3_img(buff[:3], trsh)
 
    def diff_3_img(self, buff, trsh):
        t0, t1, t2 = buff
        d1 = cv2.absdiff(t2, t1)
        d2 = cv2.absdiff(t1, t0)
        res = cv2.bitwise_or(d1, d2)
        _, res = cv2.threshold(res, trsh, 255, cv2.THRESH_BINARY)
        return res
 
 
 
class SettingsPanel(QWidget):
    def __init__(self, parent_app):
        super().__init__(parent_app)
        self.app = parent_app
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            SettingsPanel {
                background-color: #0d0d0d;
                border-left: 1px solid #1e1e1e;
            }
            SettingsPanel QLabel {
                color: #909090;
                background-color: transparent;
                font-size: 11px;
            }
            SettingsPanel QLabel#sp_title {
                color: #e8e8e8;
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 3px;
                background-color: transparent;
            }
            SettingsPanel QLabel#sp_section {
                color: #505050;
                font-size: 9px;
                letter-spacing: 3px;
                background-color: transparent;
            }
            SettingsPanel QLabel#sp_version {
                color: #222222;
                font-size: 10px;
                background-color: transparent;
            }
            SettingsPanel QPushButton {
                background-color: #161616;
                color: #aaaaaa;
                border: 1px solid #242424;
                padding: 5px 12px;
                border-radius: 4px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                text-align: left;
            }
            SettingsPanel QPushButton:hover {
                background-color: #1e1e1e;
                border: 1px solid #383838;
                color: #cccccc;
            }
            SettingsPanel QPushButton#sp_icon_btn {
                background-color: transparent;
                border: none;
                color: #333333;
                font-size: 15px;
                padding: 4px 6px;
            }
            SettingsPanel QPushButton#sp_icon_btn:hover {
                color: #888888;
                background-color: #1a1a1a;
                border-radius: 4px;
            }
            SettingsPanel QPushButton#sp_hk_btn {
                background-color: #111f11;
                border: 1px solid #1f3d1f;
                color: #4ade80;
                font-size: 11px;
                padding: 3px 10px;
                border-radius: 3px;
                min-width: 28px;
                text-align: center;
            }
            SettingsPanel QPushButton#sp_hk_btn:hover {
                border-color: #3a7a3a;
                color: #6eeea0;
            }
            SettingsPanel QPushButton#sp_hk_btn_blue {
                background-color: #111a2a;
                border: 1px solid #1f2f4a;
                color: #60a5fa;
                font-size: 11px;
                padding: 3px 10px;
                border-radius: 3px;
                min-width: 28px;
                text-align: center;
            }
            SettingsPanel QPushButton#sp_hk_btn_blue:hover {
                border-color: #3a6aaa;
                color: #80c0ff;
            }
            SettingsPanel QPushButton#sp_aot_on {
                background-color: #111f11;
                color: #4ade80;
                border: 1px solid #1f3d1f;
                padding: 4px 12px;
                border-radius: 3px;
                font-size: 11px;
                text-align: center;
            }
            SettingsPanel QPushButton#sp_aot_off {
                background-color: #141414;
                color: #777777;
                border: 1px solid #1e1e1e;
                padding: 4px 12px;
                border-radius: 3px;
                font-size: 11px;
                text-align: center;
            }
            SettingsPanel QPushButton#sp_aot_off:hover {
                color: #666666;
                border-color: #333333;
            }
            SettingsPanel QSpinBox {
                background-color: #141414;
                color: #cccccc;
                border: 1px solid #242424;
                border-radius: 3px;
                padding: 4px 6px;
                font-family: 'Consolas', monospace;
            }
            SettingsPanel QCheckBox {
                color: #909090;
                spacing: 8px;
                background-color: transparent;
                font-size: 11px;
            }
            SettingsPanel QCheckBox::indicator {
                width: 13px; height: 13px;
                border-radius: 2px;
                border: 1px solid #2a2a2a;
                background: #141414;
            }
            SettingsPanel QCheckBox::indicator:checked {
                background: #4ade80;
                border-color: #4ade80;
            }
            SettingsPanel QFrame {
                color: #1a1a1a;
            }
        """)
        self._build()
        self.hide()
 
    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)
 
        header = QHBoxLayout()
        title = QLabel("SETTINGS")
        title.setObjectName("sp_title")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setObjectName("sp_icon_btn")
        close_btn.clicked.connect(self.hide)
        header.addWidget(close_btn)
        layout.addLayout(header)
 
        self._divider(layout)
 
        aot_row = QHBoxLayout()
        aot_lbl = QLabel("Always on top")
        aot_row.addWidget(aot_lbl)
        aot_row.addStretch()
        self.aot_btn = QPushButton("○  off")
        self.aot_btn.setObjectName("sp_aot_off")
        self.aot_btn.setCheckable(True)
        self.aot_btn.clicked.connect(self._toggle_always_on_top)
        aot_row.addWidget(self.aot_btn)
        layout.addLayout(aot_row)
 
        self._divider(layout)
 
        sec1 = QLabel("HOTKEYS")
        sec1.setObjectName("sp_section")
        layout.addWidget(sec1)
 
        fish_row = QHBoxLayout()
        fish_row.addWidget(QLabel("Toggle fishing"))
        fish_row.addStretch()
        self.fish_hk_btn = QPushButton()
        self.fish_hk_btn.setObjectName("sp_hk_btn")
        self.fish_hk_btn.clicked.connect(self.app._change_hotkey)
        fish_row.addWidget(self.fish_hk_btn)
        layout.addLayout(fish_row)
 
        pos_row = QHBoxLayout()
        pos_row.addWidget(QLabel("Snap coordinates"))
        pos_row.addStretch()
        self.pos_hk_btn = QPushButton()
        self.pos_hk_btn.setObjectName("sp_hk_btn_blue")
        self.pos_hk_btn.clicked.connect(self.app._change_pos_hotkey)
        pos_row.addWidget(self.pos_hk_btn)
        layout.addLayout(pos_row)
 
        self._divider(layout)
 
        sec2 = QLabel("DETECTION")
        sec2.setObjectName("sp_section")
        layout.addWidget(sec2)
 
        flo = QFormLayout()
        flo.setSpacing(8)
        flo.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.input_treshold = QSpinBox()
        self.input_sensivity = QSpinBox()
        self.input_treshold.setMaximum(255)
        self.input_sensivity.setMaximum(999)
        flo.addRow("Threshold", self.input_treshold)
        flo.addRow("Sensitivity", self.input_sensivity)
        layout.addLayout(flo)
 
        self._divider(layout)
 
        sec3 = QLabel("POTIONS")
        sec3.setObjectName("sp_section")
        layout.addWidget(sec3)
 
        pflo = QFormLayout()
        pflo.setSpacing(8)
        pflo.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.input_drink_potions = QCheckBox()
        self.input_drink_delay = QSpinBox()
        self.input_drink_delay.setMaximum(3600)
        pflo.addRow("Enable", self.input_drink_potions)
        pflo.addRow("Interval (sec)", self.input_drink_delay)
        layout.addLayout(pflo)
 
        layout.addStretch()
 
        ver = QLabel("TerraFish v" + __version__)
        ver.setObjectName("sp_version")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ver)
 
    def _divider(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
 
    def _toggle_always_on_top(self, checked):
        win = self.app
        if checked:
            win.setWindowFlags(win.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            self.aot_btn.setText("●  on")
            self.aot_btn.setObjectName("sp_aot_on")
        else:
            win.setWindowFlags(win.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            self.aot_btn.setText("○  off")
            self.aot_btn.setObjectName("sp_aot_off")
        self.aot_btn.style().unpolish(self.aot_btn)
        self.aot_btn.style().polish(self.aot_btn)
        win.show()
 
    def refresh_hotkey_labels(self):
        self.fish_hk_btn.setText(self.app._hotkey.upper())
        self.pos_hk_btn.setText(self.app._update_pos_hotkey.upper())
 
    def sync_to_app(self, app):
        app.input_treshold.setValue(self.input_treshold.value())
        app.input_sensivity.setValue(self.input_sensivity.value())
        app.input_drink_potions.setChecked(self.input_drink_potions.isChecked())
        app.input_drink_delay.setValue(self.input_drink_delay.value())
 
 
 
shift = 50
 
class AppUi(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tracker = MovementTracker(3)
        self.state_machine = None
        self.potion_drink_time = None
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.setWindowTitle('TerraFish')
        self.setMouseTracking(True)
        self.setMinimumWidth(340)
        self.setFixedWidth(340)
        self._hotkey = 'f'
        self._update_pos_hotkey = 'v'
        self._init_hidden_inputs()
        self._init_layout()
 
    def _init_hidden_inputs(self):
        """Hidden inputs kept for config/logic compatibility"""
        self.input_screen_x = QSpinBox()
        self.input_screen_y = QSpinBox()
        self.input_treshold = QSpinBox()
        self.input_sensivity = QSpinBox()
        self.input_drink_potions = QCheckBox()
        self.input_drink_delay = QSpinBox()
        self.input_screen_x.setMaximum(QApplication.primaryScreen().size().width())
        self.input_screen_y.setMaximum(QApplication.primaryScreen().size().height())
        self.input_treshold.setMaximum(255)
        self.input_sensivity.setMaximum(999)
        self.input_drink_delay.setMaximum(3600)
 
    def _init_layout(self):
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
 
        root = QVBoxLayout(self._centralWidget)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
 
        topbar = QWidget()
        topbar.setFixedHeight(44)
        topbar.setStyleSheet("background-color: #0a0a0a; border-bottom: 1px solid #1a1a1a;")
        tbl = QHBoxLayout(topbar)
        tbl.setContentsMargins(14, 0, 10, 0)
 
        title = QLabel("TERRAFISH")
        title.setObjectName("title")
        tbl.addWidget(title)
        tbl.addStretch()
 
        self.settings_btn = QPushButton("[ = ]")
        self.settings_btn.setObjectName("icon_btn")
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self._toggle_settings)
        tbl.addWidget(self.settings_btn)
 
        root.addWidget(topbar)
 
        self.content_area = QWidget()
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(14, 14, 14, 14)
        content_layout.setSpacing(10)
 
        previews = QHBoxLayout()
        previews.setSpacing(8)
        self.label1 = QLabel()
        self.label1.setStyleSheet("border: 1px solid #1f1f1f; border-radius: 3px; background-color: #050505;")
        self.label1.setFixedSize(shift*2, shift*2)
        self.label2 = QLabel()
        self.label2.setStyleSheet("border: 1px solid #1f1f1f; border-radius: 3px; background-color: #050505;")
        self.label2.setFixedSize(shift*2, shift*2)
        previews.addWidget(self.label1)
        previews.addWidget(self.label2)
        previews.addStretch()
 
        badge_col = QVBoxLayout()
        badge_col.addStretch()
        self.state_code_label = QLabel("IDLE")
        self.state_code_label.setObjectName("status_code")
        self.state_code_label.setStyleSheet("color: #2a2a2a; font-size: 22px; font-weight: bold; letter-spacing: 2px;")
        badge_col.addWidget(self.state_code_label)
        badge_col.addStretch()
        previews.addLayout(badge_col)
        content_layout.addLayout(previews)
 
        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        content_layout.addWidget(self.progress)
 
        self.state_status = QLabel("Ready")
        self.state_status.setStyleSheet("color: #4a4a4a; font-size: 11px;")
        content_layout.addWidget(self.state_status)
 
        self.potion_status = QLabel("")
        self.potion_status.setStyleSheet("color: #3a3a3a; font-size: 10px;")
        content_layout.addWidget(self.potion_status)
 
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #1a1a1a; margin: 4px 0;")
        content_layout.addWidget(line)
 
        coord_row = QHBoxLayout()
        coord_row.setSpacing(6)
        x_lbl = QLabel("X")
        x_lbl.setStyleSheet("color: #3a3a3a; font-size: 11px;")
        coord_row.addWidget(x_lbl)
        self.vis_x = QSpinBox()
        self.vis_x.setMaximum(QApplication.primaryScreen().size().width())
        self.vis_x.setFixedWidth(70)
        coord_row.addWidget(self.vis_x)
 
        y_lbl = QLabel("Y")
        y_lbl.setStyleSheet("color: #3a3a3a; font-size: 11px;")
        coord_row.addWidget(y_lbl)
        self.vis_y = QSpinBox()
        self.vis_y.setMaximum(QApplication.primaryScreen().size().height())
        self.vis_y.setFixedWidth(70)
        coord_row.addWidget(self.vis_y)
 
        self.snap_btn = QPushButton("[ + ]  snap")
        self.snap_btn.setToolTip("Snap to mouse position [{}]".format(self._update_pos_hotkey))
        self.snap_btn.clicked.connect(self._xy_pos_update)
        coord_row.addWidget(self.snap_btn)
        coord_row.addStretch()
        content_layout.addLayout(coord_row)
 
        self.mouse_status = QLabel("")
        self.mouse_status.setStyleSheet("color: #2a2a2a; font-size: 10px;")
        content_layout.addWidget(self.mouse_status)
 
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setStyleSheet("color: #1a1a1a; margin: 4px 0;")
        content_layout.addWidget(line2)
 
        self.start = QPushButton("[ > ]  start fishing")
        self.start.setObjectName("start_btn")
        self.start.setProperty("active", "false")
        self.start.clicked.connect(self._on_push_button)
        content_layout.addWidget(self.start)
 
        bottom_row = QHBoxLayout()
        self.save = QPushButton(" save preset ")
        self.save.clicked.connect(self._save_config)
        bottom_row.addWidget(self.save)
 
        self.b_create_preset = QPushButton("[ + ]")
        self.b_create_preset.setObjectName("icon_btn")
        self.b_create_preset.setFixedWidth(48)
        self.b_create_preset.setToolTip("Add preset")
        self.b_create_preset.clicked.connect(self._add_preset)
        bottom_row.addWidget(self.b_create_preset)
 
        self.b_rename_preset = QPushButton("[ ~ ]")
        self.b_rename_preset.setObjectName("icon_btn")
        self.b_rename_preset.setFixedWidth(48)
        self.b_rename_preset.setToolTip("Rename preset")
        self.b_rename_preset.clicked.connect(self._rename_preset)
        bottom_row.addWidget(self.b_rename_preset)
 
        self.b_delete_preset = QPushButton("[ - ]")
        self.b_delete_preset.setObjectName("icon_btn")
        self.b_delete_preset.setFixedWidth(48)
        self.b_delete_preset.setToolTip("Delete preset")
        self.b_delete_preset.clicked.connect(self._del_preset)
        bottom_row.addWidget(self.b_delete_preset)
 
        content_layout.addLayout(bottom_row)
 
        self.list = QListWidget()
        self.list.setFixedHeight(90)
        content_layout.addWidget(self.list)
 
        content_layout.addStretch()
        root.addWidget(self.content_area)
 
        self.settings_panel = SettingsPanel(self)
        self.settings_panel.hide()
 
        self._hotkey_listener = Listener(on_press=self._keypress_event)
        self._hotkey_listener.start()
 
        self._update_list_from_config()
        self._load_config()
        self.list.itemSelectionChanged.connect(self._on_preset_changed)
 
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_display)
        self.timer.setInterval(66)
        self.timer.start()
 
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'settings_panel') and self.settings_panel.isVisible():
            self._position_settings_panel()
 
    def _position_settings_panel(self):
        w = min(260, self.width())
        self.settings_panel.setGeometry(self.width() - w, 44, w, self.height() - 44)
 
    def _toggle_settings(self):
        if self.settings_panel.isVisible():
            self.settings_panel.hide()
            self.settings_btn.setProperty("active", "false")
        else:
            self.settings_panel.input_treshold.setValue(self.input_treshold.value())
            self.settings_panel.input_sensivity.setValue(self.input_sensivity.value())
            self.settings_panel.input_drink_potions.setChecked(self.input_drink_potions.isChecked())
            self.settings_panel.input_drink_delay.setValue(self.input_drink_delay.value())
            self.settings_panel.refresh_hotkey_labels()
            self._position_settings_panel()
            self.settings_panel.show()
            self.settings_panel.raise_()
            self.settings_btn.setProperty("active", "true")
        self.settings_btn.style().unpolish(self.settings_btn)
        self.settings_btn.style().polish(self.settings_btn)
 
    def _get_treshold(self):
        if self.settings_panel.isVisible():
            return self.settings_panel.input_treshold.value()
        return self.input_treshold.value()
 
    def _get_sensivity(self):
        if self.settings_panel.isVisible():
            return self.settings_panel.input_sensivity.value()
        return self.input_sensivity.value()
 
    def _get_drink_potions(self):
        if self.settings_panel.isVisible():
            return self.settings_panel.input_drink_potions.isChecked()
        return self.input_drink_potions.isChecked()
 
    def _get_drink_delay(self):
        if self.settings_panel.isVisible():
            return self.settings_panel.input_drink_delay.value()
        return self.input_drink_delay.value()
 
    def _keypress_event(self, key):
        try:
            if self._hotkey == key.char:
                QTimer.singleShot(0, self._on_push_button)
            elif self._update_pos_hotkey == key.char:
                QTimer.singleShot(0, self._xy_pos_update)
        except AttributeError:
            return
 
    def _change_hotkey(self):
        if self._hotkey_listener.running:
            self._hotkey_listener.stop()
        dialog = QDialog(self)
        dialog.keyPressEvent = lambda key: self._assign_hotkey(key, dialog)
        dialog.setWindowTitle('Press desired fishing hotkey')
        dialog.setFixedSize(240, 60)
        dialog.exec()
        self._hotkey_listener = Listener(on_press=self._keypress_event)
        self._hotkey_listener.start()
        self.settings_panel.refresh_hotkey_labels()
 
    def _assign_hotkey(self, key, dialog):
        if key.text() != '' and key.text() != self._update_pos_hotkey:
            self._hotkey = key.text()
        dialog.close()
 
    def _change_pos_hotkey(self):
        if self._hotkey_listener.running:
            self._hotkey_listener.stop()
        dialog = QDialog(self)
        dialog.keyPressEvent = lambda key: self._assign_pos_hotkey(key, dialog)
        dialog.setWindowTitle('Press desired snap hotkey')
        dialog.setFixedSize(240, 60)
        dialog.exec()
        self._hotkey_listener = Listener(on_press=self._keypress_event)
        self._hotkey_listener.start()
        self.settings_panel.refresh_hotkey_labels()
        self.snap_btn.setToolTip("Snap to mouse position [{}]".format(self._update_pos_hotkey))
 
    def _assign_pos_hotkey(self, key, dialog):
        if key.text() != '' and key.text() != self._hotkey:
            self._update_pos_hotkey = key.text()
        dialog.close()
 
    def _xy_pos_update(self):
        pos = pyautogui.position()
        self.vis_x.setValue(pos.x)
        self.vis_y.setValue(pos.y)
        self.input_screen_x.setValue(pos.x)
        self.input_screen_y.setValue(pos.y)
 
    def _update_list_from_config(self):
        self.list.clear()
        for each in self.config.keys():
            self.list.addItem((each + '.')[:-1])
        self.list.setCurrentRow(0)
 
    def _add_preset(self):
        text, ok = QInputDialog.getText(self, 'New preset', 'Preset name:')
        if ok and text:
            self.list.addItem(text)
            self.list.setCurrentRow(self.list.count() - 1)
            self._save_config()
 
    def _rename_preset(self):
        preset = self._get_current_preset()
        if preset == 'DEFAULT':
            QMessageBox.critical(self, "Nope", "DEFAULT preset cannot be renamed")
            return
        text, ok = QInputDialog.getText(self, 'Rename preset', 'New name:', text=preset)
        if ok and text and text != preset:
            if preset in self.config:
                self.config[text] = dict(self.config[preset])
                self.config.remove_section(preset)
            row = self.list.currentRow()
            self.list.takeItem(row)
            self.list.insertItem(row, text)
            self.list.setCurrentRow(row)
            self._save_config()
 
    def _del_preset(self):
        if self.list.count() <= 1:
            QMessageBox.warning(self, "Warning", "Can't delete the last preset")
            return
        preset = self._get_current_preset()
        if preset == 'DEFAULT':
            QMessageBox.critical(self, "Nope", "DEFAULT preset cannot be deleted")
            return
        reply = QMessageBox.question(self, 'Delete', 'Delete "{}"?'.format(preset),
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.list.takeItem(self.list.currentRow())
            self.config.remove_section(preset)
            self._update_list_from_config()
            self._save_config()
 
    def _on_preset_changed(self):
        self._load_config()
 
    def _load_config(self):
        name = self._get_current_preset()
        if not name:
            return
        if name not in self.config:
            self.config[name] = {}
        x = int(self.config[name].get('screen_x', 850))
        y = int(self.config[name].get('screen_y', 850))
        self.vis_x.setValue(x)
        self.vis_y.setValue(y)
        self.input_screen_x.setValue(x)
        self.input_screen_y.setValue(y)
        self.input_treshold.setValue(int(self.config[name].get('treshold', 6)))
        self.input_sensivity.setValue(int(self.config[name].get('sensivity', 55)))
        self.input_drink_potions.setChecked(self.config[name].get('drink_potions', 'False') == 'True')
        self.input_drink_delay.setValue(int(self.config[name].get('drink_delay', 185)))
 
    def _save_config(self):
        name = self._get_current_preset()
        if not name:
            return
        if self.settings_panel.isVisible():
            self.settings_panel.sync_to_app(self)
        if name not in self.config:
            self.config[name] = {}
        self.config[name]['screen_x'] = str(self.vis_x.value())
        self.config[name]['screen_y'] = str(self.vis_y.value())
        self.config[name]['treshold'] = str(self.input_treshold.value())
        self.config[name]['sensivity'] = str(self.input_sensivity.value())
        self.config[name]['drink_potions'] = str(self.input_drink_potions.isChecked())
        self.config[name]['drink_delay'] = str(self.input_drink_delay.value())
        self.config[name]['button_to_drink'] = 'b'
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)
 
    def _on_push_button(self):
        if self.state_machine:
            self.state_machine = None
            self.potion_drink_time = None
            self.start.setText("[ > ]  start fishing")
            self.start.setProperty("active", "false")
            self._set_enabled(True)
        else:
            self.state_machine = FisherStateMachine()
            self.potion_drink_time = time.time()
            self.start.setText("[ . ]  stop fishing")
            self.start.setProperty("active", "true")
            self._set_enabled(False)
        self.start.style().unpolish(self.start)
        self.start.style().polish(self.start)
 
    def _set_enabled(self, state):
        self.save.setEnabled(state)
        self.vis_x.setEnabled(state)
        self.vis_y.setEnabled(state)
        self.snap_btn.setEnabled(state)
        self.b_create_preset.setEnabled(state)
        self.b_rename_preset.setEnabled(state)
        self.b_delete_preset.setEnabled(state)
        self.list.setEnabled(state)
        self.settings_btn.setEnabled(state)
        if hasattr(self, 'settings_panel'):
            self.settings_panel.input_treshold.setEnabled(state)
            self.settings_panel.input_sensivity.setEnabled(state)
            self.settings_panel.input_drink_potions.setEnabled(state)
            self.settings_panel.input_drink_delay.setEnabled(state)
 
    def _get_current_preset(self):
        item = self.list.currentItem()
        return item.text() if item else None
 
    def _update_display(self):
        x = self.vis_x.value()
        y = self.vis_y.value()
        t = self._get_treshold()
 
        im = ImageGrab.grab((x - shift, y - shift, x + shift, y + shift))
        frame = cv2.cvtColor(numpy.array(im), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        preview = self.tracker.get_diff(gray, t)
        count = cv2.countNonZero(preview)
        sense = count * self._get_sensivity() / ((shift * 2) ** 2)
 
        if self.state_machine:
            self.state_machine.update(sense)
 
        pixmap1 = QPixmap.fromImage(ImageQt(im))
        self.label1.setPixmap(pixmap1)
        h, w = preview.shape
        cv2qimg = QImage(preview.data, w, h, w, QImage.Format.Format_Grayscale8)
        self.label2.setPixmap(QPixmap.fromImage(cv2qimg))
 
        self.progress.setValue(min(100, int(sense * 100)))
 
        if self.state_machine:
            state = self.state_machine.state
            self.state_code_label.setText(state.code)
            colors = {"REEL": "#4ade80", "WAIT": "#60a5fa", "CAST": "#facc15", "INIT": "#888888"}
            c = colors.get(state.code, "#888888")
            self.state_code_label.setStyleSheet(
                "color: {}; font-size: 22px; font-weight: bold; letter-spacing: 2px;".format(c))
            self.state_status.setText(state.description)
            self.mouse_status.setText("")
        else:
            self.state_code_label.setText("IDLE")
            self.state_code_label.setStyleSheet(
                "color: #2a2a2a; font-size: 22px; font-weight: bold; letter-spacing: 2px;")
            coords = QCursor.pos()
            self.mouse_status.setText("cursor ({}, {})".format(coords.x(), coords.y()))
            self.state_status.setText("preset: {}".format(self._get_current_preset()))
 
        drink_potions = self._get_drink_potions()
        drink_delay = self._get_drink_delay()
        if drink_potions:
            if self.potion_drink_time:
                drinking_in = int(self.potion_drink_time + drink_delay - time.time())
                self.potion_status.setText("potion in {}s".format(max(0, drinking_in)))
                if drinking_in <= 0:
                    btn = self.config[self._get_current_preset()].get('button_to_drink', 'b')
                    self.potion_drink_time = time.time()
                    pyautogui.keyDown(btn)
                    time.sleep(0.02)
                    pyautogui.keyUp(btn)
            else:
                self.potion_status.setText("potion every {}s".format(drink_delay))
        else:
            self.potion_status.setText("")
 
 
def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    view = AppUi()
    view.show()
    sys.exit(app.exec())
 
if __name__ == '__main__':
    main()