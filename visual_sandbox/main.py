"""Launch entry point for the standalone Combat Visual Sandbox."""

import sys

from PySide6.QtWidgets import QApplication

try:
    from .sandbox import CombatVisualSandbox
except ImportError:  # Direct ``py visual_sandbox/main.py`` execution.
    from sandbox import CombatVisualSandbox


def main() -> int:
    app = QApplication(sys.argv)
    window = CombatVisualSandbox()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
