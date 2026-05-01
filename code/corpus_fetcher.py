"""
corpus_fetcher.py — Web scraper for support sites.

Scrapes HackerRank, Claude, and Visa support pages and saves them as JSON
files under data/hackerrank/, data/claude/, and data/visa/.
"""

from __future__ import annotations

import json
import time
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent.parent / "data"

SOURCES = [
    {
        "name": "hackerrank",
        "seed_url": "https://support.hackerrank.com/hc/en-us",
        "domain": "support.hackerrank.com",
        "path_patterns": ["/articles/", "/hc/", "/en/", "/support/", "/help/", "/faq/"],
        "max_pages": 80,
    },
    {
        "name": "claude",
        "seed_url": "https://support.claude.com/en/",
        "domain": "support.claude.com",
        "path_patterns": ["/articles/", "/hc/", "/en/", "/support/", "/help/", "/faq/"],
        "max_pages": 80,
    },
    {
        "name": "visa",
        "seed_url": "https://www.visa.co.in/support.html",
        "domain": "www.visa.co.in",
        "path_patterns": ["/support/", "/help/", "/faq/", "/en/", "/articles/"],
        "max_pages": 80,
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; SupportTriageBot/1.0; "
        "+https://github.com/hackerrank-orchestrate)"
    )
}

MIN_CONTENT_LENGTH = 100
MAX_CONTENT_LENGTH = 8000
REQUEST_DELAY = 0.5


def _extract_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text[:MAX_CONTENT_LENGTH]


def _extract_title(soup: BeautifulSoup) -> str:
    if soup.title:
        return soup.title.string.strip()
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    return "Untitled"


def _is_valid_url(url: str, domain: str, path_patterns: list[str]) -> bool:
    parsed = urlparse(url)
    if parsed.netloc != domain:
        return False
    path = parsed.path.lower()
    return any(pat in path for pat in path_patterns)


def _fetch_page(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as exc:
        print(f"  [warn] Failed to fetch {url}: {exc}")
        return None


def scrape_source(source: dict) -> int:
    name = source["name"]
    domain = source["domain"]
    seed_url = source["seed_url"]
    path_patterns = source["path_patterns"]
    max_pages = source["max_pages"]

    out_dir = DATA_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)

    visited: set[str] = set()
    queue: list[str] = [seed_url]
    saved = 0

    print(f"\n[corpus] Scraping {name} from {seed_url} (max {max_pages} pages)")

    while queue and saved < max_pages:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        print(f"  [{saved + 1}/{max_pages}] {url}")
        soup = _fetch_page(url)
        if soup is None:
            time.sleep(REQUEST_DELAY)
            continue

        content = _extract_text(soup)
        if len(content) < MIN_CONTENT_LENGTH:
            time.sleep(REQUEST_DELAY)
            continue

        title = _extract_title(soup)
        page_data = {"url": url, "title": title, "content": content}

        safe_name = re.sub(r"[^\w]", "_", url)[-80:]
        out_path = out_dir / f"{safe_name}.json"
        out_path.write_text(json.dumps(page_data, ensure_ascii=False, indent=2), encoding="utf-8")
        saved += 1

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            absolute = urljoin(url, href)
            absolute = absolute.split("#")[0].split("?")[0]
            if absolute not in visited and _is_valid_url(absolute, domain, path_patterns):
                queue.append(absolute)

        time.sleep(REQUEST_DELAY)

    print(f"[corpus] Saved {saved} pages for {name}")
    return saved


def fetch_all_corpus() -> None:
    total = 0
    for source in SOURCES:
        total += scrape_source(source)
    print(f"\n[corpus] Done. Total pages saved: {total}")


if __name__ == "__main__":
    fetch_all_corpus()
