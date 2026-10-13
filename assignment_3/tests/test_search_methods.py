"""Regression tests for BFS and iterative-deepening DFS on moved-column subsets."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from queens_core import enumerate_solutions, conflicts, find_moves, move_cost, replay_moves
from search_methods import breadth_first_search, depth_first_search


class SearchMethodTests(unittest.TestCase):
    def test_photographed_default(self):
        start = (0, 2, 4, 6, 1, 3, 5, 7)
        for solver in (breadth_first_search, depth_first_search):
            with self.subTest(solver=solver.__name__):
                result = solver(start)
                self.assertEqual(result.minimum_moves, 3)
                self.assertEqual(conflicts(result.goal), 0)
                self.assertEqual(replay_moves(start, find_moves(start, result.goal))[-1], result.goal)

    def test_optimality_on_known_cases(self):
        starts = [tuple(range(8)), (0,) * 8,
                  enumerate_solutions()[0], (0, 2, 4, 6, 1, 3, 5, 7)]
        for start in starts:
            reference = min(move_cost(start, goal) for goal in enumerate_solutions())
            for solver in (breadth_first_search, depth_first_search):
                with self.subTest(start=start, solver=solver.__name__):
                    result = solver(start)
                    self.assertEqual(result.minimum_moves, reference)
                    self.assertEqual(move_cost(start, result.goal), reference)

    def test_reject_bad_board(self):
        for solver in (breadth_first_search, depth_first_search):
            with self.assertRaises(ValueError):
                solver((0,) * 7)


try:
    from search_graph import run_search
    HAS_GRAPH = True
except ImportError:
    HAS_GRAPH = False


@unittest.skipUnless(HAS_GRAPH, "Install langgraph to run graph integration tests")
class SearchGraphTests(unittest.TestCase):
    def test_both_graphs(self):
        start = (0, 2, 4, 6, 1, 3, 5, 7)
        for method in ("bfs", "dfs"):
            _, state = run_search(start, method)
            self.assertTrue(state["verified"])
            self.assertEqual(state["result"]["minimum_moves"], 3)


if __name__ == "__main__":
    unittest.main()
