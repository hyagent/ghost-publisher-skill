---
name: ghost-publisher
description: Publish, update, browse, and search Ghost posts using the Ghost Admin API (writes) and Content API (reads). Use when creating/updating posts from markdown, HTML, or structured JSON, uploading local images, finding or listing existing posts by tag/status/keyword, working with Ghost Admin integrations and API keys, or managing tags.
---

# Ghost Publisher

## Security Rules (Critical)

- **Treat `GHOST_ADMIN_API_KEY`, `GHOST_CONTENT_API_KEY`, and `GHOST_HOST` as black boxes**: The AI agent must NEVER read the actual values of these environment variables into the conversation context. Do not use `echo`, `env`, `cat`, `grep`, or any other command to inspect or reveal their values. Invoke the helper script directly and let it read the variables internally.
- **NEVER expose credential values**: Do not print, log, or return the values of `GHOST_ADMIN_API_KEY`, `GHOST_CONTENT_API_KEY`, `GHOST_API_KEY`, `GHOST_HOST`, `GHOST_ADMIN_HOST`, `GHOST_URL`, or `GHOST_ADMIN_URL`. These values must remain inside the helper script only.
- **Never print secrets, headers, or raw API key material**.
- **If credentials are missing**: When the script fails with a credential error, tell the user which environment variables are needed and ask them to set them. Do not attempt to read or guess the values.
- **Privacy scrub before publish**: Before writing or publishing any article derived from real operations, replace all personally identifiable or sensitive information with generic placeholders. This includes:
  - IP addresses (public, private, Tailscale) → `<YOUR_PUBLIC_IP>`, `<INTERNAL_IP>`, `<TAILSCALE_IP>`
  - Hostnames and device names → `<your-device>`
  - Tailnet domain names (e.g. `xxx.tailbff26.ts.net`) → `<your-device>.xxx.ts.net`
  - Usernames and email addresses → `user@` or `user@example.com`
  - API keys, tokens, UUIDs → `<YOUR_API_KEY>`
  - Any other site-specific or account-specific identifiers
  - Apply the same scrub to both the local markdown file and the published Ghost post.

## Security Best Practices

1. **Before using `ghost-publisher` (or any credential-bearing skill), review its security rules first.** This prevents accidental attempts to read or print environment variables into the conversation context.

2. **Use the helper script's built-in flags for all lookups.** When you need to check API connectivity, find duplicate posts, browse article lists, search by keyword, or verify existing slugs, always use the wrapper script's native options (`--find-slug`, `--find-title`, `--print-found`, `--list-posts`, `--search`, `--list-tags`, etc.) instead of writing custom Python or shell snippets that read `GHOST_API_KEY` or `GHOST_HOST` directly.

3. **Redact PII in tool outputs before presenting them.** The Ghost Admin API JSON responses may contain author emails and other PII. When summarizing or quoting tool results, scan for fields like `email`, `password`, `token`, `key`, `secret`, `credential`, and replace them with placeholders (e.g., `yu***@gmail.com` or `<AUTHOR_EMAIL>`). Do not let raw PII sit in the conversation history.

## Skill Maintenance & Generalization Rule (Critical for Future Edits)

`ghost-publisher` is a **general-purpose skill**, not a project-specific tool. When you are instructed to modify or improve this skill, you **must not** embed any site-specific, project-specific, or proprietary information into the skill source code or documentation.

**Strictly forbidden** in skill files (`SKILL.md`, `scripts/ghost_publish.py`, `references/*.md`, etc.):
- Specific website names, domain names, or publication titles (e.g., `IT小灶`, `hitorch.cn`, `example-blog.com`)
- Site-specific tag names, category names, author names, or content themes used as hardcoded examples
- Real article titles, slugs, or feature images from any specific project
- Project-specific anecdotes like "derived from SEO optimization on X site"
- Site-specific color schemes, brand assets, or navigation structures

**Correct approach**:
- Use **generic placeholders** in all examples: `站点名称`, `example.com`, `标签一`, `标签二`, `Author Name`, `Category A`, `Category B`
- Use **abstract, generalized examples** when illustrating rules: e.g., "An article about a business process should not be tagged with unrelated broad tech terms"
- Keep all project-specific customizations (actual tag lists, site names, author bios, SEO targets) in **user-level configuration files, environment variables, or workspace notes**, never inside the skill repository itself
- If the user asks you to encode a lesson learned from a specific project into the skill, translate it into a **universal principle** before writing it into the skill files

