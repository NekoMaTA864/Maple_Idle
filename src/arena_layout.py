"""Shared coordinate convention for the vertical battle presentation.

The layout is intentionally small and deterministic.  It describes where the
presentation places actors; it does not own combat state or gameplay rules.
"""

from dataclasses import dataclass


Point = tuple[float, float]


@dataclass(frozen=True)
class ArenaLayout:
    """Coordinates for a top-enemy / bottom-player battle canvas."""

    width: float
    height: float

    @property
    def enemy_y(self) -> float:
        return max(54.0, self.height * 0.26)

    @property
    def player_y(self) -> float:
        return min(max(self.enemy_y + 92.0, self.height * 0.62), max(0.0, self.height - 118.0))

    @property
    def skill_bar_y(self) -> float:
        return min(max(self.player_y + 58.0, self.height * 0.81), max(0.0, self.height - 28.0))

    def enemy_positions(self, total: int) -> tuple[Point, ...]:
        total = max(1, min(5, int(total)))
        ratio_map = {
            1: (0.50,),
            2: (0.38, 0.62),
            3: (0.26, 0.50, 0.74),
            4: (0.18, 0.39, 0.61, 0.82),
            5: (0.14, 0.32, 0.50, 0.68, 0.86),
        }
        return tuple((self.width * ratio, self.enemy_y) for ratio in ratio_map[total])

    def enemy_position(self, index: int = 0, total: int = 1) -> Point:
        positions = self.enemy_positions(total)
        return positions[max(0, min(int(index), len(positions) - 1))]

    def enemy_anchors(self, index: int = 0, total: int = 1) -> dict[str, Point]:
        x, y = self.enemy_position(index, total)
        return {
            "center": (x, y),
            "hit": (x, y + 2.0),
            "ground": (x, y + 34.0),
        }

    def enemy_anchor(self, name: str = "center", index: int = 0, total: int = 1) -> Point:
        anchors = self.enemy_anchors(index, total)
        if name not in anchors:
            raise KeyError(f"Unknown enemy anchor: {name}")
        return anchors[name]

    def player_position(self) -> Point:
        return (self.width * 0.50, self.player_y)

    def companion_position(self) -> Point:
        """Reserve a nearby staging point without creating a permanent actor."""
        return (self.width * 0.66, self.player_y - 26.0)

    def skill_positions(self, count: int = 4) -> tuple[Point, ...]:
        count = max(1, int(count))
        spacing = min(76.0, max(52.0, self.width * 0.14))
        center = self.width * 0.50
        start = center - spacing * (count - 1) / 2.0
        return tuple((start + spacing * index, self.skill_bar_y) for index in range(count))
