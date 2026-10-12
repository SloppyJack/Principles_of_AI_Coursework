"""
main.py
主入口：组装所有模块，运行求解，输出结果并生成可视化。
"""

from astar_agent import run_astar
from visualize import (
    print_board,
    plot_search_stats,
    plot_solution_path,
    plot_workflow,
)


# =========================================================
# 实验用的初态与目标态（经典测试用例）
# =========================================================
#
# INITIAL_STATE = [2, 8, 3,
#                  1, 6, 4,
#                  7, 0, 5]

INITIAL_STATE = [3, 5, 6,
                 8, 4, 7,
                 2, 1, 0]

GOAL_STATE    = [1, 2, 3,
                 8, 0, 4,
                 7, 6, 5]


def main():
    # ---------- 1. 打印问题 ----------
    print("=" * 60)
    print("八数码最短路径求解实验")
    print("=" * 60)
    print("初始状态：")
    print_board(tuple(INITIAL_STATE), indent="    ")
    print("目标状态：")
    print_board(tuple(GOAL_STATE), indent="    ")

    # ---------- 2. 运行 A* + LangGraph ----------
    graph, final = run_astar(INITIAL_STATE, GOAL_STATE, verbose=True)

    if final is None:
        print("[错误] 未获得最终状态。")
        return

    # ---------- 3. 输出工作流结构图 ----------
    plot_workflow(graph)

    # ---------- 4. 输出结果 ----------
    if final["solved"]:
        path = final["path"]
        print("\n" + "=" * 60)
        print(f"找到最短路径！总步数 = {len(path)}")
        print(f"操作序列：{path}")
        print("=" * 60)

        # ---------- 5. 生成可视化图表 ----------
        plot_search_stats(final)
        plot_solution_path(INITIAL_STATE, GOAL_STATE, path)
    else:
        print("\n无解：初始状态无法到达目标状态。")

    # ---------- 6. 小结 ----------
    print("\n[小结]")
    print(f"  初始状态：{INITIAL_STATE}")
    print(f"  目标状态：{GOAL_STATE}")
    if final["solved"]:
        print(f"  最短步数：{len(final['path'])}")
        print(f"  移动路径：{final['path']}")
    print("  已在 output/ 目录生成 3 张图片：")
    print("    - workflow.png       （LangGraph 工作流结构）")
    print("    - search_stats.png   （Open/Closed 集合变化）")
    print("    - solution_path.png  （最短路径每步棋盘）")


if __name__ == "__main__":
    main()