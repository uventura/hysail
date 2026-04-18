from __future__ import annotations

from rich.progress import Progress

_progress: Progress | None = None


def get_progress() -> Progress | None:
    return _progress


def set_progress(progress: Progress | None) -> None:
    global _progress
    _progress = progress
