from abc import ABC, abstractmethod

from app.core.models import (
    Action,
    GameState,
    Observation,
)


class GameEngine(ABC):
    """
    Abstract class representing a game engine.

    Will be implemented for each games independantly.
    """

    @abstractmethod
    def reset(self) -> GameState:
        """
        Start a new game.

        Returns:
            GameState: The initial state of the game.
        """
        ...

    @abstractmethod
    def get_state(self) -> GameState:
        """
        Get the current public state of the game.

        Returns:
            GameState: The current state of the game.
        """
        ...

    @abstractmethod
    def get_observation(self, player_id: str) -> Observation:
        """
        Get the observation for a specific players.

        Args:
            player_id (str): The ID of the players.

        Returns:
            Observation: The observation for the specified players.
        """
        ...

    @abstractmethod
    def step(self, action: Action) -> GameState:
        """
        Apply an action to the game and update the state.

        Args:
            action (Action): The action to be applied.

        Returns:
            GameState: The updated state of the game.
        """
        ...


class Agent(ABC):
    """
    Abstract class representing an agent.
    """

    @abstractmethod
    def act(self, observation: Observation) -> Action:
        """
        Decide on an action based on the (visible) observation.

        Args:
            observation (Observation): The observation for the agent.

        Returns:
            Action: The action decided by the agent.
        """
        ...
