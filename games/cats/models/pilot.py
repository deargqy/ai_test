"""Return the chosen cat's recorded ability, evidence and decision priorities."""
from game_profile import GameProfile
from game_pilots import select


def predict(state):
    game = GameProfile("cats")
    phase = state.get("phase")
    if phase is not None and phase not in game.phases:
        raise ValueError(f"未知决策阶段 {phase}")
    return select(game.pilots, state["pilot"], phase)
