# resume-builder

Tailors Rohan's resume to a job description: select from the master resume,
render Jake's Resume template as LaTeX, compile, and measure the fit.

**Read [`INSTRUCTIONS.md`](INSTRUCTIONS.md) in full before producing a resume.**
It is the spec — selection rules, hard constraints, fit rules, and how to fix
each violation. This file only names the traps that are easy to fall into
without reading it.

## The three that bite

1. **The Huang Climate Lab title defaults to `Software Engineer (UTRA)`.**
   Upgrade to `Machine Learning Engineer (UTRA)` only when the role being
   applied for actually *builds* ML. A JD asking for "AI literacy" or prompt
   engineering, or name-dropping AI in its company blurb, does **not** qualify —
   that mistake has been made before. `check.py` fails the run on it.

2. **Never invent experience.** `master.txt` is the only source of bullets,
   metrics and technologies. Reframing what a bullet already says is fine;
   adding a capability is not. Preserve every number exactly.

3. **Never show a resume you have not compiled and checked.** Write the `.tex`,
   run pdflatex, run `python check.py out/<name>.pdf`, fix what it flags, repeat
   until it prints PASS. Do not estimate fit by eye — the checker measures page
   count, bullet line counts, line fill, how close each last line comes to the
   right edge, heading gaps, Technical Skills wrapping, bottom fill, and the
   title rule, and its exit status gates the loop.

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

## Layout

| Path | |
|---|---|
| `master.txt` | exhaustive master resume — the source of truth for content |
| `coursework.txt` | transcript-backed course list — the source for `Relevant Coursework` |
| `master_resume.tex` | the same content as LaTeX; keep the two in sync |
| `template_head.tex` | fixed prefix every tailored resume is built on |
| `INSTRUCTIONS.md` | the tailoring spec |
| `check.py` | fit checker; exit 0 only on PASS |
| `jds/`, `out/` | job descriptions in, tailored resumes out |
