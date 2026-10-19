import pytest

from app.core.models import Player
from app.games.poker.engine import PokerEngine

# Default test configuration
DEFAULT_PLAYERS = [
    Player(id="1", name="Player 1"),
    Player(id="2", name="Player 2"),
    Player(id="3", name="Player 3"),
]

DEFAULT_STARTING_STACK = 100
DEFAULT_SMALL_BLIND = 1
DEFAULT_BIG_BLIND = 2


def create_engine(**overrides) -> PokerEngine:
    """Create a PokerEngine with default test parameters."""
    config = {
        "players": DEFAULT_PLAYERS,
        "starting_stack": DEFAULT_STARTING_STACK,
        "small_blind": DEFAULT_SMALL_BLIND,
        "big_blind": DEFAULT_BIG_BLIND,
    }

    config.update(overrides)
    return PokerEngine(**config)


def test_poker_engine_initialization():
    engine = create_engine()

    assert engine.players == DEFAULT_PLAYERS
    assert engine.starting_stack == DEFAULT_STARTING_STACK
    assert engine.small_blind == DEFAULT_SMALL_BLIND
    assert engine.big_blind == DEFAULT_BIG_BLIND


def test_poker_engine_reset():
    engine = create_engine()

    game_state = engine.reset()

    assert game_state.is_terminal is False
    assert game_state.current_player_id == "3"

    assert engine._state is not None
    assert engine._state.stacks == [
        99,
        98,
        100,
    ]  # (player 1: small blind, player 2: big blind)
    assert engine._state.total_pot_amount == 3


@pytest.mark.parametrize(
    "overrides",
    [
        {"players": []},
        {"players": [DEFAULT_PLAYERS[0]]},
        {"starting_stack": 0},
        {"starting_stack": -100},
        {"small_blind": 0},
        {"small_blind": -1},
        {"big_blind": 0},
        {"big_blind": -1},
        {"small_blind": 3, "big_blind": 2},
        {"small_blind": 2, "big_blind": 2},
        {
            "players": [
                Player(id="1", name="Player 1"),
                Player(id="1", name="Player 2"),
            ]
        },
    ],
)
def test_invalid_initialization(overrides):
    with pytest.raises(ValueError):
        create_engine(**overrides)


def test_get_state_before_reset():
    engine = create_engine()

    with pytest.raises(RuntimeError):
        engine.get_state()


def test_get_state_after_reset():
    engine = create_engine()
    engine.reset()

    state = engine.get_state()

    assert state.is_terminal is False
    assert state.current_player_id == "3"


def test_observation_before_reset():
    engine = create_engine()

    with pytest.raises(RuntimeError):
        engine.get_observation("1")


def test_observation_unknown_player():
    engine = create_engine()
    engine.reset()

    with pytest.raises(ValueError):
        engine.get_observation("unknown")


def test_observation_contains_game_data():
    engine = create_engine()
    engine.reset()

    observation = engine.get_observation("3")

    assert observation.player_id == "3"
    assert len(observation.game_data["hole_cards"]) == 2
    assert observation.game_data["board_cards"] == []
    assert observation.game_data["pot"] == 3
    assert observation.game_data["street"] == 0
    assert observation.game_data["current_player_id"] == "3"
    assert len(observation.game_data["players"]) == 3

    observation = engine.get_observation("1")
    assert observation.game_data["players"][0]["id"] == "1"
    assert observation.game_data["current_player_id"] == "3"


def test_observation_hides_opponent_cards():
    engine = create_engine()
    engine.reset()

    obs1 = engine.get_observation("1")
    obs2 = engine.get_observation("2")

    assert len(obs1.game_data["hole_cards"]) == 2
    assert len(obs2.game_data["hole_cards"]) == 2

    assert set(obs1.game_data["hole_cards"]).isdisjoint(
        set(obs2.game_data["hole_cards"])
    )

    assert "hole_cards" not in obs1.game_data["players"][1]
    assert "hole_cards" not in obs2.game_data["players"][0]


def test_legal_actions_before_reset():
    engine = create_engine()

    with pytest.raises(RuntimeError):
        engine._get_legal_actions()


def test_observation_legal_actions():
    engine = create_engine()
    engine.reset()

    observation = engine.get_observation("3")

    actions = {action.type: action for action in observation.legal_actions}

    assert "fold" in actions
    assert "check_or_call" in actions
    assert "raise_to" in actions

    assert actions["check_or_call"].parameters["amount"] == 2

    assert actions["raise_to"].parameters["min_amount"] == 4
    assert actions["raise_to"].parameters["max_amount"] == 100


def test_observation_no_legal_actions_for_inactive_player():
    engine = create_engine()
    engine.reset()

    observation = engine.get_observation("1")

    assert observation.legal_actions == []


