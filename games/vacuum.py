"""Configurable linear-room vacuum-world state transitions."""

from __future__ import annotations

State = tuple[int, tuple[bool, ...]]


def make_start(room_count: int, dirty: tuple[bool, ...] | None = None, start: int = 0) -> State:
    if room_count < 2:
        raise ValueError("The vacuum world needs at least two rooms.")
    if dirty is None:
        dirty = (True,) * room_count
    if len(dirty) != room_count:
        raise ValueError("There must be one cleanliness value per room.")
    return start, tuple(dirty)


def is_goal(state: State) -> bool:
    return not any(state[1])


def successors(state: State) -> list[tuple[str, State]]:
    position, dirty = state
    result: list[tuple[str, State]] = []
    if position > 0:
        result.append(("LEFT", (position - 1, dirty)))
    if position < len(dirty) - 1:
        result.append(("RIGHT", (position + 1, dirty)))
    if dirty[position]:
        clean = list(dirty)
        clean[position] = False
        result.append(("SUCK", (position, tuple(clean))))
    return result
