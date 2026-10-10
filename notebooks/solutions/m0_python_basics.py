"""Milestone 0 answer key - loops, edge cases, dicts and Big-O."""

from __future__ import annotations


def count_positives(nums):
    """A running count is just a variable you update inside the loop."""
    count = 0
    for n in nums:
        if n > 0:
            count += 1
    return count


def largest(nums):
    """Guard the empty case first, then start best at a real item, not 0.

    Starting at 0 is the classic bug: it silently returns 0 for an all-negative
    list, which is exactly what the edge-case test is there to catch.
    """
    if not nums:
        return None
    best = nums[0]
    for n in nums[1:]:
        if n > best:
            best = n
    return best


def word_counts(words):
    """``.get(word, 0)`` gives the old count even for a word not seen yet."""
    counts = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    return counts


def has_duplicate(nums):
    """One pass with a set: each ``in`` check is O(1), so the whole thing is O(n)."""
    seen = set()
    for n in nums:
        if n in seen:
            return True
        seen.add(n)
    return False
