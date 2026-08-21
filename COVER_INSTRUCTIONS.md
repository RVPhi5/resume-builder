# Cover Letter Instructions

## Task
When I ask for a cover letter, produce a **one-page** letter as LaTeX, built on
the same letterhead as my resumes, compiled to PDF and checked with
`check_cover.py`.

A cover letter is not a resume in prose. The resume already lists what I did and
what it measured. The letter says, in my voice, what kind of work I want and why
this company. If a sentence would be better as a resume bullet, cut it.

## Source of truth
`master.txt` is the only source for anything factual — projects, roles,
technologies, metrics. **Never invent experience.** The letter may describe that
work loosely ("flight software for a CubeSat", "a production data pipeline")
where the resume is exact, but loose is not the same as new: if `master.txt`
doesn't say it, it doesn't go in.

Dates, company names, and my degree program are never adapted.

## Length and shape
- **150–200 words of body** is the target. `check_cover.py` accepts 120–260 and
  fails outside that; it does not fail you for being at 150 rather than 200,
  so aim short.
- **Three paragraphs.** A fourth is allowed only when the middle paragraph is
  covering two genuinely different bodies of work and reads as a pile otherwise.
- **Paragraph one:** what I'm applying for, what I study, and one plain sentence
  about the kind of software I've built. No thesis statement about myself.
- **Paragraph two:** the work. One or two concrete things, described the way I'd
  describe them out loud. This is where the letter earns its page.
- **Paragraph three:** why this company, and a short close. Two sentences.

## Voice — this is the part that gets rewritten
Write it the way a competent junior would say it to another engineer. Plain,
specific, a little understated. Concretely:

- **Use contractions.** "I'm", "I've", "I'd". Zero contractions reads as
  generated, and the checker fails a letter without at least two.
- **No em-dashes.** Not `---`, not `\textemdash`, not a literal `—`. Use a
  comma, a colon, or two sentences. (`--` in a date range is fine.)
- **No self-characterizing thesis lines.** "I write software for systems that
  have to keep working when something goes wrong" is the shape to avoid: it
  describes what I *am* rather than what I did.
- **No claims on my own humility.** "The work I'm proudest of there is
  unglamorous" — cut. Just say what the work was.
- **No flattering the employer.** "SpaceX builds hardware where that standard is
  the baseline, and I would like to learn from engineers who hold it" — cut.
  Say what I want to work on; let the company be the place that does it.
- **No aphorisms or lesson-morals.** Anything ending "...is the engineering, not
  the cleanup afterward" or "taught me that X" is a line written for effect.
- **No stock phrases.** Passionate, excited, thrilled, fast-paced, leverage,
  cutting-edge, proven track record, perfect fit. The checker holds a longer
  list and fails on any of them.

The test for any sentence: would I say this out loud to an engineer at the
company, or is it aimed at a reader I imagine being impressed? Cut the second
kind.

## Metrics
**Keep them out unless one carries the paragraph.** The resume goes in the same
envelope and every number is already there. At most one number in the letter,
and only when the sentence collapses without it. "Making it faster, and figuring
out why it fails when it does" beats "cutting runtime 74%" here — the letter is
for register, the resume is for evidence.

## Awards
Awards are not accomplishments in a letter; they are validation of one. Mention a
fellowship or award only as a clause attached to the work it funded, never as its
own sentence and never as the subject of a paragraph.

## Structure to write
The letterhead comes from `template_head.tex`, identical to every resume. Write
only the body below, starting after the head's `\end{center}`:

```latex
\vspace{14pt}

\begin{flushleft}
<Month D, YYYY> \\[10pt]
Hiring Team \\
<Company>
\end{flushleft}

\vspace{6pt}

Dear Hiring Team, \\[8pt]

<paragraph one>

\vspace{6pt}

<paragraph two>

\vspace{6pt}

<paragraph three>

\vspace{10pt}

\begin{flushleft}
Sincerely, \\[6pt]
Rohan Vittal
\end{flushleft}

\end{document}
```

Address it to "Hiring Team" unless the posting names a person. Date it the day
it's built; if I submit later I'll change that line myself.

## Workflow
```bash
# the JD is saved the same way as for a resume
jds/<stem>.txt                    ->  out/<stem>_cover_<YYYY-MM-DD>.tex

# write the body somewhere scratch, then:
cat template_head.tex <body>.tex > out/<stem>_cover_<YYYY-MM-DD>.tex

pdflatex -interaction=nonstopmode -halt-on-error -output-directory=out \
    out/<stem>_cover_<YYYY-MM-DD>.tex
python check_cover.py out/<stem>_cover_<YYYY-MM-DD>.pdf
```

Concatenate once. Every fix after that is an ordinary edit to the file in
`out/`. Keep `.tex` files bare-LF. Delete `out/*.aux`, `*.log`, `*.out` when
done, and leave everything else in `out/` alone.

The `_cover` marker in the filename is what lets the checker find the JD: it
strips the trailing date and then `_cover` to get back to `jds/<stem>.txt`. A
letter that doesn't resolve to a JD still compiles, but the checker says so.

## How to fix what the checker flags
| Flag | Fix |
|---|---|
| `PAGES != 1` | Cut a paragraph. A cover letter never spills. |
| body over/under words | Cut or add one concrete clause about the work, not adjectives. |
| `LONG` paragraph | Split it, or drop the least specific sentence. |
| `RUNON` | One sentence swallowed two ideas. Break it at the conjunction. |
| `EMDASH` | Comma, colon, or full stop. |
| `PHRASE` | Say the specific thing the phrase was standing in for. |
| `VOICE` | Delete the sentence and state what I did instead. Do not rephrase it — the shape is the problem, not the wording. |
| `PLACEHOLDER` | Fill it. Usually a company name from a previous letter. |
| contractions | Loosen one or two sentences; don't sprinkle them mechanically. |

**Never show me a letter you haven't compiled and checked.** Same rule as the
resume: write the `.tex`, compile, run `check_cover.py`, fix, repeat until it
prints PASS. Cap at 6 iterations, then show me what's outstanding.

## Output
Then tell me, briefly:
- which work I claimed and why it fits this JD
- anything the JD asked for that the letter deliberately doesn't address
- whether the letter and the tailored resume overlap too much
