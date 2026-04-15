#!/usr/bin/env python3
"""
Marginal Revolution Daily Digest
Fetches new posts and generates an HTML digest with a text excerpt of each post.
"""

import json
import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

load_dotenv(Path(__file__).parent / ".env")

SCRIPT_DIR = Path(__file__).parent
STATE_FILE = SCRIPT_DIR / "state" / "last_run.json"
TEMPLATES_DIR = SCRIPT_DIR / "templates"
MR_FEED_URL = "https://marginalrevolution.com/feed"
REQUESTS_TIMEOUT = 30
FETCH_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MR-Digest/1.0; +https://marginalrevolution.com)"}

log = logging.getLogger(__name__)


def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_run": None}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def fetch_feed() -> feedparser.FeedParserDict:
    log.info("Fetching MR RSS feed...")
    feed = feedparser.parse(MR_FEED_URL, request_headers=FETCH_HEADERS)
    if feed.bozo and not feed.entries:
        raise RuntimeError(f"Feed parse error: {feed.bozo_exception}")
    return feed


def filter_new_posts(feed: feedparser.FeedParserDict, last_run: str | None) -> list:
    today = date.today()
    posts = []

    for entry in feed.entries:
        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

        if last_run is None:
            # First run: only today's posts
            if published.date() == today:
                posts.append((entry, published))
        else:
            cutoff = datetime.fromisoformat(last_run)
            if published > cutoff:
                posts.append((entry, published))

    # Oldest first so the digest reads chronologically
    posts.sort(key=lambda x: x[1])
    return posts


def fetch_post_html(url: str) -> str:
    resp = requests.get(url, headers=FETCH_HEADERS, timeout=REQUESTS_TIMEOUT)
    resp.raise_for_status()
    return resp.text


EXCERPT_CHARS = 1000

# Block-level tags we keep in the excerpt (others are skipped)
_BLOCK_TAGS = {"p", "blockquote", "ul", "ol", "pre", "h2", "h3", "h4"}


def extract_excerpt(raw_html: str) -> str:
    """Return an HTML excerpt preserving block structure (p, blockquote, lists, etc.)
    up to approximately EXCERPT_CHARS of visible text."""
    from bs4 import Tag

    soup = BeautifulSoup(raw_html, "lxml")
    content = (
        soup.find("div", class_="entry-content")
        or soup.find("div", class_="post-content")
        or soup.find("article")
        or soup.find("main")
        or soup
    )

    for tag in content.find_all(["script", "style", "nav", "footer", "aside", "form"]):
        tag.decompose()

    char_count = 0
    kept = []
    last_tag_name = None

    for child in content.children:
        if not isinstance(child, Tag) or child.name not in _BLOCK_TAGS:
            continue

        text_len = len(child.get_text())

        if char_count + text_len > EXCERPT_CHARS:
            if not kept:
                # First block alone exceeds limit — truncate its text, keep the tag
                plain = " ".join(child.get_text(separator=" ").split())
                trimmed = plain[:EXCERPT_CHARS].rsplit(" ", 1)[0]
                kept.append(f"<{child.name}>{trimmed}…</{child.name}>")
            else:
                # Append ellipsis inside the closing tag of the last kept block
                close = f"</{last_tag_name}>"
                last = kept[-1]
                if last.endswith(close):
                    kept[-1] = last[: -len(close)].rstrip() + "…" + close
                else:
                    kept[-1] = last.rstrip() + "…"
            break

        kept.append(str(child))
        char_count += text_len
        last_tag_name = child.name

    return "\n".join(kept)


def build_digest_html(posts: list, run_time: datetime) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)
    template = env.get_template("digest.html")
    return template.render(
        posts=posts,
        generated_at=run_time,
        date_str=run_time.strftime("%A, %B %-d, %Y"),
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    state = load_state()
    last_run = state.get("last_run")
    run_time = datetime.now(timezone.utc)

    log.info("Last run: %s", last_run or "never (first run)")

    tmp_dir = Path(f"/tmp/mr-digest-{run_time.strftime('%Y%m%d-%H%M%S')}")
    tmp_dir.mkdir(parents=True)
    log.info("Working directory: %s", tmp_dir)

    feed = fetch_feed()
    new_posts = filter_new_posts(feed, last_run)

    if not new_posts:
        log.info("No new posts since last run. Nothing to send.")
        return

    log.info("Found %d new post(s)", len(new_posts))

    digest_posts = []
    for i, (entry, published) in enumerate(new_posts):
        log.info("[%d/%d] %s", i + 1, len(new_posts), entry.title)
        try:
            raw_html = fetch_post_html(entry.link)
            (tmp_dir / f"post_{i+1:02d}_raw.html").write_text(raw_html, encoding="utf-8")

            excerpt = extract_excerpt(raw_html)
            log.info("  Excerpt: %d chars", len(excerpt))

            digest_posts.append(
                {
                    "title": entry.title,
                    "url": entry.link,
                    "published": published,
                    "summary": excerpt,
                    "author": getattr(entry, "author", None),
                }
            )
        except Exception as exc:
            log.error("  Failed to process %s: %s", entry.link, exc)

    if not digest_posts:
        log.error("All posts failed to process. Aborting.")
        sys.exit(1)

    html = build_digest_html(digest_posts, run_time)
    digest_path = tmp_dir / "digest.html"
    digest_path.write_text(html, encoding="utf-8")
    log.info("Digest written to %s", digest_path)

    # Save state before sending so a mail failure doesn't re-process posts
    save_state({"last_run": run_time.isoformat()})

    from mailer import send_digest

    send_digest(html, run_time)
    log.info("Done.")


if __name__ == "__main__":
    main()
