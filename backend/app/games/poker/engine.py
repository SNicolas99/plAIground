from typing import Any

from pokerkit import Automation, State, NoLimitTexasHoldem

from app.core.interfaces import GameEngine
from app.core.models import Player, Action, Observation, GameState

AUTOMATIONS = (
    Automation.ANTE_POSTING,
    Automation.BET_COLLECTION,
    Automation.BLIND_OR_STRADDLE_POSTING,
    Automation.BOARD_DEALING,
    Automation.CARD_BURNING,
    Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
    Automation.HOLE_DEALING,
    Automation.HAND_KILLING,
    Automation.CHIPS_PUSHING,
    Automation.CHIPS_PULLING,
)


class PokerEngine(GameEngine):
    def __init__(
        self,
        players: list[Player],
        starting_stack: int = 100,
        small_blind: int = 1,
        big_blind: int = 2,
    ) -> None:

        # Validate parameters
        if len(players) < 2:
            raise ValueError("At least two players are required")

        if starting_stack <= 0:
            raise ValueError("Starting stack must be positive")

        if not (small_blind > 0 and big_blind > 0):
            raise ValueError("Blinds must be positive")

        if small_blind >= big_blind:
            raise ValueError("Small blind must be less than big blind")

        player_ids: list[str] = [player.id for player in players]
        if len(set(player_ids)) != len(player_ids):
            raise ValueError("Player IDs must be unique")

        self.players = players
        self.starting_stack = starting_stack
        self.small_blind = small_blind
        self.big_blind = big_blind

        self._state: State | None = None

    def reset(self) -> GameState:

        self._state = NoLimitTexasHoldem.create_state(
            automations=AUTOMATIONS,
            ante_trimming_status=True,  # Uniform antes
            raw_antes=0,
            raw_blinds_or_straddles=(self.small_blind, self.big_blind),
            min_bet=self.big_blind,
            raw_starting_stacks=self.starting_stack,
            player_count=len(self.players),
        )

        return self.get_state()

    def get_state(self) -> GameState:

        if self._state is None:
            raise RuntimeError("Game not initialized")

        actor_index: int | None = self._state.actor_index

        player_id: str | None = (
            self.players[actor_index].id if actor_index is not None else None
        )

        return GameState(
            current_player_id=player_id,
            is_terminal=not self._state.status,
        )

    def _get_legal_actions(self) -> list[Action]:
        """Helper function to get legal actions for the current player."""

        if self._state is None:
            raise RuntimeError("Game not initialized")

        actions: list[Action] = []

        if self._state.actor_index is None:
            return actions

        if self._state.can_fold():
            actions.append(Action(type="fold"))

        if self._state.can_check_or_call():
            actions.append(
                Action(
                    type="check_or_call",
                    parameters={
                        "amount": self._state.checking_or_calling_amount,
                    },
                )
            )

        if self._state.can_complete_bet_or_raise_to():
            actions.append(
                Action(
                    type="raise_to",
                    parameters={
                        "min_amount": self._state.min_completion_betting_or_raising_to_amount,
                        "max_amount": self._state.max_completion_betting_or_raising_to_amount,
                    },
                )
            )

        return actions

    def get_observation(self, player_id: str) -> Observation:

        if self._state is None:
            raise RuntimeError("Game not initialized")

        player_ids: list[str] = [player.id for player in self.players]

        if player_id not in player_ids:
            raise ValueError(f"Player {player_id} not found in the game")

        # Fill in the game data
        player_index: int = player_ids.index(player_id)

        hole_cards: list[str] = [
            str(card) for card in self._state.hole_cards[player_index]
        ]

        board_cards: list[str] = [
            str(card) for board in self._state.board_cards for card in board
        ]

        players_data: list[dict[str, Any]] = [
            {
                "id": player.id,
                "name": player.name,
                "stack": self._state.stacks[i],
                "bet": self._state.bets[i],
            }
            for i, player in enumerate(self.players)
        ]

        return Observation(
            player_id=player_id,
            game_data={
                "hole_cards": hole_cards,
                "board_cards": board_cards,
                "players": players_data,
                "pot": self._state.total_pot_amount,
                "street": self._state.street_index,
                "current_player_id": self.get_state().current_player_id,
            },
            legal_actions=(
                self._get_legal_actions()
                if self.get_state().current_player_id == player_id
                else []
            ),
        )

    def step(self, action: Action) -> GameState:

        if self._state is None:
            raise RuntimeError("Game not initialized")

        if self._state.actor_index is None:
            raise RuntimeError("No player is currently active")

        if action.type == "fold":
            self._state.fold()

        elif action.type == "check_or_call":
            self._state.check_or_call()

        elif action.type == "raise_to":
            amount = action.parameters.get("amount")

            if type(amount) is not int:
                raise ValueError("Raise amount must be an integer")

            if amount <= 0:
                raise ValueError("Raise amount must be positive")

            if not self._state.can_complete_bet_or_raise_to(amount):
                raise ValueError(f"Invalid raise amount: {amount}")

            self._state.complete_bet_or_raise_to(amount=amount)

        else:
            raise ValueError(f"Invalid action type: {action.type}")

        return self.get_state()