def test_step_before_reset():
    engine = create_engine()

    with pytest.raises(RuntimeError):
        engine.step(Action(type="fold"))


def test_step_fold():
    engine = create_engine()
    engine.reset()

    # Player 3 acts first
    new_state = engine.step(Action(type="fold"))

    # Player 1 (small blind) acts next
    assert new_state.current_player_id == "1"
    assert new_state.is_terminal is False


def test_step_check_or_call():
    engine = create_engine()
    engine.reset()

    new_state = engine.step(Action(type="check_or_call"))

    assert new_state.current_player_id == "1"

    assert engine._state is not None
    assert engine._state.stacks == [99, 98, 98]
    assert engine._state.total_pot_amount == 5


def test_step_unknown_action():
    engine = create_engine()
    engine.reset()

    with pytest.raises(ValueError):
        engine.step(Action(type="unknown_action"))


def test_step_raise_to():
    engine = create_engine()
    engine.reset()

    new_state = engine.step(
        Action(
            type="raise_to",
            parameters={"amount": 20},
        )
    )

    assert new_state.current_player_id == "1"

    assert engine._state is not None
    assert engine._state.stacks == [99, 98, 80]
    assert engine._state.total_pot_amount == 23


@pytest.mark.parametrize(
    "parameters",
    [
        {},
        {"amount": 0},
        {"amount": -10},
        {"amount": 3},  # Below minimum raise
        {"amount": 101},  # Above available stack
        {"amount": 20.5},
        {"amount": "20"},
        {"amount": True},
        {"amount": None},
    ],
)
def test_step_raise_to_invalid_amount(parameters):
    engine = create_engine()
    engine.reset()

    with pytest.raises(ValueError):
        engine.step(
            Action(
                type="raise_to",
                parameters=parameters,
            )
        )

    # Invalid actions must not advance the game
    assert engine.get_state().current_player_id == "3"
    assert engine._state.stacks == [99, 98, 100]


def test_game_ends_when_everyone_else_folds():
    engine = create_engine()
    engine.reset()

    # Player 3 folds
    state = engine.step(Action(type="fold"))
    assert state.current_player_id == "1"

    # Player 1 folds
    state = engine.step(Action(type="fold"))

    assert state.is_terminal is True
    assert state.current_player_id is None

    assert engine._state is not None
    assert engine._state.stacks == [99, 98, 103]
    assert sum(engine._state.stacks) == 300


import pytest

from app.core.models import Player, Action
from app.games.poker.engine import PokerEngine

# Default test configuration
DEFAULT_PLAYERS = [
    Player(id="1", name="Player 1"),
    Player(id="2", name="Player 2"),
    Player(id="3", name="Player 3"),
]

DEFAULT_STARTING_STACK = 100
DEFAULT_SMALL_BLIND = 1
DEFAULT_BIG_BLIND = 2


def create_engine(**overrides) -> PokerEngine:
    """Create a PokerEngine with default test parameters."""
    config = {
        "players": DEFAULT_PLAYERS,
        "starting_stack": DEFAULT_STARTING_STACK,
        "small_blind": DEFAULT_SMALL_BLIND,
        "big_blind": DEFAULT_BIG_BLIND,
    }

    config.update(overrides)
    return PokerEngine(**config)


def test_poker_engine_initialization():
    engine = create_engine()

    assert engine.players == DEFAULT_PLAYERS
    assert engine.starting_stack == DEFAULT_STARTING_STACK
    assert engine.small_blind == DEFAULT_SMALL_BLIND
    assert engine.big_blind == DEFAULT_BIG_BLIND


def test_poker_engine_reset():
    engine = create_engine()

    game_state = engine.reset()

    assert game_state.is_terminal is False
    assert game_state.current_player_id == "3"

    assert engine._state is not None
    assert engine._state.stacks == [
        99,
        98,
        100,
    ]  # (player 1: small blind, player 2: big blind)
    assert engine._state.total_pot_amount == 3


@pytest.mark.parametrize(
    "overrides",
    [
        {"players": []},
        {"players": [DEFAULT_PLAYERS[0]]},
        {"starting_stack": 0},
        {"starting_stack": -100},
        {"small_blind": 0},
        {"small_blind": -1},
        {"big_blind": 0},
        {"big_blind": -1},
        {"small_blind": 3, "big_blind": 2},
        {"small_blind": 2, "big_blind": 2},
        {
            "players": [
                Player(id="1", name="Player 1"),
                Player(id="1", name="Player 2"),
            ]
        },
    ],
)
def test_invalid_initialization(overrides):
    with pytest.raises(ValueError):
        create_engine(**overrides)


def test_get_state_before_reset():
    engine = create_engine()

    with pytest.raises(RuntimeError):
        engine.get_state()


