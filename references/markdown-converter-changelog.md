# Markdown-to-HTML Converter Changelog

Read this file when you encounter formatting issues in published Ghost articles
(tables, blockquotes, inline formatting, etc.) and need to understand the
current capabilities and known history of `markdown_to_html()`.

## Capability summary

The built-in `markdown_to_html()` function in `scripts/ghost_publish.py` handles:

- Headings, paragraphs, code blocks, and inline formatting (bold / italic / links / images)
- **Tables**: `| col1 | col2 |` → `<table>` with `<thead>` and `<tbody>`; inline formatting inside cells works
- **Blockquotes**: `> text` → `<blockquote>` with recursive markdown parsing for nested content
- **Horizontal rules**: `---` or `***` → `<hr />`
- **Symbol normalization**: LaTeX-style arrows (e.g. `$\rightarrow$`) → Unicode equivalents (`→`)

## Quick diagnostic test

```python
from scripts.ghost_publish import markdown_to_html
html = markdown_to_html("| **A** | B |\n|---|---|\n| **C** | D |")
assert '<strong>' in html, "Bold not working in tables!"
```

## Fix history

1. **Initial version**: Headings, lists, code blocks, and inline formatting only.
2. **2026-04-03 fix #1**: Added table and blockquote support.
3. **2026-04-03 fix #2**: Fixed table cell inline formatting.
   - Root cause: `parse_table()` was defined before `inline()` in the same function scope; Python closure rules prevented access.
   - Solution: Pass `inline` as a parameter to `parse_table(lines, start_idx, inline_fn)`.
4. **2026-04-05**: Added horizontal rule support (`---` / `***` → `<hr />`).
5. **2026-04-10**: Added symbol normalization for LaTeX-style arrows.
6. **2026-04-11**: Added tag management commands (`--list-tags`, `--merge-tags`, `--delete-empty-tags`) and tag conflict detection.
7. **2026-04-13**: Added bulk metadata update (`--bulk-meta-file`); metadata-only updates no longer require content re-upload.
8. **2026-04-16**: Added `--list-posts` and `--search`; improved `find_post` to use NQL filter first.
9. **2026-04-27**: Fixed table-row detection — lines containing `|` inside Markdown links were misidentified as table rows. Changed guard to `line.strip().startswith("|")`.
