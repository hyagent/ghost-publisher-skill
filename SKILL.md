---
name: ghost-publisher
description: Publish or update Ghost posts with rich article content and local image uploads using the Ghost Admin API. Use when creating/updating posts from markdown, HTML, or structured JSON, uploading local images, or working with Ghost Admin integrations and API keys.
---

# Ghost Publisher

Use this skill to prepare and publish Ghost posts deterministically from the command line.

## Workflow

### Standard Publishing Workflow

1. **Draft first**: Always start with `--status draft` to create/update a draft.
2. **Find existing post**: Before publishing, check if a post with the same title/slug already exists:
   ```bash
   python3 scripts/ghost_publish.py --find-slug "existing-slug" --print-found
   ```
3. **Update, don't duplicate**: When updating, **always use `--find-slug` or `--update-id`** to target the existing post. Never create multiple drafts with the same title.
4. **Verify slug**: Ensure slug follows the rule: short, lowercase English or short pinyin, no dates/punctuation. If not provided, script will auto-generate a compliant slug.
5. **Publish**: Once the draft is ready, update with `--status published` using the same `--find-slug` to avoid creating a new post.
6. Verify the returned JSON (`id`, `slug`, `url`, `status`).

### Content Deduplication Workflow (Recommended)

Use the built-in similarity detection to avoid creating duplicate or near-duplicate content:

1. **Check for similar content before publishing**:
   ```bash
   python3 scripts/ghost_publish.py \
     --title "AI 工具使用指南" \
     --markdown-file draft.md \
     --check-similar \
     --auto-suggest \
     --status draft
   ```

2. **Review similarity report**: The script will output:
   - Similarity scores for existing posts
   - Recommendation: update vs create new
   - Suggested `--find-slug` if an update is recommended

3. **Act on recommendation**:
   - If similarity > 80%: Use `--find-slug <existing-slug>` to update
   - If similarity 60-80%: Manual judgment required
   - If similarity < 60%: Safe to create new post with `--force-create`

