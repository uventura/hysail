from __future__ import annotations

from rich.progress import Progress, TaskID

_progress: Progress | None = None


def get_progress() -> Progress | None:
    return _progress


def set_progress(progress: Progress | None) -> None:
    global _progress
    _progress = progress


def create_progress_task(
    progress: Progress | None,
    description: str,
    total: int,
) -> TaskID | None:
    if progress is None:
        return None

    return progress.add_task(description, total=total)


def advance_progress(progress: Progress | None, task_id: TaskID | None) -> None:
    if progress is None or task_id is None:
        return

    progress.advance(task_id)
