#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests

DEFAULT_API_VERSION = os.environ.get("GHOST_API_VERSION", "v6.0")

# Default tag aliases to prevent synonymous tag proliferation.
# Keys are forbidden/tag variants; values are the canonical tag names.
DEFAULT_TAG_ALIASES: Dict[str, str] = {
    "Hermes Agent": "Hermes",
    "hermes agent": "Hermes",
    "AI Agent": "Agent",
    "ai agent": "Agent",
    "记忆": "Memory",
}


class GhostPublishError(RuntimeError):
    pass


@dataclass
class GhostConfig:
    host: str
    key_id: str
    key_secret: bytes
    api_version: str = DEFAULT_API_VERSION


@dataclass
class ContentConfig:
    host: str
    content_key: str
    api_version: str = DEFAULT_API_VERSION


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """Extract YAML-like frontmatter from markdown.

    Returns (frontmatter_dict, body_without_frontmatter).
    Supports PyYAML if installed; otherwise falls back to simple key: value parsing.
    """
    pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(pattern, text, re.DOTALL)
    if not match:
        return {}, text

    fm_text = match.group(1)
    body = text[match.end():]

    try:
        import yaml
        parsed = yaml.safe_load(fm_text)
        if isinstance(parsed, dict):
            return parsed, body
    except Exception:
        pass

    result: Dict[str, Any] = {}
    for line in fm_text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            result[key] = val
    return result, body


def _first_env(*names: str) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def load_config() -> GhostConfig:
    host = _first_env("GHOST_ADMIN_HOST", "GHOST_HOST", "GHOST_ADMIN_URL", "GHOST_URL")
    # GHOST_ADMIN_API_KEY takes priority — it is the custom integration key that
    # supports write operations. GHOST_API_KEY is kept for backward compatibility
    # but may be the read-only Content API key; prefer the admin key.
    api_key = _first_env("GHOST_ADMIN_API_KEY", "GHOST_API_KEY")
    api_version = _first_env("GHOST_API_VERSION") or DEFAULT_API_VERSION
    if not host:
        raise GhostPublishError(
            "Ghost host is not configured. Set one of the following environment variables: "
            "GHOST_ADMIN_HOST, GHOST_HOST, GHOST_ADMIN_URL, or GHOST_URL."
        )
    if not api_key:
        raise GhostPublishError(
            "Ghost Admin API key is not configured. Set GHOST_ADMIN_API_KEY (preferred) "
            "or GHOST_API_KEY as an environment variable."
        )
    if ":" not in api_key:
        raise GhostPublishError("API key must be in the form <id>:<hex_secret>")
    key_id, secret = api_key.split(":", 1)
    if not key_id or not secret:
        raise GhostPublishError("API key must be in the form <id>:<hex_secret>")
    if not host.startswith(("http://", "https://")):
        host = "https://" + host
    host = host.rstrip("/")
    try:
        key_secret = bytes.fromhex(secret)
    except ValueError as exc:
        raise GhostPublishError("API key secret must be hex-encoded") from exc
    return GhostConfig(host=host, key_id=key_id, key_secret=key_secret, api_version=api_version)


def load_content_config(cfg: GhostConfig) -> Optional["ContentConfig"]:
    """Load Content API config. Returns None if GHOST_CONTENT_API_KEY is not set."""
    content_key = _first_env("GHOST_CONTENT_API_KEY")
    if not content_key:
        return None
    return ContentConfig(host=cfg.host, content_key=content_key, api_version=cfg.api_version)


