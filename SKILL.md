---
name: ghost-publisher
description: Publish or update Ghost posts with rich article content and local image uploads using the Ghost Admin API. Use when creating/updating posts from markdown, HTML, or structured JSON, uploading local images, or working with Ghost Admin integrations and API keys.
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

1. **Draft first**: Always start with `--status draft` to create/update a draft.
2. **Find existing post**: Before publishing, check if a post with the same title/slug already exists:
   ```bash
   python3 scripts/ghost_publish.py --find-slug "existing-slug" --print-found
   ```
3. **Update, don't duplicate**: When updating, **always use `--find-slug` or `--update-id`** to target the existing post. Never create multiple drafts with the same title.
4. **Verify slug**: Ensure slug follows the rule: short, lowercase English or short pinyin, no dates/punctuation. If not provided, script will auto-generate a compliant slug.
5. **Publish**: Once the draft is ready, update with `--status published` using the same `--find-slug` to avoid creating a new post.
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

1. **Find an existing post first**
   ```bash
   python3 scripts/ghost_publish.py --find-slug "existing-slug" --print-found
   python3 scripts/ghost_publish.py --find-title "Existing Title" --print-found
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

2. **Update an existing post when appropriate**
   ```bash
   python3 scripts/ghost_publish.py \
     --find-slug "existing-slug" \
     --markdown-file draft.md \
     --status draft
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

