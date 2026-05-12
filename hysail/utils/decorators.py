import os
import time
import functools

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from hysail.logger.logger import execution_logger


def _graph_file_name(func):
    qualified_name = f"{func.__module__}.{func.__qualname__}"
    sanitized_name = qualified_name.replace("<", "").replace(">", "")
    return sanitized_name.replace(".", "_") + "_timeit.png"


def _save_timeit_graph(func, average_times):
    calls = list(range(1, len(average_times) + 1))
    output_dir = execution_logger.get_log_directory()
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, _graph_file_name(func))

    figure, axis = plt.subplots()
    axis.plot(calls, average_times, marker="o", linewidth=2)
    axis.set_title(f"{func.__module__}.{func.__qualname__} average execution time")
    axis.set_xlabel("call")
    axis.set_ylabel("average time (s)")
    axis.grid(True, linestyle="--", alpha=0.4)
    figure.tight_layout()
    figure.savefig(output_file)
    plt.close(figure)


def timeit(runs=1, detailed=False):
    def decorator(func):
        average_times = []

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            times = []
            for _ in range(runs):
                start = time.perf_counter()
                result = func(*args, **kwargs)
                times.append(time.perf_counter() - start)

            avg = sum(times) / runs
            average_times.append(avg)
            _save_timeit_graph(func, average_times)
            if detailed:
                for run_index, elapsed in enumerate(times, start=1):
                    execution_logger.debug(
                        f"[{func.__name__}] Run {run_index}: {elapsed:.6f}s"
                    )
            execution_logger.debug(
                f"[{func.__name__}] Call {len(average_times)} Avg: {avg:.6f}s ({runs} runs)"
            )
            return result

        return wrapper

    return decorator
