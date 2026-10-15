"""
Sample unoptimized code for Mode 2 testing.
Contains deliberate anti-patterns that EcoCode should detect and fix.
"""


def find_duplicates(nums):
    """Find all duplicate elements in a list - UNOPTIMIZED VERSION."""
    # R005: append-in-loop anti-pattern (could be list comprehension)
    # R001-like: nested loop with O(n^2) approach
    duplicates = []
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] == nums[j] and nums[i] not in duplicates:
                duplicates.append(nums[i])
    return sorted(duplicates)
