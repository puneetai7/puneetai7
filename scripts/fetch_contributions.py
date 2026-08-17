"""Scrape the public contribution calendar into data/contributions.json.

No token needed: github.com/users/<name>/contributions is a public HTML fragment.
"""

import json
import os
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USER = os.environ.get("PROFILE_USER", "puneetai7")
URL = f"https://github.com/users/{USER}/contributions"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"


def scrape():
    resp = requests.get(
        URL,
        headers={
            "User-Agent": "profile-readme-bot",
            "X-Requested-With": "XMLHttpRequest",
        },
        timeout=30,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    days = []
    for cell in soup.select("td.ContributionCalendar-day"):
        date = cell.get("data-date")
        if not date:
            continue
        level = int(cell.get("data-level") or 0)
        # The count lives in a sibling tooltip keyed by the cell id, or in the
        # cell's own text depending on which template GitHub served.
        count = 0
        tip = soup.select_one(f'tool-tip[for="{cell.get("id")}"]')
        text = (tip.get_text() if tip else cell.get_text()).strip()
        head = text.split(" ", 1)[0]
        if head.isdigit():
            count = int(head)
        elif text.lower().startswith("no contributions"):
            count = 0
        days.append({"date": date, "level": level, "count": count})

    days.sort(key=lambda d: d["date"])
    return days


def main():
    days = scrape()
    if not days:
        print("no contribution cells found — layout changed?", file=sys.stderr)
        return 1

    payload = {
        "user": USER,
        "days": days,
        "total": sum(d["count"] for d in days),
        "start": days[0]["date"],
        "end": days[-1]["date"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT.name}: {len(days)} days, {payload['total']} contributions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
