# resume-builder

Tailors Rohan's resume to a job description: select from the master resume,
render Jake's Resume template as LaTeX, compile, and measure the fit. Cover
letters are built the same way against their own spec — see **Cover letters**
below.

**Read [`INSTRUCTIONS.md`](INSTRUCTIONS.md) in full before producing a resume.**
It is the spec — selection rules, hard constraints, fit rules, and how to fix
each violation. This file only names the traps that are easy to fall into
without reading it.

## The three that bite

1. **The Huang Climate Lab title defaults to `Software Engineer`.**
   Upgrade to `Machine Learning Engineer` only when the role being applied for
   actually *builds* ML. A JD asking for "AI literacy" or prompt engineering, or
   name-dropping AI in its company blurb, does **not** qualify — that mistake
   has been made before. `check.py` fails the run on it. **Never append
   `(UTRA)`**, or any parenthetical, to a title or company: an ATS reads
   `Title (X)` as `Title @ X` and splits the entry in two.

   More generally, the page is only half the deliverable — the PDF's text layer
   is the other half, and `\extracolsep{\fill}` gives a parser no column
   structure to read. `\resumeSubheading` is called
   `{Organization}{Location}{Title}{Dates}`, locations are `City, ST` or
   `City, Country`, months are spelled out in full, and no glyph may come from a
   Type3 font. See **ATS parsing** in `INSTRUCTIONS.md`; `check.py` enforces all
   of it.

2. **Never invent experience.** `master.txt` is the only source of bullets,
   metrics and technologies. Reframing what a bullet already says is fine;
   adding a capability is not. Preserve every number exactly.

3. **Never show a resume you have not compiled and checked.** Write the `.tex`,
   run pdflatex, run `python check.py out/<name>.pdf`, fix what it flags, repeat
   until it prints PASS. Do not estimate fit by eye — the checker measures page
   count, bullet line counts, line fill, how close each last line comes to the
   right edge, heading gaps, Technical Skills wrapping, bottom fill, the
   title rule, and the ATS text-layer rules, and its exit status gates the loop.

## What a build reads

`INSTRUCTIONS.md`, `master.txt`, `coursework.txt`, and the JD. That is the whole
list. `coursework.txt` is small and is the only source for the `Relevant
Coursework` line — pick from it per JD, the same way bullets are picked, and
never list a course it does not contain. `check.py`
is run, not read — open it only when the checker itself is being changed or is
suspected wrong. `master_resume.tex` is not an input to tailoring at all.
Together those two are ~64 KB of context for zero benefit on a normal build.

## Workflow

Every resume is `template_head.tex` (preamble, custom commands, contact block —
fixed, identical in every resume) concatenated with a tailored body that starts
at `\section{Education}` and ends with `\end{document}`. **Write only the body**,
then `cat` it onto the head. Copying those bytes with the shell rather than
regenerating them saves ~2.5 KB of output per build, and the result is an
ordinary standalone `.tex` — no `\input`, nothing to carry alongside it.

```bash
# save the JD first — check.py finds it by filename stem
jds/<stem>.txt                     ->  out/<stem>_<YYYY-MM-DD>.tex

# write the tailored body somewhere scratch, then:
cat template_head.tex <body>.tex > out/<stem>_<YYYY-MM-DD>.tex

pdflatex -interaction=nonstopmode -halt-on-error -output-directory=out \
    out/<stem>_<YYYY-MM-DD>.tex
python check.py out/<stem>_<YYYY-MM-DD>.pdf
```

Concatenate once, at the start. Every fix after that is an ordinary edit to the
file in `out/` — the head is only a starting point, not a live dependency.

Keep `.tex` files bare-LF, as every existing one is. Writing them from Python on
Windows needs `newline=""`, or the head lands CRLF and the built resume ends up
with mixed line endings.

Delete the LaTeX intermediates (`out/*.aux`, `*.log`, `*.out`) when the build is
done. Leave everything else in `out/` alone: it is gitignored, so nothing there
is recoverable, and past tailored resumes are not yours to decide about.

Then append the build's gaps to [`GAPS.txt`](GAPS.txt) — the running ledger of
what each JD asked for that `master.txt` cannot support. It is the same list the
build already reports back, kept so the pattern across applications is visible;
the file's own header holds the entry format and the HARD/SOFT convention.
A bullet cut for space is not a gap and does not go in it.

## Cover letters

**Read [`COVER_INSTRUCTIONS.md`](COVER_INSTRUCTIONS.md) in full before writing
one.** Same shape as the resume loop — write the body, `cat` it onto
`template_head.tex`, compile, run `python check_cover.py out/<name>.pdf`, fix
what it flags, repeat until PASS — but the rules being measured are different,
and so are the traps:

1. **A cover letter is not the resume in prose.** 150–200 words, three
   paragraphs, at most one metric. Every number is already on the resume in the
   same envelope; repeating them spends the letter's only advantage, which is
   voice.

2. **The voice rules are the spec, not a preference.** No em-dashes, no
   self-characterizing thesis lines ("I write software for systems that…"), no
   claims on one's own humility ("the work I'm proudest of"), no flattering the
   employer, no aphorisms, no stock phrases. `check_cover.py` holds the pattern
   list and fails the run on a hit. Every one of those patterns is there
   because a draft got rejected for it by hand.

3. **`VOICE` means delete the sentence, not rewrite it.** The shape is the
   problem. Rephrasing a thesis line produces another thesis line; state what
   was actually done instead.

Naming is `out/<jd-stem>_cover_<YYYY-MM-DD>.tex`. The `_cover` marker is load
bearing: the checker strips the date and then `_cover` to find `jds/<stem>.txt`,
so a letter for the same JD as a resume sits beside it and resolves to the same
posting.

## Layout

| Path | |
|---|---|
| `master.txt` | exhaustive master resume — the source of truth for content |
| `coursework.txt` | transcript-backed course list — the source for `Relevant Coursework` |
| `master_resume.tex` | the same content as LaTeX; keep the two in sync |
| `template_head.tex` | fixed prefix every tailored resume is built on |
| `INSTRUCTIONS.md` | the tailoring spec |
| `COVER_INSTRUCTIONS.md` | the cover letter spec — length, shape, voice rules |
| `GAPS.txt` | running ledger of what each JD asked for and I can't claim |
| `check.py` | resume fit checker; exit 0 only on PASS |
| `check_cover.py` | cover letter fit and voice checker; exit 0 only on PASS |
| `jds/`, `out/` | job descriptions in, tailored resumes out |
