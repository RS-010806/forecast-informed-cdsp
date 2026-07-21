"""Generate the paper figures.

Key principle: build each figure at the physical size it occupies on the page, so the
document applies no downscaling and every label renders at its true point size. The text
column is 6.83 in wide; full-width figures are 6.5 in and we insert them at 624 px
(= 6.5 in at 96 dpi). Point sizes set below are therefore the sizes seen on the page.

Applied throughout: short panel titles at one consistent size, axis labels carrying units
for every reported quantity, consistent terminology, legends placed clear of the data, and
no annotation text overlapping the plotted data.
"""

import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import iran_cdsp as m

os.makedirs("figs", exist_ok=True)

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif", "Times New Roman"],
    "font.size": 9.5,
    "axes.titlesize": 10, "axes.titlepad": 7,
    "axes.labelsize": 9.5,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8.5,
    "text.color": "black", "axes.labelcolor": "black",
    "xtick.color": "black", "ytick.color": "black",
    "axes.edgecolor": "black", "axes.titlecolor": "black",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.22, "grid.linewidth": 0.5,
    "axes.linewidth": 0.7,
    "xtick.major.width": 0.7, "ytick.major.width": 0.7,
    "xtick.major.size": 3, "ytick.major.size": 3,
    "lines.linewidth": 1.5, "lines.markersize": 4.5,
    "figure.dpi": 200, "savefig.dpi": 300, "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "legend.frameon": True, "legend.framealpha": 1.0,
    "legend.edgecolor": "black", "legend.borderpad": 0.4,
    "legend.handlelength": 1.6, "legend.columnspacing": 1.0,
})

C = {"solar": "#E8A33D", "hydro": "#5B8FB0", "geothermal": "#8C4A3B", "biofuel": "#4A7C59",
     "accept": "#3F6F53", "reject": "#8C4A3B", "neutral": "#5A5A5A",
     "s1": "#2F5D50", "s2": "#33475B"}

D_POINT = m.demand_design_value("point")

# ---------------------------------------------------------------- Figure 1
s1 = pd.DataFrame([m.screen_config(n, k, D_POINT) for n, k in m.NAMED_CONFIGS.items()])
order = list(range(len(s1)))[::-1]
names = [s1["config"][i] for i in order]
cols = [C["accept"] if s1["status"][i].startswith("Acceptable") else C["reject"] for i in order]
yp = np.arange(len(names))

fig, ax = plt.subplots(1, 3, figsize=(6.5, 2.5), sharey=True)
fig.subplots_adjust(wspace=0.30, bottom=0.34)

ax[0].barh(yp, [s1["renewable_share"][i] * 100 for i in order], color=cols, height=0.62,
           edgecolor="black", linewidth=0.4)
ax[0].axvline(10, ls="--", color="black", lw=1.0)
ax[0].set_xlabel("Renewable share (%)")
ax[0].set_title("Renewable share", fontweight="bold")
ax[0].set_xlim(0, 16)

ax[1].barh(yp, [s1["emissions_Mt"][i] for i in order], color=cols, height=0.62,
           edgecolor="black", linewidth=0.4)
ax[1].axvline(172, ls="--", color="black", lw=1.0)
ax[1].set_xlabel("Emissions (Mt CO$_2$/yr)")
ax[1].set_title("Emissions", fontweight="bold")
ax[1].set_xlim(158, 178)
ax[1].set_xticks([160, 166, 172, 178])

ax[2].barh(yp, [s1["cost_bnUSD"][i] for i in order], color=cols, height=0.62,
           edgecolor="black", linewidth=0.4)
ax[2].axvline(28.8, ls="--", color="black", lw=1.0)
ax[2].set_xlabel("Cost (bn USD/yr)")
ax[2].set_title("Cost", fontweight="bold")
ax[2].set_xlim(27.6, 29.2)
ax[2].set_xticks([27.8, 28.3, 28.8])

ax[0].set_yticks(yp)
ax[0].set_yticklabels(names)

