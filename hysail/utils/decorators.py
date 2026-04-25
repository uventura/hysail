import os
import time
import functools

from hysail.logger.execution_logger import execution_logger

ENABLE_TIMING = os.getenv("DEBUG_TIME", "0").lower() in ("1", "true", "on")


def timeit(runs=1, detailed=False):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not ENABLE_TIMING:
                return func(*args, **kwargs)

            times = []
            for _ in range(runs):
                start = time.perf_counter()
                result = func(*args, **kwargs)
                times.append(time.perf_counter() - start)

            avg = sum(times) / runs
            execution_logger.debug(f"[{func.__name__}] Avg: {avg:.6f}s ({runs} runs)")
            return result

        return wrapper

    return decorator
