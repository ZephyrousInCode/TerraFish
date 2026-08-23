"""Platform-abstracted input simulation for mouse clicks and key presses."""
from __future__ import annotations

import logging
import random
import subprocess
import sys
import time

import pyautogui

logger = logging.getLogger(__name__)

_MIN_HOLD = 0.015
_MAX_HOLD = 0.045


class InputError(RuntimeError):
    """Raised when a simulated click/key press could not be delivered."""


def _hold_time() -> float:
    return random.uniform(_MIN_HOLD, _MAX_HOLD)


def mouse_click() -> None:
    hold = _hold_time()
    try:
        if sys.platform.startswith("linux"):
            subprocess.run(["xdotool", "mousedown", "1"], check=True, timeout=2)
            time.sleep(hold)
            subprocess.run(["xdotool", "mouseup", "1"], check=True, timeout=2)
        else:
            pyautogui.mouseDown()
            time.sleep(hold)
            pyautogui.mouseUp()
    except FileNotFoundError as exc:
        raise InputError(
            "xdotool is not installed. Install it with your package "
            "manager, e.g. `sudo apt install xdotool`."
        ) from exc
    except subprocess.SubprocessError as exc:
        raise InputError(f"Could not simulate mouse click: {exc}") from exc
    except pyautogui.FailSafeException as exc:
        raise InputError(
            "pyautogui fail-safe triggered (cursor hit a screen corner)."
        ) from exc


def key_press(key: str) -> None:
    if not key:
        return
    hold = _hold_time()
    try:
        if sys.platform.startswith("linux"):
            subprocess.run(["xdotool", "key", key], check=True, timeout=2)
        else:
            pyautogui.keyDown(key)
            time.sleep(hold)
            pyautogui.keyUp(key)
    except FileNotFoundError as exc:
        raise InputError(
            "xdotool is not installed. Install it with your package "
            "manager, e.g. `sudo apt install xdotool`."
        ) from exc
    except subprocess.SubprocessError as exc:
        raise InputError(f"Could not simulate key press '{key}': {exc}") from exc
    except pyautogui.FailSafeException as exc:
        raise InputError(
            "pyautogui fail-safe triggered (cursor hit a screen corner)."
        ) from exc
