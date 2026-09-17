"""Launch the shared vertical VFX Debug Gallery."""

import os
import sys


SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


from tools.vfx_gallery import main


if __name__ == "__main__":
    raise SystemExit(main())
