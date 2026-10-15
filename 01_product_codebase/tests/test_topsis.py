"""
test_topsis.py — Unit tests for the TOPSIS decision engine.

Verifies min-max normalization, weighted scoring, and candidate ranking
with known numerical examples.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ecocode.models.profile_result import ProfileResult
from ecocode.models.code_candidate import CodeCandidate
from ecocode.decision_engine.normalizer import normalize_min_max, normalize_candidates
from ecocode.decision_engine.topsis_scorer import compute_topsis_scores
from ecocode.decision_engine.ranking import select_best_candidate, rank_candidates


def _make_candidate(id: str, time_ms: float, mem_kb: float, energy_j: float) -> CodeCandidate:
    """Helper to create a test candidate with known metrics."""
    c = CodeCandidate(id=id, source_code=f"# {id}", origin="test")
    c.is_valid = True
    c.profile = ProfileResult(
        execution_time_ms=time_ms,
        peak_memory_kb=mem_kb,
        energy_joules=energy_j,
        num_runs=3,
    )
    return c


class TestNormalization:
    """Tests for min-max normalization."""

    def test_basic_normalization(self):
        values = [10, 20, 30]
        result = normalize_min_max(values)
        assert result == [0.0, 0.5, 1.0], f"Expected [0.0, 0.5, 1.0], got {result}"

    def test_identical_values(self):
        values = [5, 5, 5]
        result = normalize_min_max(values)
        assert result == [0.0, 0.0, 0.0], f"Expected [0.0, 0.0, 0.0], got {result}"

    def test_two_values(self):
        values = [100, 200]
        result = normalize_min_max(values)
        assert result == [0.0, 1.0], f"Expected [0.0, 1.0], got {result}"

    def test_empty_list(self):
        result = normalize_min_max([])
        assert result == [], f"Expected [], got {result}"


class TestTOPSIS:
    """Tests for TOPSIS scoring with the worked example from the report."""

    def test_report_example(self):
        """
        Verify the exact TOPSIS calculation from the pre-technical report:
        C1: T=150, M=3000, E=1.20 → Score ≈ 0.5349
        C2: T=95,  M=4500, E=0.78 → Score ≈ 0.1500 (BEST)
        C3: T=200, M=2000, E=1.50 → Score ≈ 0.8500
        """
        c1 = _make_candidate("C1", time_ms=150, mem_kb=3000, energy_j=1.20)
        c2 = _make_candidate("C2", time_ms=95, mem_kb=4500, energy_j=0.78)
        c3 = _make_candidate("C3", time_ms=200, mem_kb=2000, energy_j=1.50)

        candidates = [c1, c2, c3]
        scores = compute_topsis_scores(candidates)

        # Check scores match expected values (within tolerance)
        assert abs(scores[0] - 0.5349) < 0.01, f"C1 score {scores[0]} != ~0.5349"
        assert abs(scores[1] - 0.1500) < 0.01, f"C2 score {scores[1]} != ~0.1500"
        assert abs(scores[2] - 0.8500) < 0.01, f"C3 score {scores[2]} != ~0.8500"

    def test_best_candidate_selection(self):
        """Verify that the candidate with the lowest score is selected."""
        c1 = _make_candidate("C1", time_ms=150, mem_kb=3000, energy_j=1.20)
        c2 = _make_candidate("C2", time_ms=95, mem_kb=4500, energy_j=0.78)
        c3 = _make_candidate("C3", time_ms=200, mem_kb=2000, energy_j=1.50)

        candidates = [c1, c2, c3]
        scores = compute_topsis_scores(candidates)

        for c, s in zip(candidates, scores):
            c.topsis_score = s

        winner = select_best_candidate(candidates)
        assert winner is not None
        assert winner.id == "C2", f"Expected C2, got {winner.id}"

    def test_ranking_order(self):
        """Verify candidates are ranked best to worst."""
        c1 = _make_candidate("C1", time_ms=150, mem_kb=3000, energy_j=1.20)
        c2 = _make_candidate("C2", time_ms=95, mem_kb=4500, energy_j=0.78)
        c3 = _make_candidate("C3", time_ms=200, mem_kb=2000, energy_j=1.50)

        candidates = [c1, c2, c3]
        scores = compute_topsis_scores(candidates)
        for c, s in zip(candidates, scores):
            c.topsis_score = s

        ranked = rank_candidates(candidates)
        assert ranked[0].id == "C2"  # Best
        assert ranked[1].id == "C1"  # Middle
        assert ranked[2].id == "C3"  # Worst


class TestDataModels:
    """Tests for data model serialization."""

    def test_profile_result_to_dict(self):
        pr = ProfileResult(
            execution_time_ms=100.123,
            peak_memory_kb=2048.5,
            energy_joules=0.005678,
            num_runs=3,
        )
        d = pr.to_dict()
        assert d["execution_time_ms"] == 100.123
        assert d["peak_memory_kb"] == 2048.5
        assert d["num_runs"] == 3

    def test_code_candidate_to_dict(self):
        c = CodeCandidate(id="test", source_code="pass", origin="test")
        d = c.to_dict()
        assert d["id"] == "test"
        assert d["source_code"] == "pass"
        assert d["is_valid"] is False


def run_all_tests():
    """Run all test classes and report results."""
    test_classes = [TestNormalization, TestTOPSIS, TestDataModels]
    total = 0
    passed = 0
    failed = 0

    for cls in test_classes:
        print(f"\n{'='*60}")
        print(f"Running: {cls.__name__}")
        print(f"{'='*60}")

        instance = cls()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                total += 1
                try:
                    getattr(instance, method_name)()
                    print(f"  [PASS] {method_name}")
                    passed += 1
                except AssertionError as e:
                    print(f"  [FAIL] {method_name}: {e}")
                    failed += 1
                except Exception as e:
                    print(f"  [ERROR] {method_name}: {type(e).__name__}: {e}")
                    failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print(f"{'='*60}")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
