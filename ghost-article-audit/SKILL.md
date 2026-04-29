---
name: ghost-article-audit
description: Audit previously written or published Ghost articles from Hermes sessions. Use when asked how many Ghost articles were created/published, what their topics were, or when session_search summaries may have missed the final publish event.
---

# Ghost Article Audit

Use this skill when the user asks for an inventory of Ghost articles, themes, publish status, or publication history.

## When to use
- 用户问：一共写了几篇 Ghost 文章、分别是什么主题、哪些已经发布
- 需要从历史会话里回溯文章，而不是写新文章
- `session_search` 的摘要可能漏掉最终发布步骤或只给出部分线索

## Recommended workflow

1. **先用 session_search 粗筛**
   - 用多个关键词并列搜索：
     - `Ghost OR publish OR 文章 OR article`
     - 文章标题关键词、slug、站点域名、作者名
   - 优先找包含以下线索的会话：
     - `slug:`
     - `url:`
     - `status": "published"`
     - `status": "draft"`
     - `ghost-publisher`

2. **再查原始 session JSONL 日志**
   - 不要只信摘要；摘要可能漏掉“最后一次发布”或“草稿改发布”的原子动作。
   - 用 `grep` / `grep -R` 直接扫 `~/.hermes/sessions/*.jsonl`，重点看：
     - 站点域名（如你的 Ghost 博客域名）
     - `slug`
     - `status": "published"`
     - `status": "draft"`
     - 文章标题片段
   - 如果今天的会话很多，优先按日期限定，例如：
     - `~/.hermes/sessions/YYYYMMDD*.jsonl`

3. **确认“真文章”而不是推荐卡片**
   - Ghost 首页或文章页里出现的推荐文章、相关内容卡片、站点推荐，不要自动算入本次统计。
   - 只有满足下面任一条件，才算一篇可确认的文章：
     - 出现发布命令返回的 post JSON（含 `id` / `slug` / `url` / `status`）
     - 出现可访问的 Ghost 文章 URL
     - 出现明确的文章标题 + 发布/草稿状态

4. **用浏览器做最终核验**
   - 如果标题/slug 还不确定，打开最终 URL 看页面标题和正文。
   - 优先确认：
     - 页面标题
     - slug 是否一致
     - 状态是否已发布

## Practical rules

- 统计文章数量时，按“可确认的独立文章”计数，不按“会话里提到过几次”计数。
- 如果一个会话经历了“草稿 → 发布”，只算 **1 篇文章**。
- 如果同一篇文章有多个 URL，优先以最终公开 URL 为准。
- 若 session_search 结果和 raw log 冲突，以 raw log 和 Ghost 返回的 post JSON 为准。

## Useful grep patterns

```bash
grep -R -n 'status\\": \\\"published\\\"' ~/.hermes/sessions/YYYYMMDD*.jsonl
grep -R -n 'your-ghost-domain.com/' ~/.hermes/sessions/YYYYMMDD*.jsonl
grep -R -n 'slug\\": \\\"' ~/.hermes/sessions/YYYYMMDD*.jsonl
grep -R -n 'ghost-publisher|published|draft|url\\":' ~/.hermes/sessions/YYYYMMDD*.jsonl
```

## Output shape

When answering the user, report:
- confirmed count
- each article title
- theme/subject
- status if known (`draft` / `published`)
- final URL if known
- note any uncertain candidates separately instead of counting them

## Pitfalls

- `session_search` summaries can miss final publish events.
- Site homepage recommendations may look like article evidence but are not publication proof.
- Do not count a repeated draft/publish update as a second article.
- If a title appears only in a recommendation card and not in a publish log, mark it as unconfirmed.
