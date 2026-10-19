from app.agents.random_agent import RandomAgent
from app.core.models import Action, GameState, Observation, Player
from app.games.poker.engine import PokerEngine

PLAYERS = [
    Player(id="1", name="Alice"),
    Player(id="2", name="Bob"),
    Player(id="3", name="Charlie"),
]


def test_random_agent_plays_poker():
    engine = PokerEngine(players=PLAYERS)
    agent = RandomAgent(seed=42)

    state: GameState = engine.reset()

    assert state.current_player_id == "3"

    observation = engine.get_observation(player_id=state.current_player_id)

    action: Action = agent.act(observation=observation)
    new_state: GameState = engine.step(action=action)

    assert new_state != state


def random_agent_can_play_complete_hand():
    engine = PokerEngine(players=PLAYERS)

    agents = {player.id: RandomAgent(seed=i) for i, player in enumerate(PLAYERS)}

    state: GameState = engine.reset()

    actions_count = 0
    max_actions = 1000

    while not state.is_terminal:
        assert actions_count < max_actions, (
            f"Game did not terminate after {max_actions} actions"
        )

        player_id: str | None = state.current_player_id
        assert player_id is not None

        observation: Observation = engine.get_observation(player_id=player_id)

        action: Action = agents[player_id].act(observation=observation)
        state = engine.step(action=action)
        actions_count += 1

    assert state.is_terminal
    assert 0 < actions_count < max_actions

    assert engine._state is not None
    assert sum(engine._state.stacks) == 300
