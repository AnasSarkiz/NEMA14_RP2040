"""Recognize only the reviewed passive-orientation diagnostic class.

A placement summary alone cannot qualify the log: the same command can also
report real placement DRC failures. Unknown diagnostics require review.
"""
import re


def orientation_advisories_only(log):
    summary = re.match(r"placement summary: (\d+) suboptimal orientations\n", log)
    if not summary or not re.search(r"placement drc:\s*Errors: 0\s*Warnings: 0\s*$", log):
        return False
    count = int(summary.group(1))
    if count <= 0 or "worst issues:\n" not in log or "board top-layer utilization:" not in log:
        return False
    issues = log.split("worst issues:\n", 1)[1].split("board top-layer utilization:", 1)[0]
    rows = [row.strip() for row in issues.splitlines() if row.strip()]
    pattern = r"\d+\. ([A-Za-z0-9_]+) connections cross the routing path between its pads\. Suggested move: rotate \1 180 degrees\."
    return len(rows) == count and all(re.fullmatch(pattern, row) for row in rows)