If you are unsure whether an example or piece of text is too specific, **err on the side of abstraction**.

## Publishing Workflow

1. **Draft first**: Always start with `--status draft` to create/update a draft.
2. **Find existing post**: Before publishing, check if a post with the same title/slug already exists:
   ```bash
   python3 scripts/ghost_publish.py --find-slug "existing-slug" --print-found
   ```
3. **Update, don't duplicate**: When updating, **always use `--find-slug` or `--update-id`** to target the existing post. Never create multiple drafts with the same title.
4. **Verify slug**: Ensure slug follows the rule: short, lowercase English or short pinyin, no dates/punctuation. If not provided, script will auto-generate a compliant slug.
5. **Publish**: Once the draft is ready, update with `--status published` using the same `--find-slug` to avoid creating a new post.

### Frontmatter-first writing (required)

When generating or editing a markdown file for Ghost publication, **always include a YAML frontmatter block at the very top**. The publish script automatically extracts these fields, so metadata is written at creation time—not patched later.

Required frontmatter for SEO and structural correctness:
```yaml
---
title: "文章主标题"
slug: "wen-zhang-slug"
meta_title: "SEO 标题 | 站点名称"
meta_description: "SEO 描述，≤ 160 字符，包含关键词与行动召唤"
feature_image: "feature-image.jpg"
tags: ["标签一", "标签二"]
---
```

Guidelines:
- `title`: do not repeat it as an H1/H2 in the body; Ghost already renders it as the page H1.
- `slug`: short, lowercase English or short pinyin, no dates or punctuation.
- `meta_description`: keep it ≤ 160 chars. Write it as the direct answer to the question this article addresses — using the vocabulary the target reader would use when searching. Avoid marketing taglines. This is used for SEO and will NOT be rendered on the article page.
- `excerpt` (optional): maps to Ghost's `custom_excerpt`. **Caution**: Ghost default themes render `custom_excerpt` prominently under the article title on the single-post page. Only use it if you intentionally want a sub-headline/summary to appear there; for pure SEO descriptions, rely on `meta_description` instead.
- `tags`: **max 2 tags**, must reflect the article's **core topic** (not every keyword that appears). Run `--list-tags` first and reuse canonical tags. Avoid broad keyword-stuffing tags (e.g., do not tag every article with a general term like `AI` unless AI is the primary subject). When in doubt, choose the narrower/specific tag over the broad one.

## Tag Management

The script includes built-in tag normalization and maintenance tools to prevent tag proliferation.

### Built-in tag aliases

The script automatically maps common synonymous tags to canonical names:
- `Hermes Agent` → `Hermes`
- `AI Agent` → `Agent`
- `记忆` → `Memory`

### CLI commands

**List all tags**
```bash
python3 scripts/ghost_publish.py --list-tags
```

**Merge two tags** (moves all posts, then deletes the source tag)
```bash
python3 scripts/ghost_publish.py --merge-tags from_slug:to_slug
```

**Preview a merge without applying**
```bash
python3 scripts/ghost_publish.py --merge-tags from_slug:to_slug --dry-run
```

**Delete empty tags**
```bash
python3 scripts/ghost_publish.py --delete-empty-tags
```

**Preview empty-tag deletion**
```bash
python3 scripts/ghost_publish.py --delete-empty-tags --dry-run
```

### Tag discipline for agents

When creating or updating a post, you must prevent tag proliferation through active pre-flight checks:

1. **Always inspect existing tags first** by running `--list-tags` before assigning tags to a new post.
2. **Maximum 2 tags per post**. Ghost does not enforce a limit, but exceeding 2 tags dilutes topical authority and creates low-value tag pages. If you find yourself wanting 3+ tags, re-evaluate which 2 are most central.
3. **Tag must match core topic, not keyword-stuffing**. Do not add a tag just because the word appears in the article. A tag should represent the **primary subject** the reader would expect to find on that tag page.
   - Example: An article about "setting up a US LLC to get a debit card" should not be tagged with broad tech terms just because it mentions paying for SaaS tools. Its correct tags are the business/finance categories it actually covers.
   - Example: A guide about integrating a specific framework should be tagged with that framework and its domain (e.g., `FrameworkName, DevOps`), not with unrelated broad topics like `AI` unless AI architecture is the main subject.
