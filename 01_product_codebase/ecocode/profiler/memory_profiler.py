"""
memory_profiler.py — Peak RAM (RSS) measurement during code execution.

Uses tracemalloc (built-in) to track Python memory allocations within
a subprocess, capturing the peak memory footprint.
"""

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


def measure_peak_memory(code: str,
                        num_runs: int = None,
                        function_name: Optional[str] = None,
                        test_cases: Optional[List[Dict[str, Any]]] = None) -> List[float]:
    """
    Measure peak memory usage of a code string across multiple runs.

    Uses tracemalloc to hook into CPython's memory allocator and capture
    the high-water mark of allocated memory during execution.

    Args:
        code: Python source code to profile.
        num_runs: Number of measurement runs. Defaults to config value.
        function_name: Optional function name to execute during profiling.
        test_cases: Optional test case inputs to pass during execution.

    Returns:
        List of peak memory values in kilobytes, one per run.
    """
    # Strip top-level executable code to prevent timeouts/blocking during memory profiling
    code = strip_blocking_top_level_code(code)

    if num_runs is None:
        num_runs = get_config_value("testing", "num_runs", 3)

    # Encode test cases as base64 if provided
    test_cases_b64 = ""
    if test_cases:
        test_cases_b64 = base64.b64encode(json.dumps(test_cases).encode("utf-8")).decode("ascii")

    func_name_repr = json.dumps(function_name) if function_name else "None"

    memory_script = textwrap.dedent(f'''\
import tracemalloc
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

results = []
for i in range({num_runs}):
    tracemalloc.start()

    _run_workload()

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_kb = peak / 1024.0  # bytes → kilobytes
    results.append(peak_kb)

print(json.dumps(results))
''')

    # Execute in subprocess
    fd, temp_path = tempfile.mkstemp(prefix="ecocode_mem_", suffix=".py", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(memory_script)

        timeout = get_config_value("testing", "timeout_seconds", 10) * num_runs
        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tempfile.gettempdir(),
        )

        if result.returncode != 0:
            logger.error(f"Memory profiler error: {result.stderr[:300]}")
            return [0.0] * num_runs

        memories = json.loads(result.stdout.strip().split('\n')[-1])
        logger.debug(f"Memory measurements (KB): {[f'{m:.1f}' for m in memories]}")
        return memories

    except subprocess.TimeoutExpired:
        logger.error("Memory profiler timed out")
        return [0.0] * num_runs

    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Memory profiler parse error: {e}")
        return [0.0] * num_runs

    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass
