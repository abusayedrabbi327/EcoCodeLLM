"""
file_utils.py — Temporary file and directory helpers.

Handles writing code candidates to temp files for isolated execution,
reading source files, and managing output directories.
"""

import os
import tempfile
from pathlib import Path

from ecocode.utils.logger import get_logger

logger = get_logger(__name__)


def write_temp_script(code: str, prefix: str = "ecocode_", suffix: str = ".py") -> str:
    """
    Write a code string to a temporary .py file.

    Args:
        code: The Python source code string.
        prefix: Filename prefix for identification.
        suffix: File extension.

    Returns:
        str: Absolute path to the created temp file.
    """
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(code)
    except Exception:
        os.close(fd)
        raise

    logger.debug(f"Wrote temp script: {path} ({len(code)} chars)")
    return path


def read_source_file(file_path: str) -> str:
    """
    Read a Python source file and return its contents.

    Args:
        file_path: Path to the .py file.

    Returns:
        str: The file contents as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a .py file.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")
    if path.suffix != ".py":
        raise ValueError(f"Expected a .py file, got: {path.suffix}")

    content = path.read_text(encoding="utf-8")
    logger.debug(f"Read source file: {file_path} ({len(content)} chars)")
    return content


def ensure_output_dir(subdir: str) -> Path:
    """
    Ensure an output subdirectory exists and return its path.

    Args:
        subdir: Subdirectory name under outputs/ (e.g., 'generated_code').

    Returns:
        Path: Absolute path to the output directory.
    """
    output_dir = Path(__file__).resolve().parent.parent.parent / "outputs" / subdir
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def save_code_to_file(code: str, directory: Path, filename: str) -> Path:
    """
    Save a code string to a named file in the given directory.

    Args:
        code: The Python source code.
        directory: Target directory path.
        filename: Target filename (e.g., 'candidate_001.py').

    Returns:
        Path: The full path to the saved file.
    """
    filepath = directory / filename
    filepath.write_text(code, encoding="utf-8")
    logger.info(f"Saved code to: {filepath}")
    return filepath


def cleanup_temp_file(path: str) -> None:
    """Safely remove a temporary file if it exists."""
    try:
        if os.path.exists(path):
            os.remove(path)
            logger.debug(f"Cleaned up temp file: {path}")
    except OSError as e:
        logger.warning(f"Failed to clean up temp file {path}: {e}")


def strip_blocking_top_level_code(code: str) -> str:
    """
    Strips top-level executable statements from a Python code string,
    retaining only imports, function definitions, and class definitions.
    This prevents blocking UI prompts (like plt.show()) or heavy main loops
    from executing during correctness testing and profiling.
    """
    import ast
    try:
        tree = ast.parse(code)
        new_body = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                new_body.append(node)
        if new_body:
            return ast.unparse(ast.Module(body=new_body, type_ignores=[]))
    except Exception:
        pass
    return code
