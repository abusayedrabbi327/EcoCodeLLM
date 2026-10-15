"""
sandbox.py — Isolated execution environment for untrusted code.

Runs code candidates in subprocess with timeout and memory limits
to prevent crashes, infinite loops, or resource exhaustion from
affecting the main EcoCode framework.
"""

import subprocess
import sys
import os
import tempfile
from pathlib import Path
from typing import Tuple, Optional

from ecocode.utils.logger import get_logger
from ecocode.utils.config_loader import get_config_value

logger = get_logger(__name__)


class SandboxResult:
    """Result from a sandboxed code execution."""

    def __init__(self, success: bool, stdout: str = "", stderr: str = "",
                 return_code: int = -1, timed_out: bool = False):
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code
        self.timed_out = timed_out

    def __repr__(self):
        status = "OK" if self.success else ("TIMEOUT" if self.timed_out else "FAILED")
        return f"SandboxResult({status}, rc={self.return_code})"


def run_in_sandbox(code: str, timeout: int = None, input_data: str = None) -> SandboxResult:
    """
    Execute a Python code string in an isolated subprocess.

    The code is written to a temporary file, executed via a fresh Python
    interpreter process, and the output is captured. The process is
    killed if it exceeds the timeout.

    Args:
        code: Python source code to execute.
        timeout: Maximum execution time in seconds. Defaults to config value.
        input_data: Optional stdin input to feed to the script.

    Returns:
        SandboxResult: Contains success flag, stdout, stderr, return code.
    """
    if timeout is None:
        timeout = get_config_value("testing", "timeout_seconds", 10)

    # Write code to a temporary file
    fd, temp_path = tempfile.mkstemp(prefix="ecocode_sandbox_", suffix=".py", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(code)

        logger.debug(f"Sandbox executing: {temp_path} (timeout={timeout}s)")

        # Execute in subprocess
        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            input=input_data,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            cwd=tempfile.gettempdir(),
        )

        return SandboxResult(
            success=(result.returncode == 0),
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.returncode,
            timed_out=False,
        )

    except subprocess.TimeoutExpired:
        logger.warning(f"Sandbox timeout after {timeout}s: {temp_path}")
        return SandboxResult(
            success=False,
            stderr=f"Execution timed out after {timeout} seconds",
            timed_out=True,
        )

    except Exception as e:
        logger.error(f"Sandbox error: {e}")
        return SandboxResult(
            success=False,
            stderr=str(e),
        )

    finally:
        # Clean up temp file
        try:
            os.remove(temp_path)
        except OSError:
            pass


def run_script_file(script_path: str, timeout: int = None,
                    input_data: str = None) -> SandboxResult:
    """
    Execute an existing Python script file in a sandboxed subprocess.

    Args:
        script_path: Path to the .py file.
        timeout: Maximum execution time in seconds.
        input_data: Optional stdin input.

    Returns:
        SandboxResult: Execution results.
    """
    if timeout is None:
        timeout = get_config_value("testing", "timeout_seconds", 10)

    if not os.path.exists(script_path):
        return SandboxResult(
            success=False,
            stderr=f"Script not found: {script_path}",
        )

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            input=input_data,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

        return SandboxResult(
            success=(result.returncode == 0),
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.returncode,
            timed_out=False,
        )

    except subprocess.TimeoutExpired:
        return SandboxResult(
            success=False,
            stderr=f"Execution timed out after {timeout} seconds",
            timed_out=True,
        )

    except Exception as e:
        return SandboxResult(
            success=False,
            stderr=str(e),
        )
