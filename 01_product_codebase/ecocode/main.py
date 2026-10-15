"""
main.py — CLI entry point and mode router for EcoCode-LLM.

Provides the command-line interface that users interact with.
Routes to Mode 1 (Generate & Select) or Mode 2 (Analyze & Rewrite)
based on user arguments.

Usage:
    Mode 1: python -m ecocode.main --mode 1 --prompt "..." --test-file tests.json
    Mode 2: python -m ecocode.main --mode 2 --input-file code.py --test-file tests.json
"""

import json
import sys
import os
from pathlib import Path

# Ensure project root directory is in sys.path for direct file execution
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import click

from ecocode.utils.logger import get_logger
from ecocode.utils.config_loader import load_config
from ecocode.utils.display import (
    print_banner,
    print_mode_header,
    print_candidates_table,
    print_code_block,
    print_improvement_summary,
    print_success,
    print_error,
    print_warning,
    print_info,
)
from ecocode.mode1_selection.selector import run_mode1
from ecocode.mode2_rewriting.ast_parser import parse_code
from ecocode.mode2_rewriting.pattern_detector import detect_patterns
from ecocode.mode2_rewriting.refactoring_rules import apply_all_refactoring_rules
from ecocode.mode2_rewriting.code_reconstructor import reconstruct_code, generate_diff_summary
from ecocode.mode1_selection.solution_pool import (
    create_pool,
    filter_by_tests,
    profile_valid_candidates,
    get_valid_candidates,
)
from ecocode.decision_engine.new_topsis_score import assign_scores_to_candidates
from ecocode.decision_engine.ranking import select_best_candidate, compute_improvement_stats
from ecocode.models.evaluation_report import EvaluationReport
from ecocode.testing.test_runner import load_test_cases
from ecocode.utils.file_utils import read_source_file, ensure_output_dir, save_code_to_file

logger = get_logger(__name__)


@click.command()
@click.option(
    "--mode", "-m",
    type=click.Choice(["1", "2"]),
    required=True,
    help="Mode 1: Generate & Select | Mode 2: Analyze & Rewrite"
)
@click.option(
    "--prompt", "-p",
    type=str,
    default=None,
    help="(Mode 1) Natural language programming problem description."
)
@click.option(
    "--input-file", "-i",
    type=click.Path(exists=False),
    default=None,
    help="(Mode 2) Path to existing Python source file to optimize."
)
@click.option(
    "--test-file", "-t",
    type=click.Path(exists=True),
    required=True,
    help="Path to test cases JSON file."
)
@click.option(
    "--num-candidates", "-n",
    type=int,
    default=None,
    help="(Mode 1) Number of code variants to generate."
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default=None,
    help="Path for the output report JSON file."
)
@click.option(
    "--config", "-c",
    type=click.Path(exists=True),
    default=None,
    help="Path to custom config.yaml file."
)
def main(mode, prompt, input_file, test_file, num_candidates, output, config):
    """
    🌿 EcoCode-LLM: A Green AI Framework for Energy-Efficient Code Generation.

    Generate optimized code (Mode 1) or refactor existing code (Mode 2)
    for minimal energy consumption while preserving correctness.
    """
    # Print banner
    print_banner()

    # Load configuration
    try:
        cfg = load_config(config)
    except (FileNotFoundError, ValueError) as e:
        print_error(str(e))
        sys.exit(1)

    # Route to the appropriate mode
    if mode == "1":
        _run_mode1_pipeline(prompt, test_file, num_candidates, output)
    elif mode == "2":
        _run_mode2_pipeline(input_file, test_file, output)


def _run_mode1_pipeline(prompt, test_file, num_candidates, output):
    """Execute Mode 1: Multi-Solution Generation & Selection."""
    if not prompt:
        print_error("Mode 1 requires --prompt (-p) argument.")
        sys.exit(1)

    report = run_mode1(
        prompt=prompt,
        test_file=test_file,
        num_candidates=num_candidates,
        output_path=output,
    )

    if report is None:
        print_error("Mode 1 pipeline failed.")
        sys.exit(1)

    if report.winner:
        print_success("Mode 1 complete! Optimal code selected.")
    else:
        print_warning("No valid candidates found.")


