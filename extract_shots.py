#!/usr/bin/env python3
"""Extract per-player shots + a league FG%-by-distance baseline from the
2015-16 NBA play-by-play logs, and write a compact shots.json for the
interactive hexbin chart (shotchart.html).

Data source: https://eightthirtyfour.com/data (2015-16 combined PbP CSV).
Set CSV below to your local copy of the combined-stats file.
"""
import csv, json, math, os
from collections import defaultdict

# --- input: local path to the 2015-16 combined play-by-play CSV ---
CSV = os.environ.get(
    "NBA_PBP_CSV",
    "/Users/ricardo/Personal/datasets/nba/2015-16/[10-20-2015]-[06-20-2016]-combined-stats.csv",
)
# --- output: written next to this script; copy to the website's asset dir to deploy ---
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots.json")

# Hero + storyline players for the chart's dropdown (Curry first).
PLAYERS = [
    "Stephen Curry", "Klay Thompson", "Kevin Durant", "Russell Westbrook",
    "LeBron James", "Kyrie Irving", "James Harden", "Kawhi Leonard",
    "Damian Lillard", "DeMar DeRozan", "Anthony Davis", "Kobe Bryant",
    "Chris Paul", "Draymond Green",
]
WANT = set(PLAYERS)

csv.field_size_limit(10**7)

player_shots = defaultdict(list)            # name -> [[x, y, made(0/1)], ...]
league_makes = defaultdict(int)             # makes by integer foot of distance
league_att = defaultdict(int)               # attempts by integer foot of distance
total_shots = 0

with open(CSV, newline="", encoding="utf-8", errors="replace") as f:
    r = csv.DictReader(f)
    for row in r:
        if row["event_type"] not in ("shot", "miss"):      # made / missed FG attempts
            continue
        if "Regular Season" not in row["data_set"]:
            continue
        ox, oy = row["original_x"], row["original_y"]
        if ox == "" or oy == "":
            continue
        try:
            x = int(float(ox)); y = int(float(oy))
        except ValueError:
            continue
        made = 1 if row["result"] == "made" else 0
        try:
            dist = int(round(float(row["shot_distance"])))
        except (ValueError, TypeError):
            dist = int(round(math.hypot(x, y) / 10.0))      # 10 court units = 1 ft
        dist = max(0, min(dist, 35))
        league_att[dist] += 1
        league_makes[dist] += made
        total_shots += 1
        if row["player"] in WANT:
            player_shots[row["player"]].append([x, y, made])

league_by_dist = [
    round(league_makes[d] / league_att[d], 4) if league_att[d] else None
    for d in range(0, 36)
]
lt_makes, lt_att = sum(league_makes.values()), sum(league_att.values())
found = [p for p in PLAYERS if p in player_shots]

with open(OUT, "w") as f:
    json.dump({
        "leagueByDistance": league_by_dist,     # index = feet, value = FG%
        "leagueOverall": round(lt_makes / lt_att, 4),
        "players": {p: player_shots[p] for p in found},
        "playerOrder": found,
    }, f, separators=(",", ":"))

print(f"total regular-season shots: {total_shots:,}")
print(f"league overall FG%: {lt_makes / lt_att:.3f}")
for p in found:
    s = player_shots[p]
    print(f"  {p:20s} {len(s):5d} shots  FG% {sum(z[2] for z in s) / len(s):.3f}")
print(f"wrote {OUT} ({os.path.getsize(OUT) / 1024:.0f} KB)")
