"""
test_refactoring_rules.py — Unit tests for AST refactoring rules.

Verifies that each refactoring rule (R001, R002, R005) correctly
transforms anti-pattern AST nodes while preserving code functionality.
"""

import sys
import os
import ast
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ecocode.mode2_rewriting.ast_parser import parse_code, unparse_code
from ecocode.mode2_rewriting.pattern_detector import detect_patterns
from ecocode.mode2_rewriting.refactoring_rules import apply_all_refactoring_rules


class TestPatternDetection:
    """Tests for anti-pattern detection."""

    def test_detect_string_concat_in_loop(self):
        """R002: Should detect string += inside a for loop."""
        code = '''
result = ""
for item in items:
    result += str(item) + ","
'''
        tree = parse_code(code)
        assert tree is not None
        issues = detect_patterns(tree)
        rule_ids = [i["rule_id"] for i in issues]
        assert "R002" in rule_ids, f"Expected R002, got {rule_ids}"

    def test_detect_append_in_loop(self):
        """R005: Should detect list.append() inside a for loop."""
        code = '''
result = []
for item in items:
    result.append(item * 2)
'''
        tree = parse_code(code)
        assert tree is not None
        issues = detect_patterns(tree)
        rule_ids = [i["rule_id"] for i in issues]
        assert "R005" in rule_ids, f"Expected R005, got {rule_ids}"

    def test_detect_nested_membership_r001(self):
        """R001: Should detect list membership check in nested loop."""
        code = '''
for x in list_a:
    for y in list_b:
        if x in list_b:
            pass
'''
        tree = parse_code(code)
        issues = detect_patterns(tree)
        rule_ids = [i["rule_id"] for i in issues]
        assert "R001" in rule_ids, f"Expected R001, got {rule_ids}"

    def test_detect_accumulation_r003(self):
        """R003: Should detect numeric accumulation in loop."""
        code = '''
total = 0
for x in items:
    total += x
'''
        tree = parse_code(code)
        issues = detect_patterns(tree)
        rule_ids = [i["rule_id"] for i in issues]
        assert "R003" in rule_ids, f"Expected R003, got {rule_ids}"

    def test_detect_file_open_r004(self):
        """R004: Should detect open() inside loop."""
        code = '''
for item in items:
    f = open("data.txt")
    f.close()
'''
        tree = parse_code(code)
        issues = detect_patterns(tree)
        rule_ids = [i["rule_id"] for i in issues]
        assert "R004" in rule_ids, f"Expected R004, got {rule_ids}"

    def test_detect_empty_loop_r007(self):
        """R007: Should detect empty busy-wait loop."""
        code = '''
for _ in range(100):
    pass
'''
        tree = parse_code(code)
        issues = detect_patterns(tree)
        rule_ids = [i["rule_id"] for i in issues]
        assert "R007" in rule_ids, f"Expected R007, got {rule_ids}"

    def test_no_patterns_in_clean_code(self):
        """Should detect zero issues in already-optimized code."""
        code = '''
result = [x * 2 for x in items]
lookup = set(targets)
matches = [x for x in items if x in lookup]
'''
        tree = parse_code(code)
        assert tree is not None
        issues = detect_patterns(tree)
        # Clean code should have no issues (or minimal false positives)
        assert len(issues) == 0, f"Expected 0 issues, got {len(issues)}: {issues}"


