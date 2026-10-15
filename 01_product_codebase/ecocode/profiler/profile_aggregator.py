"""
profile_aggregator.py — Combines all profiler results into a unified report.

Orchestrates the time, memory, and energy profilers, runs them
against a code candidate, and produces a single ProfileResult object.
"""

from typing import Optional, List, Dict, Any

from ecocode.profiler.time_profiler import measure_execution_time
from ecocode.profiler.memory_profiler import measure_peak_memory
from ecocode.profiler.energy_profiler import measure_energy
from ecocode.models.profile_result import ProfileResult
from ecocode.utils.logger import get_logger
from ecocode.utils.config_loader import get_config_value

logger = get_logger(__name__)


def profile_code(code: str,
                 num_runs: int = None,
                 function_name: Optional[str] = None,
                 test_cases: Optional[List[Dict[str, Any]]] = None) -> ProfileResult:
    """
    Run all profilers against a code string and aggregate results.

    Pipeline:
    1. Time profiler → list of execution times (ms)
    2. Memory profiler → list of peak memory values (KB)
    3. Energy profiler → list of energy values (J) based on time
    4. Average all measurements and package into ProfileResult

    Args:
        code: Python source code to profile.
        num_runs: Number of profiling runs (overrides config).
        function_name: Optional function name to execute during profiling.
        test_cases: Optional test case inputs to pass during execution.

    Returns:
        ProfileResult: Aggregated metrics with raw readings.
    """
    if num_runs is None:
        num_runs = get_config_value("testing", "num_runs", 3)

    logger.info(f"Starting profiling ({num_runs} runs)...")

    # --- Step 1: Measure execution time ---
    logger.info("  [TIME] Measuring execution time...")
    time_readings = measure_execution_time(
        code, num_runs=num_runs, function_name=function_name, test_cases=test_cases
    )

    # --- Step 2: Measure peak memory ---
    logger.info("  [MEM] Measuring peak memory usage...")
    memory_readings = measure_peak_memory(
        code, num_runs=num_runs, function_name=function_name, test_cases=test_cases
    )

    # --- Step 3: Measure / estimate energy ---
    logger.info("  [ENERGY] Measuring energy consumption...")
    energy_readings, energy_method = measure_energy(time_readings)

    # --- Step 4: Aggregate ---
    avg_time = sum(time_readings) / len(time_readings) if time_readings else 0.0
    avg_memory = sum(memory_readings) / len(memory_readings) if memory_readings else 0.0
    avg_energy = sum(energy_readings) / len(energy_readings) if energy_readings else 0.0

    # Build raw readings for transparency
    raw_readings = []
    for i in range(min(len(time_readings), len(memory_readings), len(energy_readings))):
        raw_readings.append({
            "run": i + 1,
            "time_ms": round(time_readings[i], 3),
            "memory_kb": round(memory_readings[i], 2),
            "energy_j": round(energy_readings[i], 6),
        })

    result = ProfileResult(
        execution_time_ms=avg_time,
        peak_memory_kb=avg_memory,
        energy_joules=avg_energy,
        num_runs=num_runs,
        raw_readings=raw_readings,
        energy_method=energy_method,
    )

    logger.info(f"  [RESULT] Profile complete: {result}")
    return result
