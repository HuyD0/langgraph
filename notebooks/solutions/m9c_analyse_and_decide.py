"""Milestone 9c answer key - flaky questions, and regressions and improvements."""

from __future__ import annotations


def flaky(run0, run1):
    """Questions whose result differs between two runs of the same version: noise, not evidence."""
    return sorted(qid for qid in run0 if run0[qid] != run1[qid])


def changes(old, new):
    """Questions the new version got right that the old didn't (improvements), and the reverse (regressions)."""
    improvements = sorted(qid for qid in old if new[qid] and not old[qid])
    regressions = sorted(qid for qid in old if old[qid] and not new[qid])
    return {"improvements": improvements, "regressions": regressions}
