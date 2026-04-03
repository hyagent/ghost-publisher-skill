# Ghost docs notes

## Content API

- Read-only API for published content.
- Base URL: `https://{admin_domain}/ghost/api/content/`
- Use `Accept-Version: v{major}.{minor}`.
- API keys are for the Content API only; do not use it for writes.

## Admin API authentication

- Admin API keys are used to generate short-lived JWTs.
- The JWT uses `HS256`, a `kid` header, `iat`/`exp`, and `aud: /admin/`.
- Send the token in the `Authorization` header as `Ghost <jwt>`.
- The docs describe integration tokens, staff access tokens, and user auth; this skill uses integration/admin-key auth.

## Posts create/update

- Admin API posts support publishing content via `posts` endpoints.
- Ghost 5+ stores post content as Lexical by default.
- For HTML workflows, pass HTML content and request `source=html` so Ghost interprets the HTML payload.
- The helper should keep `html` as the publish payload for markdown/HTML workflows and only emit `lexical` when explicitly requested.

## Images

### Upload endpoint

- Upload to `POST /ghost/api/admin/images/upload/`.
- Send multipart form data (`Content-Type: multipart/form-data`).
- Form fields:
  - `file` (required): The image blob or file data to upload.
  - `ref` (optional): A reference string so the response can be mapped back to the original local path/name.
- **Important:** The images upload endpoint does NOT accept `alt`, `title`, or other metadata fields. Alt text is set when embedding the image in post content (HTML or lexical), not during upload.
- The response shape:
  ```json
  {
    "images": [
      {
        "url": "https://your-ghost-site/content/images/2024/01/filename.jpg"
      }
    ]
  }
  ```
- The returned `url` is used to embed the image in post content. When uploading inline, you must separately handle alt text in the HTML `<img>` tag or lexical node.

### Best practices

- Upload images before creating/updating posts so you have the URLs.
- Store the mapping from local file → Ghost URL for replacing local references in content.
- If using the helper's `--image` flag or `images` list in JSON, paths are resolved and uploaded, then local references in HTML/Markdown are rewritten to the Ghost CDN URLs.

## Practical notes

- Local images are uploaded one at a time.
- Feature images can be local files or existing URLs.
- Keep `draft` as the default publish status unless publishing is intentional.
