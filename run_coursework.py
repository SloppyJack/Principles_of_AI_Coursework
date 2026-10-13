"""Non-invasive selector: run the original 8-Puzzle or the new 8-Queens task."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description="AI Coursework task launcher")
    parser.add_argument("task", choices=["puzzle", "queens"],
                        help="puzzle=原八数码; queens=新八皇后")
    args, remaining = parser.parse_known_args()
    folder = ROOT / ("assignment_2" if args.task == "puzzle" else "assignment_3")
    script = folder / "main.py"
    if not script.is_file():
        parser.error(f"缺少 {script}，请先在原仓库根目录合并扩展文件")
    return subprocess.call([sys.executable, str(script), *remaining], cwd=str(folder))


if __name__ == "__main__":
    sys.exit(main())