handles = [Patch(facecolor=C["accept"], edgecolor="black", label="Acceptable"),
           Patch(facecolor=C["reject"], edgecolor="black", label="Rejected"),
           Line2D([0], [0], ls="--", color="black", lw=1.0, label="Requirement level")]
fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.0))
fig.savefig("figs/fig_screening.png")
plt.close(fig)

# ---------------------------------------------------------------- Figure 2
keys = ["lower", "earlier", "point", "upper", "widened"]
ticks = ["363.6", "377.1", "389.8", "408.5", "428.9"]
dem, sup, rsh, cst, feas = [], [], [], [], []
for k in keys:
    Dv = m.demand_design_value(k)
    sol = m.build_and_solve(k, "archimedean")
    ok = sol["status"] == "Optimal"
    dem.append(Dv); feas.append(ok)
    sup.append(sol["supply_TWh"] if ok else 0.0)
    rsh.append(sol["renewable_share"] * 100 if ok else np.nan)
    cst.append(sol["cost_bnUSD"] if ok else np.nan)
ceiling = m.max_system_generation()
xp = np.arange(len(keys))

fig, ax = plt.subplots(1, 2, figsize=(6.5, 3.15))
fig.subplots_adjust(wspace=0.62, bottom=0.40)

ax[0].bar(xp - 0.19, dem, 0.38, color=C["neutral"], edgecolor="black", linewidth=0.4,
          label="Demand assumed")
# Draw the generation bar only where a feasible configuration exists. Where none exists we
# leave the slot empty and mark it, rather than drawing a zero bar that would wrongly read
# as zero generation.
xs_ok = [xp[i] + 0.19 for i, ok in enumerate(feas) if ok]
ys_ok = [sup[i] for i, ok in enumerate(feas) if ok]
ax[0].bar(xs_ok, ys_ok, 0.38, color=C["accept"], edgecolor="black", linewidth=0.4,
          label="Generation delivered")
ax[0].axhline(ceiling, ls="--", color=C["reject"], lw=1.1,
              label=f"System ceiling, {ceiling:.0f} TWh/yr")
for i, ok in enumerate(feas):
    if not ok:
        ax[0].plot(i + 0.19, 22, marker="x", color=C["reject"], markersize=6.5,
                   markeredgewidth=1.6, linestyle="none",
                   label="No feasible configuration")
ax[0].set_xticks(xp); ax[0].set_xticklabels(ticks)
ax[0].set_xlabel("Demand assumed (TWh/yr)")
ax[0].set_ylabel("Electricity (TWh/yr)")
ax[0].set_title("Demand and generation", fontweight="bold")
ax[0].set_ylim(0, 500)
ax[0].set_yticks([0, 100, 200, 300, 400])
ax[0].legend(loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=1)

ok_i = [i for i, f in enumerate(feas) if f]
ax[1].plot([xp[i] for i in ok_i], [rsh[i] for i in ok_i], "-o", color=C["s1"], label="Renewable share")
axb = ax[1].twinx(); axb.spines["right"].set_visible(True); axb.grid(False)
axb.tick_params(axis="x", labelbottom=False, bottom=False)
axb.plot([xp[i] for i in ok_i], [cst[i] for i in ok_i], "-s", color=C["s2"], label="Cost")
ax[1].axvline(3.5, ls=":", color=C["reject"], lw=1.1)
ax[1].set_xticks(xp); ax[1].set_xticklabels(ticks)
ax[1].set_xlabel("Demand assumed (TWh/yr)")
ax[1].set_ylabel("Renewable share (%)", color=C["s1"])
axb.set_ylabel("Cost (bn USD/yr)", color=C["s2"])
ax[1].set_title("Response to the demand value", fontweight="bold")
ax[1].set_ylim(9, 20.5); ax[1].set_yticks([10, 12, 14, 16])
axb.set_ylim(26.6, 31.6); axb.set_yticks([27.0, 28.0, 29.0, 30.0])
h1, l1 = ax[1].get_legend_handles_labels(); h2, l2 = axb.get_legend_handles_labels()
h1.append(Line2D([0], [0], ls=":", color=C["reject"], lw=1.1)); l1.append("Feasibility limit")
ax[1].legend(h1 + h2, l1 + l2, loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=1)
fig.savefig("figs/fig_demand.png")
plt.close(fig)