def test_get_state_after_reset():
    engine = create_engine()
    engine.reset()

    state = engine.get_state()

    assert state.is_terminal is False
    assert state.current_player_id == "3"


def test_observation_before_reset():
    engine = create_engine()

    with pytest.raises(RuntimeError):
        engine.get_observation("1")


def test_observation_unknown_player():
    engine = create_engine()
    engine.reset()

    with pytest.raises(ValueError):
        engine.get_observation("unknown")


def test_observation_contains_game_data():
    engine = create_engine()
    engine.reset()

    observation = engine.get_observation("3")

    assert observation.player_id == "3"
    assert len(observation.game_data["hole_cards"]) == 2
    assert observation.game_data["board_cards"] == []
    assert observation.game_data["pot"] == 3
    assert observation.game_data["street"] == 0
    assert observation.game_data["current_player_id"] == "3"
    assert len(observation.game_data["players"]) == 3

    observation = engine.get_observation("1")
    assert observation.game_data["players"][0]["id"] == "1"
    assert observation.game_data["current_player_id"] == "3"


def test_observation_hides_opponent_cards():
    engine = create_engine()
    engine.reset()

    obs1 = engine.get_observation("1")
    obs2 = engine.get_observation("2")

    assert len(obs1.game_data["hole_cards"]) == 2
    assert len(obs2.game_data["hole_cards"]) == 2

    assert set(obs1.game_data["hole_cards"]).isdisjoint(
        set(obs2.game_data["hole_cards"])
    )

    assert "hole_cards" not in obs1.game_data["players"][1]
    assert "hole_cards" not in obs2.game_data["players"][0]


def test_legal_actions_before_reset():
    engine = create_engine()

    with pytest.raises(RuntimeError):
        engine._get_legal_actions()


def test_observation_legal_actions():
    engine = create_engine()
    engine.reset()

    observation = engine.get_observation("3")

    actions = {action.type: action for action in observation.legal_actions}

    assert "fold" in actions
    assert "check_or_call" in actions
    assert "raise_to" in actions

    assert actions["check_or_call"].parameters["amount"] == 2

    assert actions["raise_to"].parameters["min_amount"] == 4
    assert actions["raise_to"].parameters["max_amount"] == 100


def test_observation_no_legal_actions_for_inactive_player():
    engine = create_engine()
    engine.reset()

    observation = engine.get_observation("1")

    assert observation.legal_actions == []


def test_step_before_reset():
    engine = create_engine()

    with pytest.raises(RuntimeError):
        engine.step(Action(type="fold"))


def test_step_fold():
    engine = create_engine()
    engine.reset()

    # Player 3 acts first
    new_state = engine.step(Action(type="fold"))

    # Player 1 (small blind) acts next
    assert new_state.current_player_id == "1"
    assert new_state.is_terminal is False


def test_step_check_or_call():
    engine = create_engine()
    engine.reset()

    new_state = engine.step(Action(type="check_or_call"))

    assert new_state.current_player_id == "1"

    assert engine._state is not None
    assert engine._state.stacks == [99, 98, 98]
    assert engine._state.total_pot_amount == 5


def test_step_unknown_action():
    engine = create_engine()
    engine.reset()

    with pytest.raises(ValueError):
        engine.step(Action(type="unknown_action"))


def test_step_raise_to():
    engine = create_engine()
    engine.reset()

    new_state = engine.step(
        Action(
            type="raise_to",
            parameters={"amount": 20},
        )
    )

    assert new_state.current_player_id == "1"

    assert engine._state is not None
    assert engine._state.stacks == [99, 98, 80]
    assert engine._state.total_pot_amount == 23


@pytest.mark.parametrize(
    "parameters",
    [
        {},
        {"amount": 0},
        {"amount": -10},
        {"amount": 3},  # Below minimum raise
        {"amount": 101},  # Above available stack
        {"amount": 20.5},
        {"amount": "20"},
        {"amount": True},
        {"amount": None},
    ],
)
def test_step_raise_to_invalid_amount(parameters):
    engine = create_engine()
    engine.reset()

    with pytest.raises(ValueError):
        engine.step(
            Action(
                type="raise_to",
                parameters=parameters,
            )
        )

    # Invalid actions must not advance the game
    assert engine.get_state().current_player_id == "3"
    assert engine._state.stacks == [99, 98, 100]


def test_game_ends_when_everyone_else_folds():
    engine = create_engine()
    engine.reset()

    # Player 3 folds
    state = engine.step(Action(type="fold"))
    assert state.current_player_id == "1"

    # Player 1 folds
    state = engine.step(Action(type="fold"))

    assert state.is_terminal is True
    assert state.current_player_id is None

    assert engine._state is not None
    assert engine._state.stacks == [99, 101, 100]
    assert sum(engine._state.stacks) == 300
