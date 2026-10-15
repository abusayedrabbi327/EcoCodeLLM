"""
evaluation_report.py — Data class for the final comparison output.

Captures the full evaluation context: all candidates, the winner,
improvement percentages, and metadata for the generated report.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from ecocode.models.code_candidate import CodeCandidate


@dataclass
class EvaluationReport:
    """
    The final output artifact produced by the EcoCode pipeline.

    Attributes:
        problem_description: The original prompt (Mode 1) or code description (Mode 2).
        mode: 'mode1_selection' or 'mode2_rewriting'.
        total_candidates: Total number of candidates generated or considered.
        valid_candidates: Number that passed functional tests.
        candidates: Full list of all CodeCandidate objects.
        winner: The selected optimal code candidate.
        improvement_pct: Percentage improvements {time, memory, energy}
                         comparing winner vs worst valid candidate.
        timestamp: ISO-format timestamp of when the evaluation was run.
    """
    problem_description: str = ""
    mode: str = "mode1_selection"
    total_candidates: int = 0
    valid_candidates: int = 0
    candidates: List[CodeCandidate] = field(default_factory=list)
    winner: Optional[CodeCandidate] = None
    improvement_pct: Dict[str, float] = field(default_factory=lambda: {
        "time": 0.0,
        "memory": 0.0,
        "energy": 0.0,
    })
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def compute_improvements(self):
        """
        Calculate improvement percentages by comparing the winner
        against the worst valid candidate in the pool.
        """
        valid = [c for c in self.candidates if c.is_valid and c.profile]
        if len(valid) < 2 or self.winner is None or self.winner.profile is None:
            return

        # Find worst candidate (highest TOPSIS score)
        worst = max(valid, key=lambda c: c.topsis_score if c.topsis_score is not None else 0)

        if worst.profile is None:
            return

        # Calculate percentage reduction (negative = improvement)
        def pct_change(best_val, worst_val):
            if worst_val == 0:
                return 0.0
            return ((best_val - worst_val) / worst_val) * 100.0

        self.improvement_pct = {
            "time": round(pct_change(
                self.winner.profile.execution_time_ms,
                worst.profile.execution_time_ms
            ), 1),
            "memory": round(pct_change(
                self.winner.profile.peak_memory_kb,
                worst.profile.peak_memory_kb
            ), 1),
            "energy": round(pct_change(
                self.winner.profile.energy_joules,
                worst.profile.energy_joules
            ), 1),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the full report to a dictionary for JSON export."""
        return {
            "problem_description": self.problem_description,
            "mode": self.mode,
            "total_candidates": self.total_candidates,
            "valid_candidates": self.valid_candidates,
            "candidates": [c.to_dict() for c in self.candidates],
            "winner": self.winner.to_dict() if self.winner else None,
            "improvement_pct": self.improvement_pct,
            "timestamp": self.timestamp,
        }

    def __repr__(self) -> str:
        winner_id = self.winner.id if self.winner else "None"
        return (
            f"EvaluationReport(mode='{self.mode}', "
            f"total={self.total_candidates}, valid={self.valid_candidates}, "
            f"winner='{winner_id}')"
        )
