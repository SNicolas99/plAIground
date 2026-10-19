import pytest

from app.agents.random_agent import RandomAgent
from app.core.models import Player
from app.core.orchestrator import GameOrchestrator
from app.games.poker.engine import PokerEngine

PLAYERS = [
    Player(id="1", name="Alice"),
    Player(id="2", name="Bob"),
    Player(id="3", name="Charlie"),
]


def test_orchestrator_initialization():
    engine = PokerEngine(players=PLAYERS)

    agents = {player.id: RandomAgent(seed=i) for i, player in enumerate(PLAYERS)}

    orchestrator = GameOrchestrator(
        engine=engine,
        agents=agents,
    )

    assert orchestrator.engine is engine
    assert orchestrator.agents == agents


def test_orchestrator_requires_agents():
    engine = PokerEngine(players=PLAYERS)

    with pytest.raises(ValueError):
        GameOrchestrator(engine=engine, agents={})


def create_orchestrator() -> GameOrchestrator:
    """Helper function to create a GameOrchestrator with default parameters."""
    engine = PokerEngine(players=PLAYERS)

    agents = {player.id: RandomAgent(seed=i) for i, player in enumerate(PLAYERS)}

    return GameOrchestrator(engine=engine, agents=agents)


def test_play_turn():
    orchestrator = create_orchestrator()
    orchestrator.engine.reset()

    old_state = orchestrator.engine.get_state()

    new_state = orchestrator.play_turn()

    assert new_state != old_state
    assert old_state.current_player_id != new_state.current_player_id
    assert old_state.current_player_id == "3"


def test_play_turn_before_reset():
    orchestrator = create_orchestrator()

    with pytest.raises(RuntimeError):
        orchestrator.play_turn()


def test_play_game():
    orchestrator = create_orchestrator()

    final_state = orchestrator.play_game()

    assert final_state.is_terminal is True
    assert final_state.current_player_id is None

    # Chip conservation
    poker_state = orchestrator.engine._state

    assert poker_state is not None
    assert sum(poker_state.stacks) == 300


@pytest.mark.parametrize("max_turns", [0, -1, -100])
def test_play_game_invalid_max_turns(max_turns):
    orchestrator = create_orchestrator()

    with pytest.raises(ValueError):
        orchestrator.play_game(max_turns=max_turns)


def test_orchestrator_records_turns():
    orchestrator = create_orchestrator()

    final_state = orchestrator.play_game()

    assert final_state.is_terminal
    assert len(orchestrator.history) > 0

    for i, record in enumerate(orchestrator.history):
        assert record.turn_number == i + 1
        assert record.player_id in {"1", "2", "3"}
        assert record.action.type in {
            "fold",
            "check_or_call",
            "raise_to",
        }

    assert orchestrator.history[-1].is_terminal


def test_orchestrator_history_resets():
    orchestrator = create_orchestrator()

    orchestrator.play_game()
    first_history = orchestrator.history.copy()

    orchestrator.play_game()

    assert len(first_history) > 0
    assert len(orchestrator.history) > 0
    assert orchestrator.history[0].turn_number == 1
