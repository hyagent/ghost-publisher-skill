# Content style rules

Use these defaults when generating post content for Ghost before publishing.

## Writing defaults

- Favor objective technical writing over opinionated phrasing.
- Minimize subjective evaluation words such as “simple”, “complex”, “easy”, and “hard”. Use them only when attributed to a source or clearly scoped to a specific context.
- Do not assume the reader’s background, skill level, or prior knowledge.
- Prefer concrete descriptions of facts, process, constraints, results, evidence, tradeoffs, and boundaries.
- When relevant, include:
  - the problem or goal
  - the steps taken
  - what was observed or measured
  - limitations, edge cases, and pitfalls
  - where the approach does and does not apply

## Ghost-specific structure

- Keep `title` separate from body content; do not repeat the title as an H1/H2 in the article body unless that heading serves a distinct editorial purpose.
- Write a slug that is short, lowercase, and easy to read. Prefer concise English or short pinyin; avoid long sentences, dates, and punctuation.
- For markdown workflows, normalize spacing and heading structure before publish:
  - strip a leading title heading if it matches the post title
  - keep one blank line between blocks
  - normalize list markers and numbering
  - remove duplicated or malformed list prefixes
- Preserve useful structure with headings, lists, code blocks, and short paragraphs so the post is easy to scan.
