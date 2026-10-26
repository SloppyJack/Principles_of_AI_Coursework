# 遗传算法小组作业

统一问题：100位二进制OneMax，最大化1的个数，理论最优为100。
已运行DEAP官方原始示例，以及10种受控配置×30个配对种子，共300次扩展实验。

## 阅读与提交

- `REPORT.md`：完整中文实验报告，包含原始代码运行、参数、八种算子、统计表、图表和分析。
- `ga.py`：统一扩展实现，包含3种选择、3种交叉、2种变异。
- `run_experiments.py`：先运行未改动的官方代码，再运行全部单因素对照。
- `plot.py`：只根据已保存数据重新生成统计和图表，不重新执行GA。
- `test_ga.py`：算子不变量、种子复现、精英保留及预算检查。
- `vendor/`：原版源码、原许可证和固定提交/SHA256；本次自写代码与原版明确分开。
- `results/`：原始输出、300次结果、每次101代的历史、初始种群、统计与图表。
- `results/verification.json`：预算、初始种群、最优串、源文件哈希及完整重跑一致性核对结果。


## 使用 uv 复现

在本目录执行，Python 3.12及以上：

```bash
uv sync --locked
uv run python -m unittest discover -s . -p 'test_*.py' -v

# 不覆盖已有结果。完整复现使用同一组种子，产生新的结果目录。
uv run python run_experiments.py --output results_reproduced
# 重新生成统计图表
uv run python plot.py results_reproduced
```

本次运行环境与依赖版本保存在 `results/manifest.json`，依赖解析保存在 `uv.lock`。
归档中保留本次原始实验结果；复现的耗时受环境影响，不要求逐位相同。
同一NumPy版本下，固定种子的适应度、逐代历史及最优串应能复现。

## 单次自定义实验

```bash
uv run python - <<'PY'
from ga import Config, run

# 修改某一项，其余保持基准；有效算子名称参见ga.py。
result = run(Config(pc=0.5, crossover="uniform"), seed=20261023)
print(result["final_best"], result["first_hit"], result["evaluations"])
PY
```

`Pc`是每对父母触发交叉的概率。基本变异为每位独立概率`1/length`；
自适应为`Pm=(1+2*(1-D))/length`，其中`D=mean(4*p*(1-p))`。
不在扩展实现中另设个体变异概率，避免与原版`mutpb`混淆。
所有配置固定运行100代，即使已找到100也继续，采用相同的8080次评价预算。

## 数据字段与统计约定

- `runs.csv`：每次运行的配置、种子、终值、成功标记、首次最优代、评价次数、耗时与最优串。
- `runs.jsonl`：每行一次完整实验，另含全部逐代best/mean/diversity/pm。
- `initial_seed_*.json`：每种子完整初始种群；各配置的SHA256相同，便于公平性核查。
- `summary.csv/json`：均值、样本标准差、成功率、惩罚到达代数及同种子配对bootstrap区间。
- `original_stdout.txt` / `original_result.json`：未修改的DEAP示例实际输出。

失败的`first_hit`为空（JSON为null），`penalized_hit`取101；成功取首次达到100的代数。
成功代数均值仅包含成功运行，不能独自代表所有运行。
bootstrap以种子为配对单位，10000次重采样、统计种子314159；区间未经多重比较校正。
耗时只作运行记录，不比较NumPy不同实现的理论复杂度。

## 原始源码与许可

源代码：https://github.com/DEAP/deap/blob/8a96fd3a75026f7b30e835f595a5199c75634ddf/examples/ga/onemax_short.py

官方说明：https://deap.readthedocs.io/en/stable/examples/ga_onemax_short.html

`vendor/onemax_short.py`保留原许可证声明；`vendor/DEAP_LICENSE.txt`随源代码提交。
下载内容及SHA256见`vendor/SOURCE.json`，可核查原版源码的完整性。
