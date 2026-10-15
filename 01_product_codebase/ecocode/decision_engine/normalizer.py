"""
normalizer.py — Min-max normalization for multi-metric comparison.

Scales raw profiler values (time, memory, energy) into the [0, 1] range
using min-max normalization to prevent unit conflicts in TOPSIS scoring.

Formula: x_norm = (x - x_min) / (x_max - x_min)
If all values are identical, all normalized values become 0.0.
"""

from typing import List, Dict

from ecocode.utils.logger import get_logger

logger = get_logger(__name__)


def normalize_min_max(values: List[float]) -> List[float]:
    """
    Apply min-max normalization to a list of values.

    Maps all values to the [0, 1] range where:
    - 0.0 = the minimum (best) value
    - 1.0 = the maximum (worst) value

    If all values are identical, all normalized values are 0.0
    (no differentiation possible).

    Args:
        values: List of raw metric values.

    Returns:
        List of normalized values in [0, 1].
    """
    if not values:
        return []

    v_min = min(values)
    v_max = max(values)
    spread = v_max - v_min

    if spread == 0:
        # All values identical — no differentiation possible
        return [0.0] * len(values)

    normalized = [(v - v_min) / spread for v in values]
    return normalized


def normalize_candidates(candidates: list) -> List[Dict[str, float]]:
    """
    Normalize the profiling metrics across all candidates.

    Extracts time, memory, and energy from each candidate's ProfileResult,
    normalizes each metric independently, and returns a list of
    normalized metric dicts aligned with the candidate order.

    Args:
        candidates: List of CodeCandidate objects with profile data.

    Returns:
        List of dicts: [{'time': norm_t, 'memory': norm_m, 'energy': norm_e}, ...]
    """
    # Extract raw values
    times = []
    memories = []
    energies = []

    for c in candidates:
        if c.profile is None:
            logger.warning(f"Candidate {c.id} has no profile data, using zeros")
            times.append(0.0)
            memories.append(0.0)
            energies.append(0.0)
        else:
            times.append(c.profile.execution_time_ms)
            memories.append(c.profile.peak_memory_kb)
            energies.append(c.profile.energy_joules)

    # Normalize each metric independently
    norm_times = normalize_min_max(times)
    norm_memories = normalize_min_max(memories)
    norm_energies = normalize_min_max(energies)

    # Package results
    normalized = []
    for i in range(len(candidates)):
        normalized.append({
            "time": norm_times[i],
            "memory": norm_memories[i],
            "energy": norm_energies[i],
        })

    logger.debug(
        f"Normalized metrics for {len(candidates)} candidates: "
        f"T={[f'{n['time']:.3f}' for n in normalized]}, "
        f"M={[f'{n['memory']:.3f}' for n in normalized]}, "
        f"E={[f'{n['energy']:.3f}' for n in normalized]}"
    )

    return normalized
