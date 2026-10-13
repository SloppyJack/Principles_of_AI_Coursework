"""LangGraph-based exhaustive, globally optimal minimum-move 8-Queens agent.

Preserves assignment_2's init/search/route_decision/StateGraph pattern.
Every search graph iteration evaluates one *complete valid* target board.
"""
from __future__ import annotations

from typing import TypedDict

from langgraph.graph import StateGraph, END

from queens_core import Board, enumerate_solutions, move_cost, validate_board


class QueensState(TypedDict, total=False):
    initial: Board
    candidates: tuple[Board, ...]
    cursor: int
    checked: int
    best: Board | None
    best_cost: int
    finished: bool
    candidate_costs: list[int]
    best_costs: list[int]
    improvements: list[dict]


def init_node(state: QueensState) -> dict:
    candidates = enumerate_solutions()
    return {
        "candidates": candidates,
        "cursor": 0,
        "checked": 0,
        "best": None,
        "best_cost": 9,  # cost is in [0, 8]; all candidates beat sentinel
        "finished": len(candidates) == 0,
        "candidate_costs": [],
        "best_costs": [],
        "improvements": [],
    }


def search_node(state: QueensState) -> dict:
    if state["finished"]:
        return {}
    cursor = state["cursor"]
    target = state["candidates"][cursor]
    cost = move_cost(state["initial"], target)
    improved = cost < state["best_cost"]
    best = target if improved else state["best"]
    best_cost = cost if improved else state["best_cost"]
    improvements = state["improvements"]
    if improved:
        improvements = improvements + [
            {"candidate_number": cursor + 1, "min_moves": best_cost, "board": list(target)}
        ]
    return {
        "cursor": cursor + 1,
        "checked": state["checked"] + 1,
        "best": best,
        "best_cost": best_cost,
        "finished": cursor + 1 == len(state["candidates"]),
        "candidate_costs": state["candidate_costs"] + [cost],
        "best_costs": state["best_costs"] + [best_cost],
        "improvements": improvements,
    }


def route_decision(state: QueensState) -> str:
    return "finished" if state["finished"] else "continue_search"


def build_graph():
    workflow = StateGraph(QueensState)
    workflow.add_node("init", init_node)
    workflow.add_node("search", search_node)
    workflow.set_entry_point("init")
    workflow.add_edge("init", "search")
    workflow.add_conditional_edges(
        "search", route_decision,
        {"continue_search": "search", "finished": END},
    )
    return workflow.compile()


def run_queens(initial: list[int] | tuple[int, ...], verbose: bool = False):
    """Return (compiled_graph, final_shared_state).

    Explicit graph recursion_limit allows all 92 graph search steps even on
    LangGraph versions with a low default limit (older versions defaulted to 25).
    """
    board = validate_board(initial)
    graph = build_graph()
    final = None
    for state in graph.stream(
        {"initial": board},
        stream_mode="values",
        config={"recursion_limit": 256},
    ):
        if verbose and state.get("checked", 0) and state.get("checked", 0) % 10 == 0:
            print(f"  搜索进度：{state['checked']:>2}/92，当前最优：{state['best_cost']} 步")
        final = state
    if final is None or final.get("best") is None or not final.get("finished"):
        raise RuntimeError("LangGraph 未完成最优解搜索")
    return graph, final
