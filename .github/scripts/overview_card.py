#!/usr/bin/env python3
"""Render metrics/overview.svg from the GitHub GraphQL API.

The metrics overview card spent most of its rows on counts that are zero only
because the work behind them is private - reviews, issues, org membership - so
it read as an inactive account. This shows a few true numbers instead, and says
outright how much of the work is private.

Needs a token with `repo` scope for restrictedContributionsCount to be real.
"""
import datetime, json, os, sys, urllib.request

import card

ACCOUNT = """
query { viewer {
  createdAt
  repositories(ownerAffiliations: OWNER, isFork: false) { totalCount }
} }"""

YEAR = """
query($from: DateTime!, $to: DateTime!) { viewer {
  contributionsCollection(from: $from, to: $to) {
    contributionCalendar { totalContributions }
  }
} }"""


def gql(token, query, **variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}",
                 "Content-Type": "application/json",
                 "User-Agent": "overview-card"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        sys.exit(f"GraphQL error: {payload['errors']}")
    return payload["data"]["viewer"]


def collect(token):
    account = gql(token, ACCOUNT)
    first = int(account["createdAt"][:4])
    this_year = datetime.datetime.now(datetime.timezone.utc).year
    total = 0
    # contributionsCollection only spans a year at a time, so walk the account.
    for year in range(first, this_year + 1):
        got = gql(token, YEAR, **{"from": f"{year}-01-01T00:00:00Z",
                                  "to": f"{year}-12-31T23:59:59Z"})
        total += got["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    return {"contributions": total, "since": first,
            "repositories": account["repositories"]["totalCount"],
            "years": max(1, this_year - first)}


def render(stats):
    out = card.open_svg(129, "At a glance", "GitHub contribution summary")
    columns = [
        (f"{stats['contributions']:,}", "contributions"),
        (f"{stats['repositories']:,}", "repositories"),
        (f"{stats['years']}", f"years, since {stats['since']}"),
    ]
    step = (card.WIDTH - card.PAD * 2) / len(columns)
    for i, (value, label) in enumerate(columns):
        x = card.PAD + i * step
        out.append(f'<text x="{x:.0f}" y="78" class="n">{value}</text>')
        out.append(f'<text x="{x:.0f}" y="96" class="l">{label}</text>')
    out.append(f'<text x="{card.PAD}" y="118" class="s">'
               f'Most recent work lives in private repositories</text>')
    return card.close_svg(out)


if __name__ == "__main__":
    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GH_TOKEN is not set")
    stats = collect(token)
    os.makedirs("metrics", exist_ok=True)
    with open("metrics/overview.svg", "w", encoding="utf-8") as fh:
        fh.write(render(stats))
    print(f"wrote metrics/overview.svg  {stats}")
