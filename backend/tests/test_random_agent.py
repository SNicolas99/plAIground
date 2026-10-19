import pytest

from app.agents.random_agent import RandomAgent
from app.core.models import Action, Observation


def test_random_agent_act():
    agent = RandomAgent(seed=42)

    observation = Observation(
        player_id="1",
        game_data={},
        legal_actions=[
            Action(type="check_or_call"),
        ],
    )
    action = agent.act(observation)

    assert action.type == "check_or_call"


def test_random_agent_no_legal_actions():
    agent = RandomAgent(seed=42)

    observation = Observation(player_id="1", game_data={}, legal_actions=[])
    with pytest.raises(ValueError):
        agent.act(observation)


def test_random_agent_raise():
    agent = RandomAgent(seed=42)

    observation = Observation(
        player_id="1",
        game_data={},
        legal_actions=[
            Action(
                type="raise_to",
                parameters={
                    "min_amount": 4,
                    "max_amount": 100,
                },
            ),
        ],
    )

    action = agent.act(observation)

    assert action.type == "raise_to"
    assert 4 <= action.parameters["amount"] <= 100
    assert type(action.parameters["amount"]) is int


def test_random_agent_reproducibility():
    agent1 = RandomAgent(seed=123)
    agent2 = RandomAgent(seed=123)

    observation = Observation(
        player_id="1",
        game_data={},
        legal_actions=[
            Action(type="fold"),
            Action(type="check_or_call"),
            Action(
                type="raise_to",
                parameters={
                    "min_amount": 4,
                    "max_amount": 100,
                },
            ),
        ],
    )

    decisions1 = [agent1.act(observation) for _ in range(100)]
    decisions2 = [agent2.act(observation) for _ in range(100)]

    assert decisions1 == decisions2

    assert all(
        action.type in ["fold", "check_or_call", "raise_to"] for action in decisions1
    )

    for action in decisions1:
        if action.type == "raise_to":
            assert 4 <= action.parameters["amount"] <= 100

    assert len({action.type for action in decisions1}) > 1


def test_random_agent_different_seeds():
    agent1 = RandomAgent(seed=123)
    agent2 = RandomAgent(seed=456)

    observation = Observation(
        player_id="1",
        game_data={},
        legal_actions=[
            Action(type="fold"),
            Action(type="check_or_call"),
            Action(
                type="raise_to",
                parameters={
                    "min_amount": 4,
                    "max_amount": 100,
                },
            ),
        ],
    )

    decisions1 = [agent1.act(observation) for _ in range(100)]
    decisions2 = [agent2.act(observation) for _ in range(100)]

    assert decisions1 != decisions2
