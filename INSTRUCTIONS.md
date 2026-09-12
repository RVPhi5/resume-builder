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

**Huang Climate Lab** — the default render is **`Software Engineer`**.
Upgrade it to `Machine Learning Engineer` only when the role being applied for
actually builds AI/ML.

**Never append `(UTRA)`** — or any other parenthetical — to the title. ATS
parsers read `Title (X)` as `Title @ X`, and `UTRA` is a four-letter all-caps
token, about the strongest organization signal there is: it becomes the
employer, the entry splits in two, and the real Huang heading one line below is
consumed as a second job. The award is already carried by the `Honors` line on
the education entry, where it parses as text rather than as an employer. See
**ATS parsing** below.

The test is whether the **role builds** AI/ML — models, the pipelines feeding
them, inference or agent systems. It is not enough that the JD asks for "AI
literacy" or prompt engineering as a general working skill, or that the company
blurb name-drops AI alongside VR and other technology it happens to sell; those
describe using AI tools, not engineering them. A general software engineering
role renders as `Software Engineer` even when AI is mentioned.

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

Currently recorded: **CourseTrees → https://www.coursetrees.com/**. BrownSync
ships inside CourseTrees and has no heading of its own, so it carries no link.

A hyperlink adds no rendered width, so it never affects the heading gap rules —
`\href` wraps existing text rather than adding any. Keep the underline; the
preamble loads `hyperref` with `hidelinks`, so without it a link is invisible on
the page.

## Selection
Read the JD and pick the experiences and projects that make the strongest case
for *this* role. Typically 3–4 experiences and 3–4 projects.

**Prefer more projects over deeper ones.** Breadth reads better than depth
here: 4 projects at 1 bullet each beats 2 projects at 2. **One bullet is the
default for a project.** Give a project a second bullet only when that second
bullet is genuinely relevant to *this* JD — not merely true, and not merely
impressive. Two is the ceiling either way — see the bullet-count rules below.

**CourseTrees is the sole exception.** It is the flagship, it is what I am
actually building, and it is the one project that carries real depth on the
page: it takes **three to five bullets**, selected per JD like any others. Its
bullet pool now spans two products — the course-planning platform and the
BrownSync campus-activity map that ships inside it — so pick across both by
what this JD asks for rather than taking the first few in file order.

**Its first bullet is fixed.** The traction line marked `RULE:` in master.txt --
registered users, pageviews, iOS downloads -- renders as CourseTrees' bullet one
on every JD, without exception. Only the remaining two to four slots are selected
per JD. It leads because it is the one bullet that says the thing shipped and
people use it; the engineering bullets underneath then read as work that reached
users rather than work that reached a repo. Refresh its numbers from the `VERIFY:`
line before rendering -- they move, and a stale user count is the one number in
this entry a reader can check in a browser.

Only add a project if it is actually relevant to this JD. A fourth project that
doesn't fit the role is worse than a third that does — do not pad the count.

Space is the real constraint, so budget before you commit. Measured in the
compiled PDF: a project heading row costs ~11pt, the same as one bullet line;
a two-line bullet costs ~23pt. A new 1-bullet project therefore costs ~34pt and
a 2-bullet one ~58pt. Adding a project means cutting a bullet or two elsewhere.

Balance two things:
- **Relevance** — does it match what this JD asks for?
- **Strength** — is it impressive on its own? Keep genuinely strong bullets
  (hard metrics, production scope, real technical depth) even when the JD
  doesn't name that technology. Don't let a keyword mismatch cut my best work.

Never render a bare header — see the bullet-count rules below for the minimum
each kind of entry carries.

## Coursework
`coursework.txt` holds every course I have actually taken, parsed from my
transcript, with an approved short label for each. It is the **only** source for
the Education section's `Relevant Coursework` line — that line is selected per
JD exactly like bullets are, not copied from a fixed list.

- **Pick the courses this JD cares about, most relevant first.** Five is the
  usual count because that fills about one rendered line; the line is measured
  like any other bullet, so adjust the count to keep it one line at 90%+ fill.