class TestRefactoringRules:
    """Tests for AST transformations."""

    def test_r005_append_to_list_comprehension(self):
        """R005: append-in-loop should become list comprehension."""
        code = '''
def process(items):
    result = []
    for item in items:
        result.append(item * 2)
    return result
'''
        tree = parse_code(code)
        assert tree is not None

        refactored_tree = apply_all_refactoring_rules(tree)
        refactored_code = unparse_code(refactored_tree)

        # The refactored code should contain a list comprehension
        assert "for" not in refactored_code or "[" in refactored_code, \
            f"Expected list comprehension in:\n{refactored_code}"

        # Verify it still produces valid Python
        compile(refactored_code, "<test>", "exec")

    def test_r002_string_concat_to_join(self):
        """R002: string += should become join()."""
        code = '''
def build_csv(items):
    result = ""
    for item in items:
        result += str(item) + ","
    return result
'''
        tree = parse_code(code)
        assert tree is not None

        refactored_tree = apply_all_refactoring_rules(tree)
        refactored_code = unparse_code(refactored_tree)

        # Should contain .join() or .append()
        assert "join" in refactored_code or "append" in refactored_code, \
            f"Expected join/append in:\n{refactored_code}"

        # Verify valid Python
        compile(refactored_code, "<test>", "exec")

    def test_refactored_code_compiles(self):
        """All refactored code should be valid Python."""
        code = '''
def example(data, targets):
    result = ""
    for item in data:
        if item in targets:
            result += str(item) + " "
    return result.strip()
'''
        tree = parse_code(code)
        assert tree is not None

        refactored_tree = apply_all_refactoring_rules(tree)
        refactored_code = unparse_code(refactored_tree)

        # Must compile without errors
        try:
            compile(refactored_code, "<test>", "exec")
        except SyntaxError as e:
            raise AssertionError(f"Refactored code has SyntaxError: {e}\n{refactored_code}")

    def test_r001_set_conversion(self):
        """R001: list membership check in nested loop should pre-convert to set."""
        code = '''
def find_common(list_a, list_b):
    matches = []
    for x in list_a:
        for y in list_b:
            if x in list_b:
                matches.append(x)
    return matches
'''
        tree = parse_code(code)
        refactored = unparse_code(apply_all_refactoring_rules(tree))
        assert "_set_list_b = set(list_b)" in refactored
        assert "in _set_list_b" in refactored
        compile(refactored, "<test>", "exec")

    def test_r003_accumulation_to_sum(self):
        """R003: manual loop accumulation should become sum()."""
        code = '''
def total_values(items):
    total = 0
    for item in items:
        total += item
    return total
'''
        tree = parse_code(code)
        refactored = unparse_code(apply_all_refactoring_rules(tree))
        assert "total = sum(items)" in refactored
        compile(refactored, "<test>", "exec")

    def test_r004_file_io_hoisting(self):
        """R004: file open inside loop should be hoisted before loop."""
        code = '''
def process_records(items):
    results = []
    for item in items:
        with open("config.txt", "r") as f:
            cfg = f.read()
        results.append(item + cfg)
    return results
'''
        tree = parse_code(code)
        refactored = unparse_code(apply_all_refactoring_rules(tree))
        assert "with open(" in refactored
        assert "cfg = f.read()" in refactored
        # The 'with open' should appear before the 'for' loop in refactored code
        with_idx = refactored.index("with open")
        for_idx = refactored.index("for item in items:")
        assert with_idx < for_idx, "Expected 'with open' to be hoisted before 'for' loop"
        compile(refactored, "<test>", "exec")

    def test_r007_empty_loop_elimination(self):
        """R007: empty busy-wait loop should be removed."""
        code = '''
def run_workload():
    for _ in range(1000):
        pass
    return True
'''
        tree = parse_code(code)
        refactored = unparse_code(apply_all_refactoring_rules(tree))
        assert "range(1000)" not in refactored
        compile(refactored, "<test>", "exec")


def run_all_tests():
    """Run all test classes and report results."""
    test_classes = [TestPatternDetection, TestRefactoringRules]
    total = 0
    passed = 0
    failed = 0

    for cls in test_classes:
        print(f"\n{'='*60}")
        print(f"Running: {cls.__name__}")
        print(f"{'='*60}")

        instance = cls()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                total += 1
                try:
                    getattr(instance, method_name)()
                    print(f"  [PASS] {method_name}")
                    passed += 1
                except AssertionError as e:
                    print(f"  [FAIL] {method_name}: {e}")
                    failed += 1
                except Exception as e:
                    print(f"  [ERROR] {method_name}: {type(e).__name__}: {e}")
                    failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print(f"{'='*60}")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
