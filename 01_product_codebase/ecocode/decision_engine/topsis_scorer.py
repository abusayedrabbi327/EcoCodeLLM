"""
topsis_scorer.py — Weighted TOPSIS score calculator.

Implements the Technique for Order of Preference by Similarity to Ideal
Solution (TOPSIS), adapted for energy-efficient code selection.

The Performance Index Score for each candidate:
    S_i = w_E × E_norm + w_T × T_norm + w_M × M_norm

Where:
    w_E = 0.50 (energy weight — highest priority)
    w_T = 0.35 (time weight)
    w_M = 0.15 (memory weight)

Lower S_i = better candidate (closer to ideal zero-consumption solution).
"""

from typing import List, Dict

from ecocode.decision_engine.normalizer import normalize_candidates
from ecocode.utils.logger import get_logger
from ecocode.utils.config_loader import get_config_value

logger = get_logger(__name__)


def compute_topsis_scores(candidates: list) -> List[float]:
    """
    Compute TOPSIS scores for all candidates.

    Steps:
    1. Normalize all metrics via min-max scaling
    2. Apply configurable weights
    3. Compute weighted sum for each candidate

    Args:
        candidates: List of CodeCandidate objects with profile data.

    Returns:
        List of TOPSIS scores (float), aligned with candidate order.
        Lower is better.
    """
    if not candidates:
        return []

    # Load weights from config
    w_energy = get_config_value("weights", "energy", 0.50)
    w_time = get_config_value("weights", "time", 0.35)
    w_memory = get_config_value("weights", "memory", 0.15)

    logger.info(
        f"TOPSIS weights: Energy={w_energy}, Time={w_time}, Memory={w_memory}"
    )

    # Step 1: Normalize metrics
    normalized = normalize_candidates(candidates)

    # Step 2: Compute weighted scores
    scores = []
    for i, norm in enumerate(normalized):
        score = (
            w_energy * norm["energy"] +
            w_time * norm["time"] +
            w_memory * norm["memory"]
        )
        scores.append(round(score, 6))
        logger.debug(
            f"  {candidates[i].id}: "
            f"E_norm={norm['energy']:.4f} × {w_energy} + "
            f"T_norm={norm['time']:.4f} × {w_time} + "
            f"M_norm={norm['memory']:.4f} × {w_memory} "
            f"= {score:.6f}"
        )

    return scores


def assign_scores_to_candidates(candidates: list) -> None:
    """
    Compute TOPSIS scores and assign them to each candidate in-place.

    Args:
        candidates: List of CodeCandidate objects. Their .topsis_score
                    attribute will be updated.
    """
    scores = compute_topsis_scores(candidates)

    for candidate, score in zip(candidates, scores):
        candidate.topsis_score = score

    # Log ranking
    ranked = sorted(candidates, key=lambda c: c.topsis_score)
    logger.info("TOPSIS Ranking:")
    for rank, c in enumerate(ranked, 1):
        logger.info(f"  #{rank}: {c.id} (Score: {c.topsis_score:.6f})")