- **Render the `RESUME LABEL` verbatim.** The registrar titles in that file are
  truncated abbreviations (`Prog Des: Data Structure & Alg`), not course names.
  Shortening a label further is allowed only to clear a fit flag.
- **Never list a course that is not in `coursework.txt`.** The AP placement
  credits at the top of that file are transfer credit — I placed out of them and
  never took them, so they are not coursework and never appear on a resume.
- **Order by relevance to the JD**, not by date, level, or grade. Never render a
  grade next to a course.
- `Data Structures & Algorithms` earns its place on nearly any software JD, and
  most postings name it outright. Check it against the JD before dropping it for
  something more specialized.

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
5. **A project carries one bullet by default, and never more than two** —
   every project except CourseTrees. The second bullet has to earn its place
   against this specific JD: a project the JD makes central can take two,
   everything else takes one. If you cannot say why the second bullet matters
   *for this role*, cut it.
6. **CourseTrees carries three to five bullets.** It is the flagship and the
   only entry exempt from rule 5. Fewer than three undersells the one thing on
   the page that is a real product; more than five crowds out the breadth that
   makes the rest of the section work. Draw them from both the platform and the
   BrownSync feature, weighted to the JD.

Together these set the realistic ceiling: about three experiences at two to
three bullets each, CourseTrees at three to five, and two to three further
projects at one bullet each, plus the education lines, fills one page. Adding
an entry anywhere means dropping something somewhere else — check the space budget above before committing.

## ATS parsing — non-negotiable
A resume is read twice: once by a person looking at the page, and once by a
parser reading the PDF's text layer, where `\extracolsep{\fill}` produces no
column structure at all — just two text runs sharing a baseline. The parser
guesses where the left cell ends and what the right one is. Date-shaped runs
guess well; everything else does not. Every rule here exists because a real
submission was mangled by one of them.

1. **`\resumeSubheading` is called organization-first:**
   `{Organization}{Location}{Title}{Dates}`. Never title-first. A title-first
   call puts an organization-plus-location pair on the *second* line of every
   entry — which is exactly the shape of a new job header — so as soon as the
   first line has yielded a company, the second line opens a phantom second
   job that swallows the entry's bullets. This is Jake's original argument
   order, and it is the order every parser is tuned for.
2. **No parentheticals in an organization or title cell.** Not
   `Software Engineer (UTRA)`, not `Brown Space Engineering (PVDX CubeSat)`.
   An acronym in parentheses is promoted to a separate employer; anything that
   does not look like an acronym is silently discarded. If the detail matters,
   put it in a bullet, where it is prose.
3. **Locations are `City, ST` or `City, Country`.** Nothing else validates.
   A campus or site name — `Harwell Science & Innovation Campus, UK` — fails
   the location validator, and unvalidated trailing text falls through into the
   description block, where it is prepended to the entry's bullets. Mirico Ltd.
   renders as **`Didcot, UK`** (the postal town for the Harwell campus).
4. **Spell every month out in full.** `September 2024`, never `Sep. 2024`. The
   period reads as a sentence terminator and truncates the range to a single
   date; the parser then mirrors the start year into the end year, so
   `Sep. 2024 -- May 2028` lands as 2024–2024.
5. **The degree renders as `Bachelor of Science in Applied
   Mathematics-Computer Science`** — Brown's official concentration name, and
   hyphenated rather than joined with "and". Field of Study is a controlled
   picklist in most systems; a conjunction matches no entry and the parser will
   not split it to pick a winner, so the field comes back empty.
6. **Keep `\href` on every link.** Parsers read PDF link annotations, not the
   glyphs, so a bare visible `github.com/RVPhi5` still delivers the full URL.
   This is the one thing the current template already gets right.
7. **Keep labeled key-value pairs labeled.** `\textbf{GPA:} 3.93` parses because it is
   a labeled pair; a bare `3.93` does not.
