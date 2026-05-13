from pathlib import Path

from hysail.logger.logger import execution_logger
from hysail.utils import decorators
from hysail.utils.decorators import _graph_file_name, timeit
from hysail.utils.debug import set_debugging


def test_timeit_creates_graph_in_execution_log_directory_when_debug_enabled(tmp_path):
    original_log_file = execution_logger.log_file
    execution_logger.log_file = str(tmp_path / "execution.log")
    set_debugging(True)

    try:

        @timeit(runs=3)
        def decorated_sum():
            return sum(range(10))

        result = decorated_sum()

        graph_path = Path(tmp_path) / _graph_file_name(decorated_sum)

        assert result == 45
        assert graph_path.exists()
        assert graph_path.stat().st_size > 0
    finally:
        set_debugging(False)
        execution_logger.log_file = original_log_file


def test_timeit_does_not_create_graph_when_debug_disabled(tmp_path):
    original_log_file = execution_logger.log_file
    execution_logger.log_file = str(tmp_path / "execution.log")
    set_debugging(False)

    try:

        @timeit(runs=3)
        def decorated_sum():
            return sum(range(10))

        result = decorated_sum()

        graph_path = Path(tmp_path) / _graph_file_name(decorated_sum)

        assert result == 45
        assert not graph_path.exists()
    finally:
        execution_logger.log_file = original_log_file


def test_timeit_accumulates_average_per_function_call_when_debug_enabled(monkeypatch):
    captured_average_times = []
    perf_counter_values = iter([0.0, 1.0, 2.0, 3.0, 10.0, 12.0, 20.0, 22.0])

    def fake_perf_counter():
        return next(perf_counter_values)

    def fake_save_timeit_graph(func, average_times):
        captured_average_times.append((func.__name__, list(average_times)))

    monkeypatch.setattr(decorators.time, "perf_counter", fake_perf_counter)
    monkeypatch.setattr(decorators, "_save_timeit_graph", fake_save_timeit_graph)
    monkeypatch.setattr(decorators, "is_debugging", lambda: True)

    @timeit(runs=2)
    def decorated_sum():
        return sum(range(5))

    assert decorated_sum() == 10
    assert decorated_sum() == 10
    assert captured_average_times == [
        (
            "decorated_sum",
            [
                1.0,
            ],
        ),
        ("decorated_sum", [1.0, 2.0]),
    ]


def test_timeit_does_not_save_graph_when_debug_disabled(monkeypatch):
    save_graph_calls = []
    call_count = 0

    def decorated_sum():
        nonlocal call_count
        call_count += 1
        return sum(range(5))

    def fake_save_timeit_graph(func, average_times):
        save_graph_calls.append((func.__name__, list(average_times)))

    monkeypatch.setattr(decorators, "is_debugging", lambda: False)
    monkeypatch.setattr(decorators, "_save_timeit_graph", fake_save_timeit_graph)

    decorated_sum = timeit(runs=2)(decorated_sum)

    assert decorated_sum() == 10
    assert call_count == 1
    assert save_graph_calls == []
