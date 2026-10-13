"""LangGraph adapter for BFS and depth-first (iterative deepening) search.

Graph separates initial validation, deterministic search, and final verification.
Each search method performs its own frontier traversal inside search_node.
"""
from __future__ import annotations
from typing import TypedDict
from langgraph.graph import StateGraph, END
from queens_core import Board, conflicts, replay_moves, validate_board
from search_methods import solve


class SearchState(TypedDict, total=False):
    initial: Board
    method: str
    result: dict
    verified: bool


def init_node(state: SearchState) -> dict:
    return {"initial": validate_board(state["initial"])}


def search_node(state: SearchState) -> dict:
    result = solve(state["initial"], state["method"])
    return {"result": result.as_dict()}


def verify_node(state: SearchState) -> dict:
    result = state["result"]
    initial = state["initial"]
    final = tuple(x - 1 for x in result["goal_rows_1based"])
    moves = result["moves_1based"]
    verified = (replay_moves(initial, moves)[-1] == final and
                conflicts(final) == 0 and
                len(moves) == result["minimum_moves"])
    if not verified:
        raise AssertionError("Search solution failed verification")
    return {"verified": True}


def build_search_graph():
    graph = StateGraph(SearchState)
    graph.add_node("init", init_node)
    graph.add_node("search", search_node)
    graph.add_node("verify", verify_node)
    graph.set_entry_point("init")
    graph.add_edge("init", "search")
    graph.add_edge("search", "verify")
    graph.add_edge("verify", END)
    return graph.compile()


def run_search(initial: Board, method: str):
    if method not in ("bfs", "dfs"):
        raise ValueError("method must be bfs or dfs")
    graph = build_search_graph()
    state = graph.invoke({"initial": validate_board(initial), "method": method})
    if not state.get("verified"):
        raise AssertionError("Graph did not verify search result")
    return graph, state
