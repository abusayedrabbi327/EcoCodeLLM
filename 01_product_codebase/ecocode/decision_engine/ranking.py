"""
ranking.py — Final ranking and selection logic.

Takes scored candidates and selects the optimal solution (lowest TOPSIS score).
Also computes improvement statistics comparing the winner to the worst candidate.
"""

from typing import List, Optional, Dict

from ecocode.models.code_candidate import CodeCandidate
from ecocode.utils.logger import get_logger

logger = get_logger(__name__)


def select_best_candidate(candidates: List[CodeCandidate]) -> Optional[CodeCandidate]:
    """
    Select the candidate with the lowest TOPSIS score.

    Args:
        candidates: List of scored CodeCandidate objects.

    Returns:
        The best (most energy-efficient) candidate, or None if no
        valid scored candidates exist.
    """
    # Filter to only valid, scored candidates
    scored = [
        c for c in candidates
        if c.is_valid and c.topsis_score is not None
    ]

    if not scored:
        logger.error("No valid, scored candidates available for selection")
        return None

    # Select best candidate (highest closeness if classical TOPSIS, lowest score if legacy)
    if getattr(scored[0], "topsis_closeness", None) is not None:
        winner = max(scored, key=lambda c: getattr(c, "topsis_closeness", 0.0))
        logger.info(
            f"[WINNER] Selected: {winner.id} "
            f"(Classical TOPSIS Closeness C_i: {winner.topsis_closeness:.4f})"
        )
    else:
        winner = min(scored, key=lambda c: c.topsis_score)
        logger.info(
            f"[WINNER] Selected: {winner.id} "
            f"(TOPSIS Score: {winner.topsis_score:.6f})"
        )

    return winner


def compute_improvement_stats(candidates: List[CodeCandidate],
                               winner: CodeCandidate) -> Dict[str, float]:
    """
    Compute improvement percentages comparing the winner vs the worst
    valid candidate in the pool.

    Args:
        candidates: All valid, profiled candidates.
        winner: The selected best candidate.

    Returns:
        Dict with percentage changes for time, memory, and energy.
        Negative values indicate improvement (reduction).
    """
    valid = [c for c in candidates if c.is_valid and c.profile is not None]

    if len(valid) < 2 or winner.profile is None:
        return {"time": 0.0, "memory": 0.0, "energy": 0.0}

    # Find worst candidate
    if getattr(valid[0], "topsis_closeness", None) is not None:
        worst = min(valid, key=lambda c: getattr(c, "topsis_closeness", 1.0))
    else:
        worst = max(valid, key=lambda c: c.topsis_score if c.topsis_score else 0)

    if worst.profile is None:
        return {"time": 0.0, "memory": 0.0, "energy": 0.0}

    def pct(best_val, worst_val):
        if worst_val == 0:
            return 0.0
        return round(((best_val - worst_val) / worst_val) * 100, 1)

    improvements = {
        "time": pct(winner.profile.execution_time_ms, worst.profile.execution_time_ms),
        "memory": pct(winner.profile.peak_memory_kb, worst.profile.peak_memory_kb),
        "energy": pct(winner.profile.energy_joules, worst.profile.energy_joules),
    }

    logger.info(
        f"Improvements vs worst: "
        f"Time={improvements['time']}%, "
        f"Memory={improvements['memory']}%, "
        f"Energy={improvements['energy']}%"
    )

    return improvements


def rank_candidates(candidates: List[CodeCandidate]) -> List[CodeCandidate]:
    """
    Return candidates sorted by TOPSIS score (best first).

    Args:
        candidates: List of scored CodeCandidate objects.

    Returns:
        Sorted list with the best candidate at index 0.
    """
    scored = [c for c in candidates if c.topsis_score is not None or getattr(c, "topsis_closeness", None) is not None]
    if scored and getattr(scored[0], "topsis_closeness", None) is not None:
        return sorted(scored, key=lambda c: getattr(c, "topsis_closeness", 0.0), reverse=True)
    return sorted(scored, key=lambda c: c.topsis_score)
