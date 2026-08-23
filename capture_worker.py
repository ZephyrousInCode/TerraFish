"""Background worker that owns the capture -> diff -> state-machine loop
so the GUI thread never blocks on screen grabs or OpenCV work."""
from __future__ import annotations

import logging
import time

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage
from PIL.ImageQt import ImageQt

from . import input_backend
from .fishing_state import FishingStateMachine
from .vision import (
    CaptureRegion,
    MovementTracker,
    ScreenCaptureError,
    grab_region,
    motion_score,
    preprocess,
)

logger = logging.getLogger(__name__)


class CaptureWorker(QThread):
    frame_ready = pyqtSignal(QImage, QImage)
    sense_updated = pyqtSignal(float)
    state_changed = pyqtSignal(str, str)
    idle = pyqtSignal()
    potion_status = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, interval_ms: int = 66, parent=None):
        super().__init__(parent)
        self.interval = interval_ms / 1000.0
        self._running = False
        self._fishing = False

        self._tracker = MovementTracker(3)
        self._state_machine: FishingStateMachine | None = None
        self._potion_drink_time: float | None = None

        self.region = CaptureRegion(850, 850)
        self.threshold = 6
        self.sensitivity = 55
        self.drink_potions = False
        self.drink_delay = 185
        self.drink_key = "b"

    def start_fishing(self) -> None:
        self._fishing = True
        self._state_machine = FishingStateMachine()
        self._potion_drink_time = time.time()
        self._tracker.reset()

    def stop_fishing(self) -> None:
        self._fishing = False
        self._state_machine = None
        self._potion_drink_time = None
        self._tracker.reset()

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        self._running = True
        while self._running:
            tick_start = time.monotonic()
            try:
                self._tick()
            except Exception as exc:  # last-resort safety net
                # _tick() already handles the specific errors we expect
                # (capture failures, input-simulation failures). This
                # catches anything genuinely unexpected so one bad
                # frame can't silently kill the whole capture loop --
                # it logs and keeps ticking instead.
                logger.exception("Unexpected error in capture loop")
                self.error.emit(f"Unexpected error: {exc}")
                time.sleep(0.5)
            remaining = self.interval - (time.monotonic() - tick_start)
            if remaining > 0:
                time.sleep(remaining)

    def _tick(self) -> None:
        region = self.region
        try:
            im = grab_region(region)
        except ScreenCaptureError as exc:
            self.error.emit(f"Screen capture failed: {exc}")
            time.sleep(0.5)
            return

        gray = preprocess(im)
        mask = self._tracker.diff(gray, self.threshold)
        sense = motion_score(mask, self.sensitivity, region.size ** 2)
        self.sense_updated.emit(sense)

        raw_image = ImageQt(im).copy()
        h, w = mask.shape
        diff_image = QImage(mask.data, w, h, w, QImage.Format.Format_Grayscale8).copy()
        self.frame_ready.emit(raw_image, diff_image)

        if self._fishing and self._state_machine:
            try:
                self._state_machine.update(sense)
            except input_backend.InputError as exc:
                self.error.emit(str(exc))
                return
            info = self._state_machine.info()
            self.state_changed.emit(info.code, info.description)
            self._handle_potions()
        else:
            self.idle.emit()

    def _handle_potions(self) -> None:
        if not self.drink_potions:
            self.potion_status.emit("")
            return
        if self._potion_drink_time is None:
            self._potion_drink_time = time.time()
        remaining = int(self._potion_drink_time + self.drink_delay - time.time())
        if remaining <= 0:
            try:
                input_backend.key_press(self.drink_key)
            except input_backend.InputError as exc:
                self.error.emit(str(exc))
            self._potion_drink_time = time.time()
            remaining = self.drink_delay
        self.potion_status.emit(f"potion in {max(0, remaining)}s")
