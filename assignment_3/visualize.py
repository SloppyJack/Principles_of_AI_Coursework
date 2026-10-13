"""Offline figures and Mermaid workflow source for the 8-Queens extension."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, FancyArrowPatch

from queens_core import Board, find_moves, replay_moves


def draw_board(ax, board: Board, title: str, changed_cols: set[int] | None = None):
    changed_cols = changed_cols or set()
    ax.set_xlim(0, 8)
    ax.set_ylim(8, 0)
    ax.set_aspect("equal")
    ax.set_xticks([i + 0.5 for i in range(8)], [str(i + 1) for i in range(8)])
    ax.set_yticks([i + 0.5 for i in range(8)], [str(i + 1) for i in range(8)])
    ax.tick_params(length=0, labelsize=8)
    ax.set_title(title, fontsize=11)
    for row in range(8):
        for col in range(8):
            ax.add_patch(Rectangle((col, row), 1, 1,
                                   facecolor="#e4eaf2" if (row + col) % 2 == 0 else "#8ea8c0",
                                   edgecolor="white", linewidth=0.5))
    for col, row in enumerate(board):
        ax.text(col + 0.5, row + 0.5, "Q", fontsize=22,
                color="#bd2424" if col in changed_cols else "#11365b",
                weight="bold", ha="center", va="center")
    for spine in ax.spines.values():
        spine.set_visible(False)


def plot_solution(initial: Board, target: Board, path: str | Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    moves = find_moves(initial, target)
    boards = replay_moves(initial, moves)
    ncols = 3
    nrows = (len(boards) + ncols - 1) // ncols
    fig, axs = plt.subplots(nrows, ncols, figsize=(4 * ncols, 4.25 * nrows))
    axs = list(axs.flat) if hasattr(axs, "flat") else [axs]
    for i, (ax, board) in enumerate(zip(axs, boards)):
        if i == 0:
            caption = "Initial board"
            changed = set()
        else:
            move = moves[i - 1]
            caption = (f"Move {i}: column {move['column']}, "
                       f"row {move['from_row']} -> {move['to_row']}")
            if i == len(boards) - 1:
                caption += " (goal)"
            changed = {move["column"] - 1}
        draw_board(ax, board, caption, changed)
    for ax in axs[len(boards):]:
        ax.set_axis_off()
    fig.suptitle(f"8-Queens: globally optimal {len(moves)} queen moves", fontsize=15)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_search(final: dict, path: str | Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    x = list(range(1, len(final["candidate_costs"]) + 1))
    fig, ax = plt.subplots(figsize=(9, 4.7))
    ax.scatter(x, final["candidate_costs"], s=17, alpha=0.5, label="Candidate cost")
    ax.plot(x, final["best_costs"], color="#d35400", lw=2.2,
            label="Best cost so far")
    ax.set_title("8-Queens: Global Optimality by Exhaustive Search")
    ax.set_xlabel("Valid arrangement evaluated (1..92)")
    ax.set_ylabel("Number of queens moved")
    ax.set_ylim(-0.25, 8.5)
    ax.set_yticks(range(9))
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_workflow(graph, out_dir: str | Path):
    """Draw an offline workflow PNG and export the actual LangGraph Mermaid."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        mermaid = graph.get_graph().draw_mermaid()
    except Exception as exc:
        mermaid = f"%% Could not export graph: {exc}\n"
    (out_dir / "workflow.mmd").write_text(mermaid, encoding="utf-8")

    fig, ax = plt.subplots(figsize=(8, 6.7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    def box(x, y, title, subtitle, color="#ebf2fa"):
        patch = FancyBboxPatch((x, y), 5, 1.15,
                               boxstyle="round,pad=0.13,rounding_size=0.12",
                               ec="#4b647b", fc=color, lw=1.4)
        ax.add_patch(patch)
        ax.text(x + 2.5, y + 0.79, title, ha="center", va="center",
                fontsize=13, weight="bold")
        ax.text(x + 2.5, y + 0.34, subtitle, ha="center", va="center", fontsize=9)

    def arrow(a, b):
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=15,
                                     color="#607d8b", linewidth=1.8))

    box(2.5, 8.4, "START / init", "validate and enumerate 92 valid targets")
    box(2.5, 5.7, "search", "evaluate cost and update best solution", "#dcf3ed")
    box(2.5, 3.0, "route_decision", "more valid targets?", "#fff0d9")
    box(2.5, 0.3, "END", "return global optimal result")
    arrow((5, 8.4), (5, 6.95))
    arrow((5, 5.7), (5, 4.35))
    arrow((5, 3), (5, 1.65))
    ax.text(5.2, 2.4, "finished", fontsize=10)
    arrow((2.5, 3.65), (1.0, 3.65))
    arrow((1.0, 3.65), (1.0, 6.28))
    arrow((1.0, 6.28), (2.5, 6.28))
    ax.text(0.15, 5.0, "continue", fontsize=10)
    fig.tight_layout()
    fig.savefig(out_dir / "workflow.png", dpi=160)
    plt.close(fig)
