"""
test_generator.py — Auto-generates basic test cases from a problem prompt.

When the user doesn't provide a test file, this module can generate
minimal test cases using the LLM or simple heuristics to at least
verify the function executes without errors.
"""

import json
from typing import List, Dict, Any

from ecocode.utils.logger import get_logger

logger = get_logger(__name__)


def generate_basic_test_cases(function_name: str,
                               sample_input: Any = None,
                               sample_output: Any = None) -> List[Dict[str, Any]]:
    """
    Generate minimal test cases when no test file is provided.

    This creates basic smoke tests that verify:
    1. The function exists and is callable
    2. The function returns without error for sample input
    3. The function produces the expected sample output (if provided)

    Args:
        function_name: Name of the function to test.
        sample_input: A sample input value or dict.
        sample_output: Expected output for the sample input.

    Returns:
        List of test case dicts.
    """
    test_cases = []

    if sample_input is not None and sample_output is not None:
        test_cases.append({
            "input": sample_input,
            "expected_output": sample_output,
        })
        logger.info(f"Generated 1 test case from provided sample I/O")
    else:
        logger.warning(
            "No sample I/O provided — only smoke testing will be performed. "
            "Consider providing a test file for proper validation."
        )

    return test_cases


def create_test_file(function_name: str, test_cases: List[Dict[str, Any]],
                     output_path: str) -> str:
    """
    Write test cases to a JSON file in the expected format.

    Args:
        function_name: Name of the function being tested.
        test_cases: List of {input, expected_output} dicts.
        output_path: Where to save the JSON file.

    Returns:
        str: Path to the created file.
    """
    data = {
        "function_name": function_name,
        "test_cases": test_cases,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Created test file: {output_path} ({len(test_cases)} cases)")
    return output_path
