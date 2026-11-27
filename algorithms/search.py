"""Small, reusable graph-search implementations for the visualizer."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import heapq
from itertools import count
from typing import Callable, Generic, Hashable, TypeVar

State = TypeVar("State", bound=Hashable)
Action = TypeVar("Action")


@dataclass
class SearchResult(Generic[State, Action]):
    states: list[State]
    actions: list[Action]
    expanded: int
    discovered: int
    total_cost: float | int | None = None


def _reconstruct(
    start: State,
    goal: State,
    parents: dict[State, tuple[State, Action] | None],
    expanded: int,
    total_cost: float | int | None = None,
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
    return SearchResult(states, actions, expanded, len(parents), total_cost)


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


def uniform_cost_search(
    start: State,
    is_goal: Callable[[State], bool],
    successors: Callable[[State], list[tuple[Action, State]]],
    cost_fn: Callable[[Action], float | int] | None = None,
) -> SearchResult[State, Action] | None:
    """Return a minimum-cost path using Uniform Cost Search."""
    if is_goal(start):
        return _reconstruct(start, start, {start: None}, 0, 0)

    order = count()
    frontier: list[tuple[float | int, int, State]] = [(0, next(order), start)]
    parents: dict[State, tuple[State, Action] | None] = {start: None}
    best_cost: dict[State, float | int] = {start: 0}
    closed: set[State] = set()
    expanded = 0

    while frontier:
        cost, _, state = heapq.heappop(frontier)
        if state in closed or cost > best_cost[state]:
            continue
        closed.add(state)
        expanded += 1
        if is_goal(state):
            return _reconstruct(start, state, parents, expanded, cost)
        for action, child in successors(state):
            if child in closed:
                continue
            step_cost = cost_fn(action) if cost_fn is not None else 1
            new_cost = cost + step_cost
            if new_cost < best_cost.get(child, float("inf")):
                best_cost[child] = new_cost
                parents[child] = (state, action)
                heapq.heappush(frontier, (new_cost, next(order), child))
    return None