def make_jwt(cfg: GhostConfig, ttl_seconds: int = 300) -> str:
    header = {"alg": "HS256", "typ": "JWT", "kid": cfg.key_id}
    now = int(time.time())
    payload = {"iat": now, "exp": now + ttl_seconds, "aud": "/admin/"}

    def b64(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode().rstrip("=")

    header_b64 = b64(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = b64(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    sig = hmac.new(cfg.key_secret, signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{b64(sig)}"


def admin_base(cfg: GhostConfig) -> str:
    return urljoin(cfg.host + "/", "/ghost/api/admin/")


def content_base(cc: "ContentConfig") -> str:
    return urljoin(cc.host + "/", "/ghost/api/content/")


def session(cfg: GhostConfig) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "Authorization": f"Ghost {make_jwt(cfg)}",
        "Accept-Version": cfg.api_version,
    })
    return s


def content_session(cc: "ContentConfig") -> requests.Session:
    """Return a requests.Session pre-configured for the Content API (read-only)."""
    s = requests.Session()
    s.headers.update({"Accept-Version": cc.api_version})
    # Content API key is passed as a query param, not a header — attach to session params
    s.params = {"key": cc.content_key}  # type: ignore[assignment]
    return s


def upload_image(cfg: GhostConfig, path: Path) -> str:
    """Upload a local image to Ghost and return the remote URL.

    Note: The Ghost Admin API images endpoint does NOT accept alt text or other
    metadata — only the image file itself. Alt text must be embedded in the
    post content (HTML img tag or lexical node).
    """
    if not path.exists():
        raise GhostPublishError(f"image not found: {path}")
    url = urljoin(admin_base(cfg), "images/upload/")
    suffix = path.suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }
    mime_type = mime_map.get(suffix, "application/octet-stream")
    with path.open("rb") as f:
        files = {"file": (path.name, f, mime_type)}
        data = {"ref": path.name}
        resp = session(cfg).post(url, files=files, data=data, timeout=60)
    if resp.status_code >= 300:
        raise GhostPublishError(f"image upload failed: {resp.status_code} {resp.text[:500]}")
    payload = resp.json()
    return payload["images"][0]["url"]


def html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def normalize_markdown(md: str, title: Optional[str] = None) -> str:
    lines = md.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    title_norm = title.strip() if title else None
    out: List[str] = []
    skipping_title = False

    for i, raw in enumerate(lines):
        line = raw.expandtabs(2).rstrip()
        stripped = line.strip()

        if i == 0 and title_norm:
            m = re.match(r"^#\s+(.+?)\s*$", stripped)
            if m and m.group(1).strip() == title_norm:
                skipping_title = True
                continue
        if skipping_title:
            if not stripped:
                continue
            skipping_title = False

        out.append(line)

    normalized: List[str] = []
    prev_blank = True
    for line in out:
        stripped = line.strip()
        is_block = bool(re.match(r"^(#{1,6}\s+|([-*]|\d+)\s+)", stripped))
        if not stripped:
            if not prev_blank:
                normalized.append("")
            prev_blank = True
            continue
        if is_block and normalized and normalized[-1] != "":
            normalized.append("")
        normalized.append(line)
        prev_blank = False
    while normalized and normalized[-1] == "":
        normalized.pop()
    return "\n".join(normalized)


def normalize_symbols(text: str) -> str:
    """Convert common LaTeX-style symbols to Unicode equivalents."""
    replacements = {
        r"$\rightarrow$": "→",
        r"$\leftarrow$": "←",
        r"$\Rightarrow$": "⇒",
        r"$\Leftarrow$": "⇐",
        r"$\leftrightarrow$": "↔",
    }
    for latex, unicode_sym in replacements.items():
        text = text.replace(latex, unicode_sym)
    return text


def markdown_to_html(md: str, title: Optional[str] = None) -> str:
    md = normalize_symbols(md)
    lines = normalize_markdown(md, title=title).split("\n")
    out: List[str] = []
    in_ul = False
    in_ol = False
    in_code = False
    in_blockquote = False
    code_buf: List[str] = []
    blockquote_buf: List[str] = []

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def close_blockquote() -> None:
        nonlocal in_blockquote, blockquote_buf
        if in_blockquote:
            quote_html = markdown_to_html("\n".join(blockquote_buf), title=None)
            out.append(f"<blockquote>{quote_html}</blockquote>")
            blockquote_buf = []
            in_blockquote = False

    def inline(s: str) -> str:
        s = html_escape(s)
        s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img alt="\1" src="\2" />', s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        return s

    def list_item_text(line: str) -> str:
        m = re.match(r"^\s*([-*]|\d+\.)\s+(.*)$", line)
        return m.group(2) if m else line

    def parse_table(lines: List[str], start_idx: int, inline_fn) -> tuple:
        """Parse a GFM table starting at start_idx. Returns (html_lines, next_idx).

        GFM table structure:
          Row 0: header cells  | col1 | col2 |
          Row 1: separator     |------|------| (cells contain only dashes, colons, spaces)
          Row 2+: data rows
        """
        table_lines = []
        i = start_idx
        while i < len(lines) and "|" in lines[i]:
            table_lines.append(lines[i])
            i += 1

        # Need at least header + separator
        if len(table_lines) < 2:
            return ([], start_idx + 1)

        def split_row(row: str) -> List[str]:
            cells = row.split("|")
            # Strip leading/trailing empty strings from outer pipes
            if cells and not cells[0].strip():
                cells = cells[1:]
            if cells and not cells[-1].strip():
                cells = cells[:-1]
            return [c.strip() for c in cells]

        html_lines = ["<table><thead><tr>"]
        for cell in split_row(table_lines[0]):
            html_lines.append(f"<th>{inline_fn(cell)}</th>")
        html_lines.append("</tr></thead><tbody>")

        # Skip separator row (row 1), then emit data rows
        for row in table_lines[2:]:
            if re.match(r"^[\s|:\-]+$", row):
                continue  # skip any extra separator rows
            html_lines.append("<tr>")
            for cell in split_row(row):
                html_lines.append(f"<td>{inline_fn(cell)}</td>")
            html_lines.append("</tr>")

        html_lines.append("</tbody></table>")
        return (html_lines, i)

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):
            close_lists()
            close_blockquote()
            if in_code:
                out.append("<pre><code>" + html_escape("\n".join(code_buf)) + "</code></pre>")
                in_code = False
                code_buf = []
            else:
                in_code = True
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        if not line.strip():
            close_lists()
            close_blockquote()
            i += 1
            continue

        if line.lstrip().startswith("> ") or line.strip() == ">":
            close_lists()
            if not in_blockquote:
                in_blockquote = True
            blockquote_buf.append(re.sub(r"^>\s?", "", line))
            i += 1
            continue
        elif in_blockquote:
            close_blockquote()

        if re.match(r'^\s*(-{3,}|\*{3,}|_{3,})\s*$', line):
            close_lists()
            close_blockquote()
            out.append("<hr />")
            i += 1
            continue

        if line.strip().startswith("|"):
            close_lists()
            close_blockquote()
            table_html, next_idx = parse_table(lines, i, inline)
            out.extend(table_html)
            i = next_idx
            continue

        # Headings h1-h6
        heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading_match:
            close_lists()
            close_blockquote()
            level = len(heading_match.group(1))
            out.append(f"<h{level}>{inline(heading_match.group(2))}</h{level}>")
            i += 1
            continue

        if re.match(r"^\s*[-*] ", line):
            close_blockquote()
            if in_ol:
                out.append("</ol>"); in_ol = False
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append(f"<li>{inline(list_item_text(line))}</li>")
            i += 1
            continue
        if re.match(r"^\s*\d+\. ", line):
            close_blockquote()
            if in_ul:
                out.append("</ul>"); in_ul = False
            if not in_ol:
                out.append("<ol>"); in_ol = True
            out.append(f"<li>{inline(list_item_text(line))}</li>")
            i += 1
            continue

        close_lists()
        close_blockquote()
        out.append(f"<p>{inline(line)}</p>")
        i += 1

    close_lists()
    close_blockquote()
    if in_code:
        out.append("<pre><code>" + html_escape("\n".join(code_buf)) + "</code></pre>")
    return "\n".join(out)