4. **Force create** (when you know it's different enough):
   ```bash
   python3 scripts/ghost_publish.py \
     --title "AI 工具使用指南" \
     --markdown-file draft.md \
     --check-similar \
     --force-create \
     --status draft
   ```

## Rules

- Read credentials only inside the helper script.
- Never print secrets, headers, or raw API key material.
- Use the Ghost Admin API for writes; the Content API is read-only.
- Prefer `draft` unless publishing is explicitly intended.
- Use `source=html` for HTML/markdown workflows; use `source=lexical` only when providing a lexical payload directly.
- Treat `title` and body as separate fields: do not repeat the article title as an H1/H2 in the body when Ghost already receives `title`.
- **Slug rules**:
  - Always provide explicit `--slug` for important posts
  - If not provided, script auto-generates a compliant slug (short, lowercase English/short pinyin, max 40 chars)
  - Avoid long phrases, dates, and punctuation in slugs
  - Verify auto-generated slugs are human-readable before publishing
- When updating existing posts, **always use `--find-slug` or `--update-id`** to avoid creating duplicates
- **Use `--check-similar`** when publishing new content to detect potential duplicates before they are created
- **Prefer updating over creating**: If content similarity > 80%, update the existing post rather than creating a new one
- Normalize markdown before publish so headings, blank lines, bullets, and numbered lists become clean HTML; never preserve raw duplicated list markers like `• - item` or `1. 1. item`.
- When generating technical article content, default to objective writing: reduce subjective opinions, avoid labels like "simple/complex/easy/hard" unless attributed or clearly context-bound, and do not pre-judge the reader's knowledge.
- Prefer concrete facts, process, constraints, results, evidence, pitfalls, and boundaries. Include these when they help the reader understand what was done and what the approach covers.
- Keep structure useful for scanability: clear headings, short paragraphs, lists, and code blocks when needed.

See `references/content-rules.md` for the reusable writing defaults.

## Helper script

`scripts/ghost_publish.py` handles:

- Admin JWT generation from a Ghost admin API key
- Image upload via the Admin API images endpoint (multipart form data)
- Markdown-to-HTML conversion for simple content
- Post creation with tags, authors, excerpt, slug, status, and optional feature image
- Post deletion by ID or slug (via `--delete` flag)
- HTML or lexical publish payload selection
- Tag and author normalization supporting both short form (strings) and long form (objects)

### Supported env vars

- Host: `GHOST_HOST` or `GHOST_ADMIN_HOST` or `GHOST_URL` or `GHOST_ADMIN_URL`
- API key: `GHOST_API_KEY` or `GHOST_ADMIN_API_KEY`
- Optional API version: `GHOST_API_VERSION` (defaults to `v6.0`)

### Tags and authors

Ghost API supports two forms for linking tags and authors to posts:

**Short form** (convenient for CLI):
- Tags: string names → `"Tag Name"` (auto-created if not found)
- Authors: email addresses → `"author@example.com"`

**Long form** (for JSON input with metadata):
- Tags: objects with `name`, `description`, `slug` fields
- Authors: objects with `id` or `email` fields

CLI flags:
- `--tag "name"` or `--tag "name:description:slug"` (colon-separated for metadata)
- `--author "email@example.com"` or `--author '{"id": "..."}'` (JSON object for advanced)

Ghost automatically creates unmatched tags and falls back to the owner role user when no author is matched. See [Ghost API docs on tags and authors](https://docs.ghost.org/admin-api/posts/creating-a-post#tags-and-authors).

Tag normalization (`_normalize_tags`):
- Short form: `"Tag Name"` → `{"name": "Tag Name"}`
- Convenience: `"name:desc:slug"` → `{"name": "name", "description": "desc", "slug": "slug"}`
- Long form: dict objects passed through as-is

Author normalization (`_normalize_authors`):
- Short form: `"email@example.com"` → `{"email": "email@example.com"}`
- Long form: dict objects with `id`/`email`/`name` passed through as-is

### Image uploads and alt text

- The Ghost Admin API images upload endpoint (`/images/upload/`) only accepts the image file. It does NOT accept alt text or metadata fields.
- Alt text belongs in the post content: `<img alt="..." src="...">` in HTML or the corresponding lexical node.
- The helper uploads images and replaces local references in HTML. Alt text is preserved from the original `<img>` tag or markdown `![]()` syntax.
- The `--feature-image-alt` flag is provided for symmetry but is not transmitted to Ghost; consider including alt text in your HTML or lexical content directly.

### Similarity Detection Options

- `--check-similar`: Enable similarity detection before publishing
- `--similarity-threshold`: Title similarity threshold (0-1, default: 0.7)
- `--content-threshold`: Content similarity threshold (0-1, default: 0.5)
- `--auto-suggest`: Auto-suggest update vs create based on similarity scores
- `--force-create`: Force create new post even if similar posts exist

### Example usage

**Check for similar posts before publishing:**

```bash
python3 scripts/ghost_publish.py \
  --title "AI 工具使用指南" \
  --markdown-file draft.md \
  --check-similar \
  --auto-suggest \
  --status draft
```

**Publish a post:**

```bash
python3 scripts/ghost_publish.py \
  --title "My post" \
  --markdown-file post.md \
  --tag "Ghost" --tag "Publishing" \
  --author "me@example.com" \
  --status draft
```

```bash
python3 scripts/ghost_publish.py \
  --input post.json
```

```bash
# Using colon-separated tag metadata: name:description:slug
python3 scripts/ghost_publish.py \
  --title "Tutorial" \
  --markdown-file guide.md \
  --tag "Tutorial:Ghost CMS Guide:ghost-tutorial"
```

**Delete a post:**

To delete a post, use the `--delete` flag with either `--post-id` or `--slug`:

```bash
# Delete by post ID
python3 scripts/ghost_publish.py --delete --post-id "69cf414488c28c0001b36454"

# Delete by slug (will auto-lookup ID)
python3 scripts/ghost_publish.py --delete --slug "ghost-test-publish"
```

The deletion endpoint returns `204 No Content` on success. The output includes the deleted post ID for confirmation.

### Structured input shape

- `title` required
- `html`, `markdown`, or `lexical` required
- `tags`, `authors`, `status`, `excerpt`, `slug`, `feature_image`, `images` optional
- `tags` may be strings (short form) or objects with `name`/`description`/`slug`
- `authors` may be email strings (short form) or objects with `id`/`email`
- `images` may be a list of local paths or objects with `path`/`src`/`file` plus optional `alt`
- For markdown input, the helper should strip a leading title heading if it matches `title`, then emit normalized HTML.

## Reference docs

- `references/ghost-docs.md`: current Ghost API behavior relevant to this skill.
- `references/ghost-llms-full.txt`: comprehensive Ghost Admin API documentation for LLM/agent indexing and detailed reference. Useful for resolving edge cases, understanding API nuances, or when the skill behavior needs updating.
- `references/ghost-llms.txt`: Ghost documentation index for discovering available API sections.

These llms files follow [Mintlify's LLM standard](https://docs.ghost.org/llm.md) and provide up-to-date API reference material. When in doubt about Ghost API behavior, consult `references/ghost-llms-full.txt`.

## Known issues and lessons

### Markdown conversion limitations (2026-04-03)

The `markdown_to_html()` function in `scripts/ghost_publish.py` has evolved through iterative improvements based on real publishing issues:

1. **Initial version**: Only handled headings, lists, code blocks, and inline formatting (bold/italic/links/images)
2. **2026-04-03 fix #1**: Added support for:
   - **Tables**: `| col1 | col2 |` → `<table>` with `<thead>` and `<tbody>`
   - **Blockquotes**: `> text` → `<blockquote>` with recursive markdown parsing for nested content
3. **2026-04-03 fix #2**: Fixed table cell inline formatting:
   - **Root cause**: `parse_table()` was defined before `inline()` in the same function scope, but Python closure rules prevented access
   - **Solution**: Pass `inline` as a parameter to `parse_table(lines, start_idx, inline_fn)`
   - **Result**: `**bold**` in table cells now correctly converts to `<strong>bold</strong>`
4. **2026-04-05 fix**: Added support for horizontal rules:
   - **Syntax**: `---`, `***`, or `___` (3 or more characters)
   - **Output**: `<hr />`
   - **Use case**: Section dividers in markdown content

If you encounter formatting issues in published Ghost articles:
1. Check if the markdown uses tables, blockquotes, or inline formatting within tables
2. Verify the current `markdown_to_html()` function handles them correctly
3. Run a quick Python test before publishing:
   ```python
   from scripts.ghost_publish import markdown_to_html
   html = markdown_to_html("| **A** | B |\n|---|---|\n| **C** | D |")
   assert '<strong>' in html, "Bold not working in tables!"
   ```
4. If not, extend the parser before publishing

### Horizontal rules (thematic breaks)

Markdown `---`, `***`, or `___` lines are now supported and render as `<hr>` elements in Ghost.

**Supported syntax:**
- `---` (3 or more hyphens)
- `***` (3 or more asterisks)
- `___` (3 or more underscores)

**If you want to remove horizontal rules** (e.g., they appear as unwanted visual clutter):
- Remove them from the source markdown with: `sed -i '/^---$/d' draft.md`
- Consider using headings or spacing instead for section separation

### Verify with visual screenshot

Always verify published Ghost drafts with PinchTab before marking complete:
```bash
PINCHTAB_URL=http://localhost:9868 pinchtab nav "<ghost-draft-url>"
sleep 2
PINCHTAB_URL=http://localhost:9868 pinchtab screenshot --full -o draft.png
```
Check for:
- Tables rendered correctly (not as pipe-delimited text)
- Blockquotes styled properly (not showing raw `>` symbols)
- Bold text in table cells visible (e.g., `**MiMo-V2-Pro**` appears bold)
- No unwanted `<hr>` lines
- Proper heading hierarchy

### Publishing workflow

When ready to publish:
1. Fix all formatting issues in the draft
2. **Check for similar posts** (recommended):
   ```bash
   python3 scripts/ghost_publish.py \
     --title "Title" \
     --markdown-file draft.md \
     --check-similar \
     --auto-suggest \
     --status draft
   ```
3. Based on similarity report, either:
   - Update existing: Use `--find-slug` to update the correct post
   - Create new: Use `--force-create` if the content is sufficiently different
4. Verify the published URL and status in the JSON output

### Similarity Detection Algorithm

The similarity detection uses a lightweight approach combining:

1. **Title Similarity**: Sequence matching + containment detection
   - Exact match: 100%
   - One title contains the other: 90%
   - Sequence similarity ratio for partial matches

2. **Content Similarity**: Jaccard similarity on token sets
   - Extracts tokens (Chinese characters + English words)
   - Compares token set overlap
   - Works on HTML content (automatically extracts text)

3. **Combined Score**: Weighted average (title 60%, content 40%)

**Thresholds:**
- >= 80%: High similarity → Strongly recommend update
- 60-79%: Medium similarity → Manual judgment
- < 60%: Low similarity → Safe to create new

### Content Deduplication Best Practices

1. **Always use `--check-similar`** for new content
2. **Review the similarity report** before deciding
3. **Update existing posts** when similarity > 80%
4. **Use consistent slugs** for related content series
5. **Add tags** to distinguish similar but different topics