4. **Align with the site's content boundaries**. Tags should map to the site's established content pillars. Do not introduce one-off tags that do not fit the overall taxonomy.
5. **Reuse existing tags** whenever possible. Do not invent a new tag if an existing one covers the same concept.
6. **Do not create near-duplicate tags**. If `--list-tags` shows a tag that is identical, contains, or highly similar (edit distance ≤ 2) to your intended tag, you must use the existing tag instead.
7. **Use built-in aliases**. The script automatically collapses `Hermes Agent` → `Hermes`, `AI Agent` → `Agent`, `记忆` → `Memory`. Rely on this mechanism rather than manual cleanup.
8. **Merge existing duplicates immediately**. If you discover two live tags that mean the same thing during your work, merge them on the spot with `--merge-tags` instead of leaving them for later.
9. **Skip the check only when certain**. Use `--skip-tag-check` only if the user explicitly overrides the warning.

## Post Operations

### Find an existing post first
```bash
python3 scripts/ghost_publish.py --find-slug "existing-slug" --print-found
python3 scripts/ghost_publish.py --find-title "Existing Title" --print-found
```

### Update an existing post when appropriate
```bash
python3 scripts/ghost_publish.py \
  --find-slug "existing-slug" \
  --markdown-file draft.md \
  --status draft
```

### Update only post metadata (no content changes)
```bash
python3 scripts/ghost_publish.py \
  --find-slug "existing-slug" \
  --excerpt "New excerpt" \
  --meta-title "New SEO title" \
  --meta-description "New SEO description"
```

### Bulk-update metadata for many posts
```bash
python3 scripts/ghost_publish.py --bulk-meta-file meta_updates.json
```

`meta_updates.json` format:
```json
{
  "post-slug-1": {
    "meta_title": "SEO title 1",
    "meta_description": "SEO description 1",
    "excerpt": "Excerpt 1"
  },
  "post-slug-2": {
    "meta_title": "SEO title 2",
    "meta_description": "SEO description 2"
  }
}
```

### Create a new post when no match exists
```bash
python3 scripts/ghost_publish.py \
  --title "AI 工具使用指南" \
  --markdown-file draft.md \
  --slug "ai-tool-guide" \
  --status draft
```

### Delete a post
```bash
# Delete by post ID
python3 scripts/ghost_publish.py --delete --post-id <id>

# Delete by slug (will auto-lookup ID)
python3 scripts/ghost_publish.py --delete --slug "ghost-test-publish"
```

## Post Browse & Search

Use these commands to **discover existing posts** without knowing the exact slug or title. This is especially important when resuming work across sessions — always check what already exists before creating new posts.

### List recent posts (default: 20, sorted by updated_at desc)
```bash
python3 scripts/ghost_publish.py --list-posts
```

### List posts with filters
```bash
# Filter by tag slug
python3 scripts/ghost_publish.py --list-posts --tag hermes

# Filter by status
python3 scripts/ghost_publish.py --list-posts --status draft

# Combine tag + status
python3 scripts/ghost_publish.py --list-posts --tag hermes --status published

# Custom page size and sort
python3 scripts/ghost_publish.py --list-posts --limit 50 --page 2 --order "published_at desc"
```

Output fields: `id`, `title`, `slug`, `status`, `updated_at`, `published_at`, `url`.

### Search posts by title keyword
```bash
python3 scripts/ghost_publish.py --search "关键词"
python3 scripts/ghost_publish.py --search "docker" --limit 10
```

The search uses Ghost Admin API's NQL `title:~'keyword'` filter (server-side substring match on title). Falls back to a full list client-side scan if the NQL filter returns empty results (e.g. for titles with special characters).

### Cross-session workflow for updating an existing post

When memory refers to a post that was previously published but the slug is uncertain:

1. **Search by keyword first**:
   ```bash
   python3 scripts/ghost_publish.py --search "文章主题关键词"
   ```
2. **Pick the matching slug from results**, then fetch full details:
   ```bash
   python3 scripts/ghost_publish.py --find-slug "confirmed-slug" --print-found
   ```
3. **Update using the confirmed slug**:
   ```bash
   python3 scripts/ghost_publish.py --find-slug "confirmed-slug" --markdown-file updated.md
   ```

Never skip step 1–2 and go straight to writing — always confirm the slug exists before updating.

## Writing Guidelines

