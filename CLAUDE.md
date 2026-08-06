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
   count, bullet line counts, line fill, heading gaps, bottom fill, and the
   title rule, and its exit status gates the loop.

## Workflow

```bash
# save the JD first — check.py finds it by filename stem
jds/<stem>.txt                     ->  out/<stem>_<YYYY-MM-DD>.tex

pdflatex -interaction=nonstopmode -halt-on-error -output-directory=out \
    out/<stem>_<YYYY-MM-DD>.tex
python check.py out/<stem>_<YYYY-MM-DD>.pdf
```

Delete the LaTeX intermediates (`out/*.aux`, `*.log`, `*.out`) when the build is
done. Leave everything else in `out/` alone: it is gitignored, so nothing there
is recoverable, and past tailored resumes are not yours to decide about.

## Layout

| Path | |
|---|---|
| `master.txt` | exhaustive master resume — the source of truth for content |
| `master_resume.tex` | the same content as LaTeX; keep the two in sync |
| `INSTRUCTIONS.md` | the tailoring spec |
| `check.py` | fit checker; exit 0 only on PASS |
| `jds/`, `out/` | job descriptions in, tailored resumes out |
