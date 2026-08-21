#!/usr/bin/env python3
"""Measure cover letter fit and voice: page count, body length, paragraph
shape, em-dashes, placeholder leftovers, and the stock phrases that make a
letter read as generated rather than written.

Usage:
    python check_cover.py out/some_cover.pdf
    python check_cover.py out/some_cover.pdf --brief   # drop the all-OK tables

Exit status is 0 only when the PDF is exactly one page, the body is inside the
length window, every paragraph is inside its own window, and nothing is flagged
for voice, dashes, or placeholders — so this can gate an iteration loop the way
check.py does for resumes.

Structural checks read the .tex sitting next to the PDF, not the PDF text:
paragraph boundaries survive there, and a `\\textemdash` written as a control
sequence is still visible. The PDF is opened for page count and to confirm the
letterhead actually rendered.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("PyMuPDF is required: pip install pymupdf")


# A cover letter is read in under a minute by someone with a stack of them.
# Below the floor it says nothing the resume does not; above the ceiling it
# stops being read. Measured on the body only — date block, salutation and
# sign-off are not part of the argument.
WORDS_MIN = 120
WORDS_MAX = 260

# Paragraph shape. Three is the natural structure (who I am / what I have
# built / why here); a fourth is allowed when the middle splits across two
# genuinely different bodies of work. Beyond that the letter is a resume in
# prose. A paragraph over the ceiling is a wall the reader skips.
PARAS_MIN = 3
PARAS_MAX = 4
PARA_WORDS_MAX = 110

# A sentence past this length has usually swallowed two ideas and a subclause.
SENTENCE_WORDS_MAX = 45

# At least this many contractions across the body. Zero contractions is the
# clearest single signal of stiff, generated-sounding prose; requiring a couple
# costs nothing and keeps the register conversational.
CONTRACTIONS_MIN = 2

# Em-dashes only. `--` (en-dash) is left alone: it is how this repo writes
# date ranges and compound ranges, and it never carries the dramatic pause an
# em-dash does.
EMDASH_PATTERNS = [
    (r"---", "--- (LaTeX em-dash)"),
    (r"\\textemdash", r"\textemdash"),
    ("\u2014", "— (literal em-dash)"),
]

# Stock phrases. Each one is a thing a real person rarely writes about their
# own work but a template always does. Matched case-insensitively on the body.
BANNED_PHRASES = [
    "i am passionate", "i'm passionate", "passion for",
    "i am excited to", "i'm excited to", "thrilled",
    "dream job", "dream company", "perfect fit", "ideal candidate",
    "fast-paced", "hit the ground running", "wear many hats",
    "leverage my", "utilize my", "skill set",
    "proven track record", "results-driven", "self-starter",
    "team player", "think outside the box", "goes without saying",
    "i believe i would be", "i would be a great",
    "as you can see from my resume", "please do not hesitate",
    "cutting-edge", "state-of-the-art", "world-class",
    "at its core", "ever since i was", "i have always been",
    "from a young age", "little did i know",
]

# Voice patterns: the writerly constructions that read as authored-for-effect
# rather than said. These are the shapes Rohan has rejected by hand — a
# self-characterizing thesis line ("I write software that..."), a possessive
# claim on one's own humility ("the work I am proudest of"), and flattery
# aimed at the employer's standards. Regexes, matched on the body.
VOICE_PATTERNS = [
    (r"\bwork (i am|i'm) (most )?proud(est)? of\b", "self-praising aside"),
    (r"\bi (write|build|make) software (that|for systems)\b", "thesis-statement self-description"),
    (r"\bis the baseline\b", "flattering the employer's standards"),
    (r"\bengineers who (hold|share|live)\b", "flattering the employer's standards"),
    (r"\b(is|are) the engineering,? not\b", "aphorism"),
    (r"\bnot the cleanup\b", "aphorism"),
    (r"\btaught me that\b", "lesson-moral construction"),
    (r"\bwhat (drew|draws) me to\b", "stock opening"),
    (r"\bi was drawn to\b", "stock opening"),
    (r"\bthe kind of (engineer|person) who\b", "self-characterization"),
]

# Anything still bracketed or shouting is an unfilled slot from a prior letter.
PLACEHOLDER_PATTERNS = [
    (r"\[[^\]]{2,40}\]", "bracketed placeholder"),
    (r"\bTODO\b", "TODO"),
    (r"\bXXX+\b", "XXX"),
    (r"\bCompany Name\b", "Company Name"),
    (r"\bYour Name\b", "Your Name"),
]

CONTRACTION_RE = re.compile(r"\b\w+['\u2019](m|s|t|re|ve|ll|d)\b", re.I)
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\u2019./+-]*")


def tex_path_for(pdf_path: str) -> Path:
    """The .tex a compiled letter came from sits beside it, same stem."""
    return Path(pdf_path).with_suffix(".tex")


def jd_for(pdf_path: str) -> tuple[str, Path | None]:
    """Output is out/<jd-stem>_cover_<YYYY-MM-DD>.pdf, so stripping the date and
    the _cover marker recovers the JD stem the letter was written against."""
    stem = re.sub(r"_\d{4}-\d{2}-\d{2}$", "", Path(pdf_path).stem)
    stem = re.sub(r"_cover$", "", stem)
    for root in (Path.cwd(), Path(__file__).resolve().parent):
        cand = root / "jds" / f"{stem}.txt"
        if cand.exists():
            return stem, cand
    return stem, None


def strip_tex(s: str) -> str:
    """Reduce LaTeX to the words a reader sees. Deliberately lossy: this feeds
    word counts and phrase matching, not rendering."""
    s = re.sub(r"(?m)^\s*%.*$", "", s)                    # comment lines
    s = re.sub(r"\\\\(\[[^\]]*\])?", " ", s)              # line breaks
    s = re.sub(r"\\(vspace|hspace)\{[^}]*\}", " ", s)
    s = re.sub(r"\\(begin|end)\{[^}]*\}", " ", s)
    s = re.sub(r"\\(emph|textbf|textit|underline|href)\{", " ", s)
    s = re.sub(r"\\[A-Za-z]+\*?", " ", s)                 # any other command
    s = s.replace("~", " ").replace("\\%", "%").replace("\\&", "&")
    s = re.sub(r"[{}]", " ", s)
    return s


def extract_body(tex: str) -> tuple[list[str], str]:
    """Body paragraphs: everything between the salutation and the sign-off.

    The letterhead ends at the last \\end{center} of the shared prefix, the
    salutation is the `Dear ...` line, and the closing is `Sincerely`. Anything
    outside that is address furniture, not argument, and is not counted.
    """
    tail = tex.rsplit(r"\end{center}", 1)[-1]

    m = re.search(r"(?mi)^\s*Dear\b.*$", tail)
    if m:
        tail = tail[m.end():]

    m = re.search(r"(?mi)^\s*(Sincerely|Regards|Best|Thank you)\b", tail)
    if m:
        tail = tail[:m.start()]

    paras = []
    for block in re.split(r"\n\s*\n", tail):
        text = " ".join(strip_tex(block).split())
        if len(WORD_RE.findall(text)) >= 5:   # skip \vspace-only blocks
            paras.append(text)
    return paras, " ".join(paras)


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [p.strip() for p in parts if p.strip()]


def scan(body: str, raw_tail: str) -> list[tuple[str, str, str]]:
    """Return (FLAG, what, evidence) for every voice/dash/placeholder hit."""
    hits = []
    for pat, label in EMDASH_PATTERNS:
        # Dashes are scanned on the raw source too: \textemdash survives
        # stripping as nothing at all, and would otherwise pass unseen.
        for hay in (body, raw_tail):
            if re.search(pat, hay):
                hits.append(("EMDASH", label, excerpt(hay, pat)))
                break
    for phrase in BANNED_PHRASES:
        if phrase in body.lower():
            hits.append(("PHRASE", phrase, excerpt(body, re.escape(phrase))))
    for pat, label in VOICE_PATTERNS:
        if re.search(pat, body, re.I):
            hits.append(("VOICE", label, excerpt(body, pat)))
    for pat, label in PLACEHOLDER_PATTERNS:
        if re.search(pat, body):
            hits.append(("PLACEHOLDER", label, excerpt(body, pat)))
    return hits


def excerpt(text: str, pattern: str, width: int = 52) -> str:
    m = re.search(pattern, text, re.I)
    if not m:
        return ""
    lo = max(0, m.start() - width // 3)
    s = text[lo:lo + width].strip()
    return ("..." if lo else "") + s + ("..." if lo + width < len(text) else "")


def main() -> int:
    ap = argparse.ArgumentParser(description="Cover letter fit and voice checker.")
    ap.add_argument("pdf", help="path to the compiled cover letter PDF")
    ap.add_argument("--brief", action="store_true",
                    help="print only the totals and the verdict")
    args = ap.parse_args()
    table = not args.brief

    tex = tex_path_for(args.pdf)
    if not tex.exists():
        sys.exit(f"No .tex beside the PDF at {tex} — structure cannot be measured.")

    try:
        doc = fitz.open(args.pdf)
    except Exception as exc:
        sys.exit(f"Could not open {args.pdf}: {exc}")

    pages = doc.page_count
    rendered = doc[0].get_text() if pages else ""

    source = tex.read_text(encoding="utf-8")
    raw_tail = source.rsplit(r"\end{center}", 1)[-1]
    paras, body = extract_body(source)
    words = len(WORD_RE.findall(body))

    stem, jd = jd_for(args.pdf)
    fails: list[str] = []

    print(f"FILE       {args.pdf}")
    print(f"PAGES      {pages}" + ("" if pages == 1 else "   <-- must be exactly 1"))
    print(f"JD         jds/{stem}.txt" + ("" if jd else "   <-- not found (letter is unanchored)"))
    print(f"BODY       {words} words in {len(paras)} paragraphs "
          f"(want {WORDS_MIN}-{WORDS_MAX} words, {PARAS_MIN}-{PARAS_MAX} paragraphs)")

    if pages != 1:
        fails.append(f"page count is {pages}, must be exactly 1")
    if not paras:
        print("\nNo body found — is there a `Dear ...` line and a `Sincerely` above the name?")
        return 1
    if words < WORDS_MIN:
        fails.append(f"body is {words} words, under the {WORDS_MIN}-word floor")
    if words > WORDS_MAX:
        fails.append(f"body is {words} words, over the {WORDS_MAX}-word ceiling")
    if len(paras) < PARAS_MIN:
        fails.append(f"{len(paras)} body paragraphs, want at least {PARAS_MIN}")
    if len(paras) > PARAS_MAX:
        fails.append(f"{len(paras)} body paragraphs, want at most {PARAS_MAX}")

    if "Rohan Vittal" not in rendered:
        fails.append("letterhead missing — was template_head.tex concatenated?")

    if table:
        print(f"\n{'#':>3}  {'WORDS':>5}  {'FLAG':<9}  PARAGRAPH")
        print("-" * 100)
    for i, p in enumerate(paras, start=1):
        long_sentence = max((len(WORD_RE.findall(s)) for s in sentences(p)), default=0)
        flag = "OK"
        if len(WORD_RE.findall(p)) > PARA_WORDS_MAX:
            flag = "LONG"
            fails.append(f"paragraph {i} is {len(WORD_RE.findall(p))} words "
                         f"(max {PARA_WORDS_MAX}) — split it or cut a clause")
        elif long_sentence > SENTENCE_WORDS_MAX:
            flag = "RUNON"
            fails.append(f"paragraph {i} has a {long_sentence}-word sentence "
                         f"(max {SENTENCE_WORDS_MAX}) — break it in two")
        if table:
            marker = " " if flag == "OK" else "!"
            print(f"{i:>3}  {len(WORD_RE.findall(p)):>5}  {flag:<9}{marker} {p[:60]}...")
    if table:
        print("-" * 100)

    contractions = len(CONTRACTION_RE.findall(body))
    hits = scan(body, raw_tail)

    if table:
        print(f"\n{'FLAG':<12}  {'WHAT':<38}  EVIDENCE")
        print("-" * 100)
        if not hits:
            print("(none)")
        for flag, what, ev in hits:
            print(f"{flag:<12}  {what[:38]:<38}  {ev}")
        print("-" * 100)

    for flag, what, ev in hits:
        if flag == "EMDASH":
            fails.append(f"em-dash present ({what}) — use a comma, a colon, or two sentences")
        elif flag == "PHRASE":
            fails.append(f'stock phrase "{what}" — say the specific thing instead')
        elif flag == "VOICE":
            fails.append(f"{what} — state what you did, not what it says about you")
        else:
            fails.append(f"unfilled {what} left in the body")

    print(f"CONTRACT   {contractions} contractions "
          f"(want >= {CONTRACTIONS_MIN}; zero reads stiff)")
    if contractions < CONTRACTIONS_MIN:
        fails.append(f"{contractions} contractions, want at least {CONTRACTIONS_MIN} "
                     f"— loosen a sentence or two")

    if fails:
        print("\nFAIL")
        for f in fails:
            print(f"  - {f}")
        return 1

    print("\nPASS — one page, inside length, nothing flagged for voice or dashes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
