#!/usr/bin/env python3
"""Measure resume fit: page count, column margins, bullet line usage, how close
each bullet's last line comes to the column edge, the gap inside two-column
heading rows, whether any Technical Skills category wraps, and how much empty
page is left at the bottom.

Usage:
    python check.py out/some_resume.pdf
    python check.py out/some_resume.pdf --brief     # drop the all-OK tables
    python check.py out/some_resume.pdf --debug     # dump raw line geometry

Exit status is 0 only when the PDF is exactly one page, every bullet is OK, no
heading row is COLLIDE or TIGHT, no skills category is WRAPPED, no ATS parsing
rule is violated, and at most one further line would fit beneath the last one,
so this can gate an iteration loop.
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

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

# A bullet's last line must stop at least this far short of the column edge.
# A last line that lands flush has no room for its own trailing space, so that
# space and the \vspace{-2pt} closing \resumeItem break onto a line of their
# own: invisible in the extracted text, but ~11pt of dead vertical gap before
# the next bullet, against a normal bullet-to-bullet step of ~13pt. One
# interword space at \small is ~3pt, so this is that floor plus slack.
# Only the *last* line is tested — a wrapped line reaching the margin is just
# an ordinary line break and is what the 90% fill rule is asking for.
FLUSH_MIN = 4.0          # pt
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

# Bottom fill. The preamble pins the text block to a known place on letterpaper:
# fullpage's 1in margins, then \topmargin -0.5in and \textheight +1.0in, leaving
# text to run from 36pt to 756pt down the 792pt page. Everything below the last
# baseline is unused page, and a gap deep enough for two more lines reads as a
# resume that ran out of things to say.
TEXT_BOTTOM = 756.0
MAX_SPARE_LINES = 1      # at most this many further body lines may fit beneath
PITCH_MIN, PITCH_MAX = 8.0, 16.0   # plausible body line pitch, for the median

# Technical Skills (INSTRUCTIONS.md fit rule 5). The block is an itemize with an
# empty label, so its lines sit at the heading indent — find_headings() already
# skips them, since a run of 3+ lines there is a wrapped paragraph rather than
# heading rows. Each category must render on exactly one line: a category that
# wraps reads as an undifferentiated dump and spends a body line the page needs
# for real content. Categories are found by their bold "Label:" prefix, so any
# line without one is a continuation of the category above it.
SKILLS_TITLE = "technical skills"
CATEGORY_RE = re.compile(r"^[A-Z][\w&/. -]{0,28}\s*:")
MAX_SKILL_LINES = 1      # a category may occupy at most this many lines

# Title adaptation (INSTRUCTIONS.md). Huang Climate Lab renders as "Software
# Engineer (UTRA)" by default; the specialist title is only earned by a JD whose
# role actually builds ML. "AI", "artificial intelligence", "AI literacy" and
# "prompt engineering" are deliberately absent from this list — they describe
# using AI tools, and treating them as ML content is the exact mistake that put
# the specialist title on a general software engineering JD.
SPECIALIST_TITLE = "Machine Learning Engineer"

# ATS parsing (INSTRUCTIONS.md, "ATS parsing"). The tabular* rows carry no
# column structure into the text layer -- a parser sees two runs sharing a
# baseline and has to guess where the left cell ends and what the right one is.
# It guesses well on date-shaped runs and badly on everything else, so these
# rules keep every right-hand cell to a shape it can recognise. Each one is
# here because a real submission was mangled by it.
#
# A \resumeSubheading emits a pair of rows: {Organization}{Location} then
# {Title}{Dates}. Row 1's right cell must therefore be a location and row 2's
# a date range; the reverse means the body was written title-first, which puts
# an organization-plus-location pair -- the exact shape of a new job header --
# on the second line of every entry.
LOCATION_RE = re.compile(
    r"^[A-Z][\w.'&-]*(?: [A-Z][\w.'&-]*)*,\s*(?:[A-Z]{2}|UK|USA|Canada)$"
)
MONTH = (r"January|February|March|April|May|June|July|August|September|"
         r"October|November|December")
DASH = r"[-\u2010-\u2015]+"   # hyphen, en/em dash, or the `--` LaTeX writes
DATERANGE_RE = re.compile(
    rf"^(?:(?:{MONTH})\s+)?\d{{4}}\s*{DASH}\s*"
    rf"(?:Present|(?:(?:{MONTH})\s+)?\d{{4}})$|"
    rf"^(?:{MONTH})\s*{DASH}\s*(?:{MONTH})\s+\d{{4}}$|"
    rf"^(?:{MONTH})\s+\d{{4}}$",
    re.IGNORECASE,
)
# "Sep. 2024" -- the period reads as a sentence terminator and truncates the
# range to a single date, which the parser then mirrors into both year fields.
ABBREV_MONTH_RE = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\.", re.IGNORECASE
)
# Field of Study is a controlled picklist; a conjunction matches no entry and
# the parser will not split it to pick a winner, so the field comes back empty.
# A glyph with no ToUnicode entry extracts as a control character or U+FFFD:
# invisible on the page, garbage to a parser. \textrightarrow was the one that
# bit -- it resolves through TS1, whose font is not installed as Type1 here, so
# pdflatex embeds a Type3 bitmap that carries no mapping at all, and every
# "87\u219223 min" metric reached the ATS as "8723 min". Use $\rightarrow$
# (CMSY10, Type1, already declared in glyphtounicode.tex) instead.
UNMAPPED_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\ufffd]")

DEGREE_CONJ_RE = re.compile(r"^(?:Bachelor|Master|Associate)\b.*\band\b")
#
# The LLM terms below are here because INSTRUCTIONS.md counts "inference or
# agent systems" as building ML: a role whose core requirement is integrating
# LLMs into backend services — RAG pipelines, tool-using agents, model serving
# — is engineering inference, not merely using an AI tool. Every one of them
# names the *building*, which is what makes them safe to match on.
#
# Bare "llm", "large language model" and "agentic" are deliberately absent, for
# the same reason as "AI" and "prompt engineering": the Roblox SWE JD says it
# experiments with "agentic coding tools, and large language models (LLMs)",
# and it is a general software engineering role. Matching those would hand the
# specialist title to exactly the JD this rule was written to refuse.
#
# Bare "rag" and bare "agent" are absent for a second reason: matching is
# substring, and "rag" is inside "storage" and "average" while "agent" is
# inside "user agent", so either would fire on JDs with no AI content at all.
ML_ROLE_TERMS = (
    "machine learning", "deep learning", "neural network", "ml engineer",
    "ml model", "model training", "model inference", "pytorch", "tensorflow",
    "scikit-learn", "computer vision", "natural language processing",
    "data scientist", "reinforcement learning", "recommender",
    "llm-powered", "llm inference", "llm serving", "integrating llms",
    "rag pipeline", "retrieval-augmented", "tool-using agent", "ai agent",
    "multi-agent", "model serving",
)


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
    row: int = 0             # 0-based position within its heading run
    run_len: int = 1         # 1 for \resumeProjectHeading, 2 for \resumeSubheading


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

    # Re-walk the runs so each surviving row knows its position within the
    # \resumeSubheading pair it came from -- the ATS rules below are about
    # which cell type belongs on which of the two rows.
    headings: list[Heading] = []
    keep = {id(l) for l in candidates if l.x1 >= edge - EDGE_TOL}
    run = []
    for line in lines + [None]:
        if line is not None and abs(line.x0 - head_left) <= COORD_TOL:
            run.append(line)
            continue
        if run and len(run) <= MAX_HEADING_RUN:
            kept = [l for l in run if id(l) in keep]
            for i, l in enumerate(kept):
                h = split_cells(l)
                h.row, h.run_len = i, len(kept)
                headings.append(h)
        run = []
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


def check_glyphs(doc: fitz.Document) -> list[tuple[str, str, str]]:
    """Find text that reaches the text layer as unmappable glyphs.

    The page can look perfect while the extracted text an ATS reads is
    corrupt, so this reads what a parser reads rather than what renders.
    """
    bad: list[tuple[str, str, str]] = []
    for page in doc:
        for raw in page.get_text().splitlines():
            m = UNMAPPED_RE.search(raw)
            if not m:
                continue
            bad.append((
                "GLYPH", raw.strip(),
                f"U+{ord(m.group()):04X} has no ToUnicode entry -- it is "
                "invisible to a parser; use a Type1 equivalent "
                "($\\rightarrow$) or declare \\pdfglyphtounicode",
            ))
    return bad


def check_ats(headings: list[Heading]) -> list[tuple[str, str, str]]:
    """Check every heading row against the ATS parsing rules.

    Returns (flag, cell, why) triples, one per violation. Only paired rows --
    the two a \\resumeSubheading emits -- are checked for cell order, since a
    lone \\resumeProjectHeading row is a project and carries a tech stack, not
    an organization. Parentheticals are likewise an experience-heading problem:
    a parser promotes `Title (ACRONYM)` to a separate employer.
    """
    bad: list[tuple[str, str, str]] = []
    for h in headings:
        for cell in (h.left_text, h.right_text):
            if ABBREV_MONTH_RE.search(cell):
                bad.append((
                    "ABBREV", cell,
                    "abbreviated month -- the period truncates the range to a "
                    "single date; spell the month out in full",
                ))
        if h.run_len < 2:
            continue                      # a project heading: no org, no dates
        if h.row == 0:
            if DATERANGE_RE.match(h.right_text.strip()):
                bad.append((
                    "ORDER", h.text,
                    "dates on row 1 -- the body was written title-first; call "
                    "\\resumeSubheading as {Organization}{Location}{Title}{Dates}",
                ))
            elif not LOCATION_RE.match(h.right_text.strip()):
                bad.append((
                    "LOCATION", h.right_text,
                    "not City, ST or City, Country -- it fails the location "
                    "validator and falls through into the description block",
                ))
            if DEGREE_CONJ_RE.match(h.left_text.strip()):
                bad.append((
                    "DEGREE", h.left_text,
                    'a conjunction matches no Field of Study picklist entry -- '
                    "hyphenate the concentration name",
                ))
        else:
            if not DATERANGE_RE.match(h.right_text.strip()):
                bad.append((
                    "DATES", h.right_text,
                    "row 2's right cell is not a date range -- check the "
                    "\\resumeSubheading argument order",
                ))
            if DEGREE_CONJ_RE.match(h.left_text.strip()):
                bad.append((
                    "DEGREE", h.left_text,
                    'a conjunction matches no Field of Study picklist entry -- '
                    "hyphenate the concentration name",
                ))
        if "(" in h.left_text:
            bad.append((
                "PAREN", h.left_text,
                "a parenthetical in an organization or title cell is promoted "
                "to a separate employer -- move the detail into a bullet",
            ))
    return bad


def find_skills(lines: list[Line]) -> list[list[Line]]:
    """Group the Technical Skills block into categories, one line list each.

    Everything after the section title belongs to the block: Technical Skills is
    the last section the template emits, so there is nothing below it to stop
    at. A line carrying a bold "Label:" prefix opens a category and every line
    after it without one is that category wrapping.
    """
    start = next(
        (i + 1 for i, l in enumerate(lines)
         if l.text.strip().rstrip(":").lower() == SKILLS_TITLE),
        None,
    )
    if start is None:
        return []

    cats: list[list[Line]] = []
    for line in lines[start:]:
        if CATEGORY_RE.match(line.text.strip()):
            cats.append([line])
        elif cats:
            cats[-1].append(line)
    return cats


def measure_tail(lines: list[Line]) -> tuple[float, float, float]:
    """Return (last baseline, body line pitch, spare lines) for the final page.

    Pitch is the median distance between consecutive baselines, restricted to
    body-sized steps: section rules, heading blocks and the gaps between
    entries are far taller than a wrapped bullet line, and letting them into
    the median would overstate the pitch and so understate the spare room.
    """
    last_page = lines[-1].page
    ys = sorted({round(l.y, 2) for l in lines if l.page == last_page})
    steps = [b - a for a, b in zip(ys, ys[1:]) if PITCH_MIN <= b - a <= PITCH_MAX]
    pitch = statistics.median(steps) if steps else PITCH_MAX
    return ys[-1], pitch, (TEXT_BOTTOM - ys[-1]) / pitch


def find_jd(pdf_path: str) -> Path | None:
    """Locate the JD this resume was tailored from.

    Output is written as out/<jd-stem>_<YYYY-MM-DD>.pdf, so stripping the date
    suffix gives the JD's filename. Looked for next to the repo root as well as
    the current directory, so the check works from either.
    """
    stem = re.sub(r"_\d{4}-\d{2}-\d{2}$", "", Path(pdf_path).stem)
    roots = [Path.cwd(), Path(pdf_path).resolve().parent.parent]
    for root in roots:
        cand = root / "jds" / f"{stem}.txt"
        if cand.is_file():
            return cand
    return None


def check_title(doc: fitz.Document, jd: Path | None) -> tuple[str, str | None]:
    """Check the adapted job title against the JD's actual ML content.

    Returns (status line, complaint). The complaint is None when the title is
    fine, when no JD could be found, or when the specialist title is not used —
    this only ever objects to claiming ML on a JD that never asked for it.
    """
    resume = "\n".join(page.get_text() for page in doc).lower()
    if SPECIALIST_TITLE.lower() not in resume:
        return f'"{SPECIALIST_TITLE}" not used — OK', None
    if jd is None:
        # The specialist title has to be earned, so an unverifiable claim fails
        # rather than passing quietly. The default title needs no JD at all.
        return (
            f'"{SPECIALIST_TITLE}" used, but no JD found to check it against  UNVERIFIED',
            f'"{SPECIALIST_TITLE}" used with no JD at jds/<stem>.txt to justify it — '
            f"save the JD there, or use the default \"Software Engineer (UTRA)\"",
        )

    text = jd.read_text(encoding="utf-8", errors="replace").lower()
    hits = [t for t in ML_ROLE_TERMS if t in text]
    if hits:
        return f'"{SPECIALIST_TITLE}" used; {jd.name} matches {", ".join(hits[:3])} — OK', None
    return (
        f'"{SPECIALIST_TITLE}" used, but {jd.name} has no ML content  SPECIALIST',
        f'"{SPECIALIST_TITLE}" on a JD with no ML content — render Huang Climate '
        f"Lab as \"Software Engineer (UTRA)\" (see INSTRUCTIONS.md)",
    )


def classify_heading(h: Heading) -> str:
    if h.gap < GAP_COLLIDE:
        return "COLLIDE"
    if h.gap < GAP_TIGHT:
        return "TIGHT"
    return "OK"


def classify(bullet: Bullet, fill: float, clearance: float) -> str:
    flags = []
    if bullet.n_lines > MAX_LINES:
        flags.append("LONG")
    if fill < SHORT_THRESHOLD:
        flags.append("SHORT")
    elif clearance < FLUSH_MIN:
        flags.append("FLUSH")
    return "+".join(flags) if flags else "OK"


def opening(text: str, width: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 1].rstrip() + "…"


def main() -> int:
    ap = argparse.ArgumentParser(description="Resume fit checker.")
    ap.add_argument("pdf", help="path to the compiled resume PDF")
    ap.add_argument("--brief", action="store_true",
                    help="print only the totals and the verdict, not the "
                         "per-bullet/heading/skills tables")
    ap.add_argument("--debug", action="store_true", help="dump raw line geometry")
    args = ap.parse_args()
    # --brief suppresses the rows, never a verdict: everything the exit status
    # depends on still prints. Re-run without it to choose *which* bullet to
    # grow on a SPARSE page — that decision needs every fill percentage.
    table = not args.brief

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
        rows.append((b, fill, right - b.last_x1, classify(b, fill, right - b.last_x1)))

    if table:
        print(f"\n{'#':>3}  {'LN':>2}  {'FILL':>6}  {'GAP':>6}  {'FLAG':<11}  BULLET")
        print("-" * 100)
        for i, (b, fill, clear, flag) in enumerate(rows, start=1):
            marker = " " if flag == "OK" else "!"
            print(f"{i:>3}  {b.n_lines:>2}  {fill*100:5.1f}%  {clear:5.1f}pt  {flag:<11}{marker} {opening(b.text, 54)}")

    flagged = [(i, b, fill, clear, flag)
               for i, (b, fill, clear, flag) in enumerate(rows, start=1) if flag != "OK"]
    n_long = sum(1 for _, _, _, _, f in flagged if "LONG" in f)
    n_short = sum(1 for _, _, _, _, f in flagged if "SHORT" in f)
    n_flush = sum(1 for _, _, _, _, f in flagged if "FLUSH" in f)

    print("-" * 100 if table else "")
    print(f"{len(bullets)} bullets: {len(bullets) - len(flagged)} OK, "
          f"{n_long} LONG, {n_short} SHORT, {n_flush} FLUSH")

    headings = find_headings(lines, left)
    head_rows = [(h, classify_heading(h)) for h in headings]
    bad_heads = [(i, h, f) for i, (h, f) in enumerate(head_rows, start=1) if f != "OK"]

    if table:
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

    bad_ats = check_ats(headings) + check_glyphs(doc)
    if table and bad_ats:
        print(f"\n{'FLAG':<9}  ATS PARSING")
        print("-" * 100)
        for flag, cell, why in bad_ats:
            print(f"{flag:<9}! {opening(cell, 88)}")
        print("-" * 100)
    print(f"ATS: {len(bad_ats)} violations")

    cats = find_skills(lines)
    cat_rows = [(c, "WRAPPED" if len(c) > MAX_SKILL_LINES else "OK") for c in cats]
    bad_cats = [(c, f) for c, f in cat_rows if f != "OK"]

    if table:
        print(f"\n{'LN':>3}  {'FLAG':<9}  TECHNICAL SKILLS CATEGORY")
        print("-" * 100)
        for c, flag in cat_rows:
            marker = " " if flag == "OK" else "!"
            body = " ".join(l.text for l in c)
            print(f"{len(c):>3}  {flag:<9}{marker} {opening(body, 80)}")
        print("-" * 100)
    if not cat_rows:
        # Not a flag — the block may genuinely be absent — but never hide it.
        print("      no Technical Skills block found — not checked")
    print(f"{len(cat_rows)} skills categories: {len(cat_rows) - len(bad_cats)} OK, "
          f"{len(bad_cats)} WRAPPED")

    # Bottom fill is only meaningful once the page count is right: on a
    # spilled resume the last page is short by definition.
    last_y, pitch, spare = measure_tail(lines)
    sparse = pages == 1 and spare >= MAX_SPARE_LINES + 1
    verdict = "SPARSE" if sparse else "OK"
    print(f"\nBOTTOM     last baseline {last_y:.1f}pt of {TEXT_BOTTOM:.0f}pt "
          f"— room for {spare:.2f} more lines at {pitch:.1f}pt pitch "
          f"(max {MAX_SPARE_LINES})  {verdict}")

    title_status, title_complaint = check_title(doc, find_jd(args.pdf))
    print(f"TITLE      {title_status}")

    ok = (pages == 1 and not flagged and not bad_heads and not bad_cats
          and not bad_ats and not sparse and title_complaint is None)
    if ok:
        print("\nPASS — one page, filled, no bullet, heading or ATS rule flagged.")
        return 0

    print("\nFAIL")
    if pages != 1:
        print(f"  - page count is {pages}, must be exactly 1")
    if title_complaint:
        print(f"  - {title_complaint}")
    for flag, cell, why in bad_ats:
        print(f"  - {flag:<5} {why:<52} {opening(cell, 40)}")
    if sparse:
        print(f"  - {spare:.2f} lines of empty page below the last line "
              f"(max {MAX_SPARE_LINES}) — add a bullet to an experience")
    for i, b, fill, clear, flag in flagged:
        why = []
        if "LONG" in flag:
            why.append(f"{b.n_lines} lines (max {MAX_LINES})")
        if "SHORT" in flag:
            why.append(f"last line {fill*100:.1f}% of column (min {SHORT_THRESHOLD*100:.0f}%)")
        if "FLUSH" in flag:
            why.append(f"last line stops {clear:.1f}pt short of the edge "
                       f"(min {FLUSH_MIN:.0f}pt) — trim a few characters")
        print(f"  - #{i:<3} {'; '.join(why):<52} {opening(b.text, 40)}")
    for c, _ in bad_cats:
        label = c[0].text.split(":")[0].strip()
        why = f"wraps onto {len(c)} lines (max {MAX_SKILL_LINES}) — drop entries, not the category"
        print(f"  - S   {why:<52} {opening(label, 40)}")
    for i, h, flag in bad_heads:
        limit = GAP_COLLIDE if flag == "COLLIDE" else GAP_TIGHT
        why = f"heading gap {h.gap:.1f}pt (min {limit:.0f}pt) — shorten the tech list"
        print(f"  - H{i:<2} {why:<52} {opening(h.text, 40)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