- Use the Ghost Admin API for writes; the Content API is read-only.
- Prefer `draft` unless publishing is explicitly intended.
- Use `source=html` for HTML/markdown workflows; use `source=lexical` only when providing a lexical payload directly.
- Treat `title` and body as separate fields: do not repeat the article title as an H1/H2 in the body when Ghost already receives `title`.
- **Frontmatter support**: When writing a markdown file, include a YAML frontmatter block at the top. The script automatically extracts `title`, `slug`, `excerpt`, `meta_title`, `meta_description`, `feature_image`, `status`, `tags`, and `authors`. Example:
  ```yaml
  ---
  title: "文章主标题"
  slug: "wen-zhang-slug"
  meta_title: "SEO 标题 | 站点名称"
  meta_description: "SEO 描述，≤ 160 字符"
  feature_image: "feature-image.jpg"
  tags: ["标签一", "标签二"]
  ---
  ```
- When modifying skill files or article drafts in a git-tracked workspace, check `git status` before editing, keep changes atomic, and create a commit after verification so every revision is recoverable.
- **Slug rules**:
  - Always provide explicit `--slug` for important posts
  - If not provided, script auto-generates a compliant slug (short, lowercase English/short pinyin, max 40 chars)
  - Avoid long phrases, dates, and punctuation in slugs
  - Verify auto-generated slugs are human-readable before publishing
- When updating existing posts, **always use `--find-slug` or `--update-id`** to avoid creating duplicates
- Normalize markdown before publish so headings, blank lines, bullets, and numbered lists become clean HTML; never preserve raw duplicated list markers like `• - item` or `1. 1. item`.
- **Content quality (GEO)**: Every article must be optimized for both human readers and generative AI absorption. Before drafting any article body, read `references/content-rules.md` and select the appropriate structure from `references/technical-review-writing-guide.md`. The non-negotiable minimums are:
  - One article = one clearly defined topic (statable in a single sentence)
  - Headers answer user sub-questions, not generic labels ("Why X fails" not "Background")
  - At least 2 of: definition, comparison, quantified data with named source, concrete example
  - Core articles ≥ 1,500 words; focused articles ≥ 800 words; never publish < 300 words
  - `meta_description` reads like a direct answer to the question the article addresses — not a marketing tagline

## Image Uploads

- The Ghost Admin API images upload endpoint (`/images/upload/`) only accepts the image file. It does NOT accept alt text or metadata fields.
- Alt text belongs in the post content: `<img alt="..." src="...">` in HTML or the corresponding lexical node.
- The helper uploads images and replaces local references in HTML. Alt text is preserved from the original `<img>` tag or markdown `![]()` syntax.

## JSON Input Format

- `title` required
- `html`, `markdown`, or `lexical` required
- `tags`, `authors`, `status`, `excerpt`, `slug`, `feature_image`, `images` optional
- `tags` may be strings (short form) or objects with `name`/`description`/`slug`
- `authors` may be email strings (short form) or objects with `id`/`email`
- `images` may be a list of local paths or objects with `path`/`src`/`file` plus optional `alt`

## Tag Normalization

**Short form** (convenient for CLI):
- Tags: string names → `"Tag Name"` (auto-created if not found)

**Long form** (for JSON input with metadata):
- Tags: objects with `name`, `description`, `slug` fields

CLI flags:
- `--tag "name"` or `--tag "name:description:slug"` (colon-separated for metadata)

Tag normalization (`_normalize_tags`):
- Short form: `"Tag Name"` → `{"name": "Tag Name"}`
- Convenience: `"name:desc:slug"` → `{"name": "name", "description": "desc", "slug": "slug"}`
- Aliases are applied before parsing so synonymous tags collapse to the canonical name.

Author normalization (`_normalize_authors`):
- Short form: `"email@example.com"` → `{"email": "email@example.com"}`

## Environment Variables

- Host: `GHOST_HOST` or `GHOST_ADMIN_HOST` or `GHOST_URL` or `GHOST_ADMIN_URL`
- Admin API key (required for writes and admin reads): `GHOST_ADMIN_API_KEY` (preferred) or `GHOST_API_KEY`
- Content API key (optional, for public-content reads): `GHOST_CONTENT_API_KEY` — currently unused by the helper script because the Admin API already covers all read operations needed for post lookup and browsing. Set this if you need to integrate with external tools that require the Content API key.

## Verification Checklist

1. **GEO content quality** (check before publishing)
   - Topic scope is narrow and can be stated in one sentence
   - Each H2/H3 corresponds to a user sub-question, not a generic label
   - Article contains at least 2 of: definition, comparison, quantified data, concrete example
   - Every quantified claim has a named, traceable source
   - Core articles: ≥ 1,500 words; focused articles: ≥ 800 words
   - `meta_description` reads like an answer to a question, not a marketing tagline
   - See `references/content-rules.md` and `references/technical-review-writing-guide.md` for full rules

