"""Screen capture and motion detection for bobber tracking."""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from PIL import ImageGrab
from PIL.Image import Image


@dataclass(frozen=True)
class CaptureRegion:
    center_x: int
    center_y: int
    radius: int = 50

    @property
    def box(self) -> tuple[int, int, int, int]:
        return (
            self.center_x - self.radius,
            self.center_y - self.radius,
            self.center_x + self.radius,
            self.center_y + self.radius,
        )

    @property
    def size(self) -> int:
        return self.radius * 2


class ScreenCaptureError(RuntimeError):
    """Raised when the screen region could not be grabbed."""


def grab_region(region: CaptureRegion) -> Image:
    try:
        return ImageGrab.grab(region.box)
    except Exception as exc:
        raise ScreenCaptureError(str(exc)) from exc


class MovementTracker:
    def __init__(self, buffer_size: int = 3):
        if buffer_size < 3:
            raise ValueError("buffer_size must be at least 3")
        self.size = buffer_size
        self._buffer: list[np.ndarray] | None = None
        self._cursor = 0

    def reset(self) -> None:
        self._buffer = None
        self._cursor = 0

    def diff(self, frame: np.ndarray, threshold: int) -> np.ndarray:
        if self._buffer is None:
            self._buffer = [frame] * self.size
        self._buffer[self._cursor] = frame
        self._cursor = (self._cursor + 1) % self.size
        ordered = self._buffer[self._cursor:] + self._buffer[:self._cursor]
        return self._diff_three(ordered[:3], threshold)

    @staticmethod
    def _diff_three(frames: list[np.ndarray], threshold: int) -> np.ndarray:
        oldest, mid, newest = frames
        d1 = cv2.absdiff(newest, mid)
        d2 = cv2.absdiff(mid, oldest)
        combined = cv2.bitwise_or(d1, d2)
        _, mask = cv2.threshold(combined, threshold, 255, cv2.THRESH_BINARY)
        return mask


def preprocess(image: Image) -> np.ndarray:
    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.GaussianBlur(gray, (21, 21), 0)


def motion_score(mask: np.ndarray, sensitivity: int, area: int) -> float:
    count = cv2.countNonZero(mask)
    return count * sensitivity / area
