"""
visualize.py
可视化模块：终端打印、搜索统计图、解路径图、LangGraph 工作流结构图。
所有依赖 matplotlib 的图内文字使用英文，避免中文字体警告。
"""

import os
import matplotlib
matplotlib.use("Agg")            # 无界面后端，直接保存图片
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from puzzle_core import apply_move


# =========================================================
# 一、终端打印：棋盘可视化
# =========================================================

def print_board(state: tuple, indent: str = "  "):
    """在终端打印一个 3x3 棋盘（空格用下划线表示）"""
    for i in range(3):
        row = state[i * 3:(i + 1) * 3]
        print(indent + " ".join("_" if x == 0 else str(x) for x in row))


# =========================================================
# 二、棋盘绘制（供路径图使用）
# =========================================================

def _draw_board_on_ax(ax, state: tuple, title: str):
    """在给定的 matplotlib 轴上画一个 3x3 棋盘"""
    ax.set_xlim(0, 3); ax.set_ylim(0, 3)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(title, fontsize=11)

    # 网格线
    for i in range(4):
        ax.plot([0, 3], [i, i], color="black", lw=1.5)
        ax.plot([i, i], [0, 3], color="black", lw=1.5)

    # 数字
    for idx, val in enumerate(state):
        r, c = idx // 3, idx % 3
        y = 2 - r
        if val == 0:
            ax.add_patch(Rectangle((c, y), 1, 1, color="#dfe6e9"))
        else:
            ax.add_patch(Rectangle((c, y), 1, 1, color="#74b9ff", alpha=0.7))
            ax.text(c + 0.5, y + 0.5, str(val),
                    ha="center", va="center", fontsize=18, weight="bold")


# =========================================================
# 三、搜索过程统计图：Open / Closed 集合大小变化
# =========================================================

def plot_search_stats(result: dict,
                      save_path: str = "output/search_stats.png"):
    """画 A* 过程中 Open / Closed 集合随步数变化的曲线"""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    steps = list(range(1, len(result["open_sizes"]) + 1))

    plt.figure(figsize=(8, 4.5))
    plt.plot(steps, result["open_sizes"],   marker="o", label="Open set size")
    plt.plot(steps, result["closed_sizes"], marker="s", label="Closed set size")
    plt.xlabel("Search step (A* expansions)")
    plt.ylabel("Set size")
    plt.title("A* Search: Open / Closed Set Size over Iterations")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"[图片] 搜索统计图已保存：{save_path}")


# =========================================================
# 四、解路径图：最短路径上每一步的棋盘
# =========================================================

def plot_solution_path(initial, goal, path,
                       save_path: str = "output/solution_path.png"):
    """把最短路径上每一步的棋盘画成子图"""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # 沿路径回放所有状态
    states = [tuple(initial)]
    cur = tuple(initial)
    for mv in path:
        cur = apply_move(cur, mv)
        states.append(cur)

    n = len(states)
    cols = 4
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(3.2 * cols, 3.2 * rows))
    axes = axes.flatten() if rows * cols > 1 else [axes]

    for i, st in enumerate(states):
        if i == 0:
            title = "Initial State"
        elif i == len(states) - 1:
            title = f"Step {i}: {path[i-1]} (Goal)"
        else:
            title = f"Step {i}: {path[i-1]}"
        _draw_board_on_ax(axes[i], st, title)

    # 隐藏多余子图
    for j in range(len(states), len(axes)):
        axes[j].axis("off")

    fig.suptitle("8-Puzzle Shortest Path Solution", fontsize=14, weight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"[图片] 解路径图已保存：{save_path}")


# =========================================================
# 五、LangGraph 工作流结构图（Mermaid）
# =========================================================

def plot_workflow(graph, save_path: str = "output/workflow.png"):
    """用 LangGraph 内置的 Mermaid 渲染器输出工作流结构图"""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    try:
        png = graph.get_graph().draw_mermaid_png()
        with open(save_path, "wb") as f:
            f.write(png)
        print(f"[图片] LangGraph 工作流结构图已保存：{save_path}")
    except Exception as e:
        print(f"[提示] 无法生成工作流图（{e}），"
              f"可改用 draw_mermaid() 查看 Mermaid 源码。")