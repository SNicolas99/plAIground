from dataclasses import dataclass, field
from typing import Any


@dataclass
class Player:
    """Player of the game."""

    id: str
    name: str


@dataclass(frozen=True)
class Action:
    """Action that can be performed by a players."""

    type: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Observation:
    """Observation for one players."""

    player_id: str
    game_data: dict[str, Any]
    legal_actions: list[Action]


@dataclass
class GameState:
    current_player_id: str | None
    is_terminal: bool = False


@dataclass(frozen=True)
class TurnRecord:
    turn_number: int
    player_id: str
    action: Action
    is_terminal: bool
