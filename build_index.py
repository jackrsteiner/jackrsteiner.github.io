#!/usr/bin/env python3
"""
Generate a root GitHub Pages index for a user account.

This script:
1. Lists public repositories for OWNER.
2. Keeps repositories that have GitHub Pages enabled.
3. Reads each Pages config to get the published Pages URL.
4. Filters to project Pages URLs under https://OWNER.github.io/<repo>/.
5. Writes public/index.html for deployment by GitHub Actions.

It uses only Python's standard library.
"""

from __future__ import annotations

import html
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


OWNER = os.environ.get("OWNER", "jackrsteiner")
TOKEN = os.environ.get("GITHUB_TOKEN")

API_VERSION = "2022-11-28"
ROOT_PAGES_REPO = f"{OWNER}.github.io"
ROOT_URL = f"https://{OWNER}.github.io"

INCLUDE_FORKS = os.environ.get("INCLUDE_FORKS", "").lower() in {"1", "true", "yes"}
INCLUDE_ARCHIVED = os.environ.get("INCLUDE_ARCHIVED", "").lower() in {"1", "true", "yes"}
INCLUDE_CUSTOM_DOMAINS = os.environ.get("INCLUDE_CUSTOM_DOMAINS", "").lower() in {
    "1",
    "true",
    "yes",
}


def github_get_json(url: str) -> Any | None:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": f"{OWNER}-pages-index-builder",
    }

    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None

        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass

        raise RuntimeError(f"GitHub API request failed: HTTP {exc.code} for {url}\n{body}") from exc


def list_public_repos(owner: str) -> list[dict[str, Any]]:
    repos: list[dict[str, Any]] = []
    page = 1

    while True:
        params = urllib.parse.urlencode(
            {
                "type": "owner",
                "sort": "updated",
                "direction": "desc",
                "per_page": 100,
                "page": page,
            }
        )
        url = f"https://api.github.com/users/{owner}/repos?{params}"
        batch = github_get_json(url)

        if not batch:
            break

        repos.extend(batch)

        if len(batch) < 100:
            break

        page += 1

    return repos


def get_pages_site(owner: str, repo_name: str) -> dict[str, Any] | None:
    url = f"https://api.github.com/repos/{owner}/{repo_name}/pages"
    pages = github_get_json(url)

    if pages is None:
        return None

    if not isinstance(pages, dict):
        raise RuntimeError(f"Unexpected Pages response for {repo_name}: {pages!r}")

    return pages


def load_profile() -> dict[str, Any]:
    path = Path("profile.json")
    if not path.exists():
        return {
            "name": OWNER,
            "headline": "GitHub Pages projects",
            "bio": "",
            "links": [],
        }

    with path.open("r", encoding="utf-8") as file:
        profile = json.load(file)

    if not isinstance(profile, dict):
        raise ValueError("profile.json must contain a JSON object.")

    return profile


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def repo_display_name(repo: dict[str, Any]) -> str:
    return repo.get("name", "").replace("-", " ").replace("_", " ").strip().title()