def load_json_arg(value: Optional[str], path: Optional[Path]) -> Dict[str, Any]:
    if path:
        return json.loads(path.read_text(encoding="utf-8"))
    if value:
        return json.loads(value)
    return {}


def replace_local_image_refs(html: str, image_map: Dict[str, str]) -> str:
    def repl(match: re.Match) -> str:
        alt, src = match.group(1), match.group(2)
        if src in image_map:
            return f'<img alt="{html_escape(alt)}" src="{image_map[src]}" />'
        return match.group(0)

    return re.sub(r'<img alt="([^"]*)" src="([^"]+)" ?/?>', repl, html)


def write_post(cfg: GhostConfig, post: Dict[str, Any], source: str, post_id: Optional[str] = None) -> Dict[str, Any]:
    if post_id:
        url = urljoin(admin_base(cfg), f"posts/{post_id}/?source={source}")
        resp = session(cfg).put(url, json={"posts": [post]}, timeout=60)
    else:
        url = urljoin(admin_base(cfg), f"posts/?source={source}")
        resp = session(cfg).post(url, json={"posts": [post]}, timeout=60)
    if resp.status_code >= 300:
        raise GhostPublishError(f"post write failed: {resp.status_code} {resp.text[:800]}")
    return resp.json()["posts"][0]


def find_post(cfg: GhostConfig, *, post_id: Optional[str] = None, slug: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Any]:
    """Look up a post by ID, slug, or title.

    - By ID: direct GET /posts/{id}/
    - By slug: direct GET /posts/slug/{slug}/  (avoids full list fetch)
    - By title: Admin API filter first (exact match via NQL), then full list scan as fallback
    Raises GhostPublishError if not found.
    """
    if post_id:
        url = urljoin(admin_base(cfg), f"posts/{post_id}/")
        resp = session(cfg).get(url, timeout=60)
        if resp.status_code == 404:
            raise GhostPublishError(f"post not found: id={post_id}")
        if resp.status_code >= 300:
            raise GhostPublishError(f"post lookup failed: {resp.status_code} {resp.text[:500]}")
        return resp.json()["posts"][0]

    if slug:
        url = urljoin(admin_base(cfg), f"posts/slug/{slug}/")
        resp = session(cfg).get(url, timeout=60)
        if resp.status_code == 404:
            raise GhostPublishError(f"post not found: slug={slug}")
        if resp.status_code >= 300:
            raise GhostPublishError(f"post lookup failed: {resp.status_code} {resp.text[:500]}")
        return resp.json()["posts"][0]

    if title:
        # Try Admin API filter first (NQL exact match on title, much faster than full scan)
        url = urljoin(admin_base(cfg), "posts/")
        params = {
            "filter": f"title:'{title}'",
            "fields": "id,title,slug,url,status,updated_at",
            "limit": "5",
        }
        resp = session(cfg).get(url, params=params, timeout=60)
        if resp.status_code < 300:
            for post in resp.json().get("posts", []):
                if post.get("title") == title:
                    return post

        # Fallback: full list scan (catches titles with special chars that trip NQL quoting)
        params_all = {"limit": "all", "fields": "id,title,slug,url,status,updated_at"}
        resp2 = session(cfg).get(url, params=params_all, timeout=60)
        if resp2.status_code >= 300:
            raise GhostPublishError(f"post lookup failed: {resp2.status_code} {resp2.text[:500]}")
        for post in resp2.json().get("posts", []):
            if post.get("title") == title:
                return post
        raise GhostPublishError(f"post not found: title={title!r}")

    raise GhostPublishError("find_post requires post_id, slug, or title")


