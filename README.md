# resume-builder

Tailors a one-page resume (and optionally a cover letter) to a specific job
description, using Jake's Resume LaTeX template. Tailoring is done by Claude
Code following a written spec; Python checkers measure the result and gate it.

## How it works

1. **Save the job description** to `jds/<stem>.txt`.
2. **Select content.** Bullets, metrics and technologies come only from
   `master.txt`; the Relevant Coursework line comes only from `coursework.txt`.
   Selection and phrasing follow `INSTRUCTIONS.md`. Nothing is invented.
3. **Build.** Write the tailored body (from `\section{Education}` to
   `\end{document}`) and prepend the fixed preamble:
   ```bash
   cat template_head.tex body.tex > out/<stem>_<YYYY-MM-DD>.tex
   pdflatex -interaction=nonstopmode -halt-on-error -output-directory=out \
       out/<stem>_<YYYY-MM-DD>.tex
   ```
4. **Check.** Fix whatever the checker flags and rebuild until it prints PASS:
   ```bash
   python check.py out/<stem>_<YYYY-MM-DD>.pdf
   ```
   It checks the layout (exactly one page, how bullets wrap, how full each
   line is, heading spacing, empty space at the bottom) and whether the PDF's
   text layer will parse cleanly in an ATS (applicant tracking system).
5. **Log gaps.** Anything the JD asks for that `master.txt` can't back up is
   appended to `GAPS.txt`, so recurring gaps across applications are visible.

Cover letters follow the same loop against `COVER_INSTRUCTIONS.md`, named
`out/<stem>_cover_<YYYY-MM-DD>.tex` and checked with `python check_cover.py`.
That checker also enforces length and a list of banned phrasings.

## Files

| Path | Purpose |
|---|---|
| `master.txt` | Exhaustive master resume; the only source of content |
| `coursework.txt` | Course list, the only source for Relevant Coursework |
| `master_resume.tex` | Same content as LaTeX; kept in sync with `master.txt` |
| `template_head.tex` | Fixed preamble and contact block for every resume |
| `INSTRUCTIONS.md` | Resume tailoring spec |
| `COVER_INSTRUCTIONS.md` | Cover letter spec |
| `check.py`, `check_cover.py` | Fit checkers; exit 0 only on PASS |
| `GAPS.txt` | Ledger of JD requirements the master resume can't support |
| `jds/`, `out/` | JDs in, built resumes out (contents are gitignored) |

## Requirements

A TeX distribution with `pdflatex`, Python 3.11+, and PyMuPDF
(`pip install pymupdf`) for the checkers.
