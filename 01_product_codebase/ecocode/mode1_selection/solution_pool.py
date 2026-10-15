"""
solution_pool.py — Pool manager for N code candidates.

Creates CodeCandidate objects from raw code strings, manages the pool
through filtering (testing) and profiling stages.
"""

from typing import List, Tuple, Dict, Any

from ecocode.models.code_candidate import CodeCandidate
from ecocode.testing.test_runner import run_tests
from ecocode.profiler.profile_aggregator import profile_code
from ecocode.utils.logger import get_logger
from ecocode.utils.display import print_info, print_warning

logger = get_logger(__name__)


def create_pool(code_strings: List[str],
                origin: str = "llm_generated") -> List[CodeCandidate]:
    """
    Create a pool of CodeCandidate objects from raw code strings.

    Args:
        code_strings: List of Python source code strings.
        origin: Origin label for all candidates.

    Returns:
        List of CodeCandidate objects with unique IDs.
    """
    pool = []
    for i, code in enumerate(code_strings):
        candidate = CodeCandidate(
            id=f"C{i+1:02d}",
            source_code=code,
            origin=origin,
        )
        pool.append(candidate)

    logger.info(f"Created pool of {len(pool)} candidates (origin={origin})")
    return pool


def filter_by_tests(pool: List[CodeCandidate],
                    function_name: str,
                    test_cases: List[Dict[str, Any]],
                    timeout: int = None) -> List[CodeCandidate]:
    """
    Run unit tests on each candidate and mark validity.

    Candidates that pass all tests get is_valid=True.
    Failed candidates remain in the pool but are marked is_valid=False.

    Args:
        pool: List of CodeCandidate objects.
        function_name: Name of the function to test.
        test_cases: Test cases to validate against.
        timeout: Max seconds per candidate test.

    Returns:
        The same pool with is_valid and test_results updated.
    """
    logger.info(f"Testing {len(pool)} candidates against {len(test_cases)} test case(s)...")
    print_info(f"Running correctness tests on {len(pool)} candidates...")

    valid_count = 0
    for candidate in pool:
        passed, results = run_tests(
            code=candidate.source_code,
            function_name=function_name,
            test_cases=test_cases,
            timeout=timeout,
        )
        candidate.is_valid = passed
        candidate.test_results = results

        if passed:
            valid_count += 1
            logger.info(f"  [PASS] {candidate.id}: All tests passed")
        else:
            logger.warning(f"  [FAIL] {candidate.id}: {results.get('failed', 0)} test(s) failed")

    if valid_count == 0:
        print_warning("No candidates passed the tests!")
    else:
        print_info(f"{valid_count}/{len(pool)} candidates passed all tests")

    return pool


def profile_valid_candidates(pool: List[CodeCandidate],
                             function_name: str = None,
                             test_cases: List[Dict[str, Any]] = None) -> List[CodeCandidate]:
    """
    Profile all valid candidates in the pool.

    Only candidates with is_valid=True are profiled.
    Others are skipped to save time.

    Args:
        pool: List of CodeCandidate objects (some valid, some not).
        function_name: Optional name of function to profile.
        test_cases: Optional test cases to run during profiling.

    Returns:
        The same pool with profile data attached to valid candidates.
    """
    valid = [c for c in pool if c.is_valid]
    logger.info(f"Profiling {len(valid)} valid candidate(s)...")
    print_info(f"Profiling {len(valid)} valid candidates for time, memory, and energy...")

    for candidate in valid:
        logger.info(f"  Profiling {candidate.id}...")
        candidate.profile = profile_code(
            candidate.source_code,
            function_name=function_name,
            test_cases=test_cases,
        )

    return pool


def get_valid_candidates(pool: List[CodeCandidate]) -> List[CodeCandidate]:
    """Return only valid candidates from the pool."""
    return [c for c in pool if c.is_valid]
