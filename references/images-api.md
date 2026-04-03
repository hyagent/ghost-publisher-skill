# Ghost Admin API — Images Endpoint Reference

**Source:** [Ghost Developer Docs — Uploading an Image](https://docs.ghost.org/admin-api/images/uploading-an-image)

## Endpoint

```
POST /ghost/api/admin/images/upload/
```

## Authentication

- Requires a Ghost Admin API key (integration token).
- JWT-based auth sent in `Authorization: Ghost <jwt>` header.
- Include `Accept-Version: v{major}.{minor}` (default: `v6.0`).

## Request

**Content-Type:** `multipart/form-data`

**Form fields:**

| Field  | Required | Type          | Description                                           |
|--------|----------|---------------|-------------------------------------------------------|
| `file` | Yes      | Blob or File  | The image data (binary) to upload.                    |
| `ref`  | No       | String        | A reference string for mapping back to local paths.   |

**Important:** The images upload endpoint does **NOT** accept `alt`, `title`, `caption`, or any other metadata fields. These are set separately in post content (HTML or lexical) when the image is embedded.

## curl example

```bash
curl -X POST \
  -H "Authorization: Ghost <your-admin-jwt>" \
  -H "Accept-Version: v6.0" \
  -F "file=@/path/to/image.jpg" \
  https://your-ghost-site/ghost/api/admin/images/upload/
```

## Response

```json
{
  "images": [
    {
      "url": "https://your-ghost-site/content/images/2024/01/image.jpg"
    }
  ]
}
```

The returned `url` is the public URL where the uploaded image is served. Use this URL in your post's HTML or lexical content to embed the image.

## Alt text handling

Alt text is **not** part of the upload API. To set alt text for an image:

- **HTML content:** Include it in the `<img>` tag:
  ```html
  <img alt="Descriptive text" src="https://your-ghost-site/content/images/2024/01/image.jpg">
  ```

- **Lexical content:** Set the `alt` property in the lexical image node.

- **Markdown:** Include alt text in the markdown syntax:
  ```markdown
  ![Descriptive text](/path/to/image.jpg)
  ```

The `ghost_publish.py` helper preserves alt text from markdown `![]()` syntax and inline `<img>` tags when replacing local file references with Ghost CDN URLs.

## Common pitfalls

1. **Sending `alt` in the upload form:** This field is ignored (or may cause errors). The Ghost images API only accepts `file` and optionally `ref`.
2. **Not sending `Content-Type: multipart/form-data`:** The request must be multipart form data. Using `requests` with `files=` handles this automatically.
3. **Expecting `alt` in the response:** The response only contains the uploaded image `url`. No alt text or metadata is returned.
4. **Using the Content API for uploads:** The Content API is read-only. Use the Admin API with an admin integration key for writes.

## Related

- `references/ghost-docs.md` — General Ghost API behavior for this skill
- `scripts/ghost_publish.py` — Implementation of image upload in the skill helper
