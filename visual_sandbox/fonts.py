"""Small shared Qt font selection for the sandbox and deterministic captures."""

from __future__ import annotations

from functools import lru_cache

from PySide6.QtGui import QFont, QFontDatabase, QFontInfo


FONT_CANDIDATES = (
    "Microsoft JhengHei UI",
    "Microsoft JhengHei",
    "Segoe UI",
    "Arial",
    "sans-serif",
)


@lru_cache(maxsize=1)
def resolved_ui_family() -> str:
    """Return the first installed UI family after QApplication exists."""
    families = {family.casefold(): family for family in QFontDatabase.families()}
    for candidate in FONT_CANDIDATES:
        family = families.get(candidate.casefold())
        if family is None:
            continue
        resolved = QFontInfo(QFont(family, 12)).family()
        if resolved:
            return resolved

    # A generic family lets Qt/fontconfig choose its platform default when a
    # minimal environment exposes no named families at all.
    return "sans-serif"


def ui_font(size: int | float, bold: bool = False) -> QFont:
    """Build a consistent UI font without hardcoding a family at call sites."""
    font = QFont(resolved_ui_family(), max(1, int(size)))
    font.setBold(bold)
    return font
