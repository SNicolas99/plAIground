from app.core.interfaces import Agent, GameEngine
from app.core.models import Action, GameState, Observation, TurnRecord


class GameOrchestrator:
    """
    Orchestrates the game between an engine and multiple agents.

    Attributes:
        engine (GameEngine): The game engine, e.g., PokerEngine.
        agents (dict[str, Agent]): A dictionary mapping player IDs to agents.
        history (list[TurnRecord]): A list of turn records for the game. Used for debugging.
    """

    def __init__(
            self,
            engine: GameEngine,
            agents: dict[str, Agent],
    ) -> None:
        """
        Initializes the GameOrchestrator with the given engine and agents.

        Args:
            engine (GameEngine): The game engine.
            agents (dict[str, Agent]): A dictionary mapping player IDs to agents.

        Raises:
            ValueError: If no agents are provided (e.g., empty dictionary).
        """

        if not agents:
            raise ValueError("At least one agent is required")

        self.engine = engine
        self.agents = agents

        self.history: list[TurnRecord] = []

    def play_turn(self) -> GameState:
        """
        Plays a turn in the game.

        Chooses the current player, gives them an observation, and then
        asks for their action.

        Returns:
            GameState: The updated game state after the turn is played.

        Raises:
            RuntimeError: If the game is already over or no player is currently active.
            ValueError: If the current player is not in the game.
        """

        state: GameState = self.engine.get_state()

        if state.is_terminal:
            raise RuntimeError("Game is already over")

        player_id: str | None = state.current_player_id
        if player_id is None:
            raise RuntimeError("No player is currently active")

        if player_id not in self.agents:
            raise ValueError(f"No agent registered for player {player_id}")

        agent: Agent = self.agents[player_id]

        # Given the player's ID, get their observation
        observation: Observation = self.engine.get_observation(player_id)

        # Ask the agent for their action based on the observation
        action: Action = agent.act(observation)

        # Apply the action to the game engine and return the updated state
        new_state: GameState = self.engine.step(action)

        # Log the turn
        record = TurnRecord(
            turn_number=len(self.history) + 1,
            player_id=player_id,
            action=Action(
                type=action.type,
                parameters=action.parameters,
            ),
            is_terminal=new_state.is_terminal,
        )
        self.history.append(record)

        return new_state

    def play_game(self, max_turns: int = 1000) -> GameState:
        """
        Play a full game until the game is over or the maximum number of turns is reached.

        Args:
            max_turns (int): The maximum number of turns to play the game (default: 1000).

        Returns:
            GameState: The final state of the game after the game is over.

        Raises:
            ValueError: If max_turns is not positive.
            RuntimeError: If the game does not terminate after max_turns.
        """

        if max_turns <= 0:
            raise ValueError("Max turns must be positive")

        state: GameState = self.engine.reset()
        turns = 0

        while not state.is_terminal:
            if turns >= max_turns:
                raise RuntimeError("Game did not terminate after max turns")

            state = self.play_turn()
            turns += 1

        return state
