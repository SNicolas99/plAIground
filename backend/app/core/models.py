from dataclasses import dataclass, field
from typing import Any


@dataclass
class Player:
    """Player of the game."""
    id: str
    name: str


@dataclass(frozen=True)
class Action:
    """Action that can be performed by a player."""
    type: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Observation:
    """Observation for one player."""
    player_id: str
    game_data: dict[str, Any]
    legal_actions: list[Action]


@dataclass
class GameState:
    current_player_id: str | None
    is_terminal: bool = False