def _run_mode2_pipeline(input_file, test_file, output):
    """Execute Mode 2: Existing Code Analysis & Refactoring."""
    print_mode_header(2, "Code Analysis & Refactoring")

    if not input_file:
        print_error("Mode 2 requires --input-file (-i) argument.")
        sys.exit(1)

    # --- Step 1: Read and validate input code ---
    print_info("Step 1: Reading input code...")
    try:
        original_code = read_source_file(input_file)
    except (FileNotFoundError, ValueError) as e:
        print_error(str(e))
        sys.exit(1)

    # --- Step 2: Load test cases ---
    print_info("Step 2: Loading test cases...")
    function_name, test_cases = load_test_cases(test_file)

    if not test_cases:
        print_error("No test cases found.")
        sys.exit(1)

    # --- Step 3: Verify original code passes tests ---
    print_info("Step 3: Verifying original code passes tests...")
    original_pool = create_pool([original_code], origin="user_provided")
    original_pool = filter_by_tests(original_pool, function_name, test_cases)

    if not original_pool[0].is_valid:
        print_error("Original code fails the test suite. Cannot proceed with optimization.")
        sys.exit(1)

    print_success("Original code passes all tests.")

    # --- Step 4: Parse to AST and detect patterns ---
    print_info("Step 4: Parsing code and detecting anti-patterns...")
    tree = parse_code(original_code)
    if tree is None:
        print_error("Failed to parse code into AST.")
        sys.exit(1)

    issues = detect_patterns(tree)

    if not issues:
        print_info("No anti-patterns detected. Code appears already efficient.")
        # Still profile the original for reporting
        original_pool = profile_valid_candidates(original_pool, function_name=function_name, test_cases=test_cases)
        print_code_block(original_code, title="Original Code (Already Efficient)")

        if output:
            report = EvaluationReport(
                problem_description=f"Mode 2 analysis of {input_file}",
                mode="mode2_rewriting",
                total_candidates=1,
                valid_candidates=1,
                candidates=original_pool,
                winner=original_pool[0],
            )
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            with open(output, "w") as f:
                json.dump(report.to_dict(), f, indent=2)
        return

    print_info(f"Found {len(issues)} anti-pattern(s). Applying refactoring rules...")

    # --- Step 5: Apply refactoring rules ---
    print_info("Step 5: Applying AST transformations...")
    refactored_tree = apply_all_refactoring_rules(tree)
    rewritten_code = reconstruct_code(refactored_tree)

    print_code_block(original_code, title="Original Code")
    print_code_block(rewritten_code, title="Rewritten Code (EcoCode Optimized)")

    # --- Step 6: Validate rewritten code ---
    print_info("Step 6: Validating rewritten code passes tests...")
    rewritten_pool = create_pool([rewritten_code], origin="ast_rewritten")
    rewritten_pool = filter_by_tests(rewritten_pool, function_name, test_cases)

    if not rewritten_pool[0].is_valid:
        print_warning("Rewritten code failed tests. Rolling back to original.")
        original_pool = profile_valid_candidates(original_pool, function_name=function_name, test_cases=test_cases)
        print_code_block(original_code, title="Rollback: Using Original Code")
        return

    print_success("Rewritten code passes all tests.")

    # --- Step 7: Profile and compare ---
    print_info("Step 7: Profiling both versions for comparison...")

    # Combine into a comparison pool
    original_pool[0].id = "Original"
    rewritten_pool[0].id = "Rewritten"
    comparison_pool = original_pool + rewritten_pool
    comparison_pool = profile_valid_candidates(comparison_pool, function_name=function_name, test_cases=test_cases)

    # Score and compare
    valid = get_valid_candidates(comparison_pool)
    assign_scores_to_candidates(valid)
    winner = select_best_candidate(valid)

    # Display results
    print_candidates_table(comparison_pool)

    if winner:
        improvements = compute_improvement_stats(valid, winner)
        print_improvement_summary(improvements)
        print_code_block(winner.source_code, title=f"WINNER: {winner.id}")
        print_success(f"Selected '{winner.id}' as the optimal version.")

        # Save outputs
        output_dir = ensure_output_dir("rewritten_code")
        save_code_to_file(winner.source_code, output_dir, "optimized_code.py")

        # Generate diff summary
        diff_summary = generate_diff_summary(original_code, rewritten_code)
        print_info(f"Diff summary:\n{diff_summary}")

        # Save report
        if output:
            report = EvaluationReport(
                problem_description=f"Mode 2 optimization of {input_file}",
                mode="mode2_rewriting",
                total_candidates=2,
                valid_candidates=len(valid),
                candidates=comparison_pool,
                winner=winner,
                improvement_pct=improvements,
            )
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            with open(output, "w") as f:
                json.dump(report.to_dict(), f, indent=2)
            logger.info(f"Report saved to: {output}")


if __name__ == "__main__":
    main()
