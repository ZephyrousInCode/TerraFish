"""Main application window for TerraFish V2."""
from __future__ import annotations

import logging

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCloseEvent, QCursor, QImage, QKeyEvent, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QDialog, QFrame, QHBoxLayout, QInputDialog, QLabel,
    QListWidget, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QSpinBox, QVBoxLayout, QWidget,
)
from pynput.keyboard import Listener

from .. import __display_badge__, __display_name__
from ..capture_worker import CaptureWorker
from ..config import DEFAULT_PRESET, ConfigManager, PresetSettings
from ..vision import CaptureRegion
from .settings_panel import SettingsPanel

logger = logging.getLogger(__name__)

PREVIEW_SIZE = 84

# (background tint, foreground) per fishing state, used for the status pill
STATE_STYLES = {
    "REEL": ("#3a2420", "#ff8a72"),
    "WAIT": ("#173733", "#45d6c4"),
    "CAST": ("#3a2f18", "#f0b268"),
}
IDLE_STYLE = ("#1c232c", "#525d6a")
PILL_TEMPLATE = (
    "background-color: {bg}; color: {fg}; border-radius: 9px; "
    "padding: 4px 11px; font-size: 10px; font-weight: 700; letter-spacing: 0.6px;"
)


class HotkeyCaptureDialog(QDialog):
    """Small modal that captures the next key press as a new hotkey.

    Bug fix: QKeyEvent.text() for Escape returns a non-empty control
    character (ASCII 0x1B), so a naive `if text: ...` check treats
    Escape as a valid captured key instead of a cancel. Escape (and a
    couple of other non-printable keys) must be handled explicitly
    *before* falling through to the generic "any printable key" case.
    """

    _CANCEL_KEYS = {
        Qt.Key.Key_Escape,
        Qt.Key.Key_Tab,
        Qt.Key.Key_Backtab,
    }

    def __init__(self, title: str, forbidden: str, parent=None):
        super().__init__(parent)
        self.forbidden = forbidden.lower()
        self.result_key: str | None = None
        self.setWindowTitle(title)
        self.setFixedSize(260, 70)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Press any key... (Esc to cancel)"))

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 (Qt override)
        if event.key() in self._CANCEL_KEYS:
            self.reject()
            return
        text = event.text()
        if text and text.isprintable() and text.lower() != self.forbidden:
            self.result_key = text
            self.accept()
        # otherwise: not a usable/printable key, or it's the other
        # hotkey -- ignore and keep waiting for a valid press.