def delete_post(cfg: GhostConfig, *, post_id: Optional[str] = None, slug: Optional[str] = None) -> str:
    """Delete a post by ID or slug. Returns the deleted post ID."""
    if not post_id and not slug:
        raise GhostPublishError("delete requires --post-id or --slug")
    post = find_post(cfg, post_id=post_id, slug=slug)
    pid = post["id"]
    url = urljoin(admin_base(cfg), f"posts/{pid}/")
    resp = session(cfg).delete(url, timeout=60)
    if resp.status_code != 204:
        raise GhostPublishError(f"post delete failed: {resp.status_code} {resp.text[:500]}")
    return pid


# ---------------------------------------------------------------------------
# Content API helpers — browse and search posts (read-only)
# ---------------------------------------------------------------------------

def list_posts(
    cfg: GhostConfig,
    *,
    tag: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    page: int = 1,
    order: str = "updated_at desc",
) -> None:
    """Print a paginated list of posts using the Admin API.

    Supports filtering by tag slug and status. Output is a JSON object with
    ``total``, ``page``, ``limit``, and a ``posts`` array of summaries.

    Args:
        tag: Filter by tag slug (e.g. ``hermes``).
        status: Filter by status: ``published``, ``draft``, ``all`` (default Admin API behaviour).
        limit: Max posts per page (max 15 for public Content API; Admin API allows higher).
        page: 1-based page number.
        order: NQL order expression, e.g. ``updated_at desc`` or ``published_at desc``.
    """
    url = urljoin(admin_base(cfg), "posts/")
    params: Dict[str, Any] = {
        "fields": "id,title,slug,url,status,updated_at,published_at",
        "limit": str(limit),
        "page": str(page),
        "order": order,
    }
    filters = []
    if tag:
        filters.append(f"tag:[{tag}]")
    if status and status != "all":
        filters.append(f"status:{status}")
    if filters:
        params["filter"] = "+".join(filters)

    resp = session(cfg).get(url, params=params, timeout=60)
    if resp.status_code >= 300:
        raise GhostPublishError(f"list posts failed: {resp.status_code} {resp.text[:500]}")
    data = resp.json()
    posts = data.get("posts", [])
    meta = data.get("meta", {}).get("pagination", {})
    print(json.dumps({
        "total": meta.get("total", len(posts)),
        "page": meta.get("page", page),
        "pages": meta.get("pages", 1),
        "limit": meta.get("limit", limit),
        "posts": [
            {
                "id": p.get("id"),
                "title": p.get("title"),
                "slug": p.get("slug"),
                "status": p.get("status"),
                "updated_at": p.get("updated_at"),
                "published_at": p.get("published_at"),
                "url": p.get("url"),
            }
            for p in posts
        ],
    }, ensure_ascii=False, indent=2))


