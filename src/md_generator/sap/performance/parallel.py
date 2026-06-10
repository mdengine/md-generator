from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Callable, TypeVar

T = TypeVar("T")
R = TypeVar("R")


def map_parallel(
    items: list[T],
    fn: Callable[[T], R],
    *,
    workers: int = 4,
    use_processes: bool = False,
) -> list[R]:
    if workers <= 1 or len(items) <= 1:
        return [fn(item) for item in items]
    executor_cls = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
    with executor_cls(max_workers=workers) as pool:
        return list(pool.map(fn, items))
