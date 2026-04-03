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
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests

DEFAULT_API_VERSION = os.environ.get("GHOST_API_VERSION", "v6.0")


class GhostPublishError(RuntimeError):
    pass


@dataclass
class GhostConfig:
    host: str
    key_id: str
    key_secret: bytes
    api_version: str = DEFAULT_API_VERSION


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def _first_env(*names: str) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def load_config() -> GhostConfig:
    host = _first_env("GHOST_ADMIN_HOST", "GHOST_HOST", "GHOST_ADMIN_URL", "GHOST_URL")
    api_key = _first_env("GHOST_ADMIN_API_KEY", "GHOST_API_KEY")
    api_version = _first_env("GHOST_API_VERSION") or DEFAULT_API_VERSION
    if not host:
        raise GhostPublishError("GHOST_HOST is required")
    if not api_key:
        raise GhostPublishError("GHOST_API_KEY is required")
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


def session(cfg: GhostConfig) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "Authorization": f"Ghost {make_jwt(cfg)}",
        "Accept-Version": cfg.api_version,
    })
    return s


def upload_image(cfg: GhostConfig, path: Path, alt: str = "") -> str:
    if not path.exists():
        raise GhostPublishError(f"image not found: {path}")
    url = urljoin(admin_base(cfg), "images/upload/")
    with path.open("rb") as f:
        # Ghost API requires explicit content type for file uploads
        mime_type = "image/png" if path.suffix.lower() == ".png" else \
                    "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else \
                    "image/gif" if path.suffix.lower() == ".gif" else \
                    "image/webp" if path.suffix.lower() == ".webp" else \
                    "application/octet-stream"
        files = {"file": (path.name, f, mime_type)}
        data = {"ref": path.name}
        if alt:
            data["alt"] = alt
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


def markdown_to_html(md: str, title: Optional[str] = None) -> str:
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

    def parse_table(lines: List[str], start_idx: int, inline_fn) -> tuple[List[str], int]:
        """Parse a markdown table starting at start_idx. Returns (html_lines, next_idx)."""
        table_lines = []
        i = start_idx
        while i < len(lines) and lines[i].strip().startswith("|"):
            table_lines.append(lines[i])
            i += 1
        if len(table_lines) < 2:
            return ([], start_idx + 1)
        
        html_lines = ["<table>"]
        header_parsed = False
        
        for row in table_lines:
            cells = [c.strip() for c in row.split("|")]
            cells = [c for c in cells if c or c == ""]
            if cells and cells[0] == "":
                cells = cells[1:]
            if cells and cells[-1] == "":
                cells = cells[:-1]
            
            if not header_parsed:
                html_lines.append("<thead><tr>")
                for cell in cells:
                    html_lines.append(f"<th>{inline_fn(cell)}</th>")
                html_lines.append("</tr></thead><tbody>")
                header_parsed = True
            elif re.match(r"^[\s\-:|]+$", row):
                continue
            else:
                html_lines.append("<tr>")
                for cell in cells:
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
        
        # Handle blockquote
        if line.lstrip().startswith("> ") or line.strip() == ">":
            close_lists()
            if not in_blockquote:
                in_blockquote = True
            blockquote_buf.append(re.sub(r"^>\s?", "", line))
            i += 1
            continue
        elif in_blockquote:
            close_blockquote()
        
        # Handle table (starts with |)
        if line.strip().startswith("|"):
            close_lists()
            close_blockquote()
            table_html, next_idx = parse_table(lines, i, inline)
            out.extend(table_html)
            i = next_idx
            continue
        
        if line.startswith("# "):
            close_lists()
            close_blockquote()
            out.append(f"<h1>{inline(line[2:])}</h1>")
            i += 1
            continue
        if line.startswith("## "):
            close_lists()
            close_blockquote()
            out.append(f"<h2>{inline(line[3:])}</h2>")
            i += 1
            continue
        if line.startswith("### "):
            close_lists()
            close_blockquote()
            out.append(f"<h3>{inline(line[4:])}</h3>")
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
    def repl(match: re.Match[str]) -> str:
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
    if post_id:
        url = urljoin(admin_base(cfg), f"posts/{post_id}/")
        resp = session(cfg).get(url, timeout=60)
        if resp.status_code >= 300:
            raise GhostPublishError(f"post lookup failed: {resp.status_code} {resp.text[:500]}")
        return resp.json()["posts"][0]
    url = urljoin(admin_base(cfg), "posts/")
    params = {"limit": "all", "fields": "id,title,slug,url,status"}
    resp = session(cfg).get(url, params=params, timeout=60)
    if resp.status_code >= 300:
        raise GhostPublishError(f"post lookup failed: {resp.status_code} {resp.text[:500]}")
    posts = resp.json().get("posts", [])
    if slug:
        for post in posts:
            if post.get("slug") == slug:
                return post
    if title:
        for post in posts:
            if post.get("title") == title:
                return post
    if not posts:
        raise GhostPublishError("post not found")
    return posts[0]


