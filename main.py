#!/usr/bin/env python3
"""Entry point for TerraFish V2."""
import logging
import sys
import traceback

from PyQt6.QtWidgets import QApplication

from terrafish.ui.main_window import AppUi
from terrafish.ui.style import STYLE

logger = logging.getLogger(__name__)


def _install_exception_hook() -> None:
    """Stop stray exceptions from silently killing the whole app.

    PyQt5.5+/PyQt6 default behaviour: if a Python exception escapes a
    Qt slot (any method connected to a signal -- a button click, a key
    press event, a QTimer.singleShot callback, ...), PyQt does NOT just
    print a traceback and move on. It calls the process's excepthook
    and then aborts the whole application immediately, with no dialog,
    no error message, nothing. From the user's side that's
    indistinguishable from "the app randomly closed itself".

    A small bug anywhere in a signal handler -- an edge case in key
    handling, a preset with an unexpected value, a timing quirk while
    toggling always-on-top -- is exactly the kind of thing that can
    trigger this. Installing our own excepthook that logs the error
    instead of the default one keeps the app running through anything
    that isn't fatal to the OS/interpreter itself.
    """

    def _hook(exc_type, exc_value, exc_tb):
        logger.error(
            "Unhandled exception in a Qt callback (app kept running):\n%s",
            "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
        )

    sys.excepthook = _hook


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    _install_exception_hook()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)

    # Don't let Qt decide on its own to quit "because no top-level
    # window is visible right now". That state can genuinely happen
    # for a moment -- e.g. toggling "always on top" forces the main
    # window's native handle to be destroyed and recreated, or a modal
    # dialog (like the hotkey-capture prompt) closes at the same
    # instant something else briefly has no visible window. Shutdown
    # is instead handled explicitly in AppUi.closeEvent().
    app.setQuitOnLastWindowClosed(False)

    window = AppUi()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
