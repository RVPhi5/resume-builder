# Resume Tailoring Instructions

## Task
When I give you a job description, produce a **one-page** tailored resume as
LaTeX using Jake's Resume template, compiled to PDF.

## Source of truth
`master.txt` is my exhaustive master resume. It contains far more bullets than
fit on one page — that is intentional. Select from it.

**Never invent experience, tools, metrics, or scope.** You may reframe and
re-emphasize what a bullet already states, and use the JD's literal terminology
where the original genuinely supports it, but never add a capability I don't
have. Preserve every number exactly as written in master.txt.

## Selection
Read the JD and pick the experiences and projects that make the strongest case
for *this* role. Typically 3–4 experiences and 2–3 projects.

Balance two things:
- **Relevance** — does it match what this JD asks for?
- **Strength** — is it impressive on its own? Keep genuinely strong bullets
  (hard metrics, production scope, real technical depth) even when the JD
  doesn't name that technology. Don't let a keyword mismatch cut my best work.

Always include at least one bullet from any entry you keep — never render a
bare header.

## Hard constraint
**Mirico Ltd. must always appear above Brown Space Engineering**, regardless of
relevance.

## Fit rules — non-negotiable
1. **Exactly one page.** Not 1.1, not 0.8.
2. **No bullet exceeds two lines.**
3. **Every bullet nearly fills its final line** — at least 90% of column width.
4. **Every heading row keeps clear space between its two cells** — at least
   20pt between the left content and the right-aligned date.

## How to fix violations
**Do not estimate any of this. Measure it.** After writing the `.tex`, compile
with pdflatex and run `python check.py out/<name>.pdf`. Fix what it flags,
recompile, re-check. Repeat until clean. Cap at 8 iterations.

**LONG (more than two lines):** tighten the wording. Cut filler and redundancy
first — "utilized" → "used", "in order to" → "to", drop hedges like "helped to"
and "worked on". If that's not enough, drop the least important clause. Never
cut a metric or a technology name to save space; those are the parts that matter.

**SHORT (last line under 90%):** lengthen with real technical substance, not
padding. Add the specific tool, the mechanism, or the measured result from
master.txt. Good: naming the library, stating what the optimization actually
did, adding the number. Bad: adjectives, "successfully", "in a fast-paced
environment", restating the same idea twice.

**COLLIDE or TIGHT (heading row):** the left cell (job title, or project name
plus tech stack) has grown wide enough that the `\extracolsep{\fill}` glue
collapses and the date crowds or touches it. **Shorten the tech stack list** —
drop the technologies least relevant to this JD, and prefer dropping ones no
kept bullet actually demonstrates. Do *not* shorten the project name, the job
title, the company, or the date to buy space; those are identifying
information. COLLIDE means it is already broken on the page; TIGHT means it
still renders but looks cramped and is one edit away from breaking.

**These interact — respect this order.** After lengthening a short bullet,
re-check it didn't become three lines. After trimming a long one, re-check it
didn't become short. Priority: (1) one page, (2) two-line maximum, (3) 90%
fill, (4) heading gap.

If a bullet genuinely can't satisfy both the two-line cap and the 90% fill,
prefer two clean lines with a slightly short second line — but tell me which
bullet, so I can rewrite it myself.

**Never show me a resume you haven't compiled and checked.** If you hit the
iteration cap without converging, show me the current state and the outstanding
flags rather than pretending it's clean.

## Output
Write `out/<jd-filename-stem>_<YYYY-MM-DD>.tex` and compile to the matching
`.pdf`. Then tell me, briefly:
- what you kept and what you cut, and why
- anything the JD asked for that I genuinely can't claim
- any bullet you couldn't get within the fit rules
- any technology you dropped from a heading's tech stack to clear a gap flag
