"""The fishing state machine: INIT -> CAST -> WAIT -> REEL -> CAST -> ..."""
from __future__ import annotations

import time
from dataclasses import dataclass

from . import input_backend

BITE_THRESHOLD = 1.0
CAST_SETTLE_TIME = 1.0
BITE_CONFIRM_TIME = 1.0
REEL_CONFIRM_TIME = 0.5
STUCK_TIMEOUT = 90.0


@dataclass
class FisherState:
    code: str
    description: str


class BaseState:
    code = "?"
    description = ""

    def __init__(self) -> None:
        self.created_at = time.time()

    @property
    def elapsed(self) -> float:
        return time.time() - self.created_at

    def update(self, sense: float) -> "BaseState | None":
        raise NotImplementedError


class InitializationState(BaseState):
    code = "INIT"
    description = "Waiting to start..."

    def update(self, sense: float) -> "BaseState | None":
        return CastingState()


class CastingState(BaseState):
    code = "CAST"
    description = "Casting the line"

    def __init__(self, do_cast: bool = True) -> None:
        super().__init__()
        if do_cast:
            input_backend.mouse_click()

    def update(self, sense: float) -> "BaseState | None":
        if self.elapsed > CAST_SETTLE_TIME and sense < BITE_THRESHOLD:
            return WaitingState()
        return None


class WaitingState(BaseState):
    code = "WAIT"
    description = "Waiting for bite..."

    def update(self, sense: float) -> "BaseState | None":
        if self.elapsed > BITE_CONFIRM_TIME and sense > BITE_THRESHOLD:
            return ReelingState()
        if self.elapsed > STUCK_TIMEOUT:
            return CastingState()
        return None


class ReelingState(BaseState):
    code = "REEL"
    description = "Hooked! Reeling in"

    def __init__(self) -> None:
        super().__init__()
        input_backend.mouse_click()

    def update(self, sense: float) -> "BaseState | None":
        if self.elapsed > REEL_CONFIRM_TIME and sense < BITE_THRESHOLD:
            return CastingState()
        return None


class FishingStateMachine:
    def __init__(self) -> None:
        self.state: BaseState = InitializationState()

    def update(self, sense: float) -> None:
        nxt = self.state.update(sense)
        if nxt is not None:
            self.state = nxt

    def info(self) -> FisherState:
        return FisherState(self.state.code, self.state.description)
