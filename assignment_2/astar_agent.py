"""
astar_agent.py
基于 A* 搜索的八数码求解智能体，使用 LangGraph 编排搜索循环。
包含：
  - LangGraph 共享状态定义 (PuzzleState)
  - 三个节点：init_node / search_node / route_decision
  - 工作流构建函数 build_graph()
  - 求解入口 solve_8_puzzle()
"""

import heapq
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from puzzle_core import (
    manhattan_distance,
    get_goal_position_map,
    get_neighbors,
    is_solvable,
    state_to_hash,
)


# =========================================================
# 一、LangGraph 共享状态
# =========================================================

class PuzzleState(TypedDict):
    """在 LangGraph 图中流动的共享状态"""
    # --- 搜索所需字段 ---
    initial: tuple                 # 初始状态
    goal: tuple                    # 目标状态
    open_heap: list                # 开放列表（优先队列）
    open_set: dict                 # 开放集 {state_hash: node_dict}
    closed_set: set                # 关闭集
    current_node: Optional[dict]   # 当前正在扩展的节点
    path: Optional[str]            # 找到的路径
    solved: bool                   # 是否已找到解
    exhausted: bool                # 开放列表是否已耗尽（无解）
    goal_pos: dict                 # 目标位置映射（预计算加速）
    counter: int                   # 堆的插入计数器（避免节点字典比较）
    # --- 可视化统计字段 ---
    step: int                      # 已扩展的节点数
    open_sizes: list               # 每步的开放集大小
    closed_sizes: list             # 每步的关闭集大小
    history: list                  # 每步扩展的棋盘状态


# =========================================================
# 二、节点函数
# =========================================================

def init_node(state: PuzzleState) -> dict:
    """初始化 A* 搜索：把初始状态封装成起点节点"""
    initial = state["initial"]
    goal = state["goal"]

    # 先做可解性检查
    if not is_solvable(initial, goal):
        return {"solved": False, "exhausted": True, "path": None}

    goal_pos = get_goal_position_map(goal)
    h = manhattan_distance(initial, goal_pos)

    start_node = {
        "state": initial, "g": 0, "h": h, "f": h,
        "parent": None, "direction": None,
        "state_hash": state_to_hash(initial),
    }

    return {
        "goal_pos": goal_pos,
        "open_heap": [(h, 0, start_node)],
        "open_set": {start_node["state_hash"]: start_node},
        "closed_set": set(),
        "current_node": None,
        "solved": False,
        "exhausted": False,
        "path": None,
        "counter": 1,
        "step": 0,
        "open_sizes": [],
        "closed_sizes": [],
        "history": [],
    }


def search_node(state: PuzzleState) -> dict:
    """执行 A* 算法的一次迭代（弹出最小 f 节点 + 扩展邻居）"""
    if state["solved"] or state["exhausted"]:
        return {}

    # 复制状态，避免直接修改原状态
    heap = list(state["open_heap"])
    open_set = dict(state["open_set"])
    closed_set = set(state["closed_set"])
    goal = state["goal"]
    goal_pos = state["goal_pos"]
    counter = state["counter"]

    # 从堆中弹出 f 值最小的节点（惰性删除：跳过已关闭节点）
    current_node = None
    while heap:
        _, _, node = heapq.heappop(heap)
        if node["state_hash"] not in closed_set:
            current_node = node
            break

    if current_node is None:
        return {"exhausted": True, "open_heap": heap}

    # 到达目标：回溯路径
    if current_node["state_hash"] == state_to_hash(goal):
        path = []
        node = current_node
        while node["parent"] is not None:
            path.append(node["direction"])
            node = node["parent"]
        return {
            "solved": True,
            "path": ''.join(reversed(path)),
            "current_node": current_node,
            "open_heap": heap,
        }

    closed_set.add(current_node["state_hash"])

    # 扩展邻居
    for neighbor_state, direction in get_neighbors(current_node["state"]):
        n_hash = state_to_hash(neighbor_state)
        if n_hash in closed_set:
            continue

        tentative_g = current_node["g"] + 1
        h = manhattan_distance(neighbor_state, goal_pos)
        f = tentative_g + h

        neighbor_node = {
            "state": neighbor_state, "g": tentative_g, "h": h, "f": f,
            "parent": current_node, "direction": direction,
            "state_hash": n_hash,
        }

        if n_hash not in open_set:
            open_set[n_hash] = neighbor_node
            heapq.heappush(heap, (f, counter, neighbor_node))
            counter += 1
        else:
            existing = open_set[n_hash]
            if tentative_g < existing["g"]:
                existing.update({"g": tentative_g, "f": f,
                                 "parent": current_node, "direction": direction})
                heapq.heappush(heap, (f, counter, existing))
                counter += 1

    step = state["step"] + 1
    return {
        "open_heap": heap,
        "open_set": open_set,
        "closed_set": closed_set,
        "current_node": current_node,
        "counter": counter,
        "step": step,
        "open_sizes": state["open_sizes"] + [len(open_set)],
        "closed_sizes": state["closed_sizes"] + [len(closed_set)],
        "history": state["history"] + [current_node["state"]],
    }


def route_decision(state: PuzzleState) -> str:
    """条件路由：根据状态决定下一步走哪条边"""
    if state["solved"]:
        return "end_solved"
    if state["exhausted"]:
        return "end_no_solution"
    return "continue_search"


# =========================================================
# 三、构建并编译 LangGraph 工作流
# =========================================================

def build_graph():
    """构建 A* 搜索的 LangGraph 工作流"""
    wf = StateGraph(PuzzleState)

    # 添加节点
    wf.add_node("init", init_node)
    wf.add_node("search", search_node)

    # 入口
    wf.set_entry_point("init")

    # 初始化后进入搜索
    wf.add_edge("init", "search")

    # 条件边：根据 route_decision 选择下一节点
    wf.add_conditional_edges(
        "search", route_decision,
        {"continue_search": "search",   # 继续搜索（形成循环）
         "end_solved": END,             # 找到解
         "end_no_solution": END}        # 无解
    )
    return wf.compile()


# =========================================================
# 四、求解入口（返回最终状态，供 main 和可视化使用）
# =========================================================

def run_astar(initial: list, goal: list, verbose: bool = True):
    """
    运行 A* 搜索，返回 (graph, final_state)。
    final_state 包含 solved / path / open_sizes / closed_sizes 等字段。
    """
    initial = tuple(initial)
    goal = tuple(goal)

    graph = build_graph()
    init_state = {"initial": initial, "goal": goal}

    # 用于终端实时打印的中文提示（可视化由 main 决定是否调用）
    print("\n" + "=" * 60)
    print("开始 A* 搜索（通过 LangGraph 流式执行）")
    print("=" * 60)

    final = None
    step = 0
    for chunk in graph.stream(init_state, stream_mode="values"):
        final = chunk
        cur = chunk.get("current_node")
        if cur is None or chunk["solved"] or chunk["exhausted"]:
            continue
        step += 1
        if verbose:
            # 这里只打印文字信息，棋盘绘制交给 visualize 模块
            print(f"\n---- 第 {step} 次扩展 ----")
            print(f"  当前节点：g={cur['g']}, h={cur['h']}, f={cur['f']}")
            print(f"  开放集大小={len(chunk['open_heap'])}，"
                  f"关闭集大小={len(chunk['closed_set'])}")
            print(f"  当前状态：{cur['state']}")

    return graph, final