3. **Create a new post when no match exists**
   ```bash
   python3 scripts/ghost_publish.py \
     --title "AI 工具使用指南" \
     --markdown-file draft.md \
     --slug "ai-tool-guide" \
     --status draft
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

- Read credentials only inside the helper script.
- Never print secrets, headers, or raw API key material.
- **Privacy scrub before publish**: Before writing or publishing any article derived from real operations, replace all personally identifiable or sensitive information with generic placeholders. This includes:
  - IP addresses (public, private, Tailscale) → `<YOUR_PUBLIC_IP>`, `<INTERNAL_IP>`, `<TAILSCALE_IP>`
  - Hostnames and device names → `<your-device>`
  - Tailnet domain names (e.g. `xxx.tailbff26.ts.net`) → `<your-device>.xxx.ts.net`
  - Usernames and email addresses → `user@` or `user@example.com`
  - API keys, tokens, UUIDs → `<YOUR_API_KEY>`
  - Any other site-specific or account-specific identifiers
  - Apply the same scrub to both the local markdown file and the published Ghost post.
- Use the Ghost Admin API for writes; the Content API is read-only.
- Prefer `draft` unless publishing is explicitly intended.
- Use `source=html` for HTML/markdown workflows; use `source=lexical` only when providing a lexical payload directly.
- Treat `title` and body as separate fields: do not repeat the article title as an H1/H2 in the body when Ghost already receives `title`.
- When modifying skill files or article drafts in a git-tracked workspace, check `git status` before editing, keep changes atomic, and create a commit after verification so every revision is recoverable.
- **Slug rules**:
  - Always provide explicit `--slug` for important posts
  - If not provided, script auto-generates a compliant slug (short, lowercase English/short pinyin, max 40 chars)
  - Avoid long phrases, dates, and punctuation in slugs
  - Verify auto-generated slugs are human-readable before publishing
- When updating existing posts, **always use `--find-slug` or `--update-id`** to avoid creating duplicates
- Normalize markdown before publish so headings, blank lines, bullets, and numbered lists become clean HTML; never preserve raw duplicated list markers like `• - item` or `1. 1. item`.
- When generating technical article content, default to objective writing: reduce subjective opinions, avoid labels like "simple/complex/easy/hard" unless attributed or clearly context-bound, and do not pre-judge the reader's knowledge.
- Prefer concrete facts, process, constraints, results, evidence, pitfalls, and boundaries. Include these when they help the reader understand what was done and what the approach covers.
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

1. **Writing style**
   - Objective, factual, and concise
   - Avoid unnecessary hype, vague praise, or reader-assumption language
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

2. **HTML rendering correctness**
   - Headings render in the expected hierarchy
   - Bullet lists, numbered lists, blockquotes, tables, and code blocks render cleanly
   - Inline code, links, and emphasis are preserved after markdown-to-HTML conversion
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

3. **Layout and readability**
   - Paragraph spacing is consistent
   - List nesting is clear
   - Code fences are closed and syntax highlighting is sensible
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

4. **Clickable URL / link correctness**
   - Use Markdown links (`[text](https://...)`) for source URLs you want readers to click
   - Avoid bare URLs when the display text matters
   - Confirm each URL points to the intended page and uses the correct anchor if present
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

5. **Final verification**
   - Open the draft in Ghost and inspect the rendered result
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

- Admin JWT generation from a Ghost admin API key
- Image upload via the Admin API images endpoint (multipart form data)
- Markdown-to-HTML conversion for simple content
- Post creation with tags, authors, excerpt, slug, status, and optional feature image
- Post deletion by ID or slug (via `--delete` flag)
- HTML or lexical publish payload selection
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

- Host: `GHOST_HOST` or `GHOST_ADMIN_HOST` or `GHOST_URL` or `GHOST_ADMIN_URL`
- API key: `GHOST_API_KEY` or `GHOST_ADMIN_API_KEY`
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

**Short form** (convenient for CLI):
- Tags: string names → `"Tag Name"` (auto-created if not found)
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

**Long form** (for JSON input with metadata):
- Tags: objects with `name`, `description`, `slug` fields
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

CLI flags:
- `--tag "name"` or `--tag "name:description:slug"` (colon-separated for metadata)
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

Tag normalization (`_normalize_tags`):
- Short form: `"Tag Name"` → `{"name": "Tag Name"}`
- Convenience: `"name:desc:slug"` → `{"name": "name", "description": "desc", "slug": "slug"}`
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

Author normalization (`_normalize_authors`):
- Short form: `"email@example.com"` → `{"email": "email@example.com"}`
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

- The Ghost Admin API images upload endpoint (`/images/upload/`) only accepts the image file. It does NOT accept alt text or metadata fields.
- Alt text belongs in the post content: `<img alt="..." src="...">` in HTML or the corresponding lexical node.
- The helper uploads images and replaces local references in HTML. Alt text is preserved from the original `<img>` tag or markdown `![]()` syntax.
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

```bash
python3 scripts/ghost_publish.py \
  --title "My post" \
  --markdown-file post.md \
  --tag "Ghost" --tag "Publishing" \
  --author "me@example.com" \
  --status draft
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

```bash
python3 scripts/ghost_publish.py \
  --input post.json
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

```bash
# Using colon-separated tag metadata: name:description:slug
python3 scripts/ghost_publish.py \
  --title "Tutorial" \
  --markdown-file guide.md \
  --tag "Tutorial:Ghost CMS Guide:ghost-tutorial"
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

```bash
# Delete by post ID
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

# Delete by slug (will auto-lookup ID)
python3 scripts/ghost_publish.py --delete --slug "ghost-test-publish"
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

- `title` required
- `html`, `markdown`, or `lexical` required
- `tags`, `authors`, `status`, `excerpt`, `slug`, `feature_image`, `images` optional
- `tags` may be strings (short form) or objects with `name`/`description`/`slug`
- `authors` may be email strings (short form) or objects with `id`/`email`
- `images` may be a list of local paths or objects with `path`/`src`/`file` plus optional `alt`
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

- `references/ghost-docs.md`: current Ghost API behavior relevant to this skill.
- `references/ghost-llms-full.txt`: comprehensive Ghost Admin API documentation for LLM/agent indexing and detailed reference. Useful for resolving edge cases, understanding API nuances, or when the skill behavior needs updating.
- `references/ghost-llms.txt`: Ghost documentation index for discovering available API sections.
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

1. **Initial version**: Only handled headings, lists, code blocks, and inline formatting (bold/italic/links/images)
2. **2026-04-03 fix #1**: Added support for:
   - **Tables**: `| col1 | col2 |` → `<table>` with `<thead>` and `<tbody>`
   - **Blockquotes**: `> text` → `<blockquote>` with recursive markdown parsing for nested content
3. **2026-04-03 fix #2**: Fixed table cell inline formatting:
   - **Root cause**: `parse_table()` was defined before `inline()` in the same function scope, but Python closure rules prevented access
   - **Solution**: Pass `inline` as a parameter to `parse_table(lines, start_idx, inline_fn)`
   - **Result**: `**bold**` in table cells now correctly converts to `<strong>bold</strong>`
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

   - **Output**: `<hr />`
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

If you encounter formatting issues in published Ghost articles:
1. Check if the markdown uses tables, blockquotes, or inline formatting within tables
2. Verify the current `markdown_to_html()` function handles them correctly
3. Run a quick Python test before publishing:
   ```python
   from scripts.ghost_publish import markdown_to_html
   html = markdown_to_html("| **A** | B |\n|---|---|\n| **C** | D |")
   assert '<strong>' in html, "Bold not working in tables!"
   ```
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

**Supported syntax:**
- `---` (3 or more hyphens)
- `***` (3 or more asterisks)
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

**If you want to remove horizontal rules** (e.g., they appear as unwanted visual clutter):
- Remove them from the source markdown with: `sed -i '/^---$/d' draft.md`
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

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
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

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
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

1. **Title Similarity**: Sequence matching + containment detection
   - Exact match: 100%
   - One title contains the other: 90%
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

2. **Content Similarity**: Jaccard similarity on token sets
   - Extracts tokens (Chinese characters + English words)
   - Compares token set overlap
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

**Thresholds:**
- >= 80%: High similarity → Strongly recommend update
- 60-79%: Medium similarity → Manual judgment
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:

1. **Always use `--check-similar`** for new content
2. **Review the similarity report** before deciding
3. **Update existing posts** when similarity > 80%
4. **Use consistent slugs** for related content series
  - **2026-04-10 fix**: Added symbol normalization to convert common LaTeX-style arrows (e.g., $\rightarrow$) to Unicode equivalents ($\to$) to prevent raw LaTeX rendering in Ghost.
  - **2026-04-05 fix**: Added support for horizontal rules:
