"""
selector.py — Mode 1 orchestrator: Generate → Test → Profile → Select.

This is the top-level coordinator for Mode 1 that chains together
all components: LLM generation, correctness filtering, profiling,
TOPSIS scoring, and final selection.
"""

import json
from pathlib import Path
from typing import Optional

from ecocode.mode1_selection.generator import generate_candidates
from ecocode.mode1_selection.solution_pool import (
    create_pool,
    filter_by_tests,
    profile_valid_candidates,
    get_valid_candidates,
)
from ecocode.decision_engine.new_topsis_score import assign_scores_to_candidates
from ecocode.decision_engine.ranking import (
    select_best_candidate,
    compute_improvement_stats,
)
from ecocode.models.code_candidate import CodeCandidate
from ecocode.models.evaluation_report import EvaluationReport
from ecocode.testing.test_runner import load_test_cases
from ecocode.utils.logger import get_logger
from ecocode.utils.display import (
    print_mode_header,
    print_candidates_table,
    print_code_block,
    print_improvement_summary,
    print_success,
    print_error,
)
from ecocode.utils.file_utils import ensure_output_dir, save_code_to_file

logger = get_logger(__name__)


def run_mode1(prompt: str, test_file: str,
              num_candidates: int = None,
              output_path: str = None) -> Optional[EvaluationReport]:
    """
    Execute the full Mode 1 pipeline: Generate & Select.

    Pipeline steps:
    1. Generate N code candidates via LLM
    2. Filter by correctness (unit tests)
    3. Profile valid candidates (time, memory, energy)
    4. Score using TOPSIS weighted formula
    5. Select and return the best candidate

    Args:
        prompt: Natural language programming problem.
        test_file: Path to test cases JSON file.
        num_candidates: Number of variants to generate.
        output_path: Optional path for the JSON report.

    Returns:
        EvaluationReport with all candidates and the winner,
        or None if the pipeline fails.
    """
    print_mode_header(1, "Multi-Solution Generation & Selection")

    # --- Step 1: Load test cases ---
    logger.info("Step 1: Loading test cases...")
    function_name, test_cases = load_test_cases(test_file)

    if not test_cases:
        print_error("No test cases found. Cannot validate candidates.")
        return None

    # --- Step 2: Generate code candidates ---
    logger.info("Step 2: Generating code candidates via LLM...")
    generation_prompt = (
        f"{prompt}\n\n"
        f"Implementation contract: define exactly one complete Python function "
        f"named `{function_name}`. Return the function definition including "
        f"the `def {function_name}(...)` line. The function must satisfy the "
        f"provided test cases."
    )
    code_strings = generate_candidates(generation_prompt, num_candidates=num_candidates)

    if not code_strings:
        print_error("Failed to generate any code candidates.")
        return None

    # --- Step 3: Create pool and filter by tests ---
    logger.info("Step 3: Testing candidates for correctness...")
    pool = create_pool(code_strings, origin="llm_generated")
    pool = filter_by_tests(pool, function_name, test_cases)

    valid = get_valid_candidates(pool)
    if not valid:
        print_error(
            "No candidates passed the test suite. "
            "Try increasing num_candidates or improving the prompt."
        )
        # Still return a report with failures documented
        report = EvaluationReport(
            problem_description=prompt,
            mode="mode1_selection",
            total_candidates=len(pool),
            valid_candidates=0,
            candidates=pool,
        )
        return report

    # --- Step 4: Profile valid candidates ---
    logger.info("Step 4: Profiling valid candidates...")
    pool = profile_valid_candidates(pool, function_name=function_name, test_cases=test_cases)

    # --- Step 5: Score and rank ---
    logger.info("Step 5: Computing TOPSIS scores...")
    assign_scores_to_candidates(valid)

    # --- Step 6: Select winner ---
    logger.info("Step 6: Selecting optimal candidate...")
    winner = select_best_candidate(valid)

    if winner is None:
        print_error("Failed to select a winner.")
        return None

    # --- Step 7: Build report ---
    improvements = compute_improvement_stats(valid, winner)
    report = EvaluationReport(
        problem_description=prompt,
        mode="mode1_selection",
        total_candidates=len(pool),
        valid_candidates=len(valid),
        candidates=pool,
        winner=winner,
        improvement_pct=improvements,
    )

    # --- Display results ---
    print_candidates_table(pool)
    print_code_block(winner.source_code, title=f"WINNER: {winner.id}")
    print_improvement_summary(improvements)
    print_success(f"Selected {winner.id} with TOPSIS score {winner.topsis_score:.6f}")

    # --- Save outputs ---
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2)
        logger.info(f"Report saved to: {output_path}")

    # Save winning code
    output_dir = ensure_output_dir("generated_code")
    save_code_to_file(winner.source_code, output_dir, f"{winner.id}_winner.py")

    return report