def delete_post(cfg: GhostConfig, *, post_id: Optional[str] = None, slug: Optional[str] = None) -> str:
    """Delete a post by ID or slug. Returns the deleted post ID."""
    if not post_id and not slug:
        raise GhostPublishError("delete requires --post-id or --slug")
    post = find_post(cfg, post_id=post_id, slug=slug)
    post_id = post["id"]
    url = urljoin(admin_base(cfg), f"posts/{post_id}/")
    resp = session(cfg).delete(url, timeout=60)
    if resp.status_code != 204:
        raise GhostPublishError(f"post delete failed: {resp.status_code} {resp.text[:500]}")
    return post_id


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Publish or update a Ghost post using the Admin API")
    p.add_argument("--input", help="JSON file with post fields")
    p.add_argument("--json", help="Inline JSON with post fields")
    p.add_argument("--title")
    p.add_argument("--markdown-file")
    p.add_argument("--html-file")
    p.add_argument("--status", choices=["draft", "published", "scheduled", "sent"])
    p.add_argument("--excerpt")
    p.add_argument("--slug")
    p.add_argument("--tag", action="append", default=[], help="Tag by name (creates if missing). Use 'name:desc:slug' for metadata or pass JSON objects.")
    p.add_argument("--author", action="append", default=[], help="Author by email address (primary author) or author object with id/name/email.")
    p.add_argument("--feature-image")
    p.add_argument("--feature-image-alt", default="", help="DEPRECATED: alt text is set in post content (HTML/lexical), not via the images upload API. This flag is preserved for backward compatibility but has no effect.")
    p.add_argument("--image", action="append", default=[], help="Local image path to upload and replace by filename or exact path")
    p.add_argument("--use-source", choices=["html", "lexical"], default="html", help="Write payload source format")
    p.add_argument("--update-id", help="Update an existing post by Ghost id")
    p.add_argument("--find-slug", help="Find an existing post by slug and update it")
    p.add_argument("--find-title", help="Find an existing post by title and update it")
    p.add_argument("--print-found", action="store_true", help="Print the found post info and exit")
    p.add_argument("--delete", action="store_true", help="Delete a post instead of publishing")
    p.add_argument("--post-id", help="Delete a post by Ghost id (use with --delete)")
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


def _normalize_tags(tags: List[Any]) -> List[Dict[str, Any]]:
    """Normalize tags to Ghost API format.

    Ghost API supports:
    - Short form: string name → {"name": "Tag Name"}
    - Long form: object with name/description/slug → passed through
    - Convenience: "name:desc:slug" syntax
    Tags that cannot be matched are automatically created by Ghost.
    """
    result: List[Dict[str, Any]] = []
    for tag in tags:
        if isinstance(tag, dict):
            result.append(tag)
        else:
            tag_str = str(tag).strip()
            if not tag_str:
                continue
            parts = tag_str.split(":", 2)
            tag_obj: Dict[str, Any] = {"name": parts[0].strip()}
            if len(parts) > 1 and parts[1].strip():
                tag_obj["description"] = parts[1].strip()
            if len(parts) > 2 and parts[2].strip():
                tag_obj["slug"] = parts[2].strip()
            result.append(tag_obj)
    return result