def generate_html(profile: dict[str, Any], sites: list[dict[str, Any]]) -> str:
    title = profile.get("name") or OWNER
    headline = profile.get("headline") or "GitHub Pages projects"
    bio = profile.get("bio") or ""

    links = profile.get("links") or []
    if not isinstance(links, list):
        links = []

    link_items = "\n".join(
        f'<a href="{esc(link.get("url", "#"))}">{esc(link.get("label", "Link"))}</a>'
        for link in links
        if isinstance(link, dict)
    )

    site_cards = "\n".join(
        f"""
        <article class="card">
          <h3><a href="{esc(site["pages_url"])}">{esc(site["title"])}</a></h3>
          <p>{esc(site.get("description") or "No description provided.")}</p>
          <p class="repo-name">{esc(site["name"])}</p>
          <p class="meta">
            <a href="{esc(site["repo_url"])}">Repository</a>
            <span aria-hidden="true">·</span>
            <a href="{esc(site["pages_url"])}">Pages site</a>
          </p>
        </article>
        """
        for site in sites
    )

    if not site_cards:
        site_cards = """
        <p>
          No project Pages sites were found. Enable GitHub Pages on one or more
          public repositories and re-run the workflow.
        </p>
        """

    updated = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(headline)}">
  <style>
    :root {{
      color-scheme: light dark;
      --max-width: 980px;
      --border: color-mix(in srgb, CanvasText 18%, transparent);
      --muted: color-mix(in srgb, CanvasText 72%, transparent);
      font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      line-height: 1.5;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      max-width: var(--max-width);
      margin: 0 auto;
      padding: 3rem 1.25rem;
      background: Canvas;
      color: CanvasText;
    }}

    a {{
      color: LinkText;
      text-underline-offset: 0.16em;
    }}

    header {{
      margin-bottom: 2.75rem;
    }}

    h1 {{
      max-width: 12ch;
      font-size: clamp(2.25rem, 8vw, 4.75rem);
      line-height: 0.96;
      letter-spacing: -0.055em;
      margin: 0 0 0.85rem;
    }}

    h2 {{
      font-size: clamp(1.4rem, 4vw, 2rem);
      margin: 0 0 1rem;
      letter-spacing: -0.03em;
    }}

    h3 {{
      margin: 0 0 0.45rem;
      font-size: 1.1rem;
    }}

    .headline {{
      max-width: 58rem;
      font-size: 1.25rem;
      margin: 0 0 0.7rem;
      color: var(--muted);
    }}

    .bio {{
      max-width: 64rem;
      margin: 0;
    }}

    nav {{
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
      margin-top: 1.2rem;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 1rem;
    }}

    .card {{
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 1.25rem;
    }}

    .card p {{
      margin: 0.5rem 0;
    }}

    .repo-name {{
      color: var(--muted);
      font-size: 0.9rem;
      font-family:
        ui-monospace,
        SFMono-Regular,
        Menlo,
        Consolas,
        monospace;
    }}

    .meta {{
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
      font-size: 0.95rem;
    }}

    footer {{
      margin-top: 3rem;
      font-size: 0.9rem;
      color: var(--muted);
    }}
  </style>
</head>
<body>
  <header>
    <h1>{esc(title)}</h1>
    <p class="headline">{esc(headline)}</p>
    <p class="bio">{esc(bio)}</p>
    <nav aria-label="Profile links">
      {link_items}
    </nav>
  </header>

  <main>
    <h2>Public GitHub Pages projects</h2>
    <section class="grid">
      {site_cards}
    </section>
  </main>

  <footer>
    Generated automatically from public GitHub repository metadata.
    Last updated: {esc(updated)}.
  </footer>
</body>
</html>
"""


def main() -> None:
    profile = load_profile()
    repos = list_public_repos(OWNER)

    sites: list[dict[str, Any]] = []

    for repo in repos:
        name = repo.get("name")

        if not name:
            continue

        if name == ROOT_PAGES_REPO:
            continue

        if repo.get("fork") and not INCLUDE_FORKS:
            continue

        if repo.get("archived") and not INCLUDE_ARCHIVED:
            continue

        # The repository list usually includes has_pages. Use it to avoid
        # unnecessary API calls, but still tolerate older/unexpected responses.
        if repo.get("has_pages") is False:
            continue

        pages = get_pages_site(OWNER, name)

        if not pages:
            continue

        pages_url = pages.get("html_url") or f"{ROOT_URL}/{name}/"

        if not isinstance(pages_url, str):
            continue

        # By default, keep only normal project Pages sites under:
        # https://OWNER.github.io/<repo>/
        #
        # Set INCLUDE_CUSTOM_DOMAINS=true if you also want to list repos whose
        # Pages sites publish to custom domains.
        if not INCLUDE_CUSTOM_DOMAINS and not pages_url.rstrip("/").startswith(f"{ROOT_URL}/"):
            continue

        sites.append(
            {
                "name": name,
                "title": repo_display_name(repo),
                "description": repo.get("description"),
                "repo_url": repo.get("html_url") or f"https://github.com/{OWNER}/{name}",
                "pages_url": pages_url,
                "updated_at": repo.get("updated_at") or "",
            }
        )

    sites.sort(key=lambda site: site["title"].lower())

    output_dir = Path("public")
    output_dir.mkdir(exist_ok=True)

    (output_dir / "index.html").write_text(
        generate_html(profile, sites),
        encoding="utf-8",
    )

    # Avoid Jekyll processing. It is harmless with Actions deploys and useful
    # if you later switch to branch-based deployment.
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    print(f"Generated index with {len(sites)} Pages site(s).")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise
