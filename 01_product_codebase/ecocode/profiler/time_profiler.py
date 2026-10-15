"""
time_profiler.py — High-precision execution time measurement.

Uses time.perf_counter_ns() for monotonic nanosecond-resolution timing.
Supports multiple runs with warmup to reduce measurement noise.
"""

import time
import sys
import os
import subprocess
import json
import base64
import tempfile
import textwrap
from typing import List, Dict, Any, Optional

from ecocode.utils.logger import get_logger
from ecocode.utils.config_loader import get_config_value
from ecocode.utils.file_utils import strip_blocking_top_level_code

logger = get_logger(__name__)


def measure_execution_time(code: str,
                           num_runs: int = None,
                           warmup_runs: int = None,
                           function_name: Optional[str] = None,
                           test_cases: Optional[List[Dict[str, Any]]] = None) -> List[float]:
    """
    Measure the execution time of a code string across multiple runs.

    Each run executes the code in a subprocess to get clean timing.
    The measurement script uses time.perf_counter_ns() for the highest
    available resolution on the OS monotonic clock.

    Args:
        code: Python source code to profile.
        num_runs: Number of timed runs. Defaults to config value.
        warmup_runs: Number of warmup runs (results discarded).
        function_name: Optional function name to execute during profiling.
        test_cases: Optional test case inputs to pass during execution.

    Returns:
        List of execution times in milliseconds, one per run.
    """
    # Strip top-level executable code to prevent timeouts/blocking during timing
    code = strip_blocking_top_level_code(code)
    if num_runs is None:
        num_runs = get_config_value("testing", "num_runs", 3)
    if warmup_runs is None:
        warmup_runs = get_config_value("profiler", "warmup_runs", 1)

    total_runs = warmup_runs + num_runs

    # Encode test cases as base64 if provided
    test_cases_b64 = ""
    if test_cases:
        test_cases_b64 = base64.b64encode(json.dumps(test_cases).encode("utf-8")).decode("ascii")

    func_name_repr = json.dumps(function_name) if function_name else "None"

    timing_script = textwrap.dedent(f'''\
import time
import json
import base64

# ===== Code Under Test =====
{code}

# ===== Workload Execution Setup =====
_tc_b64 = "{test_cases_b64}"
_func_name = {func_name_repr}

_test_cases = json.loads(base64.b64decode(_tc_b64).decode("utf-8")) if _tc_b64 else []

def _run_workload():
    fn = None
    if _func_name and _func_name in globals() and callable(globals()[_func_name]):
        fn = globals()[_func_name]
    else:
        for _k, _v in list(globals().items()):
            if callable(_v) and not _k.startswith('_') and _k not in ('json', 'base64', 'time', 'tracemalloc', 'inspect', 'sys', 'textwrap'):
                fn = _v
                break

    if fn:
        if _test_cases:
            for tc in _test_cases:
                inp = tc["input"]
                try:
                    if isinstance(inp, dict):
                        fn(**inp)
                    elif isinstance(inp, list):
                        fn(*inp)
                    else:
                        fn(inp)
                except Exception:
                    try:
                        import inspect
                        sig = inspect.signature(fn)
                        dummy_args = []
                        for p in sig.parameters.values():
                            if p.default != inspect.Parameter.empty:
                                continue
                            p_name = p.name.lower()
                            if any(x in p_name for x in ("list", "arr", "nums", "data", "lst")):
                                dummy_args.append([1, 2, 3])
                            elif any(x in p_name for x in ("dict", "map")):
                                dummy_args.append({{"a": 1}})
                            elif any(x in p_name for x in ("str", "text", "s", "name")):
                                dummy_args.append("test")
                            else:
                                dummy_args.append(5)
                        fn(*dummy_args)
                    except Exception:
                        pass
        else:
            try:
                fn()
            except Exception:
                try:
                    import inspect
                    sig = inspect.signature(fn)
                    dummy_args = [5] * len([p for p in sig.parameters.values() if p.default == inspect.Parameter.empty])
                    fn(*dummy_args)
                except Exception:
                    pass
    elif 'main' in globals() and callable(globals()['main']):
        try:
            globals()['main']()
        except Exception:
            pass

# ===== Timing Harness =====
results = []
for i in range({total_runs}):
    start = time.perf_counter_ns()

    _run_workload()

    end = time.perf_counter_ns()
    elapsed_ms = (end - start) / 1_000_000.0
    results.append(elapsed_ms)

# Discard warmup runs
actual_results = results[{warmup_runs}:]
print(json.dumps(actual_results))
''')

    # Execute in subprocess
    fd, temp_path = tempfile.mkstemp(prefix="ecocode_time_", suffix=".py", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(timing_script)

        timeout = get_config_value("testing", "timeout_seconds", 10) * total_runs
        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tempfile.gettempdir(),
        )

        if result.returncode != 0:
            logger.error(f"Time profiler error: {result.stderr[:300]}")
            return [0.0] * num_runs

        timings = json.loads(result.stdout.strip().split('\n')[-1])
        logger.debug(f"Time measurements (ms): {[f'{t:.3f}' for t in timings]}")
        return timings

    except subprocess.TimeoutExpired:
        logger.error("Time profiler timed out")
        return [0.0] * num_runs

    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Time profiler parse error: {e}")
        return [0.0] * num_runs

    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass
