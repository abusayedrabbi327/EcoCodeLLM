"""
refactoring_rules.py — AST transformation maps for energy optimization.

Implements ast.NodeTransformer subclasses that walk the AST and replace
anti-pattern subtrees with optimized equivalents.

Transformation Rules:
    R001: list membership in loop → pre-convert to set
    R002: string += in loop → list.append() + join()
    R005: list.append() in loop → list comprehension
"""

import ast
import copy
from typing import Optional

from ecocode.utils.logger import get_logger

logger = get_logger(__name__)


class StringConcatRefactorer(ast.NodeTransformer):
    """
    R002: Replaces string += concatenation in loops with list + join.

    Before:
        result = ""
        for item in items:
            result += str(item) + ","

    After:
        _parts = []
        for item in items:
            _parts.append(str(item) + ",")
        result = "".join(_parts)
    """

    def __init__(self):
        self.transformations = 0

    def visit_For(self, node: ast.For) -> ast.AST:
        """Check for-loop bodies for string += patterns."""
        new_body = []
        string_targets = {}  # Maps variable name → accumulator list name

        for stmt in node.body:
            if (isinstance(stmt, ast.AugAssign)
                    and isinstance(stmt.op, ast.Add)
                    and isinstance(stmt.target, ast.Name)
                    and self._likely_string_concat(stmt)):

                var_name = stmt.target.id
                list_name = f"_parts_{var_name}"
                string_targets[var_name] = list_name

                # Replace: var += value → _parts_var.append(value)
                append_call = ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id=list_name, ctx=ast.Load()),
                            attr="append",
                            ctx=ast.Load(),
                        ),
                        args=[stmt.value],
                        keywords=[],
                    )
                )
                ast.copy_location(append_call, stmt)
                new_body.append(append_call)
                self.transformations += 1
                logger.debug(f"R002: Transformed '{var_name} +=' to append at line {stmt.lineno}")
            else:
                new_body.append(stmt)

        if not string_targets:
            self.generic_visit(node)
            return node

        # Build the pre-loop initialization and post-loop join
        result_nodes = []

        # Pre-loop: _parts_var = []
        for var_name, list_name in string_targets.items():
            init = ast.Assign(
                targets=[ast.Name(id=list_name, ctx=ast.Store())],
                value=ast.List(elts=[], ctx=ast.Load()),
                lineno=node.lineno,
            )
            ast.fix_missing_locations(init)
            result_nodes.append(init)

        # The modified for loop
        node.body = new_body
        self.generic_visit(node)
        result_nodes.append(node)

        # Post-loop: var = "".join(_parts_var)
        for var_name, list_name in string_targets.items():
            join = ast.Assign(
                targets=[ast.Name(id=var_name, ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Constant(value=""),
                        attr="join",
                        ctx=ast.Load(),
                    ),
                    args=[ast.Name(id=list_name, ctx=ast.Load())],
                    keywords=[],
                ),
                lineno=node.end_lineno or node.lineno,
            )
            ast.fix_missing_locations(join)
            result_nodes.append(join)

        return result_nodes

    def _likely_string_concat(self, node: ast.AugAssign) -> bool:
        """Heuristic check if this += is likely string concatenation."""
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return True
        if isinstance(node.value, ast.JoinedStr):
            return True
        if isinstance(node.value, ast.BinOp) and isinstance(node.value.op, ast.Add):
            # Check if any operand is a string
            for operand in [node.value.left, node.value.right]:
                if isinstance(operand, ast.Constant) and isinstance(operand.value, str):
                    return True
                if isinstance(operand, ast.Call):
                    if isinstance(operand.func, ast.Name) and operand.func.id == "str":
                        return True
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name) and node.value.func.id == "str":
                return True
        return False


class SetConversionRefactorer(ast.NodeTransformer):
    """
    R001: Adds set() conversion before loops that use 'in' on lists.

    Detects patterns like:
        for x in list_a:
            if x in list_b:     # O(n) lookup on list

    And inserts: _set_list_b = set(list_b) before the loop,
    then replaces the comparator to use the set.
    """

    def __init__(self):
        self.transformations = 0

    def visit_For(self, node: ast.For) -> ast.AST:
        """Look for 'if x in list' patterns inside for loops."""
        set_conversions = {}

        for child in ast.walk(node):
            if isinstance(child, ast.Compare):
                for i, op in enumerate(child.ops):
                    if isinstance(op, ast.In):
                        comparator = child.comparators[i] if i < len(child.comparators) else None
                        if comparator and isinstance(comparator, ast.Name):
                            original_name = comparator.id
                            if not original_name.startswith("_set_"):
                                set_name = f"_set_{original_name}"
                                set_conversions[original_name] = set_name
                                comparator.id = set_name
                                self.transformations += 1
                                logger.debug(
                                    f"R001: Replaced 'in {original_name}' with "
                                    f"'in {set_name}' at line {child.lineno}"
                                )

        if not set_conversions:
            self.generic_visit(node)
            return node

        # Insert set() conversion assignments before the loop
        result = []
        for original_name, set_name in set_conversions.items():
            set_init = ast.Assign(
                targets=[ast.Name(id=set_name, ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(id="set", ctx=ast.Load()),
                    args=[ast.Name(id=original_name, ctx=ast.Load())],
                    keywords=[],
                ),
                lineno=node.lineno,
            )
            ast.fix_missing_locations(set_init)
            result.append(set_init)

        self.generic_visit(node)
        result.append(node)
        return result


class ListComprehensionRefactorer(ast.NodeTransformer):
    """
    R005: Converts simple append-in-loop patterns to list comprehensions.

    Before:
        result = []
        for item in items:
            result.append(item * 2)

    After:
        result = [item * 2 for item in items]
    """

    def __init__(self):
        self.transformations = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        """Process function bodies for append-in-loop patterns."""
        new_body = []
        i = 0
        while i < len(node.body):
            stmt = node.body[i]

            # Look for pattern: result = [] followed by for ... result.append(expr)
            if (isinstance(stmt, ast.Assign)
                    and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Name)
                    and isinstance(stmt.value, ast.List)
                    and len(stmt.value.elts) == 0
                    and i + 1 < len(node.body)):

                next_stmt = node.body[i + 1]
                list_name = stmt.targets[0].id

                if isinstance(next_stmt, ast.For) and self._is_simple_append_loop(next_stmt, list_name):
                    # Convert to list comprehension
                    append_value = self._get_append_value(next_stmt, list_name)
                    if append_value is not None:
                        list_comp = ast.ListComp(
                            elt=append_value,
                            generators=[
                                ast.comprehension(
                                    target=next_stmt.target,
                                    iter=next_stmt.iter,
                                    ifs=[],
                                    is_async=0,
                                )
                            ],
                        )
                        new_assign = ast.Assign(
                            targets=[ast.Name(id=list_name, ctx=ast.Store())],
                            value=list_comp,
                            lineno=stmt.lineno,
                        )
                        ast.fix_missing_locations(new_assign)
                        new_body.append(new_assign)
                        i += 2  # Skip both the init and the for loop
                        self.transformations += 1
                        logger.debug(f"R005: Converted append-loop to list comprehension at line {stmt.lineno}")
                        continue

            new_body.append(stmt)
            i += 1

        node.body = new_body
        self.generic_visit(node)
        return node

    def _is_simple_append_loop(self, for_node: ast.For, list_name: str) -> bool:
        """Check if a for loop is a simple single-append loop."""
        if len(for_node.body) != 1:
            return False
        stmt = for_node.body[0]
        if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
            return False
        call = stmt.value
        if not isinstance(call.func, ast.Attribute):
            return False
        if call.func.attr != "append":
            return False
        if not isinstance(call.func.value, ast.Name):
            return False
        if call.func.value.id != list_name:
            return False
        return True

    def _get_append_value(self, for_node: ast.For, list_name: str) -> Optional[ast.expr]:
        """Extract the expression being appended."""
        stmt = for_node.body[0]
        call = stmt.value
        if call.args:
            return call.args[0]
        return None


class BuiltinAggregationRefactorer(ast.NodeTransformer):
    """
    R003: Replaces manual loop accumulator with Python's built-in sum().

    Before:
        total = 0
        for item in items:
            total += item

    After:
        total = sum(items)
    """

    def __init__(self):
        self.transformations = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        return self._process_statement_list(node)

    def visit_Module(self, node: ast.Module) -> ast.AST:
        return self._process_statement_list(node)

    def _process_statement_list(self, node: ast.AST) -> ast.AST:
        if not hasattr(node, "body") or not isinstance(node.body, list):
            self.generic_visit(node)
            return node

        new_body = []
        i = 0
        while i < len(node.body):
            stmt = node.body[i]

            if (isinstance(stmt, ast.Assign)
                    and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Name)
                    and isinstance(stmt.value, ast.Constant)
                    and stmt.value.value in (0, 0.0)
                    and i + 1 < len(node.body)):

                next_stmt = node.body[i + 1]
                target_var = stmt.targets[0].id

                if isinstance(next_stmt, ast.For) and len(next_stmt.body) == 1:
                    loop_body_stmt = next_stmt.body[0]
                    if (isinstance(loop_body_stmt, ast.AugAssign)
                            and isinstance(loop_body_stmt.op, ast.Add)
                            and isinstance(loop_body_stmt.target, ast.Name)
                            and loop_body_stmt.target.id == target_var):

                        if (isinstance(loop_body_stmt.value, ast.Name)
                                and isinstance(next_stmt.target, ast.Name)
                                and loop_body_stmt.value.id == next_stmt.target.id):
                            new_assign = ast.Assign(
                                targets=[ast.Name(id=target_var, ctx=ast.Store())],
                                value=ast.Call(
                                    func=ast.Name(id="sum", ctx=ast.Load()),
                                    args=[next_stmt.iter],
                                    keywords=[],
                                ),
                                lineno=stmt.lineno,
                            )
                            ast.fix_missing_locations(new_assign)
                            new_body.append(new_assign)
                            i += 2
                            self.transformations += 1
                            logger.debug(f"R003: Converted accumulation loop to sum() at line {stmt.lineno}")
                            continue
                        elif isinstance(next_stmt.target, ast.Name):
                            gen_exp = ast.GeneratorExp(
                                elt=loop_body_stmt.value,
                                generators=[
                                    ast.comprehension(
                                        target=next_stmt.target,
                                        iter=next_stmt.iter,
                                        ifs=[],
                                        is_async=0,
                                    )
                                ],
                            )
                            new_assign = ast.Assign(
                                targets=[ast.Name(id=target_var, ctx=ast.Store())],
                                value=ast.Call(
                                    func=ast.Name(id="sum", ctx=ast.Load()),
                                    args=[gen_exp],
                                    keywords=[],
                                ),
                                lineno=stmt.lineno,
                            )
                            ast.fix_missing_locations(new_assign)
                            new_body.append(new_assign)
                            i += 2
                            self.transformations += 1
                            logger.debug(f"R003: Converted expression accumulation loop to sum() at line {stmt.lineno}")
                            continue

            new_body.append(stmt)
            i += 1

        node.body = new_body
        self.generic_visit(node)
        return node


class FileIoHoistingRefactorer(ast.NodeTransformer):
    """
    R004: Hoists invariant file open/read outside loops.

    Reduces O(N) filesystem I/O calls to O(1).
    """

    def __init__(self):
        self.transformations = 0

    def visit_For(self, node: ast.For) -> ast.AST:
        if not node.body:
            self.generic_visit(node)
            return node

        first_stmt = node.body[0]
        if isinstance(first_stmt, ast.With) and len(first_stmt.items) == 1:
            with_item = first_stmt.items[0]
            if isinstance(with_item.context_expr, ast.Call):
                func = with_item.context_expr.func
                is_open = (isinstance(func, ast.Name) and func.id == "open") or (
                    isinstance(func, ast.Attribute) and func.attr == "open"
                )
                if is_open:
                    loop_var_ids = {n.id for n in ast.walk(node.target) if isinstance(n, ast.Name)}
                    call_arg_ids = {n.id for n in ast.walk(with_item.context_expr) if isinstance(n, ast.Name)}
                    if not (loop_var_ids & call_arg_ids):
                        hoisted_with = copy.deepcopy(first_stmt)
                        hoisted_with.body = [
                            s for s in first_stmt.body
                            if not any(isinstance(n, ast.Name) and n.id in loop_var_ids for n in ast.walk(s))
                        ]
                        if hoisted_with.body:
                            node.body = node.body[1:]
                            self.transformations += 1
                            logger.debug(f"R004: Hoisted invariant file I/O outside loop at line {first_stmt.lineno}")
                            self.generic_visit(node)
                            return [hoisted_with, node]

        self.generic_visit(node)
        return node


class EmptyLoopRefactorer(ast.NodeTransformer):
    """
    R007: Eliminates dead / busy-wait loops that contain only `pass`.
    """
    def __init__(self):
        self.transformations = 0

    def visit_For(self, node: ast.For) -> Optional[ast.AST]:
        self.generic_visit(node)
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            self.transformations += 1
            return None
        return node


def apply_all_refactoring_rules(tree: ast.Module) -> ast.Module:
    """
    Apply all refactoring rules to an AST tree sequentially.

    Each rule transforms the tree in-place and reports the number
    of transformations made.

    Args:
        tree: The parsed AST tree.

    Returns:
        The transformed AST tree.
    """
    tree = copy.deepcopy(tree)  # Don't modify the original

    total_transforms = 0

    # R001: Set conversion for membership checks
    r001 = SetConversionRefactorer()
    tree = r001.visit(tree)
    ast.fix_missing_locations(tree)
    total_transforms += r001.transformations

    # R002: String concatenation → join
    r002 = StringConcatRefactorer()
    tree = r002.visit(tree)
    ast.fix_missing_locations(tree)
    total_transforms += r002.transformations

    # R003: Loop accumulation → sum()
    r003 = BuiltinAggregationRefactorer()
    tree = r003.visit(tree)
    ast.fix_missing_locations(tree)
    total_transforms += r003.transformations

    # R004: Invariant file I/O hoisting
    r004 = FileIoHoistingRefactorer()
    tree = r004.visit(tree)
    ast.fix_missing_locations(tree)
    total_transforms += r004.transformations

    # R005: Append-in-loop → list comprehension
    r005 = ListComprehensionRefactorer()
    tree = r005.visit(tree)
    ast.fix_missing_locations(tree)
    total_transforms += r005.transformations

    # R007: Empty busy-wait loop elimination
    r007 = EmptyLoopRefactorer()
    tree = r007.visit(tree)
    ast.fix_missing_locations(tree)
    total_transforms += r007.transformations

    logger.info(f"Applied {total_transforms} AST transformation(s) across all rules")
    return tree
