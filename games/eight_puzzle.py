"""State transitions for the 8-puzzle."""

from __future__ import annotations

import random

State = tuple[int, ...]
GOAL: State = (1, 2, 3, 4, 5, 6, 7, 8, 0)
ACTION_ORDER = ("UP", "DOWN", "LEFT", "RIGHT")
INVERSE = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}


def successors(state: State) -> list[tuple[str, State]]:
    blank = state.index(0)
    row, col = divmod(blank, 3)
    moves: list[tuple[str, int]] = []
    if row > 0:
        moves.append(("UP", blank - 3))
    if row < 2:
        moves.append(("DOWN", blank + 3))
    if col > 0:
        moves.append(("LEFT", blank - 1))
    if col < 2:
        moves.append(("RIGHT", blank + 1))
    result = []
    for action, target in moves:
        board = list(state)
        board[blank], board[target] = board[target], board[blank]
        result.append((action, tuple(board)))
    return result


def scramble(steps: int = 12, seed: int | None = None) -> State:
    """Create a solvable board by making legal moves from the goal."""
    rng = random.Random(seed)
    state = GOAL
    previous: str | None = None
    for _ in range(steps):
        choices = [(action, child) for action, child in successors(state)
                   if action != INVERSE.get(previous)]
        action, state = rng.choice(choices)
        previous = action
    return state
