"""Load the articles/writing feed for the right-hand pane.

Source of truth is config/articles.yaml (manually curated). If any RSS/Atom feeds
are configured there, their items are merged in and de-duplicated by URL, so new
posts on an RSS-capable blog appear automatically.
"""

from __future__ import annotations

import logging
import time
from functools import lru_cache
from pathlib import Path

import yaml

log = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "articles.yaml"
_CACHE_TTL_SECONDS = 900  # re-read RSS at most every 15 minutes


def _load_config() -> dict:
    if not _CONFIG_PATH.exists():
        return {}
    try:
        return yaml.safe_load(_CONFIG_PATH.read_text()) or {}
    except Exception as e:  # pragma: no cover
        log.warning("failed to parse articles.yaml: %s", e)
        return {}


def _normalize(entry: dict, source: str = "manual", default_section: str = "") -> dict | None:
    title = (entry.get("title") or "").strip()
    url = (entry.get("url") or "").strip()
    if not title or not url:
        return None
    tags = entry.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    return {
        "title": title,
        "url": url,
        "date": str(entry.get("date") or "").strip(),
        "tags": [str(t).strip() for t in tags if str(t).strip()],
        "section": (str(entry.get("section") or "").strip() or default_section),
        "source": source,
    }


def _fetch_rss(feeds: list) -> list[dict]:
    """Fetch RSS/Atom feeds. Each feed may be a URL string or a dict with
    `url` plus an optional `section` and extra `tags` merged into every item."""
    if not feeds:
        return []
    try:
        import feedparser  # optional dependency
    except ImportError:
        log.info("feedparser not installed — skipping RSS feeds")
        return []
    out: list[dict] = []
    for feed in feeds:
        if isinstance(feed, str):
            feed_url, section, extra_tags = feed, "", []
        else:
            feed_url = (feed.get("url") or "").strip()
            section = str(feed.get("section") or "").strip()
            extra_tags = feed.get("tags") or []
            if isinstance(extra_tags, str):
                extra_tags = [t.strip() for t in extra_tags.split(",") if t.strip()]
        if not feed_url:
            continue
        try:
            parsed = feedparser.parse(feed_url)
            for e in parsed.entries[:20]:
                date = ""
                if getattr(e, "published_parsed", None):
                    date = time.strftime("%Y-%m-%d", e.published_parsed)
                # Use only the configured tags (Medium categories are noisy).
                tags = list(extra_tags)
                item = _normalize(
                    {"title": getattr(e, "title", ""), "url": getattr(e, "link", ""),
                     "date": date, "tags": tags},
                    source="rss", default_section=section,
                )
                if item:
                    out.append(item)
        except Exception as e:  # pragma: no cover
            log.warning("failed to fetch RSS %s: %s", feed_url, e)
    return out


def _build(cache_bucket: int) -> list[dict]:  # cache_bucket busts the lru_cache over time
    cfg = _load_config()
    manual = [i for i in (_normalize(e) for e in (cfg.get("articles") or [])) if i]
    rss = _fetch_rss(cfg.get("rss_feeds") or [])

    seen = set()
    merged: list[dict] = []
    for item in manual + rss:
        key = item["url"].rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)

    merged.sort(key=lambda x: x["date"], reverse=True)
    return merged


@lru_cache(maxsize=2)
def _cached(cache_bucket: int) -> list[dict]:
    return _build(cache_bucket)


def load_articles() -> list[dict]:
    bucket = int(time.time() // _CACHE_TTL_SECONDS)
    return _cached(bucket)


def all_tags(articles: list[dict]) -> list[str]:
    tags: list[str] = []
    for a in articles:
        for t in a["tags"]:
            if t not in tags:
                tags.append(t)
    return sorted(tags)


def load_sections() -> list[tuple[str, list[dict]]]:
    """Group the feed into ordered (section, items) pairs for the right pane.

    Order follows `section_order` in articles.yaml; any section not listed there is
    appended alphabetically. Items within a section stay newest-first.
    """
    articles = load_articles()
    order = [str(s).strip() for s in (_load_config().get("section_order") or [])]

    groups: dict[str, list[dict]] = {}
    for a in articles:
        groups.setdefault(a.get("section") or "Other", []).append(a)

    ordered: list[tuple[str, list[dict]]] = []
    for name in order:
        if name in groups:
            ordered.append((name, groups.pop(name)))
    for name in sorted(groups):
        ordered.append((name, groups[name]))
    return ordered
