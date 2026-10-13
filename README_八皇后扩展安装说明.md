# 八皇后 LangGraph 扩展：安装说明

原仓库：https://github.com/SloppyJack/Principles_of_AI_Coursework

这是一个**增量扩展包**。由于原仓库是否授权重新分发未知，该压缩包只包含我们新写的代码，不包含 GitHub 仓库的原始文件。

1. 克隆原仓库：`git clone https://github.com/SloppyJack/Principles_of_AI_Coursework.git`
2. 解压本包，把其中的 `assignment_3/` 文件夹和 `run_coursework.py` 拷贝到克隆的仓库根目录，和 `assignment_2/` 同级。
3. 在根目录运行 `python -m pip install -r requirements.txt`。
4. 运行新功能：`python run_coursework.py queens --initial "1,2,3,4,5,6,7,8"`。
5. 输出在 `assignment_3/output/`，详细用法见 `assignment_3/README.md`。
6. 运行测试：`python -m unittest discover -s assignment_3/tests -v`。

没有外部大模型的依赖，无需 OpenAI API Key。八皇后算法按“移动了几枚皇后”计数，每列最多移动一次，中间允许冲突。
