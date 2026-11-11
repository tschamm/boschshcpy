"""Callback registry helpers: several callbacks may share one key."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

CallbackMap = dict[Any, list[Callable[[], None]]]


def add_callback(
    registry: CallbackMap, entity: Any, callback: Callable[[], None]
) -> None:
    """Register ``callback`` under ``entity`` without replacing others."""
    callbacks = registry.setdefault(entity, [])
    if callback not in callbacks:
        callbacks.append(callback)


def remove_callback(
    registry: CallbackMap,
    entity: Any,
    callback: Callable[[], None] | None = None,
) -> None:
    """Remove one callback, or every callback of ``entity`` when none is given."""
    if callback is None:
        registry.pop(entity, None)
        return
    callbacks = registry.get(entity)
    if not callbacks:
        return
    if callback in callbacks:
        callbacks.remove(callback)
    if not callbacks:
        registry.pop(entity, None)


def iter_callbacks(registry: CallbackMap) -> list[Callable[[], None]]:
    """Return a snapshot of all registered callbacks."""
    return [fn for callbacks in list(registry.values()) for fn in list(callbacks)]
