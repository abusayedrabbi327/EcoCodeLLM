"""
test_new_topsis.py — Unit tests for Classical Euclidean TOPSIS Engine.

Verifies:
1. Multi-metric weighted normalization.
2. Positive and Negative Ideal Solution computation.
3. Geometric Euclidean distance calculation (d+, d-).
4. Relative closeness coefficient (C_i in [0.0, 1.0]).
5. Optimal candidate selection (maximum closeness).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ecocode.models.profile_result import ProfileResult
from ecocode.models.code_candidate import CodeCandidate
from ecocode.decision_engine.new_topsis_score import (
    compute_classical_topsis,
    compute_topsis_scores,
    assign_scores_to_candidates,
)
from ecocode.decision_engine.ranking import select_best_candidate, rank_candidates


def _make_cand(id: str, time_ms: float, mem_kb: float, energy_j: float) -> CodeCandidate:
    """Helper to create candidate with specific metrics."""
    c = CodeCandidate(id=id, source_code=f"# {id}", origin="test")
    c.is_valid = True
    c.profile = ProfileResult(
        execution_time_ms=time_ms,
        peak_memory_kb=mem_kb,
        energy_joules=energy_j,
        num_runs=3,
    )
    return c


class TestClassicalTOPSIS:
    """Tests classical Euclidean TOPSIS mathematics."""

    def test_p01_benchmark_candidates(self):
        """
        Verify exact TOPSIS calculations for P01 (Two Sum):
        C1.1: Hash Map (0.088ms, 27.1KB, 330uJ) -> Best in Time & Energy
        C1.2: Two-Pointer (0.142ms, 26.8KB, 532.5uJ) -> Best in Memory
        C1.3: Brute-Force (0.182ms, 27.4KB, 682.5uJ) -> Worst in all
        """
        c1 = _make_cand("C1.1", time_ms=0.088, mem_kb=27.1, energy_j=0.000330)
        c2 = _make_cand("C1.2", time_ms=0.142, mem_kb=26.8, energy_j=0.0005325)
        c3 = _make_cand("C1.3", time_ms=0.182, mem_kb=27.4, energy_j=0.0006825)

        candidates = [c1, c2, c3]
        results = compute_classical_topsis(candidates)

        # C1.1 should have closeness > 0.85 (around 0.891)
        assert results[0]["closeness"] > 0.85, f"C1.1 closeness {results[0]['closeness']} should be > 0.85"
        # C1.3 (worst) should have closeness == 0.00
        assert results[2]["closeness"] == 0.00, f"C1.3 closeness {results[2]['closeness']} should be 0.0"
        # Relative ordering: C1.1 > C1.2 > C1.3
        assert results[0]["closeness"] > results[1]["closeness"] > results[2]["closeness"]

    def test_selection_and_ranking(self):
        """Verify that select_best_candidate selects the highest closeness candidate."""
        c1 = _make_cand("C1.1", time_ms=0.088, mem_kb=27.1, energy_j=0.000330)
        c2 = _make_cand("C1.2", time_ms=0.142, mem_kb=26.8, energy_j=0.0005325)
        c3 = _make_cand("C1.3", time_ms=0.182, mem_kb=27.4, energy_j=0.0006825)

        candidates = [c1, c2, c3]
        assign_scores_to_candidates(candidates)

        winner = select_best_candidate(candidates)
        assert winner is not None
        assert winner.id == "C1.1", f"Expected C1.1 as winner, got {winner.id}"

        ranked = rank_candidates(candidates)
        assert ranked[0].id == "C1.1"
        assert ranked[1].id == "C1.2"
        assert ranked[2].id == "C1.3"

    def test_identical_candidates(self):
        """When all candidates have identical profiles, closeness should be 1.0."""
        c1 = _make_cand("C1", time_ms=10.0, mem_kb=100.0, energy_j=1.0)
        c2 = _make_cand("C2", time_ms=10.0, mem_kb=100.0, energy_j=1.0)

        results = compute_classical_topsis([c1, c2])
        assert results[0]["closeness"] == 1.0
        assert results[1]["closeness"] == 1.0
