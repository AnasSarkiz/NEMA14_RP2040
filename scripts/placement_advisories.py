"""Accept only complete, recognized passive-orientation diagnostics with clean DRC."""
import re

ISSUE = r'([A-Za-z0-9_]+) connections cross the routing path between its pads\. Suggested move: rotate \1 180 degrees\.'
NUMBER = r'-?\d+(?:\.\d+)?'

def orientation_advisories_only(log):
    header = re.match(r'placement summary: (\d+) suboptimal orientations\n\s*worst issues:\n', log)
    footer = re.search(r'\nplacement drc:\nErrors: 0\nWarnings: 0\s*$', log)
    if not header or not footer:
        return False
    count = int(header.group(1))
    if count <= 0:
        return False
    try:
        worst, rest = log[header.end():footer.start()].split('\nboard top-layer utilization:\n', 1)
        utilization, rest = rest.split('\nboard-edge status:\n', 1)
        edges, flagged = rest.split('\nflagged components:\n', 1)
    except ValueError:
        return False
    rows = [s.strip() for s in worst.splitlines() if s.strip()]
    matches = [re.fullmatch(r'\d+\. ' + ISSUE, s) for s in rows]
    if len(rows) != min(count, 5) or not all(matches):
        return False
    utilization_rows = [s for s in utilization.splitlines() if s.strip()]
    if not utilization_rows or not re.fullmatch(r'- occupied: '+NUMBER+r'% \('+NUMBER+r'mm\^2 of '+NUMBER+r'mm\^2\)', utilization_rows[0]):
        return False
    if utilization_rows[1:] != ['- empty spaces over 5% of board area: none']:
        if len(utilization_rows) < 3 or utilization_rows[1] != '- empty spaces over 5% of board area:':
            return False
        # Empty board regions are informational utilization data. Accept only
        # the complete native numeric format; all actual issues remain checked.
        empty_region = r'  - ('+NUMBER+r')% \(('+NUMBER+r')mm\^2\); bounds=\(minX=('+NUMBER+r')mm, maxX=('+NUMBER+r')mm, minY=('+NUMBER+r')mm, maxY=('+NUMBER+r')mm\)'
        for row in utilization_rows[2:]:
            m = re.fullmatch(empty_region, row)
            if not m:
                return False
            percent, area, min_x, max_x, min_y, max_y = map(float, m.groups())
            if not (5 < percent <= 100 and area > 0 and min_x < max_x and min_y < max_y):
                return False
    edge_rows = [s for s in edges.splitlines() if s.strip()]
    if not edge_rows or any(not re.fullmatch(r'- [A-Za-z0-9_]+: \d+(?:\.\d+)?mm inside (top|bottom|left|right) edge', s) for s in edge_rows):
        return False
    blocks = re.split(r'(?m)(?=^- [A-Za-z0-9_]+$)', flagged.strip())
    refs = []
    for block in blocks:
        if not block.strip():
            continue
        lines = [s for s in block.splitlines() if s.strip()]
        if len(lines) != 6 or not re.fullmatch(r'- [A-Za-z0-9_]+', lines[0]):
            return False
        ref = lines[0][2:]
        if lines[1] != '  source placement: placement_mode=none' or not re.fullmatch(r'  resolved placement: center=\('+NUMBER+r'mm, '+NUMBER+r'mm\) on (top|bottom); bounds=\(minX='+NUMBER+r'mm, maxX='+NUMBER+r'mm, minY='+NUMBER+r'mm, maxY='+NUMBER+r'mm\); size=\(width='+NUMBER+r'mm, height='+NUMBER+r'mm\); anchor_alignment="center"', lines[2]) or not re.fullmatch(r'  board edge status: \d+(?:\.\d+)?mm inside (top|bottom|left|right) edge', lines[3]) or lines[4] != '  issues:':
            return False
        issue = re.fullmatch(r'  - '+ISSUE, lines[5])
        if not issue or issue.group(1) != ref:
            return False
        refs.append(ref)
    return len(refs) == count and len(set(refs)) == count and all(m.group(1) in refs for m in matches)
