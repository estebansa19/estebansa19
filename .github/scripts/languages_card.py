#!/usr/bin/env python3
"""Render metrics/languages.svg from the GitHub GraphQL API.

The metrics languages plugin renders an empty card (its own published example
has a language count but no bars), so this builds the card directly. Running it
with a token that has `repo` scope means private repositories are counted too,
which matters here because most real work lives in private repos.
"""
import collections, html, json, os, sys, urllib.request

import card

# Data, markup and config languages crowd out what is actually written by hand:
# a single SQL dump or vendored asset otherwise dominates the whole card.
EXCLUDED = {
    "plpgsql", "sql", "tsql", "html", "css", "scss", "sass", "less",
    "handlebars", "blade", "haml", "erb", "ejs", "pug", "mustache",
    "dockerfile", "makefile", "cmake", "shell", "powershell", "batchfile",
    "procfile", "vim script", "vim snippet", "roff", "tex", "coffeescript",
}
# Anything under THRESHOLD is a stray vendored file, not a language someone uses.
LIMIT, THRESHOLD, BAR_H, ROW_H = 8, 0.005, 9, 22
WIDTH, PAD = card.WIDTH, card.PAD

QUERY = """
query($cursor: String) {
  viewer {
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER,
                 isFork: false, orderBy: {field: PUSHED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}"""


def fetch(token):
    totals, colors, cursor = collections.Counter(), {}, None
    while True:
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps({"query": QUERY, "variables": {"cursor": cursor}}).encode(),
            headers={"Authorization": f"bearer {token}",
                     "Content-Type": "application/json",
                     "User-Agent": "languages-card"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.load(resp)
        if "errors" in payload:
            sys.exit(f"GraphQL error: {payload['errors']}")
        repos = payload["data"]["viewer"]["repositories"]
        for node in repos["nodes"]:
            for edge in node["languages"]["edges"]:
                name = edge["node"]["name"]
                if name.lower() in EXCLUDED:
                    continue
                totals[name] += edge["size"]
                colors[name] = edge["node"]["color"] or "#8b949e"
        if not repos["pageInfo"]["hasNextPage"]:
            return totals, colors
        cursor = repos["pageInfo"]["endCursor"]


def render(totals, colors):
    if not totals:
        sys.exit("no languages found - is the token missing `repo` scope?")
    overall = sum(totals.values())
    top = [(n, v) for n, v in totals.most_common(LIMIT) if v / overall >= THRESHOLD]
    if not top:
        top = totals.most_common(1)
    # Renormalise over what is actually shown, so the bar fills and the
    # percentages add up to 100 rather than to "100 minus the discarded tail".
    total = sum(v for _, v in top)
    inner = WIDTH - PAD * 2
    rows = (len(top) + 1) // 2
    height = 50 + BAR_H + 26 + (rows - 1) * ROW_H + 22

    out = card.open_svg(height, "Most used languages", "Most used languages")

    # One rounded strip, clipped, so segments meet flush with no seams.
    out.append(f'<clipPath id="bar"><rect x="{PAD}" y="50" width="{inner}" height="{BAR_H}" rx="{BAR_H / 2}"/></clipPath>')
    out.append('<g clip-path="url(#bar)">')
    x = float(PAD)
    for i, (name, size) in enumerate(top):
        # Snap the final segment to the edge so rounding cannot leave a gap.
        w = (PAD + inner - x) if i == len(top) - 1 else inner * size / total
        out.append(f'<rect x="{x:.2f}" y="50" width="{w:.2f}" height="{BAR_H}" fill="{colors[name]}"/>')
        x += w
    out.append('</g>')

    for i, (name, size) in enumerate(top):
        cx = PAD + (i % 2) * (inner / 2)
        cy = 50 + BAR_H + 26 + (i // 2) * ROW_H
        pct = size / total * 100
        out.append(f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{colors[name]}"/>')
        out.append(f'<text x="{cx + 16}" y="{cy}" class="l">{html.escape(name)} {pct:.1f}%</text>')

    return card.close_svg(out), top


if __name__ == "__main__":
    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GH_TOKEN is not set")
    totals, colors = fetch(token)
    os.makedirs("metrics", exist_ok=True)
    svg, shown = render(totals, colors)
    with open("metrics/languages.svg", "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote metrics/languages.svg ({len(totals)} languages found, {len(shown)} shown)")
    total = sum(v for _, v in shown)
    for name, size in shown:
        print(f"  {name:<14}{size / total * 100:>6.1f}%")
