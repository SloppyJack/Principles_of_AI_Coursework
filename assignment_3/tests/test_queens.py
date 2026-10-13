"""Unit tests; run from project root: python -m unittest discover -s assignment_3/tests -v."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from queens_core import (
    conflicts, enumerate_solutions, find_moves, is_valid_solution,
    move_cost, replay_moves, validate_board,
)


class QueensCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.targets = enumerate_solutions()

    def test_exactly_92_distinct_valid_solutions(self):
        self.assertEqual(92, len(self.targets))
        self.assertEqual(92, len(set(self.targets)))
        self.assertTrue(all(is_valid_solution(t) for t in self.targets))

    def test_diagonal_initial_attacks(self):
        self.assertEqual(28, conflicts(tuple(range(8))))

    def test_input_validation(self):
        for bad in ([0] * 7, [0] * 9, [-1] + [0] * 7,
                    [8] + [0] * 7, [True] + [0] * 7,
                    [0.0] + [0] * 7):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_board(bad)
        # Repeated rows are allowed in the initial configuration.
        self.assertEqual((0,) * 8, validate_board([0] * 8))

    def test_valid_initial_is_zero_moves(self):
        start = self.targets[0]
        self.assertEqual(0, min(move_cost(start, target) for target in self.targets))
        self.assertEqual([], find_moves(start, start))

    def test_all_8_queens_in_same_row(self):
        start = (0,) * 8
        optimal = min(self.targets, key=lambda s: (move_cost(start, s), s))
        self.assertEqual(7, move_cost(start, optimal))
        moves = find_moves(start, optimal)
        self.assertEqual(len(moves), 7)
        self.assertEqual(replay_moves(start, moves)[-1], optimal)

    def test_initial_diagonal_solution_min_moves(self):
        start = tuple(range(8))
        best = min(self.targets, key=lambda s: (move_cost(start, s), s))
        self.assertEqual(sum(a != b for a, b in zip(start, best)), move_cost(start, best))
        self.assertEqual(best, replay_moves(start, find_moves(start, best))[-1])
        self.assertTrue(is_valid_solution(best))

    def test_each_move_only_changes_its_column(self):
        start = (0,) * 8
        goal = self.targets[-1]
        moves = find_moves(start, goal)
        boards = replay_moves(start, moves)
        self.assertEqual(move_cost(start, goal), len(moves))
        for before, after in zip(boards, boards[1:]):
            self.assertEqual(1, sum(a != b for a, b in zip(before, after)))


try:
    from queens_agent import run_queens
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False


@unittest.skipUnless(HAS_LANGGRAPH, "Install project's requirements (langgraph) to run graph integration tests")
class LangGraphIntegrationTests(unittest.TestCase):
    def test_global_optimality_for_diagonal(self):
        start = tuple(range(8))
        _, state = run_queens(start)
        self.assertEqual(state["checked"], 92)
        self.assertTrue(state["finished"])
        self.assertTrue(is_valid_solution(state["best"]))
        self.assertEqual(min(move_cost(start, t) for t in enumerate_solutions()), state["best_cost"])
        self.assertEqual(92, len(state["candidate_costs"]))

    def test_already_solved_board(self):
        initial = enumerate_solutions()[0]
        _, final = run_queens(initial)
        self.assertEqual(0, final["best_cost"])
        self.assertEqual(initial, final["best"])

    def test_same_row_start(self):
        _, final = run_queens([0] * 8)
        self.assertEqual(7, final["best_cost"])
        self.assertTrue(is_valid_solution(final["best"]))


if __name__ == "__main__":
    unittest.main()
