# 一键启动脚本，等价于 python -m src.main
import sys
import runpy

if __name__ == "__main__":
    runpy.run_module("src.main", run_name="__main__")
