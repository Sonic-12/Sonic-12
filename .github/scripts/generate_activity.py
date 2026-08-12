"""
Self-hosted replacement for the github-readme-activity-graph.vercel.app badge.

That service is a shared, free-tier deployment maintained by a third party and
is frequently rate-limited / offline (see upstream repo notice + issues #197,
#199). Since this repo already self-hosts the snake + clock SVGs via GitHub
Actions -> `output` branch, we generate the activity graph the same way:
no external service, no downtime tied to someone else's Vercel quota.

Pulls the user's public events (last ~90 days, GitHub's own retention window)
via the REST API, buckets contribution-style events by day for the last N
days, and renders a small bar/area chart SVG in the same Tokyo Night palette
already used for clock.svg.
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

USERNAME = os.environ.get("GH_USERNAME", "Sonic-12")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DAYS = 30

# Event types that represent meaningful "activity" for the graph.
COUNTED_EVENTS = {
    "PushEvent": lambda p: max(1, len(p.get("commits", []))),
    "PullRequestEvent": lambda p: 1,
    "IssuesEvent": lambda p: 1,
    "IssueCommentEvent": lambda p: 1,
    "PullRequestReviewEvent": lambda p: 1,
    "PullRequestReviewCommentEvent": lambda p: 1,
    "CreateEvent": lambda p: 1,
    "ForkEvent": lambda p: 1,
}

# Tokyo Night palette (matches clock.svg / existing README theme param)
BG = "#1a1b27"
BAR_BG = "#16161e"
BORDER = "#414868"
GRID = "#292e42"
TEXT_DIM = "#565f89"
TEXT_LABEL = "#c0caf5"
ACCENT = "#7aa2f7"
ACCENT_SOFT = "#7aa2f7"
DOT_RED = "#f7768e"
DOT_YELLOW = "#e0af68"
DOT_GREEN = "#9ece6a"

W, H = 900, 260
PAD_LEFT, PAD_RIGHT = 40, 24
PAD_TOP, PAD_BOTTOM = 46, 34
PLOT_W = W - PAD_LEFT - PAD_RIGHT
PLOT_H = H - PAD_TOP - PAD_BOTTOM


def fetch_events():
    events = []
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-activity-graph-selfhost",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    for page in range(1, 4):  # events API only ever returns ~300 events / 90 days
        url = f"https://api.github.com/users/{USERNAME}/events/public?per_page=100&page={page}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            print(f"GitHub API error on page {page}: {e.code} {e.reason}")
            break
        except Exception as e:
            print(f"Failed to fetch events page {page}: {e}")
            break
        if not data:
            break
        events.extend(data)
        if len(data) < 100:
            break
    return events


def bucket_by_day(events):
    today = datetime.now(timezone.utc).date()
    counts = {today - timedelta(days=i): 0 for i in range(DAYS)}
    oldest = today - timedelta(days=DAYS - 1)

    for ev in events:
        etype = ev.get("type")
        weight_fn = COUNTED_EVENTS.get(etype)
        if not weight_fn:
            continue
        try:
            created = datetime.fromisoformat(
                ev["created_at"].replace("Z", "+00:00")
            ).date()
        except Exception:
            continue
        if created < oldest or created > today:
            continue
        counts[created] = counts.get(created, 0) + weight_fn(ev.get("payload", {}))

    ordered_days = sorted(counts.keys())
    return ordered_days, [counts[d] for d in ordered_days]


def build_svg(days, values):
    total = sum(values)
    max_val = max(values) if values else 0
    max_val = max(max_val, 1)

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" font-family="\'SF Mono\',Consolas,monospace">'
    )

    parts.append(f'''<defs>
  <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{ACCENT}" stop-opacity="0.45"/>
    <stop offset="100%" stop-color="{ACCENT}" stop-opacity="0"/>
  </linearGradient>
</defs>''')

    # card background + border
    parts.append(f'<rect width="{W}" height="{H}" rx="12" fill="{BG}"/>')
    parts.append(
        f'<rect x="0.75" y="0.75" width="{W-1.5}" height="{H-1.5}" rx="11.25" '
        f'fill="none" stroke="{BORDER}" stroke-width="1"/>'
    )

    # terminal title bar
    parts.append(
        f'<path d="M0.75,11 A11.25,11.25 0 0 1 12,0.75 H{W-12} '
        f'A11.25,11.25 0 0 1 {W-0.75},11 V32 H0.75 Z" fill="{BAR_BG}"/>'
    )
    parts.append(f'<line x1="0" y1="32" x2="{W}" y2="32" stroke="{BORDER}" stroke-width="1"/>')
    for i, c in enumerate((DOT_RED, DOT_YELLOW, DOT_GREEN)):
        parts.append(f'<circle cx="{18 + i*13}" cy="16" r="4" fill="{c}"/>')
    parts.append(
        f'<text x="{W/2}" y="21" text-anchor="middle" fill="{TEXT_DIM}" '
        f'font-size="11">activity.py — last {DAYS} days ({total} contributions)</text>'
    )

    # horizontal grid lines + y labels
    n_grid = 4
    for i in range(n_grid + 1):
        y = PAD_TOP + PLOT_H - (PLOT_H * i / n_grid)
        val = round(max_val * i / n_grid)
        parts.append(
            f'<line x1="{PAD_LEFT}" y1="{y:.1f}" x2="{W-PAD_RIGHT}" y2="{y:.1f}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{PAD_LEFT-8}" y="{y+3:.1f}" text-anchor="end" '
            f'fill="{TEXT_DIM}" font-size="9">{val}</text>'
        )

    # points for the line/area
    n = len(days)
    step = PLOT_W / max(1, n - 1)
    pts = []
    for i, v in enumerate(values):
        x = PAD_LEFT + i * step
        y = PAD_TOP + PLOT_H - (v / max_val) * PLOT_H
        pts.append((x, y))

    # area under curve
    if pts:
        area_path = f"M{pts[0][0]:.1f},{PAD_TOP+PLOT_H:.1f} "
        area_path += " ".join(f"L{x:.1f},{y:.1f}" for x, y in pts)
        area_path += f" L{pts[-1][0]:.1f},{PAD_TOP+PLOT_H:.1f} Z"
        parts.append(f'<path d="{area_path}" fill="url(#areaGrad)"/>')

        line_path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        parts.append(
            f'<path d="{line_path}" fill="none" stroke="{ACCENT}" '
            f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
        )

        for x, y in pts:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="{ACCENT}"/>')

    # x-axis: label every ~5th day
    label_every = max(1, n // 6)
    for i, d in enumerate(days):
        if i % label_every == 0 or i == n - 1:
            x = PAD_LEFT + i * step
            parts.append(
                f'<text x="{x:.1f}" y="{H-PAD_BOTTOM+16}" text-anchor="middle" '
                f'fill="{TEXT_DIM}" font-size="9">{d.strftime("%b %d")}</text>'
            )

    parts.append(
        f'<text x="{W-PAD_RIGHT}" y="{H-10}" text-anchor="end" fill="{TEXT_DIM}" '
        f'font-size="8.5">self-hosted via GitHub Actions</text>'
    )

    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    events = fetch_events()
    days, values = bucket_by_day(events)
    if not days:
        # Fallback so the workflow never fails the whole run on an API hiccup
        today = datetime.now(timezone.utc).date()
        days = [today - timedelta(days=i) for i in range(DAYS - 1, -1, -1)]
        values = [0] * DAYS
    svg = build_svg(days, values)
    os.makedirs("dist", exist_ok=True)
    with open("dist/activity-graph.svg", "w") as f:
        f.write(svg)
    print(f"wrote dist/activity-graph.svg — {sum(values)} events over {DAYS} days")
