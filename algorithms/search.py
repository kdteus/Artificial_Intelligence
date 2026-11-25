"""Small, reusable graph-search implementations for the visualizer."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable, Generic, Hashable, TypeVar

State = TypeVar("State", bound=Hashable)
Action = TypeVar("Action")


@dataclass
class SearchResult(Generic[State, Action]):
    states: list[State]
    actions: list[Action]
    expanded: int
    discovered: int


def _reconstruct(
    start: State,
    goal: State,
    parents: dict[State, tuple[State, Action] | None],
    expanded: int,
) -> SearchResult[State, Action]:
    states = [goal]
    actions: list[Action] = []
    current = goal
    while current != start:
        parent = parents[current]
        assert parent is not None
        previous, action = parent
        states.append(previous)
        actions.append(action)
        current = previous
    states.reverse()
    actions.reverse()
    return SearchResult(states, actions, expanded, len(parents))


def breadth_first_search(
    start: State,
    is_goal: Callable[[State], bool],
    successors: Callable[[State], list[tuple[Action, State]]],
) -> SearchResult[State, Action] | None:
    """Return a shortest path in an unweighted state graph."""
    frontier = deque([start])
    parents: dict[State, tuple[State, Action] | None] = {start: None}
    expanded = 0
    if is_goal(start):
        return _reconstruct(start, start, parents, expanded)
    while frontier:
        state = frontier.popleft()
        expanded += 1
        if is_goal(state):
            return _reconstruct(start, state, parents, expanded)
        for action, child in successors(state):
            if child in parents:
                continue
            parents[child] = (state, action)
            if is_goal(child):
                return _reconstruct(start, child, parents, expanded)
            frontier.append(child)
    return None


def depth_first_search(
    start: State,
    is_goal: Callable[[State], bool],
    successors: Callable[[State], list[tuple[Action, State]]],
) -> SearchResult[State, Action] | None:
    """Return a path found by iterative depth-first graph search."""
    frontier = [start]
    parents: dict[State, tuple[State, Action] | None] = {start: None}
    expanded = 0
    if is_goal(start):
        return _reconstruct(start, start, parents, expanded)
    while frontier:
        state = frontier.pop()
        expanded += 1
        if is_goal(state):
            return _reconstruct(start, state, parents, expanded)
        for action, child in successors(state):
            if child in parents:
                continue
            parents[child] = (state, action)
            if is_goal(child):
                return _reconstruct(start, child, parents, expanded)
            frontier.append(child)
    return None