# ---------------------------------------------------------------- Figure 3
ss = m.solar_scenarios()
fig, ax = plt.subplots(figsize=(4.3, 2.5))
xp = np.arange(len(ss))
vals = list(ss["Added solar (GW)"])
ax.bar(xp, vals, color=C["solar"], width=0.5, edgecolor="black", linewidth=0.5)
for i, v in enumerate(vals):
    ax.text(i, v + 0.35, f"{v:.1f}", ha="center", fontsize=9.5, fontweight="bold")
ax.set_xticks(xp)
ax.set_xticklabels(["0.162\nretained", "0.20\noptimistic", "0.12\nconservative"])
ax.set_xlabel("Assumed solar capacity factor")
ax.set_ylabel("Solar capacity added (GW)")
ax.set_title("Solar capacity required", fontweight="bold")
ax.set_ylim(0, max(vals) + 2.4)
fig.savefig("figs/fig_solar.png")
plt.close(fig)

# ---------------------------------------------------------------- Figure 4
ws = np.linspace(0, 1, 21)
rs, cs, gw = [], [], []
for w in ws:
    rest = (1 - w) / 2
    sol = m.build_and_solve("point", "archimedean",
                            weights={"renewable": w, "emissions": rest, "cost": rest})
    rs.append(sol["renewable_share"] * 100)
    cs.append(sol["cost_bnUSD"])
    gw.append([sol["x_add_GW"][t] for t in ["solarpv", "hydro", "geothermal", "biofuel"]])
gw = np.array(gw)

fig, ax = plt.subplots(1, 2, figsize=(6.5, 3.15))
fig.subplots_adjust(wspace=0.62, bottom=0.40)
ax[0].plot(ws, rs, "-o", color=C["s1"], label="Renewable share")
axb = ax[0].twinx(); axb.spines["right"].set_visible(True); axb.grid(False)
axb.tick_params(axis="x", labelbottom=False, bottom=False)
axb.plot(ws, cs, "-s", color=C["s2"], label="Cost")
ax[0].set_xlabel("Weight on the renewable goal")
ax[0].set_ylabel("Renewable share (%)", color=C["s1"])
axb.set_ylabel("Cost (bn USD/yr)", color=C["s2"])
ax[0].set_title("Performance achieved", fontweight="bold")
ax[0].set_ylim(9.0, 11.4)                  # honest range: the share is essentially constant
axb.set_ylim(28.0, 29.8)                   # honest range: the cost is essentially constant
h1, l1 = ax[0].get_legend_handles_labels(); h2, l2 = axb.get_legend_handles_labels()
ax[0].legend(h1 + h2, l1 + l2, loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=1)

ax[1].stackplot(ws, gw[:, 0], gw[:, 1], gw[:, 2], gw[:, 3],
                labels=["Solar", "Hydro", "Geothermal", "Biofuel"],
                colors=[C["solar"], C["hydro"], C["geothermal"], C["biofuel"]],
                alpha=0.95, edgecolor="white", linewidth=0.3)
ax[1].set_xlabel("Weight on the renewable goal")
ax[1].set_ylabel("Capacity added (GW)")
ax[1].set_title("Capacity mix recommended", fontweight="bold")
ax[1].set_ylim(0, 15.5)
ax[1].legend(loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=2)
fig.savefig("figs/fig_weights.png")
plt.close(fig)

from PIL import Image
print("Figures written at true display size:")
for f, disp_in in [("fig_screening", 6.5), ("fig_demand", 6.5), ("fig_solar", 4.3), ("fig_weights", 6.5)]:
    px = Image.open(f"figs/{f}.png").size
    print(f"  {f:15s} {str(px):14s} insert at {round(disp_in*96)} px = {disp_in} in, no downscaling")
