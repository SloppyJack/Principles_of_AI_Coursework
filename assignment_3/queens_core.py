"""8-Queens domain logic; independent of LangGraph and plotting.

Representation: index = column (0..7), value = row (0..7).
An atomic move changes the row of one queen within its own column.
Intermediate boards are permitted to contain attacks.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Iterable

BOARD_SIZE = 8
Board = tuple[int, ...]


def validate_board(values: Iterable[int]) -> Board:
    """Validate the one-queen-per-column input, including all row ranges."""
    try:
        board = tuple(values)
    except TypeError as exc:
        raise ValueError("棋盘必须是含 8 个整数的序列") from exc
    if len(board) != BOARD_SIZE:
        raise ValueError(f"需要恰好 {BOARD_SIZE} 列，每列放置一个皇后")
    if any(type(row) is not int or not 0 <= row < BOARD_SIZE for row in board):
        raise ValueError("每列的行位置必须为 0 到 7 的整数（内部使用 0 起始编号）")
    return board


def conflicts(board: Board) -> int:
    """Count attacking pairs (columns are distinct by construction)."""
    board = validate_board(board)
    return sum(
        board[c1] == board[c2] or abs(board[c1] - board[c2]) == c2 - c1
        for c1 in range(BOARD_SIZE)
        for c2 in range(c1 + 1, BOARD_SIZE)
    )


def is_valid_solution(board: Board) -> bool:
    return conflicts(board) == 0


@lru_cache(maxsize=1)
def enumerate_solutions() -> tuple[Board, ...]:
    """Backtracking over rows/diagonals yields every one of the 92 valid boards."""
    results: list[Board] = []
    placement: list[int] = []
    used_rows: set[int] = set()
    used_diag_down: set[int] = set()  # row - col
    used_diag_up: set[int] = set()    # row + col

    def backtrack(col: int) -> None:
        if col == BOARD_SIZE:
            results.append(tuple(placement))
            return
        for row in range(BOARD_SIZE):
            down, up = row - col, row + col
            if row in used_rows or down in used_diag_down or up in used_diag_up:
                continue
            placement.append(row)
            used_rows.add(row)
            used_diag_down.add(down)
            used_diag_up.add(up)
            backtrack(col + 1)
            placement.pop()
            used_rows.remove(row)
            used_diag_down.remove(down)
            used_diag_up.remove(up)

    backtrack(0)
    return tuple(results)


def move_cost(initial: Board, target: Board) -> int:
    """Number of queens that must be moved, NOT vertical travel distance."""
    initial = validate_board(initial)
    target = validate_board(target)
    return sum(a != b for a, b in zip(initial, target))


def find_moves(initial: Board, target: Board) -> list[dict[str, int]]:
    """One direct vertical movement per changed column, using 1-based labels."""
    initial = validate_board(initial)
    target = validate_board(target)
    return [
        {"column": col + 1, "from_row": src + 1, "to_row": dst + 1}
        for col, (src, dst) in enumerate(zip(initial, target))
        if src != dst
    ]


def replay_moves(initial: Board, moves: list[dict[str, int]]) -> list[Board]:
    """Include initial board and the board after each operation."""
    board = list(validate_board(initial))
    history = [tuple(board)]
    for move in moves:
        col, old, new = move["column"] - 1, move["from_row"] - 1, move["to_row"] - 1
        if not (0 <= col < BOARD_SIZE and 0 <= new < BOARD_SIZE and board[col] == old and old != new):
            raise ValueError(f"非法移动: {move}")
        board[col] = new
        history.append(tuple(board))
    return history


def pretty_board(board: Board) -> str:
    board = validate_board(board)
    lines = ["    " + " ".join(str(col) for col in range(1, BOARD_SIZE + 1))]
    for row in range(BOARD_SIZE):
        cells = ["Q" if board[col] == row else "." for col in range(BOARD_SIZE)]
        lines.append(f"{row+1:>2}  " + " ".join(cells))
    return "\n".join(lines)
