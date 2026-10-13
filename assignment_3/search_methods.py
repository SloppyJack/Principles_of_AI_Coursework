"""BFS / iterative-deepening DFS on subsets of queens to relocate.

One state is a bitmask of columns permitted to change. A legal target must
preserve all columns outside the mask. The first feasible mask at the smallest
depth guarantees the globally minimum number of queens moved.

This avoids expanding millions of row-by-row intermediate configurations.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from queens_core import Board, enumerate_solutions, find_moves, move_cost, validate_board


@dataclass(frozen=True)
class SearchResult:
    algorithm: str
    initial: Board
    goal: Board
    minimum_moves: int
    explored: int
    generated: int
    peak_frontier: int

    def as_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "initial_rows_1based": [x + 1 for x in self.initial],
            "goal_rows_1based": [x + 1 for x in self.goal],
            "minimum_moves": self.minimum_moves,
            "explored": self.explored,
            "generated": self.generated,
            "peak_frontier": self.peak_frontier,
            "moves_1based": find_moves(self.initial, self.goal),
        }


def matching_goal(initial: Board, mask: int, targets: tuple[Board, ...]) -> Board | None:
    for target in targets:
        if all(mask & (1 << i) or initial[i] == target[i] for i in range(8)):
            return target
    return None


def children(mask: int, last_column: int):
    # Increasing column order gives each moved-column set one canonical path.
    for col in range(last_column + 1, 8):
        yield mask | (1 << col), col


def breadth_first_search(initial: Board) -> SearchResult:
    initial = validate_board(initial)
    targets = enumerate_solutions()
    queue = deque([(0, -1)])
    explored, generated, peak = 0, 1, 1
    while queue:
        mask, last_column = queue.popleft()
        explored += 1
        goal = matching_goal(initial, mask, targets)
        if goal is not None:
            return SearchResult("bfs", initial, goal, move_cost(initial, goal),
                                explored, generated, peak)
        for next_mask, column in children(mask, last_column):
            queue.append((next_mask, column))
            generated += 1
        peak = max(peak, len(queue))
    raise RuntimeError("BFS did not find a legal arrangement")


def depth_first_search(initial: Board) -> SearchResult:
    """Iterative deepening DFS, not plain first-solution DFS."""
    initial = validate_board(initial)
    targets = enumerate_solutions()
    explored, generated, peak = 0, 0, 1
    for limit in range(9):
        stack = [(0, -1, 0)]
        generated += 1
        while stack:
            mask, last_column, depth = stack.pop()
            explored += 1
            goal = matching_goal(initial, mask, targets)
            if goal is not None:
                return SearchResult("dfs", initial, goal, move_cost(initial, goal),
                                    explored, generated, peak)
            if depth < limit:
                successors = list(children(mask, last_column))
                for next_mask, column in reversed(successors):
                    stack.append((next_mask, column, depth + 1))
                    generated += 1
                peak = max(peak, len(stack))
    raise RuntimeError("DFS did not find a legal arrangement")


def solve(initial: Board, method: str) -> SearchResult:
    if method == "bfs":
        return breadth_first_search(initial)
    if method == "dfs":
        return depth_first_search(initial)
    raise ValueError("method must be bfs or dfs")
