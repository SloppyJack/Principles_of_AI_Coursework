"""CLI: minimum number of *queens moved* to reach an attack-free 8-queen board.

Examples:
    python main.py
    python main.py --initial "1,2,3,4,5,6,7,8"
    python main.py --initial "4 2 7 3 6 8 5 1" --no-plots
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from queens_core import (
    conflicts, find_moves, is_valid_solution, pretty_board, replay_moves,
    validate_board,
)
from queens_agent import run_queens

DEFAULT_INITIAL = (0, 2, 4, 6, 1, 3, 5, 7)  # Photo example: 1-based [1, 3, 5, 7, 2, 4, 6, 8]


def parse_rows(input_string: str) -> tuple[int, ...]:
    """Human-friendly 1-based row positions, comma or space separated."""
    try:
        rows = [int(token) for token in input_string.replace(",", " ").split()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("请输入 8 个整数，例如 1,2,3,4,5,6,7,8") from exc
    if len(rows) != 8 or any(not 1 <= r <= 8 for r in rows):
        raise argparse.ArgumentTypeError("必须输入 8 个 1~8 之间的行号，每列一个")
    return validate_board([x - 1 for x in rows])


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description="LangGraph 八皇后：最少移动皇后数量")
    parser.add_argument("--initial", type=parse_rows, default=DEFAULT_INITIAL,
                        help="按列提供 8 个 1-based 行号，例如 '1,2,3,4,5,6,7,8'")
    parser.add_argument("--output-dir", type=Path,
                        default=Path(__file__).resolve().parent / "output")
    parser.add_argument("--no-plots", action="store_true", help="不生成图片")
    parser.add_argument("--verbose", action="store_true", help="打印搜索进度")
    parser.add_argument("--algorithm", choices=("enumerate", "bfs", "dfs", "compare"), default="enumerate", help="选择搜索算法")
    args = parser.parse_args(argv)

    initial = args.initial
    print("\n=== LangGraph 八皇后最少移动求解 ===")
    print("移动定义：同一列改变一个皇后的行号，计一次移动；中途允许冲突。")
    print("初始位置（按列、1-based 行号）：", [x + 1 for x in initial])
    print(pretty_board(initial))
    print("初始互相攻击的皇后对数：", conflicts(initial))

    if args.algorithm in ("bfs", "dfs", "compare"):
        from search_graph import run_search
        if args.algorithm == "compare":
            _, base_state = run_queens(initial)
            comparison = {"enumerate": {
                "minimum_moves": base_state["best_cost"],
                "explored": base_state["checked"],
                "goal_rows_1based": [x + 1 for x in base_state["best"]],
            }}
            for method in ("bfs", "dfs"):
                _, state = run_search(initial, method)
                comparison[method] = state["result"]
            if len({value["minimum_moves"] for value in comparison.values()}) != 1:
                raise AssertionError("搜索算法最优移动数不一致")
            output_dir = args.output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "comparison.json").write_text(
                json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
            print("\n=== 三种算法比较 ===")
            for method, item in comparison.items():
                print(f"{method}: 移动 {item['minimum_moves']} 次，检查 {item['explored']} 个节点")
            print("已保存：", output_dir / "comparison.json")
            return comparison
        graph, state = run_search(initial, args.algorithm)
        outcome = state["result"]
        goal = tuple(x - 1 for x in outcome["goal_rows_1based"])
        moves = find_moves(initial, goal)
        print(f"\n=== {args.algorithm.upper()} 搜索结果 ===")
        print("最少移动次数：", outcome["minimum_moves"])
        print("展开节点：", outcome["explored"])
        print("目标布局：", outcome["goal_rows_1based"])
        for index, move in enumerate(moves, 1):
            print(f"移动 {index}: 第{move['column']}列，第{move['from_row']}行 -> 第{move['to_row']}行")
        output_dir = args.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / f"result_{args.algorithm}.json").write_text(
            json.dumps(outcome, ensure_ascii=False, indent=2), encoding="utf-8")
        if not args.no_plots:
            from visualize import plot_solution, plot_workflow
            plot_solution(initial, goal, output_dir / f"solution_{args.algorithm}.png")
            plot_workflow(graph, output_dir / args.algorithm)
        return outcome

    graph, final = run_queens(initial, verbose=args.verbose)
    goal = final["best"]
    moves = find_moves(initial, goal)
    history = replay_moves(initial, moves)
    assert history[-1] == goal and is_valid_solution(goal)
    assert len(moves) == final["best_cost"]

    print("\n=== 最优结果 ===")
    print(f"遍历合法目标布局：{final['checked']} 种")
    print(f"最少移动皇后数量：{final['best_cost']}")
    print("最优目标布局（每列的行号，1-based）：", [x + 1 for x in goal])
    print(pretty_board(goal))
    for idx, move in enumerate(moves, 1):
        print(f"移动 {idx}: 第 {move['column']} 列，"
              f"第 {move['from_row']} 行 -> 第 {move['to_row']} 行")
    print("最终互相攻击的皇后对数：", conflicts(goal))

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "movement_rule": "Move one queen to any row in its existing column; intermediate attacks allowed",
        "initial_rows_1based": [x + 1 for x in initial],
        "initial_attacking_pairs": conflicts(initial),
        "goal_rows_1based": [x + 1 for x in goal],
        "goal_attacking_pairs": conflicts(goal),
        "minimum_moves": final["best_cost"],
        "checked_valid_targets": final["checked"],
        "moves_1based": moves,
        "all_candidate_costs": final["candidate_costs"],
        "best_cost_history": final["best_costs"],
        "improvements": final["improvements"],
    }
    (output_dir / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"结果 JSON：{output_dir / 'result.json'}")

    if not args.no_plots:
        from visualize import plot_solution, plot_search, plot_workflow
        plot_solution(initial, goal, output_dir / "solution_path.png")
        plot_search(final, output_dir / "search_stats.png")
        plot_workflow(graph, output_dir)
        print("图像与流程：solution_path.png、search_stats.png、workflow.png、workflow.mmd")
    return result


if __name__ == "__main__":
    main()
