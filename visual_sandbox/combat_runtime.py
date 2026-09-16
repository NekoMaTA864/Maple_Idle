"""Small, generic runtime state primitives for the visual combat sandbox."""

from __future__ import annotations

from dataclasses import dataclass, field


Number = int | float


@dataclass
class CombatRuntimeState:
    """Per-prototype resource values and expiring presentation states.

    This is intentionally a data holder, not a combat engine: it has no
    skill, damage, class, or event semantics.
    """

    resources: dict[str, Number] = field(default_factory=dict)
    resource_limits: dict[str, tuple[Number | None, Number | None]] = field(default_factory=dict)
    timed_states: dict[str, float] = field(default_factory=dict)

    def configure_resource(
        self,
        key: str,
        value: Number = 0,
        minimum: Number | None = None,
        maximum: Number | None = None,
    ) -> Number:
        """Create/update a resource and remember its optional clamp bounds."""
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError("resource minimum cannot exceed maximum")
        self.resource_limits[key] = (minimum, maximum)
        return self.set(key, value)

    def get(self, key: str, default: Number = 0) -> Number:
        return self.resources.get(key, default)

    def set(
        self,
        key: str,
        value: Number,
        minimum: Number | None = None,
        maximum: Number | None = None,
    ) -> Number:
        if minimum is not None or maximum is not None:
            old_minimum, old_maximum = self.resource_limits.get(key, (None, None))
            minimum = old_minimum if minimum is None else minimum
            maximum = old_maximum if maximum is None else maximum
            if minimum is not None and maximum is not None and minimum > maximum:
                raise ValueError("resource minimum cannot exceed maximum")
            self.resource_limits[key] = (minimum, maximum)
        minimum, maximum = self.resource_limits.get(key, (None, None))
        clamped = value
        if minimum is not None:
            clamped = max(minimum, clamped)
        if maximum is not None:
            clamped = min(maximum, clamped)
        self.resources[key] = clamped
        return clamped

    def add(self, key: str, amount: Number) -> Number:
        return self.set(key, self.get(key) + amount)

    # Explicit aliases keep call sites readable without adding another model.
    get_resource = get
    set_resource = set
    add_resource = add

    def activate(self, key: str, duration: float) -> None:
        remaining = max(0.0, float(duration))
        if remaining == 0.0:
            self.timed_states.pop(key, None)
        else:
            self.timed_states[key] = remaining

    def is_active(self, key: str) -> bool:
        return self.timed_states.get(key, 0.0) > 0.0

    def remaining(self, key: str) -> float:
        return max(0.0, self.timed_states.get(key, 0.0))

    def tick(self, dt: float) -> None:
        """Advance expiring states and remove entries that reach zero."""
        step = max(0.0, float(dt))
        for key, value in tuple(self.timed_states.items()):
            next_value = value - step
            if next_value <= 0.0:
                self.timed_states.pop(key, None)
            else:
                self.timed_states[key] = next_value
