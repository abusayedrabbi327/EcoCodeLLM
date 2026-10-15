"""
ast_parser.py — Python Abstract Syntax Tree builder and utilities.

Converts raw Python source code into an AST tree for structural analysis
and transformation. Provides utility functions for common AST operations.
"""

import ast
from typing import Optional

from ecocode.utils.logger import get_logger

logger = get_logger(__name__)


def parse_code(source_code: str) -> Optional[ast.Module]:
    """
    Parse Python source code into an Abstract Syntax Tree.

    Args:
        source_code: Valid Python source code string.

    Returns:
        ast.Module node (the root of the tree), or None if parsing fails.
    """
    try:
        tree = ast.parse(source_code)
        logger.info(f"Successfully parsed code into AST ({count_nodes(tree)} nodes)")
        return tree

    except SyntaxError as e:
        logger.error(f"AST parse failed — SyntaxError: {e}")
        return None

    except Exception as e:
        logger.error(f"AST parse failed — {type(e).__name__}: {e}")
        return None


def unparse_code(tree: ast.Module) -> str:
    """
    Convert an AST tree back into Python source code.

    Uses ast.unparse() (Python 3.9+) for clean code generation.

    Args:
        tree: The AST tree to convert.

    Returns:
        Python source code string.
    """
    try:
        source = ast.unparse(tree)
        logger.debug(f"Unparsed AST to source ({len(source)} chars)")
        return source

    except Exception as e:
        logger.error(f"AST unparse failed: {e}")
        # Fallback: try astor
        try:
            import astor
            source = astor.to_source(tree)
            logger.info("Used astor fallback for unparsing")
            return source
        except ImportError:
            logger.error("astor not installed for fallback unparsing")
            raise


def count_nodes(tree: ast.AST) -> int:
    """Count the total number of nodes in an AST tree."""
    return sum(1 for _ in ast.walk(tree))


def get_function_names(tree: ast.Module) -> list:
    """Extract all top-level function names from the AST."""
    return [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    ]


def pretty_dump(tree: ast.AST, max_depth: int = 4) -> str:
    """
    Generate a human-readable dump of the AST for debugging.

    Args:
        tree: AST node to dump.
        max_depth: Maximum nesting depth to display.

    Returns:
        Formatted string representation.
    """
    return ast.dump(tree, indent=2)
