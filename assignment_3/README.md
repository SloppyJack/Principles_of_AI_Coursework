# Assignment 3：八皇后最少移动（LangGraph）

本目录是对原仓库 `Principles_of_AI_Coursework` 的**新增功能**，复用 `assignment_2` 的 `StateGraph` / `init_node` / `search_node` / `route_decision` 编排方式，不修改原八数码程序。

## 规则

- 8 列，每列恰好 1 个皇后。`board[c]` 指第 `c` 列皇后的行（Python 内部 0-based）。初始状态可以有同一行/对角线冲突。
- 一次移动：**在同一列**将一枚皇后直接移到该列另一行；不限制跨越的行数；中途可存在冲突。
- 最终状态：同一行与任一对角线都没有 2 个皇后，同一列已由数据结构保证。
- 最小化 **被改变位置的皇后个数**，不是纵向距离之和，也不是每移动一格的步数。

## 安装与运行

在原仓库根目录执行：

```bash
python -m pip install -r requirements.txt
python run_coursework.py queens
python run_coursework.py queens --initial "1,3,5,7,2,4,6,8"
python run_coursework.py queens --initial "4,2,7,3,6,8,5,1" --no-plots
```

或在 `assignment_3` 中 `python main.py`。`--initial` 接收从**第 1 列到第 8 列**的行号，值 `1..8`，用逗号或空格分隔（空格形式需要引号）。若不传，默认采用课堂图片识别后的初始布局 `[1,3,5,7,2,4,6,8]`（列从左至右、行从上至下编号 1–8；其中第 7 列的位置依据图片作暂定识别，如图片更清晰需核对）。

原八数码不受影响：

```bash
python run_coursework.py puzzle
```

单元测试：

```bash
python -m unittest discover -s assignment_3/tests -v
```

## 目录

```
assignment_3/
├── queens_core.py        # 状态检查、冲突统计、回溯生成全部解、移动路径
├── queens_agent.py       # LangGraph 共享状态与循环搜索节点
├── search_methods.py     # BFS / 迭代加深 DFS 搜索
├── search_graph.py       # 两种搜索方法的 LangGraph 编排和结果验证
├── visualize.py          # 搜索统计、移动路径、离线工作流图
├── main.py               # 命令行接口、输出 JSON / PNG / Mermaid
├── tests/test_queens.py  # 现有核心测试
├── tests/test_search_methods.py  # BFS / DFS 最优性与图集成测试
└── output/               # 程序自动创建（不包含在压缩包中）
```

## 算法和最优性

1. `init_node`: 回溯搜索全部合法八皇后布局，结果恰好 92 种（包括旋转/镜像版本）。
2. `search_node`: 每次 LangGraph 搜索迭代选择一种布局 `target`，计算
   `cost(initial,target) = sum(initial[col] != target[col] for col in range(8))`，更新最优值。
3. `route_decision`: 还有未比较的候选则回到 `search`，否则结束。
4. `main.py`: 对最终最优解中每一列的差异生成一次纵向移动，进行独立重放和合法性验证。

因为所有 92 种合法目标都被遍历，所以最小 cost 是**全局最优**。任意一列最终行号不同至少需要移动该列皇后一次，最终行号相同可以零次移动。按差异列各移动一次可达该布局，故 cost 不仅是下界，也可实际实现。

## 输出

自动写入 `assignment_3/output`（或 `--output-dir PATH`）：

- `result.json`：初始/目标状态、最少移动数、操作序列、92 个候选的代价等；
- `solution_path.png`：初态、每次移动后的棋盘、最终布局；
- `search_stats.png`：逐候选代价与最优代价改善过程；
- `workflow.png`：离线流程示意图，不依赖 Mermaid 网络；
- `workflow.mmd`：从**实际编译的 LangGraph**导出的 Mermaid 源代码。


## 三种算法（新增 BFS / DFS）

保留原有的 `enumerate`（回溯产生 92 个合法棋盘，再在 LangGraph 中比较移动代价），另增加：

- **BFS 广度优先搜索**：每个搜索状态是允许移动的皇后列集合（8 位 bitmask），逐层添加一列；找到第一个能对应某个合法目标布局的集合时结束。队列以 `collections.deque` 实现。
- **DFS 深度优先搜索**：采用**迭代加深 DFS（IDDFS）**，深度上限从 0 到 8 逐次增加，每次用栈进行深度优先遍历；不同于普通 DFS，仍然保证全局最少移动数。

每个集合的未移动列必须保留初始行号；移动列则可以调整到合法目标的行。因为一个最终布局完全取决于变更的列集合，最小可行集合的元素数量即最小移动次数。枚举列集合使用列号递增的规范顺序来避免重复排列。同一列改变到任意行计为一次移动，中间允许冲突。这是**移动列集合的 BFS / DFS**，不是对所有 `8^8` 个中间棋盘逐一展开。

三种方法都接入 LangGraph：原方法保留 `init → search(循环) → END`，新方法使用 `init → search(BFS/DFS) → verify → END`。新方法内部的队列/栈执行搜索，LangGraph 编排初始化、搜索和独立结果验证。

```bash
python run_coursework.py queens --algorithm enumerate
python run_coursework.py queens --algorithm bfs
python run_coursework.py queens --algorithm dfs
python run_coursework.py queens --algorithm compare
python -m unittest discover -s assignment_3/tests -v
```

`compare` 将三种算法的最少移动数与搜索节点数写入 `assignment_3/output/comparison.json`。此处 `enumerate` 的 92 是合法目标布局检查数，而 BFS / DFS 的 `explored` 是列集合搜索状态检查数，**统计口径不同，不应直接作为同质的性能比较**；如需比较耗时，可单独重复计时并注明运行环境。

课堂照片识别的默认初态（行从上到下、列从左到右，均为 1-based）为 `[1,3,5,7,2,4,6,8]`，三种方法最小移动次数均为 **3**。第 7 列原图相对模糊，初态按先前约定暂定。

## 注意

- 由于搜索节点总共循环 92 次，显式设置 `recursion_limit=256`，兼容 LangGraph 早期版本较低的默认限制。
- 本项目没有调用 `openai`，无需模型权重、API Key 或 GPU。
- `LangGraph` 是流程编排器；准确的最优性来自完整枚举 92 个可行解，而非大模型自主推理。
- 如果作业要求“中间状态也必须所有皇后互不攻击”，那会是另一个问题，需要修改移动规则（普通初始状态可能根本不满足约束）。