class AppUi(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.fishing = False
        self._fish_hotkey = "f"
        self._snap_hotkey = "v"

        self.setWindowTitle(f"{__display_name__} {__display_badge__}")
        self.setMinimumWidth(360)
        self.setFixedWidth(360)

        self._build_ui()
        self._create_worker()
        self._start_hotkey_listener()

        self._refresh_preset_list()
        self._load_preset(self._current_preset_name() or DEFAULT_PRESET)
        self.settings_panel.refresh_hotkey_labels(self._fish_hotkey, self._snap_hotkey)

        self.worker.start()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_topbar())

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(12)

        content_layout.addWidget(self._build_capture_card())
        content_layout.addWidget(self._build_position_card())

        self.start_btn = QPushButton("Start fishing")
        self.start_btn.setObjectName("primary_btn")
        self.start_btn.setProperty("active", "false")
        self.start_btn.clicked.connect(self.toggle_fishing)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        content_layout.addWidget(self.start_btn)

        content_layout.addWidget(self._build_presets_card())
        content_layout.addStretch()
        root.addWidget(content)

        self.settings_panel = SettingsPanel(self)
        self.settings_panel.always_on_top_toggled.connect(self._set_always_on_top)
        self.settings_panel.change_fish_hotkey_requested.connect(
            lambda: self._capture_hotkey("fish"))
        self.settings_panel.change_snap_hotkey_requested.connect(
            lambda: self._capture_hotkey("snap"))
        self.settings_panel.closed.connect(self._on_settings_closed)

    def _build_topbar(self) -> QWidget:
        topbar = QWidget()
        topbar.setFixedHeight(48)
        topbar.setStyleSheet("background-color: #10141a; border-bottom: 1px solid #1c232c;")
        tbl = QHBoxLayout(topbar)
        tbl.setContentsMargins(16, 0, 12, 0)
        tbl.setSpacing(8)

        brand = QLabel(__display_name__)
        brand.setObjectName("brand")
        tbl.addWidget(brand)

        badge = QLabel(__display_badge__)
        badge.setObjectName("brand_badge")
        tbl.addWidget(badge)

        tbl.addStretch()

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setObjectName("icon_btn")
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.clicked.connect(self._toggle_settings)
        tbl.addWidget(self.settings_btn)
        return topbar

    def _build_capture_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        outer = QVBoxLayout(card)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        previews = QHBoxLayout()
        previews.setSpacing(6)
        self.raw_preview = self._preview_label()
        self.diff_preview = self._preview_label()
        previews.addWidget(self.raw_preview)
        previews.addWidget(self.diff_preview)
        top_row.addLayout(previews)

        status_col = QVBoxLayout()
        status_col.setSpacing(6)
        status_col.addStretch()
        self.state_pill = QLabel("IDLE")
        self.state_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_pill.setStyleSheet(PILL_TEMPLATE.format(bg=IDLE_STYLE[0], fg=IDLE_STYLE[1]))
        status_col.addWidget(self.state_pill)
        self.state_status = QLabel("Ready")
        self.state_status.setObjectName("body_dim")
        self.state_status.setWordWrap(True)
        status_col.addWidget(self.state_status)
        status_col.addStretch()
        top_row.addLayout(status_col, stretch=1)
        outer.addLayout(top_row)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        outer.addWidget(self.progress)

        self.potion_status_label = QLabel("")
        self.potion_status_label.setObjectName("hint")
        outer.addWidget(self.potion_status_label)

        return card

    @staticmethod
    def _preview_label() -> QLabel:
        lbl = QLabel()
        lbl.setStyleSheet(
            "border: 1px solid #262e38; border-radius: 8px; background-color: #0b0e12;")
        lbl.setFixedSize(PREVIEW_SIZE, PREVIEW_SIZE)
        return lbl

    def _build_position_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        outer = QVBoxLayout(card)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(10)

        eyebrow = QLabel("CAPTURE POINT")
        eyebrow.setObjectName("eyebrow")
        outer.addWidget(eyebrow)

        row = QHBoxLayout()
        row.setSpacing(8)
        screen = QApplication.primaryScreen().size()

        row.addWidget(self._dim_label("X"))
        self.x_input = QSpinBox()
        self.x_input.setMaximum(screen.width())
        self.x_input.setFixedWidth(66)
        self.x_input.valueChanged.connect(self._on_region_changed)
        row.addWidget(self.x_input)

        row.addWidget(self._dim_label("Y"))
        self.y_input = QSpinBox()
        self.y_input.setMaximum(screen.height())
        self.y_input.setFixedWidth(66)
        self.y_input.valueChanged.connect(self._on_region_changed)
        row.addWidget(self.y_input)

        row.addStretch()

        self.snap_btn = QPushButton("Snap to cursor")
        self.snap_btn.setToolTip(f"Snap to mouse position [{self._snap_hotkey}]")
        self.snap_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.snap_btn.clicked.connect(self.snap_to_cursor)
        row.addWidget(self.snap_btn)
        outer.addLayout(row)

        self.mouse_status = QLabel("")
        self.mouse_status.setObjectName("hint")
        outer.addWidget(self.mouse_status)

        return card

    @staticmethod
    def _dim_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #525d6a; font-size: 11px; font-weight: 600;")
        return lbl

    def _build_presets_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        outer = QVBoxLayout(card)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(10)

        header = QHBoxLayout()
        eyebrow = QLabel("PRESETS")
        eyebrow.setObjectName("eyebrow")
        header.addWidget(eyebrow)
        header.addStretch()

        self.add_preset_btn = self._icon_button("+", "Add preset", self._add_preset)
        header.addWidget(self.add_preset_btn)
        self.rename_preset_btn = self._icon_button("✎", "Rename preset", self._rename_preset)
        header.addWidget(self.rename_preset_btn)
        self.delete_preset_btn = self._icon_button("🗑", "Delete preset", self._delete_preset)
        header.addWidget(self.delete_preset_btn)
        outer.addLayout(header)

        self.preset_list = QListWidget()
        self.preset_list.setFixedHeight(96)
        self.preset_list.itemSelectionChanged.connect(self._on_preset_selected)
        outer.addWidget(self.preset_list)

        self.save_btn = QPushButton("Save current settings to preset")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self._save_current_preset)
        outer.addWidget(self.save_btn)

        return card

    @staticmethod
    def _icon_button(text: str, tooltip: str, slot) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("icon_btn")
        btn.setFixedWidth(30)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(slot)
        return btn

    # ------------------------------------------------------------------
    # Worker wiring
    # ------------------------------------------------------------------
    def _create_worker(self) -> None:
        self.worker = CaptureWorker(interval_ms=66)
        self.worker.frame_ready.connect(self._on_frame_ready)
        self.worker.sense_updated.connect(self._on_sense_updated)
        self.worker.state_changed.connect(self._on_state_changed)
        self.worker.idle.connect(self._on_idle)
        self.worker.potion_status.connect(self.potion_status_label.setText)
        self.worker.error.connect(self._on_worker_error)

    def _apply_settings_to_worker(self) -> None:
        self.worker.region = CaptureRegion(self.x_input.value(), self.y_input.value())
        self.worker.threshold = self.settings_panel.threshold_input.value()
        self.worker.sensitivity = self.settings_panel.sensitivity_input.value()
        self.worker.drink_potions = self.settings_panel.drink_potions_input.isChecked()
        self.worker.drink_delay = self.settings_panel.drink_delay_input.value()
        self.worker.drink_key = self.settings_panel.drink_key_input.text() or "b"

    def _on_region_changed(self, *_args) -> None:
        if hasattr(self, "worker"):
            self.worker.region = CaptureRegion(self.x_input.value(), self.y_input.value())

    def _on_frame_ready(self, raw: QImage, diff: QImage) -> None:
        self.raw_preview.setPixmap(QPixmap.fromImage(raw).scaled(
            PREVIEW_SIZE, PREVIEW_SIZE, Qt.AspectRatioMode.KeepAspectRatio))
        self.diff_preview.setPixmap(QPixmap.fromImage(diff).scaled(
            PREVIEW_SIZE, PREVIEW_SIZE, Qt.AspectRatioMode.KeepAspectRatio))

    def _on_sense_updated(self, sense: float) -> None:
        self.progress.setValue(min(100, int(sense * 100)))

    def _on_state_changed(self, code: str, description: str) -> None:
        bg, fg = STATE_STYLES.get(code, IDLE_STYLE)
        self.state_pill.setText(code)
        self.state_pill.setStyleSheet(PILL_TEMPLATE.format(bg=bg, fg=fg))
        self.state_status.setText(description)
        self.mouse_status.setText("")

    def _on_idle(self) -> None:
        self.state_pill.setText("IDLE")
        self.state_pill.setStyleSheet(PILL_TEMPLATE.format(bg=IDLE_STYLE[0], fg=IDLE_STYLE[1]))
        coords = QCursor.pos()
        self.mouse_status.setText(f"cursor  {coords.x()}, {coords.y()}")
        self.state_status.setText(f"preset: {self._current_preset_name() or '-'}")

    def _on_worker_error(self, message: str) -> None:
        self.state_status.setText(message)
        logger.error(message)

    # ------------------------------------------------------------------
    # Fishing control
    # ------------------------------------------------------------------
    def toggle_fishing(self) -> None:
        self.fishing = not self.fishing
        if self.fishing:
            self.worker.start_fishing()
            self.start_btn.setText("Stop fishing")
            self.start_btn.setProperty("active", "true")
        else:
            self.worker.stop_fishing()
            self.start_btn.setText("Start fishing")
            self.start_btn.setProperty("active", "false")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        self._set_controls_enabled(not self.fishing)

    def _set_controls_enabled(self, enabled: bool) -> None:
        for widget in (
            self.save_btn, self.x_input, self.y_input, self.snap_btn,
            self.add_preset_btn, self.rename_preset_btn,
            self.delete_preset_btn, self.preset_list, self.settings_btn,
        ):
            widget.setEnabled(enabled)
        self.settings_panel.set_enabled_for_fishing(enabled)

    def snap_to_cursor(self) -> None:
        pos = QCursor.pos()
        self.x_input.setValue(pos.x())
        self.y_input.setValue(pos.y())

    # ------------------------------------------------------------------
    # Settings panel
    # ------------------------------------------------------------------
    def _toggle_settings(self) -> None:
        if self.settings_panel.isVisible():
            self.settings_panel.hide()
            self.settings_btn.setProperty("active", "false")
        else:
            self._position_settings_panel()
            self.settings_panel.show()
            self.settings_panel.raise_()
            self.settings_btn.setProperty("active", "true")
        self.settings_btn.style().unpolish(self.settings_btn)
        self.settings_btn.style().polish(self.settings_btn)

    def _on_settings_closed(self) -> None:
        self.settings_btn.setProperty("active", "false")
        self.settings_btn.style().unpolish(self.settings_btn)
        self.settings_btn.style().polish(self.settings_btn)
        self._apply_settings_to_worker()

    def _position_settings_panel(self) -> None:
        w = min(280, self.width())
        self.settings_panel.setGeometry(self.width() - w, 48, w, self.height() - 48)

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        super().resizeEvent(event)
        if self.settings_panel.isVisible():
            self._position_settings_panel()

    def _set_always_on_top(self, checked: bool) -> None:
        # Changing window flags on an already-visible top-level window
        # forces Qt to destroy and recreate its native handle, which
        # briefly makes the window invisible. show() brings it back,
        # but focus/activation can be lost in that moment on some
        # platforms/window managers -- raise_()+activateWindow() make
        # sure keyboard input keeps going to *this* window afterwards
        # instead of silently falling through to whatever was behind it.
        if checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()
        self.raise_()
        self.activateWindow()

    # ------------------------------------------------------------------
    # Hotkeys
    # ------------------------------------------------------------------
    def _start_hotkey_listener(self) -> None:
        self._hotkey_listener = Listener(on_press=self._on_key_press)
        self._hotkey_listener.start()

    def _on_key_press(self, key) -> None:
        # This callback runs on pynput's own OS-level listener thread,
        # not on the Qt event loop. An uncaught exception here would
        # silently kill that thread (global hotkeys stop working with
        # no visible error) rather than crash the app -- but there's no
        # reason to let anything unexpected escape this boundary at
        # all, so it's caught broadly and logged.
        try:
            char = key.char
        except AttributeError:
            return  # a special key (Esc, Shift, F-keys, ...) has no .char
        try:
            if char == self._fish_hotkey:
                QTimer.singleShot(0, self.toggle_fishing)
            elif char == self._snap_hotkey:
                QTimer.singleShot(0, self.snap_to_cursor)
        except Exception:
            logger.exception("Error handling global hotkey press")

    def _capture_hotkey(self, which: str) -> None:
        forbidden = self._snap_hotkey if which == "fish" else self._fish_hotkey
        if self._hotkey_listener.running:
            self._hotkey_listener.stop()
            self._hotkey_listener.join()

        try:
            title = ("Press desired fishing hotkey" if which == "fish"
                      else "Press desired snap hotkey")
            dialog = HotkeyCaptureDialog(title, forbidden, self)
            dialog.exec()

            if dialog.result_key:
                if which == "fish":
                    self._fish_hotkey = dialog.result_key
                else:
                    self._snap_hotkey = dialog.result_key
                    self.snap_btn.setToolTip(f"Snap to mouse position [{self._snap_hotkey}]")
        finally:
            # Always restart the listener, even if something above
            # raised -- otherwise a single bad interaction here would
            # permanently disable the global fishing/snap hotkeys.
            self._start_hotkey_listener()
            self.settings_panel.refresh_hotkey_labels(self._fish_hotkey, self._snap_hotkey)

    # ------------------------------------------------------------------
    # Presets
    # ------------------------------------------------------------------
    def _current_preset_name(self) -> str | None:
        item = self.preset_list.currentItem()
        return item.text() if item else None

    def _refresh_preset_list(self) -> None:
        self.preset_list.blockSignals(True)
        self.preset_list.clear()
        for name in self.config.preset_names():
            self.preset_list.addItem(name)
        self.preset_list.setCurrentRow(0)
        self.preset_list.blockSignals(False)

    def _on_preset_selected(self) -> None:
        name = self._current_preset_name()
        if name:
            self._load_preset(name)

    def _load_preset(self, name: str) -> None:
        settings = self.config.load(name)
        self.x_input.setValue(settings.screen_x)
        self.y_input.setValue(settings.screen_y)
        self.settings_panel.threshold_input.setValue(settings.threshold)
        self.settings_panel.sensitivity_input.setValue(settings.sensitivity)
        self.settings_panel.drink_potions_input.setChecked(settings.drink_potions)
        self.settings_panel.drink_delay_input.setValue(settings.drink_delay)
        self.settings_panel.drink_key_input.setText(settings.drink_key)
        self._apply_settings_to_worker()

    def _current_settings(self) -> PresetSettings:
        return PresetSettings(
            screen_x=self.x_input.value(),
            screen_y=self.y_input.value(),
            threshold=self.settings_panel.threshold_input.value(),
            sensitivity=self.settings_panel.sensitivity_input.value(),
            drink_potions=self.settings_panel.drink_potions_input.isChecked(),
            drink_delay=self.settings_panel.drink_delay_input.value(),
            drink_key=self.settings_panel.drink_key_input.text() or "b",
        )

    def _save_current_preset(self) -> None:
        name = self._current_preset_name()
        if not name:
            return
        self.config.save(name, self._current_settings())
        self._apply_settings_to_worker()

    def _add_preset(self) -> None:
        text, ok = QInputDialog.getText(self, "New preset", "Preset name:")
        if not (ok and text):
            return
        if self.config.has_preset(text):
            QMessageBox.warning(self, "Warning", "A preset with that name already exists")
            return
        self.config.add_preset(text, self._current_settings())
        self._refresh_preset_list()
        self._select_preset_by_name(text)

    def _rename_preset(self) -> None:
        name = self._current_preset_name()
        if not name:
            return
        if name == DEFAULT_PRESET:
            QMessageBox.critical(self, "Nope", f'"{DEFAULT_PRESET}" preset cannot be renamed')
            return
        text, ok = QInputDialog.getText(self, "Rename preset", "New name:", text=name)
        if ok and text and text != name:
            if not self.config.rename_preset(name, text):
                QMessageBox.warning(self, "Warning", "That name is already taken")
                return
            self._refresh_preset_list()
            self._select_preset_by_name(text)

    def _delete_preset(self) -> None:
        if self.preset_list.count() <= 1:
            QMessageBox.warning(self, "Warning", "Can't delete the last preset")
            return
        name = self._current_preset_name()
        if not name:
            return
        if name == DEFAULT_PRESET:
            QMessageBox.critical(self, "Nope", f'"{DEFAULT_PRESET}" preset cannot be deleted')
            return
        reply = QMessageBox.question(
            self, "Delete", f'Delete "{name}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.config.delete_preset(name)
            self._refresh_preset_list()

    def _select_preset_by_name(self, name: str) -> None:
        items = self.preset_list.findItems(name, Qt.MatchFlag.MatchExactly)
        if items:
            self.preset_list.setCurrentItem(items[0])

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------
    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (Qt override)
        """Real, user-initiated shutdown path (window X button, Alt+F4,
        or an explicit close() call).

        This is the *only* place that should ever end the process. See
        main.py for why `quitOnLastWindowClosed` is turned off: without
        that, Qt can decide to quit the whole application on its own
        whenever no top-level window happens to be visible for a
        moment -- which can genuinely happen for a frame or two while
        toggling "always on top" (that forces the main window's native
        handle to be destroyed and recreated) or while a modal dialog
        closes at just the wrong instant. That self-triggered exit
        looked, from the user's side, like the app randomly closing
        when pressing keys such as Escape.
        """
        if getattr(self, "_hotkey_listener", None) and self._hotkey_listener.running:
            self._hotkey_listener.stop()
        if hasattr(self, "worker"):
            self.worker.stop()
            self.worker.wait(2000)
        super().closeEvent(event)
        QApplication.instance().quit()
