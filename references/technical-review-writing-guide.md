# Article Structure Templates

These templates cover the most common article types. Each maps to one of the high-impact GEO content types (comparison, definition, how-to, factual reference). Choose the template that matches the article's primary purpose, then adapt section headings to fit the subject.

All templates are subject to the rules in `content-rules.md`. Key constraints to keep in mind while writing:
- Each H2/H3 should answer a user sub-question
- Include at least 2 of: definition, comparison, quantified data, concrete example
- Every quantified claim needs a named source
- Word count: ≥ 1,500 words for core articles, ≥ 800 words for focused sub-topics

---

## Template 1: Comparison Article

**Use when**: comparing two or more tools, approaches, frameworks, products, or strategies.

**Why prioritize this type**: comparison articles have the highest AI absorption rate. They contain definitions, contrast data, and decision criteria — all high-value evidence units.

### Structure

```
## What is [A]? / What is [B]?
(one-paragraph definition of each; establishes baseline for the comparison)

## When to use [A]
(concrete scenarios, constraints, prerequisites)

## When to use [B]
(concrete scenarios, constraints, prerequisites)

## Head-to-head: [Dimension 1]
(e.g., performance, cost, setup complexity — pick the dimensions that matter most to the reader)

## Head-to-head: [Dimension 2]

## Head-to-head: [Dimension 3]

## Known limitations and tradeoffs
(cover weaknesses of both sides; cite community or official sources)

## Summary comparison table
| Dimension    | A   | B   |
|---|---|---|
| …            | …   | …   |

## Decision guide: which to choose
(structured recommendations by use case, not a blanket verdict)

## References
```

### Writing rules specific to comparisons

- Do not declare a winner without criteria. "A is better" is not a finding; "A outperforms B under load > 10k RPS (benchmark source)" is.
- Positive and negative evidence must be present for both sides.
- For community-sourced claims, use blockquotes with attribution:
  ```
  > "quote from user"
  > — Source (Reddit / GitHub Issues / forum)
  ```
- Add a disclaimer if the comparison relies on community feedback that may be biased.

---

## Template 2: Definition / Explanation Article

**Use when**: explaining what something is, how it works, or why it exists.

**Why prioritize this type**: definition articles are the second-highest AI absorption type. Clear, structured definitions are extracted verbatim or near-verbatim by AI systems.

### Structure

```
## What is [topic]?
(clear, direct definition in the first sentence; no preamble)

## Why [topic] exists / the problem it solves
(concrete motivation; what breaks without it)

## How [topic] works
(mechanism, architecture, or process — as concrete as the subject allows)

## Key concepts and terminology
(define sub-terms that are necessary to understand the topic)

## [Topic] vs [related concept]
(at least one comparison to an adjacent concept clarifies the boundaries)

## Common misconceptions
(address what readers often get wrong; strengthens semantic authority)

## Practical examples
(at least one concrete, end-to-end example)

## Limitations and when [topic] does not apply
(sets honest boundaries; prevents misuse)

## References
```

### Writing rules specific to definitions

- The definition in the first H2 must be self-contained — a reader (or AI) extracting just that paragraph should get a complete, accurate answer.
- Avoid circular definitions ("X is the process of doing X").
- Prefer active voice: "X converts Y into Z" over "Y is converted by X".

---

## Template 3: How-to / Step-by-step Article

**Use when**: guiding a reader through a process — setup, migration, configuration, debugging, or any sequential task.

### Structure

```
## What this guide covers
(scope: what will be set up/achieved, the starting state, and any prerequisites)

## Prerequisites
(list explicitly: tools, access levels, versions, prior knowledge)

## Step 1: [Action]
(one coherent action per step; include the command or code, and what success looks like)

## Step 2: [Action]

## Step N: [Action]

## Verification
(how to confirm the process succeeded end-to-end)

## Common errors and fixes
(the top 3–5 failure modes; each with symptom, cause, and fix)

## Limitations and edge cases
(where this guide does and does not apply)

## References
```

### Writing rules specific to how-tos

- Each step heading should contain a verb: "Install the dependency", not "Installation".
- After every non-trivial command or code block, state what the expected output or state change is.
- Do not skip steps because they seem "obvious". State prerequisites and expected environment explicitly.
- "Common errors" is a high-value section: AI systems use it to answer debugging queries that would otherwise miss the guide entirely.

---

## Template 4: Factual Reference / Data Summary

**Use when**: presenting a curated set of facts, data points, timelines, or specifications that a reader needs to look up rather than act on.

### Structure

```
## What this reference covers
(scope and intended audience)

## [Data category 1]
(table or structured list; every row has a source if the data is quantified)

## [Data category 2]

## Methodology / data sources
(how the data was gathered, when it was last updated, known gaps)

## Changelog
(if the reference is updated over time, list what changed and when)

## References
```

### Writing rules specific to factual references

- Every quantified data point needs a source inline, not just in the references section.
- State the data collection date. Stale data without a date is misleading.
- For data with significant variance across sources, note the range and explain the discrepancy.

---

## Universal Writing Principles

These apply to all article types.

### Evidence and attribution

- Every claim that can be verified should be. If it cannot, say so.
- Use direct quotation (`> "…" — Source`) for community or user feedback.
- Use "reportedly" or "according to [source]" for claims that are plausible but not independently verified.
- Do not use vague attribution: "research shows", "experts say", "it is widely believed".

### Objectivity

- Avoid subjective evaluation words ("simple", "powerful", "revolutionary") unless quoting a source.
- Distinguish between what is observed/measured and what is interpreted or inferred.
- Positive and negative aspects must both appear; omitting known weaknesses is a credibility failure.

### Verifiability

- All links must be clickable and point to the intended resource.
- All data has a source, year, and (where relevant) methodology note.
- Uncertain information is labeled; the reader should never have to guess which claims are speculative.

### Acknowledging limits

- State what the article does not cover.
- When quantitative data is unavailable, say so: "No published benchmark exists for this comparison as of [date]."
- Add a disclaimer when the article draws primarily on community discussion:
  ```
  *This article is based on publicly available community discussion and official documentation.
   It does not constitute professional advice.*
  ```
