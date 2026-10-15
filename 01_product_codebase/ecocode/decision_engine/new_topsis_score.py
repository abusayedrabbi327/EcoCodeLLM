"""
new_topsis_score.py — Classical Euclidean TOPSIS Decision Engine.

Implements the formal Technique for Order of Preference by Similarity to Ideal
Solution (TOPSIS) using geometric Euclidean distances to Positive Ideal (A+)
and Negative Ideal (A-) solutions.

Mathematical Formulation:
1. Multi-metric min-max normalization:
   x'_{ij} = (x_{ij} - min_k(x_{kj})) / (max_k(x_{kj}) - min_k(x_{kj}) + eps)

2. Weighted Normalized Values:
   v_{ij} = w_j * x'_{ij}, where sum(w_j) = 1.0
   Default weights: w_E = 0.50, w_T = 0.35, w_M = 0.15

3. Ideal Reference Points (Cost Criteria: lower is better):
   A+ = (min_i v_{i,T}, min_i v_{i,M}, min_i v_{i,E}) = (0.0, 0.0, 0.0)
   A- = (max_i v_{i,T}, max_i v_{i,M}, max_i v_{i,E}) = (w_T, w_M, w_E)

4. Euclidean Separation Distances:
   d_i^+ = sqrt( sum_j (v_{ij} - A_j^+)^2 )
   d_i^- = sqrt( sum_j (v_{ij} - A_j^-)^2 )

5. Relative Closeness to Ideal Solution:
   C_i = d_i^- / (d_i^+ + d_i^-)
   Higher C_i in [0.0, 1.0] corresponds to superior multi-criteria efficiency.
"""

import math
from typing import List, Dict, Tuple, Any
from ecocode.decision_engine.normalizer import normalize_candidates
from ecocode.utils.logger import get_logger
from ecocode.utils.config_loader import get_config_value

logger = get_logger(__name__)


def compute_classical_topsis(candidates: list) -> List[Dict[str, float]]:
    """
    Compute classical TOPSIS Euclidean distances and relative closeness.

    Args:
        candidates: List of CodeCandidate objects with profile data.

    Returns:
        List of dicts containing:
          - 'closeness': C_i in [0.0, 1.0] (higher is better)
          - 'd_plus': distance to positive ideal solution A+
          - 'd_minus': distance to negative ideal solution A-
    """
    if not candidates:
        return []

    # 1. Load configurable weights
    w_energy = float(get_config_value("weights", "energy", 0.50))
    w_time = float(get_config_value("weights", "time", 0.35))
    w_memory = float(get_config_value("weights", "memory", 0.15))

    logger.info(
        f"[TOPSIS Engine] Weights configured: Energy={w_energy:.2f}, "
        f"Time={w_time:.2f}, Memory={w_memory:.2f}"
    )

    # 2. Normalize candidates into dimensionless [0, 1] range
    normalized = normalize_candidates(candidates)

    # 3. Calculate weighted normalized values (v_ij)
    weighted_vectors = []
    for norm in normalized:
        v_t = norm["time"] * w_time
        v_m = norm["memory"] * w_memory
        v_e = norm["energy"] * w_energy
        weighted_vectors.append((v_t, v_m, v_e))

    # 4. Identify Positive (A+) and Negative (A-) Ideal Solutions
    # In cost metrics (Time, Memory, Energy), minimum is optimal
    v_t_all = [v[0] for v in weighted_vectors]
    v_m_all = [v[1] for v in weighted_vectors]
    v_e_all = [v[2] for v in weighted_vectors]

    a_plus = (min(v_t_all), min(v_m_all), min(v_e_all))
    a_minus = (max(v_t_all), max(v_m_all), max(v_e_all))

    logger.debug(f"A+ (Ideal Best): T={a_plus[0]:.4f}, M={a_plus[1]:.4f}, E={a_plus[2]:.4f}")
    logger.debug(f"A- (Ideal Worst): T={a_minus[0]:.4f}, M={a_minus[1]:.4f}, E={a_minus[2]:.4f}")

    # 5. Compute Euclidean distances and Relative Closeness C_i
    results = []
    for i, (v_t, v_m, v_e) in enumerate(weighted_vectors):
        d_plus = math.sqrt(
            (v_t - a_plus[0]) ** 2 +
            (v_m - a_plus[1]) ** 2 +
            (v_e - a_plus[2]) ** 2
        )
        d_minus = math.sqrt(
            (v_t - a_minus[0]) ** 2 +
            (v_m - a_minus[1]) ** 2 +
            (v_e - a_minus[2]) ** 2
        )

        denom = d_plus + d_minus
        if denom == 0.0:
            closeness = 1.0  # Identical best candidates
        else:
            closeness = d_minus / denom

        results.append({
            "closeness": round(closeness, 6),
            "d_plus": round(d_plus, 6),
            "d_minus": round(d_minus, 6),
        })

        cand_id = getattr(candidates[i], "id", f"C{i+1}")
        logger.debug(
            f"  {cand_id}: d+={d_plus:.4f}, d-={d_minus:.4f} -> Closeness C_i={closeness:.6f}"
        )

    return results


def compute_topsis_scores(candidates: list) -> List[float]:
    """
    Drop-in compatibility interface returning relative closeness C_i.

    Returns:
        List of closeness scores (float) where higher = better.
    """
    results = compute_classical_topsis(candidates)
    return [r["closeness"] for r in results]


def assign_scores_to_candidates(candidates: list) -> None:
    """
    Compute classical TOPSIS Euclidean scores and assign them directly to candidate objects.

    Sets:
      - candidate.topsis_closeness: C_i in [0.0, 1.0] (higher is better)
      - candidate.d_plus: distance to ideal solution
      - candidate.d_minus: distance to negative ideal solution
      - candidate.topsis_score: relative closeness C_i
    """
    if not candidates:
        return

    results = compute_classical_topsis(candidates)

    for candidate, res in zip(candidates, results):
        candidate.topsis_closeness = res["closeness"]
        candidate.d_plus = res["d_plus"]
        candidate.d_minus = res["d_minus"]
        # Set topsis_score for universal compatibility
        candidate.topsis_score = res["closeness"]

    # Log ranked candidates
    ranked = sorted(candidates, key=lambda c: getattr(c, "topsis_closeness", 0.0), reverse=True)
    logger.info("Classical Euclidean TOPSIS Ranking (Higher Closeness C_i is Best):")
    for rank, c in enumerate(ranked, 1):
        closeness = getattr(c, "topsis_closeness", 0.0)
        d_p = getattr(c, "d_plus", 0.0)
        d_m = getattr(c, "d_minus", 0.0)
        logger.info(f"  #{rank}: {c.id} (C_i={closeness:.4f}, d+={d_p:.4f}, d-={d_m:.4f})")
