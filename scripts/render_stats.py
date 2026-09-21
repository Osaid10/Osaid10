#!/usr/bin/env python3
"""Render the results card as SVG.

Two reasons this is not the usual profile stat card. It is hotlinked from
nobody: the file is committed here and served by GitHub, so it cannot
rate-limit or 404 the way the third-party cards do. And it does not report
stars, followers or merged PRs -- those measure an open-source following, not
engineering, and reporting a small number is worse than reporting none.

The headline figures are measured results from the projects, each one
reproducible from the repo it names. The language split is the one part
computed live from the GitHub API, so it stays honest as the repos change.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

USER = "Osaid10"
W, H = 1000, 170

THEMES = {
    "dark":  {"bg": "#0D1117", "panel": "#0F1621", "border": "#21262D",
              "text": "#E6EDF3", "muted": "#8B949E", "accent": "#00E5FF",
              "track": "#21262D"},
    "light": {"bg": "#FFFFFF", "panel": "#F6F8FA", "border": "#D0D7DE",
              "text": "#1F2328", "muted": "#59636E", "accent": "#0E7490",
              "track": "#E4E8EC"},
}

FONT = ("ui-sans-serif,-apple-system,BlinkMacSystemFont,'Segoe UI',"
        "Roboto,Helvetica,Arial,sans-serif")
MONO = ("ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
        "'Liberation Mono',monospace")

# Measured results, each from the eval harness or README of the named repo.
RESULTS = [
    ("39%",    "PERPLEXITY CUT",  "LoRA, 0.33% of params"),
    ("~94%",   "FACE RECOGNITION", "live RTSP video"),
    ("3,368",  "PAGES INDEXED",   "text + images, RAG"),
    ("20+",    "TASKS PER HIRE",  "agent-orchestrated"),
]

# Languages that say nothing about how someone builds software.
SKIP_LANGS = {"HTML", "CSS", "SCSS", "Jupyter Notebook", "Dockerfile",
              "Makefile", "Batchfile", "Shell", "PowerShell"}

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    pullRequests(states: MERGED) { totalCount }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


def fetch(token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}",
                 "Content-Type": "application/json",
                 "User-Agent": f"{USER}-profile-card"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if "errors" in body:
        raise RuntimeError(body["errors"])
    return body["data"]["user"]


def summarize(user: dict) -> dict:
    repos = user["repositories"]["nodes"]
    sizes: dict[str, int] = {}
    colors: dict[str, str] = {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if name in SKIP_LANGS:
                continue
            sizes[name] = sizes.get(name, 0) + edge["size"]
            colors[name] = edge["node"]["color"] or "#888888"
    top = sorted(sizes.items(), key=lambda kv: -kv[1])[:5]
    total = sum(s for _, s in top) or 1
    return {
        "repos": user["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "prs": user["pullRequests"]["totalCount"],
        "followers": user["followers"]["totalCount"],
        "langs": [(n, s / total * 100, colors[n]) for n, s in top],
    }


def render(data: dict, theme: str) -> str:
    c = THEMES[theme]

    cells = []
    for i, (value, label, sub) in enumerate(RESULTS):
        x = 68 + i * 138
        cells.append(
            f'<text x="{x}" y="92" font-family="{MONO}" font-size="29" font-weight="700" '
            f'fill="{c["text"]}">{value}</text>'
            f'<text x="{x}" y="113" font-family="{FONT}" font-size="10" font-weight="600" '
            f'letter-spacing="0.9" fill="{c["text"]}" fill-opacity="0.75">{label}</text>'
            f'<text x="{x}" y="129" font-family="{FONT}" font-size="9.5" '
            f'fill="{c["muted"]}">{sub}</text>')

    bar_x, bar_w, bar_y = 626, 306, 82
    bar, legend, cursor = [], [], float(bar_x)
    bar.append(f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="9" rx="4.5" fill="{c["track"]}"/>')
    for i, (name, pct, color) in enumerate(data["langs"]):
        seg = bar_w * pct / 100
        bar.append(f'<rect x="{cursor:.1f}" y="{bar_y}" width="{max(seg - 2, 1):.1f}" '
                   f'height="9" rx="4.5" fill="{color}"/>')
        cursor += seg
        col, row = i % 3, i // 3
        lx, ly = bar_x + col * 104, 120 + row * 20
        legend.append(
            f'<circle cx="{lx + 4}" cy="{ly - 4}" r="4" fill="{color}"/>'
            f'<text x="{lx + 14}" y="{ly}" font-family="{FONT}" font-size="11" '
            f'fill="{c["muted"]}">{name} {pct:.0f}%</text>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
     viewBox="0 0 {W} {H}" role="img" aria-label="Measured results and language split">
  <defs>
    <linearGradient id="p" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c['panel']}"/>
      <stop offset="1" stop-color="{c['bg']}"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="14" fill="url(#p)"/>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="13.5"
        fill="none" stroke="{c['border']}"/>
  <rect x="44" y="34" width="3" height="20" rx="1.5" fill="{c['accent']}"/>
  <text x="60" y="49" font-family="{MONO}" font-size="12" font-weight="600"
        letter-spacing="2.6" fill="{c['accent']}">MEASURED RESULTS</text>
  <line x1="600" y1="34" x2="600" y2="138" stroke="{c['border']}"/>
  <text x="626" y="49" font-family="{MONO}" font-size="12" font-weight="600"
        letter-spacing="2.6" fill="{c['accent']}">LANGUAGES</text>
  <text x="626" y="68" font-family="{FONT}" font-size="10"
        fill="{c['muted']}">across {data['repos']} public repositories</text>
  {''.join(cells)}
  {''.join(bar)}
  {''.join(legend)}
</svg>
"""


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("set GITHUB_TOKEN (locally: export GITHUB_TOKEN=$(gh auth token))",
              file=sys.stderr)
        return 1
    try:
        data = summarize(fetch(token))
    except (urllib.error.URLError, RuntimeError) as exc:
        # Leave the committed card in place rather than replacing it with junk.
        print(f"stats fetch failed, keeping existing card: {exc}", file=sys.stderr)
        return 1

    print(f"repos={data['repos']}")
    print("langs: " + ", ".join(f"{n} {p:.0f}%" for n, p, _ in data["langs"]))

    out = Path(__file__).resolve().parent.parent / "assets"
    out.mkdir(exist_ok=True)
    for theme in THEMES:
        (out / f"stats-{theme}.svg").write_text(render(data, theme), encoding="utf-8")
        print(f"wrote assets/stats-{theme}.svg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
