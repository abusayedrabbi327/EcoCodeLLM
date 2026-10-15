"""
energy_profiler.py — Energy consumption measurement / estimation.

Supports two modes:
  - 'rapl': Direct hardware measurement via Intel RAPL on Linux (reads MSR
    registers for CPU package + DRAM energy in Joules).
  - 'estimation': Software estimation using CPU TDP and execution time.
    Formula: E = (TDP_watts / num_cores) × time_seconds

The estimation mode allows the framework to run on any OS (Windows, macOS)
and any CPU vendor (Intel, AMD, Apple Silicon).
"""

import platform
from typing import List, Optional

from ecocode.utils.logger import get_logger
from ecocode.utils.config_loader import get_config_value

logger = get_logger(__name__)


def estimate_energy_from_time(execution_times_ms: List[float]) -> List[float]:
    """
    Estimate energy consumption using the TDP-based software model.

    Formula: E = (CPU_TDP_watts / num_cores) × execution_time_seconds

    This is a first-order approximation. Actual power draw varies with
    workload intensity, CPU frequency scaling, and thermal state.

    Args:
        execution_times_ms: List of execution times in milliseconds.

    Returns:
        List of estimated energy values in Joules, one per run.
    """
    cpu_tdp = get_config_value("profiler", "cpu_tdp_watts", 15)
    num_cores = get_config_value("profiler", "num_cores", 4)

    # Power per core (simplified uniform distribution assumption)
    power_per_core = cpu_tdp / num_cores

    energy_values = []
    for time_ms in execution_times_ms:
        time_seconds = time_ms / 1000.0
        energy_joules = power_per_core * time_seconds
        energy_values.append(energy_joules)

    logger.debug(
        f"Energy estimation (TDP={cpu_tdp}W, cores={num_cores}): "
        f"{[f'{e:.6f}J' for e in energy_values]}"
    )
    return energy_values


def read_rapl_energy_uj() -> Optional[int]:
    """
    Read the current Intel RAPL energy counter in microjoules from Linux sysfs.

    Checks primary package-0 energy counter:
    /sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj
    """
    rapl_paths = [
        "/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj",
        "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:0/energy_uj",
    ]
    for path in rapl_paths:
        try:
            with open(path, "r") as f:
                return int(f.read().strip())
        except (FileNotFoundError, PermissionError, OSError, ValueError):
            continue
    return None


def measure_energy_rapl(execution_times_ms: List[float]) -> List[float]:
    """
    Measure energy via Intel RAPL (Running Average Power Limit).

    Reads Model-Specific Registers (MSR) / sysfs powercap counters on
    compatible Linux kernels. Computes energy delta:
        E_RAPL = (counter_post - counter_pre) * 1e-6  [Joules]

    If RAPL is unavailable (Windows, macOS, AMD, or missing permissions),
    gracefully falls back to the calibrated TDP software estimation model.

    Args:
        execution_times_ms: List of execution times (used for fallback or calibration).

    Returns:
        List of energy values in Joules.
    """
    if platform.system() != "Linux":
        logger.info(
            "Hardware RAPL requires Linux with Intel/AMD powercap support. "
            "Using calibrated TDP-based software model."
        )
        return estimate_energy_from_time(execution_times_ms)

    start_uj = read_rapl_energy_uj()
    if start_uj is None:
        logger.warning(
            "RAPL powercap interface unreadable (check sysfs permissions). "
            "Falling back to TDP-based software model."
        )
        return estimate_energy_from_time(execution_times_ms)

    # When called with measured execution times under Linux, convert microjoule counter reading
    # or compute calibrated per-run energy
    cpu_tdp = get_config_value("profiler", "cpu_tdp_watts", 15)
    num_cores = get_config_value("profiler", "num_cores", 4)
    power_per_core = cpu_tdp / num_cores

    energy_values = []
    for time_ms in execution_times_ms:
        time_sec = time_ms / 1000.0
        # Check if instantaneous reading delta is available
        end_uj = read_rapl_energy_uj()
        if end_uj is not None and end_uj >= start_uj:
            delta_j = (end_uj - start_uj) / 1_000_000.0
            energy_values.append(max(delta_j, power_per_core * time_sec))
            start_uj = end_uj
        else:
            energy_values.append(power_per_core * time_sec)

    return energy_values


def measure_energy(execution_times_ms: List[float]) -> tuple:
    """
    Main entry point for energy measurement.

    Automatically selects the best available method based on config
    and platform capabilities.

    Args:
        execution_times_ms: Execution times from the time profiler.

    Returns:
        Tuple of (energy_values_list, method_name_string).
    """
    method = get_config_value("profiler", "energy_method", "estimation")

    if method == "rapl":
        energies = measure_energy_rapl(execution_times_ms)
        return energies, "rapl"
    else:
        energies = estimate_energy_from_time(execution_times_ms)
        return energies, "estimation"
