#!/usr/bin/env python3
"""Measure resume fit: page count, column margins, bullet line usage, and the
gap inside two-column heading rows.

Usage:
    python check.py out/some_resume.pdf
    python check.py out/some_resume.pdf --debug     # dump raw line geometry

Exit status is 0 only when the PDF is exactly one page, every bullet is OK, and
no heading row is COLLIDE or TIGHT, so this can gate an iteration loop.
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter
from dataclasses import dataclass, field

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("PyMuPDF is required: pip install pymupdf")


# A bullet label is a lone glyph sitting left of the text column. Jake's
# template uses itemize's default label, which extracts as U+2022 when
# glyphtounicode is loaded and as the raw CMSY slot when it is not.
# Dashes are deliberately excluded: an em-dash can legitimately begin a wrapped
# line, and this template's label is verified to be U+2022 (CMSY6).
BULLET_GLYPHS = {"•", "‣", "◦", "∙", "·", "●", "▪", "⁃", "■", "*", "\x0f"}

SHORT_THRESHOLD = 0.90   # last line must reach >= 90% of column width
MAX_LINES = 2            # a bullet may occupy at most 2 lines
COORD_TOL = 1.5          # pt; tolerance when comparing x-coordinates
BASELINE_TOL = 2.5       # pt; spans this close in baseline are one visual line
HANG_MIN = 3.0           # pt; a label must sit at least this far left of its text

# Heading rows are tabular* rows of the form {l@{\extracolsep{\fill}}r}: left
# content and a right-aligned date. When the left cell grows too wide the fill
# glue collapses to nothing and the two cells butt together.
GAP_COLLIDE = 8.0        # pt; below this the cells have visibly run together
GAP_TIGHT = 20.0         # pt; below this it still looks cramped — warn early
MAX_HEADING_RUN = 2      # \resumeSubheading emits 2 rows, \resumeProjectHeading 1
EDGE_TOL = 3.0           # pt; slack when testing whether a row reaches the edge


@dataclass
class Line:
    page: int
    y: float
    label_x0: float | None   # x0 of the bullet glyph, if this line carries one
    label: str               # the glyph itself, for --debug
    x0: float                # x0 of the first real text on the line
    x1: float                # x1 of the line's rightmost text
    text: str
    parts: list[tuple[float, float, str]]  # (x0, x1, text) per span, left to right

    @property
    def is_bullet_start(self) -> bool:
        return self.label_x0 is not None


@dataclass
class Heading:
    """A two-column tabular* row: left content, fill glue, right-aligned date."""
    page: int
    left_text: str
    right_text: str
    gap: float               # pt of clear space between the two cells
    x1: float
    text: str                # whole row, for when a collision makes the split meaningless


@dataclass
class Bullet:
    lines: list[Line] = field(default_factory=list)

    @property
    def n_lines(self) -> int:
        return len(self.lines)

    @property
    def text(self) -> str:
        return " ".join(l.text for l in self.lines)

    @property
    def last_x1(self) -> float:
        return self.lines[-1].x1

    @property
    def page(self) -> int:
        return self.lines[0].page


def extract_lines(doc: fitz.Document) -> list[Line]:
    """Flatten the document into visual text lines with geometry, in reading order.

    PyMuPDF splits one visual line into several "line" dicts whenever the font
    changes mid-line or a baseline shifts slightly (e.g. \\texttt{} fragments,
    or a \\quad-separated bold run). Those fragments must be recombined before
    any x-measurement, or a line's true right edge is understated and its
    wrapped continuations get orphaned.

    Spans are regrouped by *baseline* (span["origin"][1]), not by bbox top:
    every span typeset on one line shares an exact baseline regardless of
    glyph height, while bbox tops vary with ascenders and font size.
    """
    lines: list[Line] = []
    for pno, page in enumerate(doc, start=1):
        spans: list[dict] = []
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:  # skip images
                continue
            for line in block["lines"]:
                spans.extend(s for s in line["spans"] if s["text"].strip())

        # Reading order: top to bottom, then left to right. The bullet label is
        # \vcenter-ed, so its baseline sits ~1.3pt above its text's; sorting by
        # baseline therefore places the label first in its own line's group.
        spans.sort(key=lambda s: (round(s["origin"][1], 2), s["bbox"][0]))

        for group in group_by_baseline(spans):
            lines.append(build_line(pno, group))

    return lines


def group_by_baseline(spans: list[dict]) -> list[list[dict]]:
    """Bucket baseline-sorted spans into visual lines."""
    groups: list[list[dict]] = []
    for span in spans:
        y = span["origin"][1]
        if groups and abs(y - groups[-1][0]["origin"][1]) <= BASELINE_TOL:
            groups[-1].append(span)
        else:
            groups.append([span])
    for g in groups:
        g.sort(key=lambda s: s["bbox"][0])
    return groups


def build_line(pno: int, group: list[dict]) -> Line:
    """Split a visual line into an optional bullet label plus its body text."""
    label_x0: float | None = None
    label = ""
    body = group

    first = group[0]["text"].strip()
    if len(first) == 1 and first in BULLET_GLYPHS and len(group) > 1:
        # Only a glyph hanging clearly left of the following text is a label;
        # a lone dash or bullet flush with the text is just punctuation.
        if group[1]["bbox"][0] - group[0]["bbox"][0] >= HANG_MIN:
            label_x0 = group[0]["bbox"][0]
            label = first
            body = group[1:]

    return Line(
        page=pno,
        y=group[0]["origin"][1],
        label_x0=label_x0,
        label=label,
        x0=body[0]["bbox"][0],
        x1=max(s["bbox"][2] for s in body),
        text=" ".join(s["text"] for s in body).strip(),
        parts=[(s["bbox"][0], s["bbox"][2], s["text"]) for s in body],
    )


def infer_column(lines: list[Line]) -> tuple[float, float, str, int]:
    """Infer the text column's left and right edge from line geometry."""
    if not lines:
        sys.exit("No text lines found in PDF.")

    # Left edge: the most common line start. Bullet body text dominates the
    # document, so the mode is the hanging indent the wrapped text aligns to.
    left_counts = Counter(round(l.x0 * 2) / 2 for l in lines)
    left = left_counts.most_common(1)[0][0]

    # Right edge: the template sets \raggedright, so line ends are NOT flush
    # and their mode is meaningless. The widest line in the document is the
    # tightest lower bound on where LaTeX actually breaks.
    body = [l for l in lines if abs(l.x0 - left) <= COORD_TOL]
    ends = sorted((l.x1 for l in body), reverse=True)
    if not ends:
        sys.exit("Could not identify any body text lines.")

    # Guard against a single overhanging outlier: require corroboration before
    # trusting the widest line, and only discount it when there are enough
    # samples for the percentile to actually name a different line.
    support = sum(1 for e in ends if e >= ends[0] - 2.0)
    idx = int(len(ends) * 0.02)
    if support < 3 and idx > 0:
        right = ends[idx]
        method = (
            f"98th percentile of {len(ends)} body-line right edges "
            f"— the widest ({ends[0]:.1f}pt) was an unsupported outlier"
        )
    else:
        right = ends[0]
        method = f"widest of {len(ends)} body lines ({support} within 2pt of it)"

    return left, right, method, support