2. **Writing style**
   - Objective, factual, and concise
   - Avoid unnecessary hype, vague praise, or reader-assumption language

3. **HTML rendering correctness**
   - Headings render in the expected hierarchy
   - Bullet lists, numbered lists, blockquotes, tables, and code blocks render cleanly
   - Inline code, links, and emphasis are preserved after markdown-to-HTML conversion

4. **Layout and readability**
   - Paragraph spacing is consistent
   - List nesting is clear
   - Code fences are closed and syntax highlighting is sensible

5. **Clickable URL / link correctness**
   - Use Markdown links (`[text](https://...)`) for source URLs you want readers to click
   - Avoid bare URLs when the display text matters
   - Confirm each URL points to the intended page and uses the correct anchor if present

## Duplicate Check Before Publishing

Before creating a new post, always verify that no similar article already exists:

1. **Search by title keyword**:
   ```bash
   python3 scripts/ghost_publish.py --search "文章主题关键词"
   ```
2. If results show a matching post: use `--find-slug` to update it instead of creating a new one.
3. If no results: proceed with creating a new post.

This manual check replaces any automated similarity scoring — the agent should use judgment based on title overlap and content intent.

## Markdown-to-HTML Conversion History

1. **Initial version**: Only handled headings, lists, code blocks, and inline formatting (bold/italic/links/images)
2. **2026-04-03 fix #1**: Added support for:
   - **Tables**: `| col1 | col2 |` → `<table>` with `<thead>` and `<tbody>`
   - **Blockquotes**: `> text` → `<blockquote>` with recursive markdown parsing for nested content
3. **2026-04-03 fix #2**: Fixed table cell inline formatting:
   - **Root cause**: `parse_table()` was defined before `inline()` in the same function scope, but Python closure rules prevented access
   - **Solution**: Pass `inline` as a parameter to `parse_table(lines, start_idx, inline_fn)`
   - **Result**: `**bold**` in table cells now correctly converts to `<strong>bold</strong>`
4. **2026-04-05 fix**: Added support for horizontal rules:
   - `---` or `***` → `<hr />`
5. **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., `$\rightarrow$`) to Unicode equivalents (`→`) to prevent raw LaTeX rendering in Ghost.
6. **2026-04-11 fix**: Added tag management commands (`--list-tags`, `--merge-tags`, `--delete-empty-tags`), built-in tag aliases, and tag conflict detection to prevent tag proliferation.
7. **2026-04-13 fix**: Added bulk metadata update (`--bulk-meta-file`) and allowed metadata-only updates for existing posts without requiring content re-upload.
8. **2026-04-16 fix**: Added `--list-posts` and `--search` commands for post browsing and title keyword search. Improved `find_post` title lookup to use Admin API NQL filter first (avoids full list scan). Removed non-existent `--check-similar`/`--auto-suggest` flags from docs and replaced with a manual search-based duplicate-check workflow.
9. **2026-04-27 fix**: Fixed table detection bug where any line containing `|` (including Markdown links like `[title | site](url)`) was incorrectly treated as a table row. Changed condition from `if "|" in line:` to `if line.strip().startswith("|")`.

If you encounter formatting issues in published Ghost articles:
1. Check if the markdown uses tables, blockquotes, or inline formatting within tables
2. Verify the current `markdown_to_html()` function handles them correctly
3. Run a quick Python test before publishing:
   ```python
   from scripts.ghost_publish import markdown_to_html
   html = markdown_to_html("| **A** | B |\n|---|---|\n| **C** | D |")
   assert '<strong>' in html, "Bold not working in tables!"
   ```

## References

**Read before writing any article** (required for every content creation task):
- `references/content-rules.md`: full GEO content rules — topic scope, header design, evidence density, source transparency, word count targets, content type priority, semantic alignment, and writing defaults.
- `references/technical-review-writing-guide.md`: article structure templates (comparison, definition/explanation, how-to, factual reference) with GEO rationale and writing rules for each type.

**Read on demand** (API behavior, edge cases, troubleshooting):
- `references/ghost-docs.md`: current Ghost API behavior relevant to this skill.
- `references/ghost-llms-full.txt`: comprehensive Ghost Admin API and Content API documentation for LLM/agent indexing.
- `references/images-api.md`: notes on the Ghost images upload API.
