# Content Rules

Use these rules when generating post content for Ghost. The goal is content that is both readable by humans and optimized for generative AI absorption (GEO) — meaning AI systems can extract, synthesize, and cite the content accurately when answering related user queries.

---

## 1. Topic Scope

Each article must cover exactly one well-defined topic or question. A reader should be able to summarize the article's subject in a single sentence before reading it.

- **Narrow, not broad**: "How X works under constraint Y" beats "Everything about X".
- **State the scope explicitly** in the opening paragraph. Do not bury the topic in the middle.
- Avoid combining unrelated sub-topics into one article. Split them instead.

---

## 2. Structure: Headers as User Sub-questions

Headers are the primary navigation layer for both human readers and AI retrieval. Design them as answers to the sub-questions a reader might have about the main topic.

**Targets:**
- Core articles (≥ 1,500 words): aim for **8–12 headers** (H2 + H3 combined)
- Focused articles (800–1,500 words): aim for **4–8 headers**
- Do not publish articles under 300 words — they carry almost no evidence value

**Header design rules:**
- Each H2/H3 should correspond to a distinct user sub-question or decision point
- Prefer descriptive headers over generic ones

  ```
  ❌  "Background"
  ✅  "Why X fails under high concurrency"

  ❌  "Section 2"
  ✅  "How to choose between A and B"
  ```

- Sections should be **relatively self-contained**: a reader dropped into any section should understand its point without reading everything before it

---

## 3. Evidence Density

AI systems prioritize content they can extract as discrete, reusable units. Pack each article with multiple evidence types. The higher types in this list carry more weight:

| Priority | Evidence type | Example pattern |
|----------|--------------|-----------------|
| Highest | **Definition** | "X is defined as…" / "X refers to the practice of…" |
| Highest | **Comparison** | "Compared to Y, X differs in…" / comparison tables |
| High | **Quantified data** | "73% of… (Source, Year)" |
| High | **Concrete example** | "For instance, when A does B, the result is C" |
| Medium | **Step sequence** | "Step 1: … Step 2: …" |
| Lower | **Reference link** | Background-only citations without supporting data |

**Minimum requirement**: every article must contain at least **2 of the top-4 evidence types** (definition, comparison, data, or concrete example).

Avoid articles that consist only of reference links and summary paragraphs — they are absorbed at the lowest rate by generative AI systems.

---

## 4. Source Transparency

Every quantified claim must be traceable. Vague attribution destroys credibility for both human readers and AI systems.

```
❌  "Studies show that remote work improves productivity"
✅  "Stanford researchers found a 13% productivity increase in remote workers (Bloom et al., 2015)"

❌  "According to research…"
✅  "According to the 2025 State of DevOps Report (DORA)…"
```

Rules:
- Attribute data to a named source, organization, or publication
- Include the year when the data has a meaningful shelf life
- Use `reportedly` or `according to [source]` for claims that cannot be independently verified
- Add a disclaimer when the article draws on community feedback that may be biased

---

## 5. Word Count and Depth

Length is only valuable when paired with structure and evidence. Do not pad.

| Article type | Recommended word count |
|---|---|
| Core topic / pillar content | 1,500 – 3,000 words |
| Focused sub-topic / how-to | 800 – 1,500 words |
| Minimum viable article | 300 words |

Below 300 words: do not publish unless the format is inherently short (e.g., a changelog entry). Thin content is neither useful to readers nor to AI retrieval.

---

## 6. Content Type Priority

When choosing how to frame an article, prefer higher-impact content types:

1. **Comparison** — "A vs B", tradeoff tables, decision matrices (highest AI absorption rate)
2. **Definition / Explanation** — "What is X", "How X works"
3. **How-to / Step-by-step** — "How to do X", setup guides, migration guides
4. **Factual reference** — timelines, data summaries, changelogs

Any of these types can apply to any subject domain. A finance article, a dev-ops guide, and a product review can all use comparison or definition framing.

---

## 7. Semantic Alignment

The article's language should match the natural language a reader would use when asking about the topic. AI systems rank content by how well it semantically matches user queries.

- Write headers and opening sentences using the **vocabulary your target reader uses**, not internal jargon
- `meta_description` should read like the answer to a question, not a marketing tagline:

  ```
  ❌  "Discover our in-depth guide to container orchestration"
  ✅  "A comparison of Kubernetes and Nomad for teams running fewer than 20 services"
  ```

- Before drafting, state (mentally or in a comment) the primary question this article answers. Then verify that the title, opening paragraph, and `meta_description` all reflect that question.

---

## 8. What to Avoid

| Anti-pattern | Why |
|---|---|
| Pure Q&A format (short isolated answers) | Low evidence density; poor AI absorption |
| Padding to hit word count | Dilutes evidence density per unit |
| Vague attribution ("studies show…") | Unverifiable; reduces trust signal |
| Topic sprawl (too many unrelated sections) | Weakens topical coherence for AI retrieval |
| Repeating the post title as an H1 in the body | Ghost renders the title separately; creates duplication |
| Subjective labels ("simple", "easy", "powerful") without attribution | Reads as marketing copy, not evidence |

---

## 9. Writing Defaults

- Favor objective technical writing over opinionated phrasing.
- Do not assume the reader's background, skill level, or prior knowledge.
- Prefer concrete descriptions of facts, process, constraints, results, evidence, tradeoffs, and boundaries.
- When relevant, include: the problem or goal, the steps taken, what was observed or measured, limitations and edge cases, where the approach applies and where it does not.
- For markdown workflows, normalize spacing and heading structure before publish: strip a leading title heading if it matches the post title, keep one blank line between blocks, normalize list markers and numbering.
