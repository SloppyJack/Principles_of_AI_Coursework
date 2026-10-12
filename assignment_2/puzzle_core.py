"""
puzzle_core.py
八数码问题本体：状态表示、合法移动、启发函数、可解性判断。
本模块不依赖任何第三方库，纯 Python 实现。
"""

from typing import List, Tuple


# =========================================================
# 状态表示：3x3 棋盘按行优先展平为长度 9 的元组，空格用 0 表示
# =========================================================

def state_to_hash(state: tuple) -> str:
    """把状态元组转换为字符串，方便作为集合/字典的键"""
    return ''.join(str(x) for x in state)


def get_goal_position_map(goal: tuple) -> dict:
    """构建目标状态中每个数字的位置映射：tile -> (row, col)"""
    pos_map = {}
    for i in range(3):
        for j in range(3):
            tile = goal[i * 3 + j]
            if tile != 0:
                pos_map[tile] = (i, j)
    return pos_map


# =========================================================
# 启发函数：曼哈顿距离
# =========================================================

def manhattan_distance(state: tuple, goal_pos: dict) -> int:
    """
    计算状态的曼哈顿距离启发值：
    每个数字当前位置到目标位置的曼哈顿距离之和（空格不参与）。
    """
    distance = 0
    for i in range(3):
        for j in range(3):
            tile = state[i * 3 + j]
            if tile != 0:
                gi, gj = goal_pos[tile]
                distance += abs(i - gi) + abs(j - gj)
    return distance


# =========================================================
# 合法操作：空格与上下左右相邻数字交换
# =========================================================

def get_neighbors(state: tuple) -> List[Tuple[tuple, str]]:
    """
    生成所有合法邻居状态，返回 (新状态, 移动方向) 列表。
    移动方向用 U/D/L/R 表示（空格移动方向）。
    """
    neighbors = []
    zero_pos = state.index(0)
    row, col = zero_pos // 3, zero_pos % 3

    moves = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]
    for dr, dc, direction in moves:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            new_pos = nr * 3 + nc
            new_state = list(state)
            new_state[zero_pos], new_state[new_pos] = (
                new_state[new_pos], new_state[zero_pos]
            )
            neighbors.append((tuple(new_state), direction))
    return neighbors


def apply_move(state: tuple, move: str) -> tuple:
    """在给定状态上应用一次移动，返回新状态（用于路径回放和可视化）"""
    s = list(state)
    z = s.index(0)
    r, c = z // 3, z % 3
    if move == 'U':   n = (r - 1) * 3 + c
    elif move == 'D': n = (r + 1) * 3 + c
    elif move == 'L': n = r * 3 + (c - 1)
    else:             n = r * 3 + (c + 1)
    s[z], s[n] = s[n], s[z]
    return tuple(s)


# =========================================================
# 可解性判定：逆序数奇偶性
# =========================================================

def is_solvable(initial: tuple, goal: tuple) -> bool:
    """
    通过逆序数奇偶性判断八数码问题是否可解：
    忽略空格，计算数字序列的逆序数；
    若初态与目标态的逆序数奇偶性相同，则可解。
    """
    def inv(s):
        seq = [x for x in s if x != 0]
        return sum(1 for i in range(len(seq)) for j in range(i + 1, len(seq))
                   if seq[i] > seq[j])
    return inv(initial) % 2 == inv(goal) % 2