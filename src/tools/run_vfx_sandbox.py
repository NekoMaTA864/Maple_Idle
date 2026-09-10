"""
新楓之谷：單職業純淨技能特效沙盒 (tools/vfx_sandbox.py)
"""
import os
import sys

# 確保上一層根目錄在 sys.path 中
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from vfx_sandbox import SingleClassVFXSandbox, main

if __name__ == "__main__":
    main()
