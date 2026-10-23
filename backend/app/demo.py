from app.agents.random_agent import RandomAgent
from app.core.models import Player
from app.core.orchestrator import GameOrchestrator
from app.games.poker.engine import PokerEngine


def main() -> None:
    players = [
        Player(id="1", name="Alice"),
        Player(id="2", name="Bob"),
        Player(id="3", name="Charlie"),
    ]

    engine = PokerEngine(players=players)

    agents = {player.id: RandomAgent(seed=i) for i, player in enumerate(players)}

    orchestrator = GameOrchestrator(engine=engine, agents=agents)
    final_state = orchestrator.play_game()

    print("Game finished:", final_state.is_terminal)
    print("Final state:", final_state)

    # Temporary debugging access to PokerKit
    print("Final stacks:", engine._state.stacks)
    print("Payoffs:", engine._state.payoffs)

    print("\n--- Game History ---")

    for record in orchestrator.history:
        print(
            f"Turn {record.turn_number}: "
            f"Player {record.player_id} -> "
            f"{record.action.type} "
            f"{record.action.parameters}"
        )


if __name__ == "__main__":
    main()
