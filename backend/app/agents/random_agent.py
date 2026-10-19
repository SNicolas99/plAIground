import random

from app.core.interfaces import Agent
from app.core.models import Action, Observation


class RandomAgent(Agent):
    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def act(self, observation: Observation) -> Action:
        if not observation.legal_actions:
            raise ValueError("No legal actions available for the player.")

        action: Action = self._rng.choice(observation.legal_actions)

        if action.type == "raise_to":
            min_amount: int = action.parameters["min_amount"]
            max_amount: int = action.parameters["max_amount"]

            amount = self._rng.randint(min_amount, max_amount)

            return Action(
                type="raise_to",
                parameters={"amount": amount},
            )

        return action
