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

## Title adaptation
Job titles may be adapted to a more general equivalent when the specialized
title misrepresents the fit. This is a deliberate, narrow exception to "never
invent" — it relabels a role I actually held, it does not add experience.

**Huang Climate Lab** — the default render is **`Software Engineer (UTRA)`**.
Upgrade it to `Machine Learning Engineer (UTRA)` only when the role being
applied for actually builds AI/ML. Keep `(UTRA)` either way; it marks the
research award, not the specialization.

The test is whether the **role builds** AI/ML — models, the pipelines feeding
them, inference or agent systems. It is not enough that the JD asks for "AI
literacy" or prompt engineering as a general working skill, or that the company
blurb name-drops AI alongside VR and other technology it happens to sell; those
describe using AI tools, not engineering them. A general software engineering
role renders as `Software Engineer (UTRA)` even when AI is mentioned.

The default is deliberately the safe one: the general title fits every JD,
while the specialist title on a JD that never asked for ML misrepresents the
fit. So an upgrade must be argued for, and forgetting to decide leaves the
render correct. `check.py` fails the run if the specialist title appears on a
JD with no ML content, so this is checked, not remembered.

Do not adapt any other title unless I add it here. Company names, dates, and
locations are never adapted.

**Project role markers** (e.g. `CourseTrees — Co-Founder`) may be rendered
either in the heading's left cell or carried by the first bullet's verb
("Co-founded and help lead…") — **but not both**, or the page reads redundantly.
Prefer the heading when the gap budget allows, since it reads as standing rather
than as one more thing I did; move it into the bullet when the heading is TIGHT.
A role marker counts as job title under the COLLIDE/TIGHT rule: shorten the tech
stack to make room, never the role.

## Links
When `master.txt` records a `LINK:` for an entry, hyperlink that entry's name in
its heading, matching the header's style so it reads as a link:

```latex
\href{https://www.coursetrees.com/}{\underline{\textbf{CourseTrees}}}
```

Currently recorded: **CourseTrees → https://www.coursetrees.com/**

A hyperlink adds no rendered width, so it never affects the heading gap rules —
`\href` wraps existing text rather than adding any. Keep the underline; the
preamble loads `hyperref` with `hidelinks`, so without it a link is invisible on
the page.

## Selection
Read the JD and pick the experiences and projects that make the strongest case
for *this* role. Typically 3–4 experiences and 3–4 projects.

**Prefer more projects over deeper ones.** Breadth reads better than depth
here: 3–4 projects at 2 bullets each beats 2 projects at 3. Two bullets is both
the target and the ceiling for a project — see the bullet-count rules below.

Only add a project if it is actually relevant to this JD. A fourth project that
doesn't fit the role is worse than a third that does — do not pad the count.

Space is the real constraint, so budget before you commit. Measured in the
compiled PDF: a project heading row costs ~11pt, the same as one bullet line;
a two-line bullet costs ~23pt. A new 2-bullet project therefore costs ~58pt —
roughly two and a half two-line bullets. Adding a project means cutting two to
three bullets elsewhere, not one.

Balance two things:
- **Relevance** — does it match what this JD asks for?
- **Strength** — is it impressive on its own? Keep genuinely strong bullets
  (hard metrics, production scope, real technical depth) even when the JD
  doesn't name that technology. Don't let a keyword mismatch cut my best work.

Never render a bare header — see the bullet-count rules below for the minimum
each kind of entry carries.

## Hard constraints
These hold for every JD. They are not traded against relevance or space; if
something has to give, cut a whole entry instead of breaking one of these.

1. **Experience is listed in date order, most recent first**, by start date.
   This is what puts Mirico above Brown Space Engineering on its own; rule 2
   is the backstop for any case where it would not.
2. **Mirico Ltd. must always appear above Brown Space Engineering.**
3. **CourseTrees is always the first project listed**, whatever else is
   selected alongside it. Projects are not date-ordered — rule 1 is about
   experience only.
4. **Every experience kept carries at least two bullets.** One bullet under a
   job heading reads as a stub. If the page cannot afford two, drop that
   experience entirely and give the space to one that can.
5. **No project carries more than two bullets.** Two is the target, including
   for a flagship the JD makes central; drop to one only for a small project
   that genuinely warrants a single line.

Together these set the realistic ceiling: about three experiences and three
projects at two bullets each, plus the education line, fills one page. Adding a
fourth entry anywhere means dropping one somewhere else — check the space
budget above before committing to it.

## Fit rules — non-negotiable
1. **Exactly one page.** Not 1.1, not 0.8.
2. **No bullet exceeds two lines.**
3. **Every bullet nearly fills its final line** — at least 90% of column width.
4. **Every heading row keeps clear space between its two cells** — at least
   20pt between the left content and the right-aligned date.
5. **The page is full.** At most one further body line may fit beneath the last
   line. Two or more lines of empty page at the bottom reads as running out of
   things to say, and is as wrong as spilling onto a second page.

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

**SPARSE (two or more lines of empty page):** the page is under-filled, so add
real content rather than padding what is there. Cheapest first: a one-line
bullet grown into a full two-line one buys exactly one line, and an extra
bullet on an experience buys two. A whole extra project costs five (a heading
row plus two two-line bullets), so it only fits a page that is genuinely short.
Respect the bullet-count rules above when choosing — projects are capped at two
bullets, so a sparse page is filled from the experience side.

**These interact — respect this order.** After lengthening a short bullet,
re-check it didn't become three lines. After trimming a long one, re-check it
didn't become short. After filling a sparse page, re-check it is still one
page. Priority: (1) one page, (2) two-line maximum, (3) 90% fill, (4) heading
gap, (5) bottom fill.

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
- whether you adapted a job title, and why
