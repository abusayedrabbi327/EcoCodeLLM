"""
profile_result.py — Data class for profiling metrics of a single code execution.

Stores execution time, peak memory, energy consumption, and raw readings
from multiple profiling runs.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ProfileResult:
    """
    Holds the aggregated profiling metrics for a single code candidate.

    Attributes:
        execution_time_ms: Average execution time across all runs (milliseconds).
        peak_memory_kb: Peak Resident Set Size during execution (kilobytes).
        energy_joules: Total energy consumed — measured via RAPL or estimated (Joules).
        num_runs: Number of profiling runs that were averaged.
        raw_readings: List of per-run measurement dictionaries for transparency.
        energy_method: How energy was measured ('rapl' or 'estimation').
    """
    execution_time_ms: float = 0.0
    peak_memory_kb: float = 0.0
    energy_joules: float = 0.0
    num_runs: int = 0
    raw_readings: List[Dict[str, float]] = field(default_factory=list)
    energy_method: str = "estimation"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dictionary for JSON export."""
        return {
            "execution_time_ms": round(self.execution_time_ms, 3),
            "peak_memory_kb": round(self.peak_memory_kb, 2),
            "energy_joules": round(self.energy_joules, 6),
            "num_runs": self.num_runs,
            "energy_method": self.energy_method,
            "raw_readings": self.raw_readings,
        }

    def __repr__(self) -> str:
        return (
            f"ProfileResult(time={self.execution_time_ms:.1f}ms, "
            f"memory={self.peak_memory_kb:.0f}KB, "
            f"energy={self.energy_joules:.4f}J, "
            f"runs={self.num_runs})"
        )