def search_posts(cfg: GhostConfig, keyword: str, *, limit: int = 15) -> None:
    """Search posts by title keyword using the Admin API NQL contains operator.

    Uses ``title:~'keyword'`` filter so Ghost does server-side substring matching
    on the title field. Falls back to a client-side scan of the full list when
    the NQL filter returns zero results (e.g. special characters in keyword).

    Output: JSON object with ``keyword`` and a ``posts`` array of matches.
    """
    url = urljoin(admin_base(cfg), "posts/")
    params: Dict[str, Any] = {
        "filter": f"title:~'{keyword}'",
        "fields": "id,title,slug,url,status,updated_at,published_at",
        "limit": str(limit),
        "order": "updated_at desc",
    }
    resp = session(cfg).get(url, params=params, timeout=60)
    posts: List[Dict[str, Any]] = []
    if resp.status_code < 300:
        posts = resp.json().get("posts", [])

    if not posts:
        # Fallback: full list client-side substring match
        eprint("[INFO] NQL filter returned no results, falling back to full list scan")
        params_all = {
            "fields": "id,title,slug,url,status,updated_at,published_at",
            "limit": "all",
            "order": "updated_at desc",
        }
        resp2 = session(cfg).get(url, params=params_all, timeout=60)
        if resp2.status_code >= 300:
            raise GhostPublishError(f"search posts failed: {resp2.status_code} {resp2.text[:500]}")
        kw_lower = keyword.lower()
        posts = [
            p for p in resp2.json().get("posts", [])
            if kw_lower in (p.get("title") or "").lower()
        ][:limit]

    print(json.dumps({
        "keyword": keyword,
        "count": len(posts),
        "posts": [
            {
                "id": p.get("id"),
                "title": p.get("title"),
                "slug": p.get("slug"),
                "status": p.get("status"),
                "updated_at": p.get("updated_at"),
                "url": p.get("url"),
            }
            for p in posts
        ],
    }, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Tag management helpers
# ---------------------------------------------------------------------------

def load_tag_aliases(path: Optional[Path] = None) -> Dict[str, str]:
    aliases = dict(DEFAULT_TAG_ALIASES)
    if path and path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                aliases.update(data)
        except Exception as exc:
            eprint(f"[WARN] Failed to load tag alias file: {exc}")
    return aliases


def _normalize_tags(tags: List[Any], aliases: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    aliases = aliases or {}
    result: List[Dict[str, Any]] = []
    seen: set = set()
    for tag in tags:
        if isinstance(tag, dict):
            tag_obj = dict(tag)
            name = tag_obj.get("name", "").strip()
        else:
            tag_str = str(tag).strip()
            if not tag_str:
                continue
            # Apply alias before parsing colon-separated metadata
            canonical = aliases.get(tag_str, tag_str)
            parts = canonical.split(":", 2)
            tag_obj: Dict[str, Any] = {"name": parts[0].strip()}
            if len(parts) > 1 and parts[1].strip():
                tag_obj["description"] = parts[1].strip()
            if len(parts) > 2 and parts[2].strip():
                tag_obj["slug"] = parts[2].strip()
            name = tag_obj["name"]
        if not name:
            continue
        # Deduplicate case-insensitively
        lower = name.lower()
        if lower in seen:
            continue
        seen.add(lower)
        result.append(tag_obj)
    return result


def _fetch_all_tags(cfg: GhostConfig) -> List[Dict[str, Any]]:
    url = urljoin(admin_base(cfg), "tags/?limit=all&include=count.posts")
    resp = session(cfg).get(url, timeout=60)
    if resp.status_code >= 300:
        raise GhostPublishError(f"tags fetch failed: {resp.status_code} {resp.text[:500]}")
    return resp.json().get("tags", [])


def _find_tag(cfg: GhostConfig, *, tag_id: Optional[str] = None, slug: Optional[str] = None, name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    tags = _fetch_all_tags(cfg)
    for t in tags:
        if tag_id and t["id"] == tag_id:
            return t
        if slug and t["slug"] == slug:
            return t
        if name and t.get("name", "").strip().lower() == name.strip().lower():
            return t
    return None


def list_tags(cfg: GhostConfig) -> None:
    tags = _fetch_all_tags(cfg)
    print(json.dumps({
        "total": len(tags),
        "tags": [
            {
                "id": t["id"],
                "name": t["name"],
                "slug": t["slug"],
                "description": t.get("description"),
                "count": t.get("count", {}).get("posts", 0),
            }
            for t in tags
        ]
    }, ensure_ascii=False, indent=2))


def merge_tags(cfg: GhostConfig, from_slug: str, to_slug: str, dry_run: bool = False) -> None:
    """Move all posts from one tag to another, then delete the source tag."""
    from_tag = _find_tag(cfg, slug=from_slug)
    to_tag = _find_tag(cfg, slug=to_slug)
    if not from_tag:
        raise GhostPublishError(f"source tag not found: {from_slug}")
    if not to_tag:
        raise GhostPublishError(f"target tag not found: {to_slug}")

    # Fetch posts that use the source tag
    url = urljoin(admin_base(cfg), f"posts/?filter=tag:{from_slug}&limit=all&include=tags")
    resp = session(cfg).get(url, timeout=60)
    if resp.status_code >= 300:
        raise GhostPublishError(f"posts fetch failed: {resp.status_code} {resp.text[:500]}")
    posts = resp.json().get("posts", [])

    action = "would update" if dry_run else "updating"
    eprint(f"[{action}] {len(posts)} post(s) from '{from_tag['name']}' -> '{to_tag['name']}'")

    if dry_run:
        for p in posts:
            print(json.dumps({"id": p["id"], "title": p["title"], "action": "dry_run"}, ensure_ascii=False))
        return

    s = session(cfg)
    for p in posts:
        # Build new tag list: replace source tag with target tag object
        new_tags: List[Dict[str, Any]] = []
        seen = set()
        for t in p.get("tags", []):
            if t["slug"] == from_slug:
                continue
            key = t["name"].lower()
            if key not in seen:
                seen.add(key)
                new_tags.append({"name": t["name"]})
        # Add target if not already present
        if to_tag["name"].lower() not in seen:
            new_tags.append({"name": to_tag["name"]})

        post_url = urljoin(admin_base(cfg), f"posts/{p['id']}/?source=html")
        # Need updated_at for optimistic locking
        get_resp = s.get(post_url, timeout=60)
        if get_resp.status_code >= 300:
            eprint(f"[WARN] Failed to fetch post {p['id']}: {get_resp.status_code}")
            continue
        updated_at = get_resp.json()["posts"][0]["updated_at"]

        put_resp = s.put(post_url, json={"posts": [{"tags": new_tags, "updated_at": updated_at}]}, timeout=60)
        if put_resp.status_code >= 300:
            eprint(f"[WARN] Failed to update post {p['id']}: {put_resp.status_code} {put_resp.text[:300]}")
        else:
            print(json.dumps({"id": p["id"], "title": p["title"], "action": "tag_merged"}, ensure_ascii=False))

    # Delete source tag
    del_url = urljoin(admin_base(cfg), f"tags/{from_tag['id']}/")
    del_resp = s.delete(del_url, timeout=60)
    if del_resp.status_code == 204:
        print(json.dumps({"deleted_tag": from_tag["name"], "slug": from_slug}, ensure_ascii=False))
    else:
        eprint(f"[WARN] Failed to delete tag {from_slug}: {del_resp.status_code} {del_resp.text[:300]}")


def delete_empty_tags(cfg: GhostConfig, dry_run: bool = False) -> None:
    tags = _fetch_all_tags(cfg)
    removed = []
    for t in tags:
        count = t.get("count", {}).get("posts", 0)
        if count == 0:
            if dry_run:
                removed.append({"id": t["id"], "name": t["name"], "slug": t["slug"], "action": "dry_run"})
            else:
                url = urljoin(admin_base(cfg), f"tags/{t['id']}/")
                resp = session(cfg).delete(url, timeout=60)
                if resp.status_code == 204:
                    removed.append({"id": t["id"], "name": t["name"], "slug": t["slug"], "action": "deleted"})
                else:
                    eprint(f"[WARN] Failed to delete tag {t['name']}: {resp.status_code}")
    print(json.dumps({"removed": removed, "count": len(removed)}, ensure_ascii=False, indent=2))


def check_tag_conflicts(cfg: GhostConfig, tag_names: List[str]) -> List[Dict[str, Any]]:
    """Check for similar existing tags before creating new ones."""
    if not tag_names:
        return []
    existing = _fetch_all_tags(cfg)
    warnings: List[Dict[str, Any]] = []
    for name in tag_names:
        lower = name.lower()
        for t in existing:
            existing_name = t["name"]
            el = existing_name.lower()
            if el == lower:
                continue  # exact match is fine
            # containment or very close
            if lower in el or el in lower or _levenshtein(lower, el) <= 2:
                warnings.append({
                    "input": name,
                    "existing": existing_name,
                    "slug": t["slug"],
                    "reason": "similar_tag",
                })
    return warnings


def _levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        return _levenshtein(b, a)
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            ins = prev[j + 1] + 1
            dele = curr[j] + 1
            sub = prev[j] + (0 if ca == cb else 1)
            curr.append(min(ins, dele, sub))
        prev = curr
    return prev[-1]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Publish or update a Ghost post using the Admin API")
    p.add_argument("--input", help="JSON file with post fields")
    p.add_argument("--json", help="Inline JSON with post fields")
    p.add_argument("--title")
    p.add_argument("--markdown-file")
    p.add_argument("--html-file")
    p.add_argument("--status", choices=["draft", "published", "scheduled", "sent"])
    p.add_argument("--excerpt")
    p.add_argument("--meta-title", help="SEO meta title for the post")
    p.add_argument("--meta-description", help="SEO meta description for the post")
    p.add_argument("--slug")
    p.add_argument("--tag", action="append", default=[], help="Tag by name. Use 'name:desc:slug' for metadata or pass JSON objects.")
    p.add_argument("--author", action="append", default=[], help="Author by email address or JSON object with id/name/email.")
    p.add_argument("--feature-image", help="Local path or URL for the post feature image")
    p.add_argument("--image", action="append", default=[], help="Local image path to upload and replace by filename or exact path")
    p.add_argument("--use-source", choices=["html", "lexical"], default="html", help="Write payload source format")
    p.add_argument("--update-id", help="Update an existing post by Ghost id")
    p.add_argument("--find-slug", help="Find an existing post by slug and update it")
    p.add_argument("--find-title", help="Find an existing post by title and update it")
    p.add_argument("--print-found", action="store_true", help="Print the found post info and exit")
    p.add_argument("--delete", action="store_true", help="Delete a post instead of publishing")
    p.add_argument("--post-id", help="Post ID for delete (use with --delete)")
    # Tag management flags
    p.add_argument("--list-tags", action="store_true", help="List all tags with post counts")
    p.add_argument("--merge-tags", help="Merge two tags: from_slug:to_slug")
    p.add_argument("--delete-empty-tags", action="store_true", help="Delete tags with zero posts")
    p.add_argument("--dry-run", action="store_true", help="Show what would change without applying")
    p.add_argument("--tag-alias-file", help="JSON file with tag alias mappings")
    p.add_argument("--skip-tag-check", action="store_true", help="Skip similar-tag conflict check on publish")
    p.add_argument("--bulk-meta-file", help="JSON file mapping slug -> {meta_title, meta_description, excerpt} for batch updates")
    # Post browsing / search flags
    p.add_argument("--list-posts", action="store_true", help="List posts (supports --status, --tag, --limit, --page, --order)")
    p.add_argument("--search", metavar="KEYWORD", help="Search posts by title keyword substring")
    p.add_argument("--limit", type=int, default=20, help="Max results for --list-posts or --search (default: 20)")
    p.add_argument("--page", type=int, default=1, help="Page number for --list-posts (default: 1)")
    p.add_argument("--order", default="updated_at desc", help="Sort order for --list-posts, e.g. 'updated_at desc' or 'published_at desc'")
    return p.parse_args()


def _iter_images(raw: Any) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    for img in raw or []:
        if isinstance(img, dict):
            src = img.get("path") or img.get("src") or img.get("file")
            alt = img.get("alt", "")
        else:
            src = str(img)
            alt = ""
        if src:
            items.append({"path": str(src), "alt": str(alt)})
    return items


def _normalize_authors(authors: List[Any]) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for author in authors:
        if isinstance(author, dict):
            result.append(author)
        else:
            author_str = str(author).strip()
            if author_str:
                result.append({"email": author_str})
    return result


def generate_slug(title: str) -> str:
    """Generate a compliant Ghost slug from title.

    Rules: short (max 40 chars), lowercase, hyphens only, no dates.
    Prioritises English keywords; falls back to individual Chinese characters.
    """
    english_words = re.findall(r'[A-Za-z]{2,}', title)
    if english_words:
        stop_words = {'the', 'is', 'a', 'an', 'to', 'of', 'in', 'for', 'on', 'with', 'and', 'or', 'by'}
        keywords = [w.lower() for w in english_words[:5] if w.lower() not in stop_words]
        slug = '-'.join(keywords[:4] if keywords else [w.lower() for w in english_words[:4]])
    else:
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', title)
        if chinese_chars:
            stop_chars = '的了是在有和为不与或及于被把将给从到向以而但如这那'
            key_chars = [c for c in chinese_chars[:8] if c not in stop_chars]
            slug = '-'.join(key_chars[:4] if key_chars else chinese_chars[:4])
        else:
            words = re.findall(r'\w+', title.lower())
            slug = '-'.join(words[:4]) if words else 'untitled'

    slug = slug[:40].rstrip('-') or 'untitled'
    return slug


def _has_meta_args(args) -> bool:
    return bool(args.excerpt or args.meta_title or args.meta_description)


def bulk_update_meta(cfg: GhostConfig, path: Path) -> None:
    """Batch-update meta_title / meta_description / excerpt for multiple posts.

    JSON format: {"post-slug": {"meta_title": "...", "meta_description": "...", "excerpt": "..."}, ...}
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise GhostPublishError("bulk-meta-file must be a JSON object mapping slug -> fields")

    s = session(cfg)
    success = []
    failed = []

    for slug, fields in data.items():
        try:
            post = find_post(cfg, slug=slug)
            if not post:
                failed.append({"slug": slug, "reason": "post not found"})
                eprint(f"[SKIP] {slug}: post not found")
                continue

            payload: Dict[str, Any] = {"updated_at": post["updated_at"]}
            if "meta_title" in fields:
                payload["meta_title"] = fields["meta_title"]
            if "meta_description" in fields:
                payload["meta_description"] = fields["meta_description"]
            if "excerpt" in fields:
                payload["custom_excerpt"] = fields["excerpt"]
            if "custom_excerpt" in fields:
                payload["custom_excerpt"] = fields["custom_excerpt"]

            if not payload:
                eprint(f"[SKIP] {slug}: no meta fields to update")
                continue

            url = urljoin(admin_base(cfg), f"posts/{post['id']}/?source=html")
            resp = s.put(url, json={"posts": [payload]}, timeout=60)
            if resp.status_code >= 300:
                raise GhostPublishError(f"update failed: {resp.status_code} {resp.text[:500]}")

            updated = resp.json()["posts"][0]
            success.append({"slug": slug, "title": updated.get("title"), "url": updated.get("url")})
            print(json.dumps({"slug": slug, "status": "ok"}, ensure_ascii=False))
        except Exception as exc:
            failed.append({"slug": slug, "reason": str(exc)})
            eprint(f"[ERR] {slug}: {exc}")

    eprint(f"\n--- Bulk meta update summary ---")
    eprint(f"Success: {len(success)}")
    eprint(f"Failed: {len(failed)}")
    if failed:
        for item in failed:
            eprint(f"  - {item['slug']}: {item['reason']}")
        raise GhostPublishError("one or more bulk meta updates failed")


def main() -> int:
    try:
        args = parse_args()
        cfg = load_config()
        aliases = load_tag_aliases(Path(args.tag_alias_file) if args.tag_alias_file else None)

        # Tag management modes
        if args.list_tags:
            list_tags(cfg)
            return 0

        if args.merge_tags:
            if ":" not in args.merge_tags:
                raise GhostPublishError("--merge-tags requires from_slug:to_slug")
            from_slug, to_slug = args.merge_tags.split(":", 1)
            merge_tags(cfg, from_slug.strip(), to_slug.strip(), dry_run=args.dry_run)
            return 0

        if args.delete_empty_tags:
            delete_empty_tags(cfg, dry_run=args.dry_run)
            return 0

        # Bulk meta update mode
        if args.bulk_meta_file:
            bulk_update_meta(cfg, Path(args.bulk_meta_file))
            return 0

        # Post browse / search modes (read-only)
        if args.list_posts:
            list_posts(
                cfg,
                tag=args.tag[0] if args.tag else None,
                status=args.status,
                limit=args.limit,
                page=args.page,
                order=args.order,
            )
            return 0

        if args.search:
            search_posts(cfg, args.search, limit=args.limit)
            return 0

        # Handle delete mode early — does not require title or content
        if args.delete:
            deleted_id = delete_post(cfg, post_id=args.post_id or args.update_id, slug=args.slug or args.find_slug)
            print(json.dumps({"deleted_id": deleted_id}, ensure_ascii=False))
            return 0

        # Find-only mode early — does not require title or content
        if args.find_slug and args.print_found:
            existing = find_post(cfg, slug=args.find_slug)
            print(json.dumps(existing, ensure_ascii=False))
            return 0

        if args.find_title and args.print_found:
            existing = find_post(cfg, title=args.find_title)
            print(json.dumps(existing, ensure_ascii=False))
            return 0

        data = load_json_arg(args.json, Path(args.input) if args.input else None)

        # If markdown_file is provided, parse optional YAML frontmatter and merge into data
        markdown_raw = None
        if args.markdown_file:
            markdown_raw = Path(args.markdown_file).read_text(encoding="utf-8")
            fm, markdown = parse_frontmatter(markdown_raw)
            for key in ("title", "slug", "excerpt", "meta_title", "meta_description",
                        "feature_image", "status", "tags", "authors"):
                if key in fm and key not in data:
                    data[key] = fm[key]
        else:
            markdown = data.get("markdown")

        title = args.title or data.get("title")
        if not title:
            raise GhostPublishError("title is required")

        html = Path(args.html_file).read_text(encoding="utf-8") if args.html_file else data.get("html")
        lexical = data.get("lexical")

        existing = None
        if args.update_id or args.find_slug or args.find_title:
            existing = find_post(cfg, post_id=args.update_id, slug=args.find_slug, title=args.find_title)
            if args.print_found:
                print(json.dumps(existing, ensure_ascii=False))
                return 0
            # Ensure updated_at is present for optimistic locking (Ghost requires it on PUT)
            if existing.get("id") and not existing.get("updated_at"):
                existing = find_post(cfg, post_id=existing["id"])

        content_provided = html is not None or markdown is not None or lexical is not None
        meta_only = existing and not content_provided and _has_meta_args(args)

        if not content_provided and not meta_only:
            raise GhostPublishError("provide markdown, html, or lexical content")

        image_map: Dict[str, str] = {}
        if content_provided:
            for img in _iter_images(list(args.image) + list(data.get("images", []))):
                path = Path(img["path"])
                remote_url = upload_image(cfg, path)
                image_map[path.name] = remote_url
                image_map[str(path)] = remote_url
                image_map[path.as_posix()] = remote_url

        source = args.use_source
        post: Dict[str, Any] = {"title": title}
        # Only set status when explicitly provided or when creating a new post
        explicit_status = args.status or data.get("status")
        if explicit_status or not existing:
            post["status"] = explicit_status or "draft"

        if content_provided:
            if source == "lexical" and lexical is not None:
                post["lexical"] = lexical
            else:
                if markdown is not None:
                    html = markdown_to_html(markdown, title=title)
                if html is None:
                    raise GhostPublishError("html is required when writing with source=html")
                html = replace_local_image_refs(html, image_map)
                post["html"] = html

        if args.slug or data.get("slug"):
            post["slug"] = args.slug or data.get("slug")
        elif not existing:
            generated = generate_slug(title)
            post["slug"] = generated
            eprint(f"[WARN] Auto-generated slug: {generated}")

        # Ghost Admin API stores manual excerpts in custom_excerpt; excerpt is read-only auto-generated.
        custom_excerpt = args.excerpt or data.get("custom_excerpt") or data.get("excerpt")
        if custom_excerpt:
            post["custom_excerpt"] = custom_excerpt

        if args.meta_title or data.get("meta_title"):
            post["meta_title"] = args.meta_title or data.get("meta_title")

        if args.meta_description or data.get("meta_description"):
            post["meta_description"] = args.meta_description or data.get("meta_description")

        tags = list(args.tag) + list(data.get("tags", []))
        if tags:
            post["tags"] = _normalize_tags(tags, aliases=aliases)

        # Tag count check (soft warning)
        if post.get("tags") and len(post["tags"]) > 2:
            eprint(f"[WARN] Post has {len(post['tags'])} tags. SEO best practice is ≤ 2 tags to preserve topical authority.")
            eprint(f"  Current tags: {[t.get('name') for t in post['tags']]}")

        # Tag conflict check before publish
        if not args.skip_tag_check and post.get("tags"):
            tag_names = [t["name"] for t in post["tags"] if isinstance(t, dict)]
            conflicts = check_tag_conflicts(cfg, tag_names)
            if conflicts:
                eprint("[WARN] Similar existing tags detected:")
                for c in conflicts:
                    eprint(f"  Input '{c['input']}' is similar to existing '{c['existing']}' (slug: {c['slug']})")
                eprint("Use --skip-tag-check to bypass this warning.")

        authors = list(args.author) + list(data.get("authors", []))
        if authors:
            post["authors"] = _normalize_authors(authors)

        feature_image = args.feature_image or data.get("feature_image")
        if feature_image:
            feature_path = Path(str(feature_image))
            if feature_path.exists():
                post["feature_image"] = upload_image(cfg, feature_path)
            else:
                post["feature_image"] = str(feature_image)

        # updated_at is required by Ghost for optimistic locking on PUT requests
        if existing and existing.get("updated_at"):
            post["updated_at"] = existing["updated_at"]

        created = write_post(cfg, post, source=source, post_id=existing.get("id") if existing else None)
        print(json.dumps({
            "id": created.get("id"),
            "slug": created.get("slug"),
            "url": created.get("url"),
            "status": created.get("status"),
        }, ensure_ascii=False))
        return 0
    except GhostPublishError as e:
        eprint(f"error: {e}")
        return 2
    except Exception as e:
        eprint(f"unexpected error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
