---
name: ghost-publisher
description: Publish or update Ghost posts with rich article content and local image uploads using the Ghost Admin API. Use when creating/updating posts from markdown, HTML, or structured JSON, uploading local images, working with Ghost Admin integrations and API keys, or managing tags.
---

# Ghost Publisher

## Security Rules (Critical)

- **Treat `GHOST_ADMIN_API_KEY` and `GHOST_HOST` as black boxes**: The AI agent must NEVER read the actual values of these two environment variables into the conversation context. Do not use `echo`, `env`, `cat`, `grep`, or any other command to inspect or reveal their values. Invoke the helper script directly and let it read the variables internally.
- **NEVER expose credential values**: Do not print, log, or return the values of `GHOST_ADMIN_API_KEY`, `GHOST_API_KEY`, `GHOST_HOST`, `GHOST_ADMIN_HOST`, `GHOST_URL`, or `GHOST_ADMIN_URL`. These values must remain inside the helper script only.
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

## Publishing Workflow

1. **Draft first**: Always start with `--status draft` to create/update a draft.
2. **Find existing post**: Before publishing, check if a post with the same title/slug already exists:
   ```bash
   python3 scripts/ghost_publish.py --find-slug "existing-slug" --print-found
   ```
3. **Update, don't duplicate**: When updating, **always use `--find-slug` or `--update-id`** to target the existing post. Never create multiple drafts with the same title.
4. **Verify slug**: Ensure slug follows the rule: short, lowercase English or short pinyin, no dates/punctuation. If not provided, script will auto-generate a compliant slug.
5. **Publish**: Once the draft is ready, update with `--status published` using the same `--find-slug` to avoid creating a new post.

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
2. **Reuse existing tags** whenever possible. Do not invent a new tag if an existing one covers the same concept.
3. **Do not create near-duplicate tags**. If `--list-tags` shows a tag that is identical, contains, or highly similar (edit distance ≤ 2) to your intended tag, you must use the existing tag instead.
4. **Use built-in aliases**. The script automatically collapses `Hermes Agent` → `Hermes`, `AI Agent` → `Agent`, `记忆` → `Memory`. Rely on this mechanism rather than manual cleanup.
5. **Merge existing duplicates immediately**. If you discover two live tags that mean the same thing during your work, merge them on the spot with `--merge-tags` instead of leaving them for later.
6. **Skip the check only when certain**. Use `--skip-tag-check` only if the user explicitly overrides the warning.

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

## Writing Guidelines

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
- API key: `GHOST_API_KEY` or `GHOST_ADMIN_API_KEY`

## Verification Checklist

1. **Writing style**
   - Objective, factual, and concise
   - Avoid unnecessary hype, vague praise, or reader-assumption language

2. **HTML rendering correctness**
   - Headings render in the expected hierarchy
   - Bullet lists, numbered lists, blockquotes, tables, and code blocks render cleanly
   - Inline code, links, and emphasis are preserved after markdown-to-HTML conversion

3. **Layout and readability**
   - Paragraph spacing is consistent
   - List nesting is clear
   - Code fences are closed and syntax highlighting is sensible

4. **Clickable URL / link correctness**
   - Use Markdown links (`[text](https://...)`) for source URLs you want readers to click
   - Avoid bare URLs when the display text matters
   - Confirm each URL points to the intended page and uses the correct anchor if present

5. **Final verification**
   - Open the draft in Ghost and inspect the rendered result

## Browser Verification

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

## Similarity Check

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

## Similarity Thresholds

- >= 80%: High similarity → Strongly recommend update
- 60-79%: Medium similarity → Manual judgment

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

- `references/ghost-docs.md`: current Ghost API behavior relevant to this skill.
- `references/ghost-llms-full.txt`: comprehensive Ghost Admin API documentation for LLM/agent indexing and detailed reference. Useful for resolving edge cases, understanding API nuances, or when the skill behavior needs updating.
- `references/ghost-llms.txt`: Ghost documentation index for discovering available API sections.