def group_bullets(lines: list[Line], left: float) -> list[Bullet]:
    """Group lines into bullets: a glyph starts one, aligned lines continue it."""
    bullets: list[Bullet] = []
    cur: Bullet | None = None
    for line in lines:
        if line.is_bullet_start:
            cur = Bullet(lines=[line])
            bullets.append(cur)
        elif cur is not None and abs(line.x0 - left) <= COORD_TOL:
            cur.lines.append(line)   # wrapped continuation
        else:
            cur = None               # heading / section rule ends the bullet
    return bullets


def find_headings(lines: list[Line], bullet_left: float) -> list[Heading]:
    """Locate two-column heading rows and measure the gap between their cells.

    Three filters, because geometry alone is not enough. The Technical Skills
    block sits at the same indent as heading rows and its lines also have only
    word-sized internal gaps, so it looks identical to a collided heading:

    1. Indent — a heading row starts at the subheading indent, left of the
       bullet column and right of the section-title indent.
    2. Run length — \\resumeSubheading emits exactly 2 rows and
       \\resumeProjectHeading exactly 1, and bullets always separate entries.
       A run of 3+ consecutive lines at that indent is therefore a wrapped
       paragraph (the skills block), not headings.
    3. Right edge — a two-cell row's date is right-aligned to the tabular edge,
       so it reaches that edge (or overruns it when the row is overfull).
       Single-cell rows stop short and are dropped.
    """
    outer = [l for l in lines if not l.is_bullet_start and abs(l.x0 - bullet_left) > COORD_TOL]
    if not outer:
        return []
    head_left = Counter(round(l.x0 * 2) / 2 for l in outer).most_common(1)[0][0]

    # Maximal runs of consecutive lines sitting at the heading indent.
    candidates: list[Line] = []
    run: list[Line] = []
    for line in lines + [None]:  # sentinel flushes the final run
        if line is not None and abs(line.x0 - head_left) <= COORD_TOL:
            run.append(line)
            continue
        if run and len(run) <= MAX_HEADING_RUN:
            candidates.extend(run)
        run = []

    if not candidates:
        return []

    # The right-aligned cells all land on the tabular edge, so the median is a
    # stable estimate even if one row is overfull and overshoots it.
    edge = statistics.median(l.x1 for l in candidates)

    headings: list[Heading] = []
    for line in candidates:
        if line.x1 < edge - EDGE_TOL:
            continue
        headings.append(split_cells(line))
    return headings


def split_cells(line: Line) -> Heading:
    """Split a heading row at its widest inter-span gap — the fill column."""
    gaps = [
        (line.parts[i + 1][0] - line.parts[i][1], i)
        for i in range(len(line.parts) - 1)
    ]
    if gaps:
        gap, idx = max(gaps)
        left = " ".join(p[2] for p in line.parts[: idx + 1]).strip()
        right = " ".join(p[2] for p in line.parts[idx + 1 :]).strip()
    else:
        gap, left, right = 0.0, line.text, ""
    return Heading(
        page=line.page, left_text=left, right_text=right,
        gap=gap, x1=line.x1, text=line.text,
    )


def classify_heading(h: Heading) -> str:
    if h.gap < GAP_COLLIDE:
        return "COLLIDE"
    if h.gap < GAP_TIGHT:
        return "TIGHT"
    return "OK"


def classify(bullet: Bullet, fill: float) -> str:
    flags = []
    if bullet.n_lines > MAX_LINES:
        flags.append("LONG")
    if fill < SHORT_THRESHOLD:
        flags.append("SHORT")
    return "+".join(flags) if flags else "OK"


def opening(text: str, width: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 1].rstrip() + "…"


def main() -> int:
    ap = argparse.ArgumentParser(description="Resume fit checker.")
    ap.add_argument("pdf", help="path to the compiled resume PDF")
    ap.add_argument("--debug", action="store_true", help="dump raw line geometry")
    args = ap.parse_args()

    try:
        doc = fitz.open(args.pdf)
    except Exception as exc:
        sys.exit(f"Could not open {args.pdf}: {exc}")

    pages = doc.page_count
    lines = extract_lines(doc)

    if args.debug:
        print("--- visual lines (page, y, label, x0, x1, text) ---")
        for l in lines:
            lab = f"{l.label!r}@{l.label_x0:.2f}" if l.label_x0 is not None else "-"
            print(f"p{l.page} y={l.y:7.2f} lab={lab:<12} x0={l.x0:7.2f} x1={l.x1:7.2f}  {opening(l.text, 58)}")
        print()

    left, right, method, support = infer_column(lines)
    width = right - left

    print(f"FILE       {args.pdf}")
    print(f"PAGES      {pages}" + ("" if pages == 1 else "   <-- must be exactly 1"))
    print(f"COLUMN     left={left:.1f}pt  right={right:.1f}pt  width={width:.1f}pt")
    print(f"           right edge inferred as {method}")
    if support < 3:
        # Too few lines reach the boundary to pin it down; the column may be
        # narrower than measured, which would overstate every fill percentage.
        print("           NOTE: few lines reach the right edge — fills may read high")

    bullets = group_bullets(lines, left)
    if not bullets:
        print("\nNo bullets detected — the extraction rule did not match this PDF.")
        print("Re-run with --debug to inspect the line geometry.")
        return 1

    rows = []
    for b in bullets:
        fill = (b.last_x1 - left) / width
        rows.append((b, fill, classify(b, fill)))

    print(f"\n{'#':>3}  {'LN':>2}  {'FILL':>6}  {'FLAG':<10}  BULLET")
    print("-" * 100)
    for i, (b, fill, flag) in enumerate(rows, start=1):
        marker = " " if flag == "OK" else "!"
        print(f"{i:>3}  {b.n_lines:>2}  {fill*100:5.1f}%  {flag:<10}{marker} {opening(b.text, 62)}")

    flagged = [(i, b, fill, flag) for i, (b, fill, flag) in enumerate(rows, start=1) if flag != "OK"]
    n_long = sum(1 for _, _, _, f in flagged if "LONG" in f)
    n_short = sum(1 for _, _, _, f in flagged if "SHORT" in f)

    print("-" * 100)
    print(f"{len(bullets)} bullets: {len(bullets) - len(flagged)} OK, {n_long} LONG, {n_short} SHORT")

    headings = find_headings(lines, left)
    head_rows = [(h, classify_heading(h)) for h in headings]
    bad_heads = [(i, h, f) for i, (h, f) in enumerate(head_rows, start=1) if f != "OK"]

    print(f"\n{'#':>3}  {'GAP':>7}  {'FLAG':<9}  HEADING (left cell | right cell)")
    print("-" * 100)
    for i, (h, flag) in enumerate(head_rows, start=1):
        marker = " " if flag == "OK" else "!"
        # Once the cells touch, the widest gap is just a word space, so the
        # left/right split is arbitrary — show the row as it actually renders.
        cells = (opening(h.text, 78) if flag == "COLLIDE"
                 else f"{opening(h.left_text, 50)}  |  {opening(h.right_text, 24)}")
        print(f"{i:>3}  {h.gap:6.1f}pt  {flag:<9}{marker} {cells}")
    print("-" * 100)
    n_collide = sum(1 for _, _, f in bad_heads if f == "COLLIDE")
    n_tight = sum(1 for _, _, f in bad_heads if f == "TIGHT")
    print(f"{len(head_rows)} headings: {len(head_rows) - len(bad_heads)} OK, "
          f"{n_collide} COLLIDE, {n_tight} TIGHT")

    ok = pages == 1 and not flagged and not bad_heads
    if ok:
        print("\nPASS — one page, no bullet or heading flagged.")
        return 0

    print("\nFAIL")
    if pages != 1:
        print(f"  - page count is {pages}, must be exactly 1")
    for i, b, fill, flag in flagged:
        why = []
        if "LONG" in flag:
            why.append(f"{b.n_lines} lines (max {MAX_LINES})")
        if "SHORT" in flag:
            why.append(f"last line {fill*100:.1f}% of column (min {SHORT_THRESHOLD*100:.0f}%)")
        print(f"  - #{i:<3} {'; '.join(why):<52} {opening(b.text, 40)}")
    for i, h, flag in bad_heads:
        limit = GAP_COLLIDE if flag == "COLLIDE" else GAP_TIGHT
        why = f"heading gap {h.gap:.1f}pt (min {limit:.0f}pt) — shorten the tech list"
        print(f"  - H{i:<2} {why:<52} {opening(h.text, 40)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
