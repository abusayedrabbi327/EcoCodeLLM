"""
code_reconstructor.py — AST-to-source code conversion with formatting.

Converts a modified AST tree back into clean, readable Python source
code. Handles edge cases in unparsing and applies basic formatting.
"""

import ast
import textwrap

from ecocode.mode2_rewriting.ast_parser import unparse_code
from ecocode.utils.logger import get_logger

logger = get_logger(__name__)


def reconstruct_code(tree: ast.Module) -> str:
    """
    Convert a transformed AST tree back into formatted Python source code.

    Steps:
    1. Unparse the AST using ast.unparse() or astor fallback
    2. Fix formatting issues (indentation, blank lines)
    3. Add a comment header noting the code was optimized

    Args:
        tree: The modified AST tree.

    Returns:
        Clean Python source code string.
    """
    # Unparse AST to source
    raw_source = unparse_code(tree)

    # Clean up the source
    source = _clean_source(raw_source)

    # Add optimization header comment
    header = "# Optimized by EcoCode-LLM (Green AI Framework)\n"
    source = header + source

    logger.info(f"Reconstructed source code ({len(source)} chars)")
    return source


def _clean_source(source: str) -> str:
    """
    Apply basic formatting cleanup to unparsed code.

    ast.unparse() sometimes produces dense, hard-to-read code.
    This function adds spacing for readability.
    """
    lines = source.split('\n')
    cleaned = []

    for i, line in enumerate(lines):
        cleaned.append(line)

        # Add blank line after function definitions
        if line.strip().startswith('def ') and i > 0:
            if i > 0 and cleaned[-2].strip() != '':
                cleaned.insert(-1, '')

    return '\n'.join(cleaned)


def generate_diff_summary(original: str, rewritten: str) -> str:
    """
    Generate a human-readable summary of changes between original
    and rewritten code.

    Args:
        original: The original source code.
        rewritten: The optimized source code.

    Returns:
        Multi-line string describing the differences.
    """
    orig_lines = original.strip().split('\n')
    new_lines = rewritten.strip().split('\n')

    summary = []
    summary.append(f"Original: {len(orig_lines)} lines")
    summary.append(f"Rewritten: {len(new_lines)} lines")
    summary.append(f"Line change: {len(new_lines) - len(orig_lines):+d}")

    return '\n'.join(summary)
