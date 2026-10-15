"""
pattern_detector.py — Anti-pattern detection via AST tree walking.

Implements ast.NodeVisitor subclasses that traverse the AST to identify
known energy-wasteful code patterns. Each detected pattern is recorded
with its rule ID, line number, and description.

Detected Patterns:
    R001: Nested loops with list membership check (O(n²))
    R002: String += concatenation inside loops
    R003: Element-wise math operations in loops (non-vectorized)
    R004: File I/O (open()) inside loop bodies
    R005: list.append() in loop that could be a list comprehension
    R006: Global variable access inside tight loops
"""

import ast
from typing import List, Dict

from ecocode.utils.logger import get_logger

logger = get_logger(__name__)


class PatternDetector(ast.NodeVisitor):
    """
    Walks an AST tree and detects energy-wasteful anti-patterns.

    Usage:
        detector = PatternDetector()
        detector.visit(tree)
        issues = detector.get_issues()
    """

    def __init__(self):
        self.issues: List[Dict[str, str]] = []
        self._in_loop = False
        self._loop_depth = 0

    def _add_issue(self, rule_id: str, line: int, description: str):
        """Record a detected anti-pattern."""
        issue = {
            "rule_id": rule_id,
            "line": line,
            "description": description,
        }
        self.issues.append(issue)
        logger.debug(f"Detected {rule_id} at line {line}: {description}")

    # ----------------------------------------------------------------
    # R001: Nested loops with 'in' membership check on list
    # ----------------------------------------------------------------
    def visit_For(self, node: ast.For):
        """Detect nested loops and loop-level patterns."""
        self._loop_depth += 1
        was_in_loop = self._in_loop
        self._in_loop = True

        # Check for nested for-loops with 'if x in list' pattern
        for child in ast.walk(node):
            if isinstance(child, ast.For) and child is not node:
                # Look for 'if element in list' inside inner loop
                for inner_node in ast.walk(child):
                    if isinstance(inner_node, ast.Compare):
                        for op in inner_node.ops:
                            if isinstance(op, ast.In):
                                self._add_issue(
                                    "R001",
                                    getattr(inner_node, 'lineno', 0),
                                    "Nested loop with list membership check (O(n²)). "
                                    "Convert target list to set for O(1) lookup."
                                )

        # Check for other patterns inside this loop
        self._check_loop_body(node)

        self.generic_visit(node)
        self._loop_depth -= 1
        self._in_loop = was_in_loop

    def _check_loop_body(self, loop_node: ast.For):
        """Check the body of a for loop for anti-patterns."""
        # R007: Empty / busy-wait loop (for ...: pass)
        if len(loop_node.body) == 1 and isinstance(loop_node.body[0], ast.Pass):
            self._add_issue(
                "R007",
                loop_node.lineno,
                "Busy-wait / empty loop detected. Consumes CPU cycles with no operational output."
            )

        for stmt in loop_node.body:
            # R002: String += inside loop
            if isinstance(stmt, ast.AugAssign) and isinstance(stmt.op, ast.Add):
                if self._is_string_target(stmt):
                    self._add_issue(
                        "R002",
                        stmt.lineno,
                        "String += concatenation inside loop. "
                        "Use list.append() + ''.join() instead."
                    )
                else:
                    # R003: Numeric accumulator / element-wise arithmetic in loop
                    self._add_issue(
                        "R003",
                        stmt.lineno,
                        "Element-wise arithmetic / loop accumulation detected. "
                        "Consider using built-in sum() or vectorized operations."
                    )

            # R004: open() call inside loop
            for child in ast.walk(stmt):
                if isinstance(child, ast.Call):
                    func_name = self._get_call_name(child)
                    if func_name == "open":
                        self._add_issue(
                            "R004",
                            child.lineno,
                            "File open() inside loop body. "
                            "Hoist file read before the loop."
                        )

            # R005: list.append() in loop (potential list comprehension)
            for child in ast.walk(stmt):
                if isinstance(child, ast.Call):
                    if self._is_append_call(child):
                        self._add_issue(
                            "R005",
                            child.lineno,
                            "list.append() inside loop. "
                            "Consider using a list comprehension."
                        )

            # R006: Repeated global or module lookup in tight loop
            for child in ast.walk(stmt):
                if isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name):
                    if child.value.id in ("math", "np", "os", "sys", "time", "random"):
                        self._add_issue(
                            "R006",
                            child.lineno,
                            f"Repeated module lookup '{child.value.id}.{child.attr}' in loop. "
                            "Hoist to a local variable reference."
                        )

    # ----------------------------------------------------------------
    # R002 helper: Check if AugAssign target is a string
    # ----------------------------------------------------------------
    def _is_string_target(self, node: ast.AugAssign) -> bool:
        """Heuristic: check if the augmented assignment likely involves strings."""
        return self._is_string_expression(node.value)

    def _is_string_expression(self, node: ast.expr) -> bool:
        """Recursively check if an expression likely produces a string."""
        # Direct string constant
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return True
        # f-string
        if isinstance(node, ast.JoinedStr):
            return True
        # str() or format() call
        if isinstance(node, ast.Call):
            name = self._get_call_name(node)
            if name in ("str", "format"):
                return True
        # BinOp with + where either operand is a string
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            if self._is_string_expression(node.left) or self._is_string_expression(node.right):
                return True
        return False

    # ----------------------------------------------------------------
    # R005 helper: Check for .append() calls
    # ----------------------------------------------------------------
    def _is_append_call(self, node: ast.Call) -> bool:
        """Check if a Call node is a .append() method call."""
        if isinstance(node.func, ast.Attribute):
            return node.func.attr == "append"
        return False

    # ----------------------------------------------------------------
    # Utility: Get function name from a Call node
    # ----------------------------------------------------------------
    def _get_call_name(self, node: ast.Call) -> str:
        """Extract the function name from a Call AST node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""

    def get_issues(self) -> List[Dict[str, str]]:
        """Return all detected anti-pattern issues."""
        return self.issues


def detect_patterns(tree: ast.Module) -> List[Dict[str, str]]:
    """
    Run the pattern detector on an AST tree.

    Args:
        tree: Parsed AST tree (from ast_parser.parse_code).

    Returns:
        List of detected issue dicts with keys: rule_id, line, description.
    """
    detector = PatternDetector()
    detector.visit(tree)

    issues = detector.get_issues()

    if issues:
        logger.info(f"Detected {len(issues)} anti-pattern(s):")
        for issue in issues:
            logger.info(f"  [{issue['rule_id']}] Line {issue['line']}: {issue['description']}")
    else:
        logger.info("No anti-patterns detected — code appears efficient")

    return issues