8. **Every glyph must survive into the text layer.** Use `$\rightarrow$`, never
   `\textrightarrow`: the latter resolves through TS1, whose font is not installed
   as Type1 here, so pdflatex embeds a Type3 bitmap with no ToUnicode entry at
   all and `87→23 min` reaches the ATS as `8723 min`. `$\rightarrow$` takes
   the same arrow from CMSY10, which is Type1 and already declared. The
   preamble pins `asciitilde` and `tilde` to U+007E for the same reason, so
   `\textasciitilde74\%` extracts as `~74%` rather than as a replacement character.

`check.py` enforces rules 1–5 and 8 from the text layer and fails the run on a
violation, so these are checked, not remembered.

## Fit rules — non-negotiable
1. **Exactly one page.** Not 1.1, not 0.8.
2. **No bullet exceeds two lines.**
3. **Every bullet nearly fills its final line** — at least 90% of column width.
4. **No bullet's final line touches the right edge** — it stops at least 4pt
   short of it. Flush is not "extra full"; it is broken. See FLUSH below.
5. **Every heading row keeps clear space between its two cells** — at least
   20pt between the left content and the right-aligned date.
6. **Each Technical Skills category fits on exactly one rendered line.**
   Languages, Frameworks, and Tools & Libraries each occupy a single line. A
   category that wraps reads as an undifferentiated dump and spends a body line
   the page needs for real content.
7. **The page is full.** At most one further body line may fit beneath the last
   line. Two or more lines of empty page at the bottom reads as running out of
   things to say, and is as wrong as spilling onto a second page.

## How to fix violations
**Do not estimate any of this. Measure it.** After writing the `.tex`, compile
with pdflatex and run `python check.py out/<name>.pdf`. Fix what it flags,
recompile, re-check. Repeat until clean. Cap at 8 iterations.

**Aim first drafts at 203–221 characters per bullet.** Measured across a
compiled page: a full body line holds ~113 characters, so that window is two
lines filled to between 90% and 98% — the target the rules below describe. This
is aim, not arithmetic: per-line width actually ranges 102–118 characters
depending on the mix, since digits, capitals and `\texttt` all run wide. One
bullet hit 96.2% at 197 characters while another reached only 92.9% at 212. So
the window makes the first compile land close and the loop short; it never
replaces the loop, and the checker remains the only authority on fill.

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

**FLUSH (last line lands on the right edge):** trim three to five characters —
that is all it takes. A last line with no room left for its own trailing space
pushes that space, and the `\vspace{-2pt}` closing the item, onto a line of
their own. Nothing shows in the text, but ~11pt of dead vertical gap opens
before the next bullet against a normal step of ~13pt, and it is obvious on the
page. Shorten the wording rather than a metric or a technology, as with LONG.
Then re-check the fill: you are aiming between 90% and roughly 98%, not at the
edge.

**WRAPPED (a Technical Skills category runs onto a second line):** cut entries,
never the category. Drop the ones this JD cares about least, preferring
technologies no kept bullet or heading actually demonstrates — the same rule as
a heading's tech stack. Do not shrink the font, merge two categories, or delete
a category outright to make the block fit. Every wrap you remove frees a body
line, so re-check the bottom fill afterwards: the page will usually want a
bullet back on the experience side.

**SPARSE (two or more lines of empty page):** the page is under-filled, so add
real content rather than padding what is there. Cheapest first: a one-line
bullet grown into a full two-line one buys exactly one line, and an extra
bullet on an experience buys two. A whole extra project costs five (a heading
row plus two two-line bullets), so it only fits a page that is genuinely short.
Respect the bullet-count rules above when choosing — projects are capped at two
bullets, so a sparse page is filled from the experience side.

**These interact — respect this order.** After lengthening a short bullet,
re-check it didn't become three lines. After trimming a long one, re-check it
didn't become short, and that it didn't land flush. After trimming a wrapped
skills category, re-check the bottom fill — you just freed a line. After filling
a sparse page, re-check it is still one page. Priority: (1) one page, (2)
two-line maximum, (3) 90% fill, (4) no flush last line, (5) heading gap,
(6) skills lines, (7) bottom fill.

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