def _normalize_authors(authors: List[Any]) -> List[Dict[str, Any]]:
    """Normalize authors to Ghost API format.

    Ghost API supports:
    - Short form: email string → {"email": "author@example.com"}
    - Long form: object with id/email → passed through
    """
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
    
    Rules:
    - Short (max 40 chars)
    - Lowercase English or short pinyin
    - No dates, punctuation (except hyphens)
    - Human-readable
    """
    import re
    import unicodedata
    
    # Try to extract key English words first
    english_words = re.findall(r'[A-Za-z]{2,}', title)
    if english_words:
        # Take first 3-4 meaningful words, filter common stop words
        stop_words = {'the', 'is', 'a', 'an', 'to', 'of', 'in', 'for', 'on', 'with', 'and', 'or', 'by'}
        keywords = [w.lower() for w in english_words[:5] if w.lower() not in stop_words]
        if keywords:
            slug = '-'.join(keywords[:4])
        else:
            slug = '-'.join([w.lower() for w in english_words[:4]])
    else:
        # Fallback for Chinese/mixed: extract meaningful parts
        # For pure Chinese, use first 2-3 key chars joined
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', title)
        if chinese_chars:
            # Take 2-4 chars that are likely keywords (avoid 的、了、是 etc.)
            stop_chars = '的了是在有和为不与或及于被把将给从到向以而但如这那'
            key_chars = [c for c in chinese_chars[:8] if c not in stop_chars]
            if key_chars:
                slug = '-'.join(key_chars[:4])
            else:
                slug = '-'.join(chinese_chars[:4])
        else:
            # Last resort: use all alphanumerics
            words = re.findall(r'\w+', title.lower())
            slug = '-'.join(words[:4]) if words else 'untitled'
    
    # Truncate to 40 chars, remove trailing hyphens
    slug = slug[:40].rstrip('-')
    # Ensure at least one character
    if not slug:
        slug = 'untitled'
    
    return slug


def main() -> int:
    try:
        args = parse_args()
        cfg = load_config()
        data = load_json_arg(args.json, Path(args.input) if args.input else None)
        title = args.title or data.get("title")
        if not title:
            raise GhostPublishError("title is required")

        markdown = Path(args.markdown_file).read_text(encoding="utf-8") if args.markdown_file else data.get("markdown")
        html = Path(args.html_file).read_text(encoding="utf-8") if args.html_file else data.get("html")
        lexical = data.get("lexical")

        # Handle delete mode
        if args.delete:
            deleted_id = delete_post(cfg, post_id=args.post_id or args.update_id, slug=args.slug or args.find_slug)
            print(json.dumps({"deleted_id": deleted_id}, ensure_ascii=False))
            return 0

        if html is None and markdown is None and lexical is None:
            raise GhostPublishError("provide markdown, html, or lexical")

        existing = None
        if args.update_id or args.find_slug or args.find_title:
            existing = find_post(cfg, post_id=args.update_id, slug=args.find_slug, title=args.find_title)
            if args.print_found:
                print(json.dumps(existing, ensure_ascii=False))
                return 0
            if existing.get("id") and not existing.get("updated_at"):
                existing = find_post(cfg, post_id=existing["id"])

        image_map: Dict[str, str] = {}
        for img in _iter_images(list(args.image) + list(data.get("images", []))):
            path = Path(img["path"])
            url = upload_image(cfg, path, alt=img["alt"])
            image_map[path.name] = url
            image_map[str(path)] = url
            image_map[path.as_posix()] = url

        source = args.use_source
        post: Dict[str, Any] = {"title": title, "status": args.status or data.get("status", "draft")}

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
            # Auto-generate slug when creating new post (not updating)
            generated = generate_slug(title)
            post["slug"] = generated
            # Warn if it's a generated slug
            eprint(f"[WARN] Auto-generated slug: {generated}")
        if args.excerpt or data.get("excerpt"):
            post["excerpt"] = args.excerpt or data.get("excerpt")
        tags = list(args.tag) + list(data.get("tags", []))
        if tags:
            post["tags"] = _normalize_tags(tags)

        authors = list(args.author) + list(data.get("authors", []))
        if authors:
            post["authors"] = _normalize_authors(authors)

        feature_image = args.feature_image or data.get("feature_image")
        if feature_image:
            feature_path = Path(str(feature_image))
            post["feature_image"] = upload_image(cfg, feature_path, alt=args.feature_image_alt) if feature_path.exists() else feature_image

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
