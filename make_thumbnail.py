#!/usr/bin/env python3
"""Render the blog thumbnail: Stephen Curry's hexbin shot map on a light card.
Reads shots.json (produced by extract_shots.py) and writes thumbnail.png.
"""
import json, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc
from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "shots.json")))
shots = np.array(D["players"]["Stephen Curry"], dtype=float)
league, lg_overall = D["leagueByDistance"], D["leagueOverall"]

CARD = "#f4f4f5"   # matches the website's light figure card
cmap = LinearSegmentedColormap.from_list("hot", ["#3b82f6", "#5b5b66", "#e0992f", "#ef4444"])

def draw_court(ax, color="#b8b8bf", lw=1.6):
    ax.add_patch(Circle((0, 0), 7.5, fill=False, color=color, lw=lw))
    ax.add_patch(Rectangle((-30, -9), 60, 0, color=color, lw=lw))
    ax.add_patch(Rectangle((-80, -47.5), 160, 190, fill=False, color=color, lw=lw))
    ax.add_patch(Rectangle((-60, -47.5), 120, 190, fill=False, color=color, lw=lw))
    ax.add_patch(Arc((0, 142.5), 120, 120, theta1=0, theta2=180, color=color, lw=lw))
    ax.add_patch(Arc((0, 142.5), 120, 120, theta1=180, theta2=360, color=color, lw=lw, ls="--"))
    ax.add_patch(Arc((0, 0), 80, 80, theta1=0, theta2=180, color=color, lw=lw))
    ax.plot([-220, -220], [-47.5, 92.5], color=color, lw=lw)
    ax.plot([220, 220], [-47.5, 92.5], color=color, lw=lw)
    th = math.degrees(math.acos(220 / 237.5))
    ax.add_patch(Arc((0, 0), 475, 475, theta1=th, theta2=180 - th, color=color, lw=lw))
    ax.add_patch(Rectangle((-250, -47.5), 500, 470, fill=False, color=color, lw=lw))

fig, ax = plt.subplots(figsize=(6, 6), dpi=120)
fig.patch.set_facecolor(CARD); ax.set_facecolor(CARD)

x, y, m = shots[:, 0], shots[:, 1], shots[:, 2]
keep = (np.abs(x) <= 250) & (y >= -47.5) & (y <= 400)
x, y, m = x[keep], y[keep], m[keep]
gs = 26
hb_cnt = ax.hexbin(x, y, gridsize=gs, extent=(-250, 250, -47.5, 400), mincnt=2, visible=False)
hb_made = ax.hexbin(x, y, C=m, reduce_C_function=np.sum, gridsize=gs,
                    extent=(-250, 250, -47.5, 400), mincnt=2, visible=False)
offs, cnt, made = hb_cnt.get_offsets(), hb_cnt.get_array(), hb_made.get_array()
verts = hb_cnt.get_paths()[0].vertices

polys, cols = [], []
cmax = np.nanpercentile(cnt[cnt > 0], 92)
for (cx, cy), c, mk in zip(offs, cnt, made):
    if not c or c < 2:
        continue
    fg = mk / c
    dist = min(35, int(round(math.hypot(cx, cy) / 10)))
    lg = league[dist] if league[dist] is not None else lg_overall
    diff = max(-0.10, min(0.10, fg - lg))
    scale = 0.30 + 0.70 * min(1.0, math.sqrt(c) / math.sqrt(cmax))
    polys.append(verts * scale + [cx, cy])
    cols.append(cmap((diff + 0.10) / 0.20))
ax.add_collection(PolyCollection(polys, facecolors=cols, edgecolors=CARD, linewidths=0.5))

draw_court(ax)
ax.set_xlim(-258, 258); ax.set_ylim(412, -55)   # flip y: baseline at the bottom
ax.set_aspect("equal"); ax.axis("off")
fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
out = os.path.join(HERE, "thumbnail.png")
fig.savefig(out, facecolor=CARD, dpi=120)
print("saved", out)
