"""Generate every figure in the manuscript.

Each figure is built at the physical size it occupies on the page, so the document applies
no downscaling and every label renders at its true point size. The text column is 6.5 in
wide, so the point sizes set below are the sizes seen on the printed page.

Applied throughout: short panel titles at one consistent size, axis labels carrying units
for every reported quantity, consistent terminology across figures, legends placed clear of
the plotted data, and no annotation text overlapping the data.
"""

import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, FancyBboxPatch, FancyArrowPatch
import iran_cdsp as m

os.makedirs("figs", exist_ok=True)

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif", "Times New Roman"],
    "font.size": 9.5, "axes.titlesize": 10, "axes.labelsize": 9.5,
    "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 8.5,
    "axes.titlepad": 7,
    "text.color": "black", "axes.labelcolor": "black",
    "xtick.color": "black", "ytick.color": "black",
    "axes.edgecolor": "black", "axes.titlecolor": "black",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.22, "grid.linewidth": 0.5,
    "axes.linewidth": 0.7, "xtick.major.width": 0.7, "ytick.major.width": 0.7,
    "xtick.major.size": 3, "ytick.major.size": 3,
    "lines.linewidth": 1.5, "lines.markersize": 4.5,
    "figure.dpi": 200, "savefig.dpi": 300, "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "legend.frameon": True, "legend.framealpha": 1.0,
    "legend.edgecolor": "black", "legend.borderpad": 0.4,
    "legend.handlelength": 1.6, "legend.columnspacing": 1.0,
})

C = {"solar": "#E8A33D", "hydro": "#5B8FB0", "geothermal": "#8C4A3B", "biofuel": "#4A7C59",
     "accept": "#3F6F53", "flag": "#C08A2E", "reject": "#8C4A3B", "neutral": "#5A5A5A",
     "s1": "#2F5D50", "s2": "#33475B", "box": "#E9EEF2", "boxedge": "#4A5A66"}

D_POINT = m.demand_design_value("point")
THR = m.thresholds_for(D_POINT)
R_TGT = THR["renewable_share"]["target"] * 100
E_TGT = THR["emissions"]["target"]
C_TGT = THR["cost"]["target"]


def fig_procedure():
    """Figure 1. The procedure as a whole."""
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    ax.set_xlim(0, 100); ax.set_ylim(0, 62); ax.axis("off"); ax.grid(False)

    def box(x, y, w, h, title, body):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.2",
                                    facecolor=C["box"], edgecolor=C["boxedge"], linewidth=0.9))
        ax.text(x + w / 2, y + h - 3.2, title, ha="center", va="top", fontsize=9.0,
                fontweight="bold", color="black")
        ax.text(x + w / 2, y + h - 8.0, body, ha="center", va="top", fontsize=8.0,
                color="black", linespacing=1.35)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=8,
                                     linewidth=0.9, color=C["boxedge"]))

    box(1, 38, 29, 23, "Forecast-informed quantity",
        "A projected value with an\nuncertainty interval, a data\ncredibility grade, and a\nmodel-form sensitivity grade")
    box(35.5, 38, 28, 23, "Decision 1: role",
        "Designers fix what the\nquantity is: fixed input,\nvariable, bound, requirement,\ntarget, or scenario")
    box(69, 38, 30, 23, "Decision 2: use of value",
        "Designers fix how the value\nis used, entering the\ncredibility and sensitivity\nresponse table")
    box(11, 15, 33, 18, "Stage 1: screening",
        "Designers test named\nconfigurations and record\nwhy each passes or fails")
    box(56, 15, 33, 18, "Stage 2: compromise DSP",
        "Designers search the whole\nallowable space and minimise\ndeviation from the goals")
    box(24, 0, 52, 11, "Traceable record",
        "Source, credibility, sensitivity, role, treatment, requirement and effect\non the recommended configuration, recorded for every quantity")

    arrow(30, 49.5, 35.5, 49.5)
    arrow(63.5, 49.5, 69, 49.5)
    arrow(49, 38, 33, 33.5)
    arrow(84, 38, 74, 33.5)
    arrow(27.5, 15, 42, 11.5)
    arrow(72.5, 15, 58, 11.5)
    arrow(44, 24, 56, 24)

    fig.savefig("figs/fig_procedure.png")
    plt.close(fig)


def fig_screening():
    """Figure 2. Stage 1 screening of the named configurations."""
    rows = [m.screen_config(n, k, D_POINT) for n, k in m.NAMED_CONFIGS.items()]
    order = list(range(len(rows)))[::-1]
    names = [rows[i]["config"] for i in order]
    cmap = {"Acceptable": C["accept"], "Acceptable with a desirable miss": C["accept"],
            "Flagged": C["flag"], "Rejected": C["reject"]}
    cols = [cmap[rows[i]["status"]] for i in order]
    yp = np.arange(len(names))

    fig, ax = plt.subplots(1, 3, figsize=(6.5, 2.5), sharey=True)
    fig.subplots_adjust(wspace=0.30, bottom=0.36)

    ax[0].barh(yp, [rows[i]["renewable_share"] * 100 for i in order], color=cols, height=0.6,
               edgecolor="black", linewidth=0.4)
    ax[0].axvline(R_TGT, ls="--", color="black", lw=1.0)
    ax[0].set_xlabel("Renewable share (%)")
    ax[0].set_title("Renewable share", fontweight="bold")
    ax[0].set_xlim(0, 17)

    ax[1].barh(yp, [rows[i]["emissions_Mt"] for i in order], color=cols, height=0.6,
               edgecolor="black", linewidth=0.4)
    ax[1].axvline(E_TGT, ls="--", color="black", lw=1.0)
    ax[1].set_xlabel("Emissions (Mt CO$_2$/yr)")
    ax[1].set_title("Emissions", fontweight="bold")
    ax[1].set_xlim(158, 178); ax[1].set_xticks([160, 166, 172, 178])

    ax[2].barh(yp, [rows[i]["cost_bnUSD"] for i in order], color=cols, height=0.6,
               edgecolor="black", linewidth=0.4)
    ax[2].axvline(C_TGT, ls="--", color="black", lw=1.0)
    ax[2].set_xlabel("Cost (bn USD/yr)")
    ax[2].set_title("Annualised cost", fontweight="bold")
    ax[2].set_xlim(27.6, 29.2); ax[2].set_xticks([27.8, 28.3, 28.8])

    ax[0].set_yticks(yp); ax[0].set_yticklabels(names)
    handles = [Patch(facecolor=C["accept"], edgecolor="black", label="Acceptable"),
               Patch(facecolor=C["flag"], edgecolor="black", label="Flagged"),
               Patch(facecolor=C["reject"], edgecolor="black", label="Rejected"),
               Line2D([0], [0], ls="--", color="black", lw=1.0, label="Requirement")]
    fig.legend(handles=handles, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.02))
    fig.savefig("figs/fig_screening.png")
    plt.close(fig)


def fig_baselines():
    """Figure 3. Comparison with simpler decision rules."""
    df = m.baseline_comparison()
    df = df[df["Total added (GW)"].notna()].reset_index(drop=True)
    labels = [r.replace(" ", "\n", 1) for r in df["Decision rule"]]
    n_met = [int(str(s).split(" of ")[0]) for s in df["Requirements satisfied"]]
    xp = np.arange(len(df))
    cols = [C["accept"] if n == 3 else (C["flag"] if n > 0 else C["reject"]) for n in n_met]

    fig, ax = plt.subplots(1, 2, figsize=(6.5, 2.9))
    fig.subplots_adjust(wspace=0.34, bottom=0.42)

    ax[0].bar(xp, df["Total added (GW)"], color=cols, edgecolor="black", linewidth=0.5, width=0.6)
    for i, v in enumerate(df["Total added (GW)"]):
        ax[0].text(i, v + 0.6, f"{v:.1f}", ha="center", fontsize=8.2)
    ax[0].set_ylabel("New capacity built (GW)")
    ax[0].set_title("Capacity the rule commits", fontweight="bold")
    ax[0].set_ylim(0, 27)
    ax[0].set_xticks(xp); ax[0].set_xticklabels(labels, fontsize=7.8)

    ax[1].bar(xp, df["Renewable share (%)"], color=cols, edgecolor="black", linewidth=0.5, width=0.6)
    ax[1].axhline(R_TGT, ls="--", color="black", lw=1.0)
    ax[1].set_ylabel("Renewable share (%)")
    ax[1].set_title("Renewable share achieved", fontweight="bold")
    ax[1].set_ylim(0, 19)
    ax[1].set_xticks(xp); ax[1].set_xticklabels(labels, fontsize=7.8)

    handles = [Patch(facecolor=C["accept"], edgecolor="black", label="All three requirements met"),
               Patch(facecolor=C["reject"], edgecolor="black", label="No requirement met"),
               Line2D([0], [0], ls="--", color="black", lw=1.0, label="Renewable requirement")]
    fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.05))
    fig.savefig("figs/fig_baselines.png")
    plt.close(fig)


def fig_demand():
    """Figure 4. Demand levels and the limit of feasibility."""
    keys = list(m.DEMAND_LEVELS.keys())
    ticks = [f"{m.DEMAND_LEVELS[k][1]:.1f}" for k in keys]
    dem, sup, rsh, cst, feas = [], [], [], [], []
    for k in keys:
        s = m.solve_cdsp(k, "weighted")
        dem.append(m.demand_design_value(k)); feas.append(s["feasible"])
        sup.append(s["generation_TWh"] if s["feasible"] else 0.0)
        rsh.append(s["renewable_share"] * 100 if s["feasible"] else np.nan)
        cst.append(s["cost_bnUSD"] if s["feasible"] else np.nan)
    ceiling = m.max_system_generation()
    xp = np.arange(len(keys))

    fig, ax = plt.subplots(1, 2, figsize=(6.5, 3.0))
    fig.subplots_adjust(wspace=0.60, bottom=0.44)

    ax[0].bar(xp - 0.19, dem, 0.38, color=C["neutral"], edgecolor="black", linewidth=0.4,
              label="Demand assumed")
    xs = [xp[i] + 0.19 for i, f in enumerate(feas) if f]
    ys = [sup[i] for i, f in enumerate(feas) if f]
    ax[0].bar(xs, ys, 0.38, color=C["accept"], edgecolor="black", linewidth=0.4,
              label="Generation delivered")
    ax[0].axhline(ceiling, ls="--", color=C["reject"], lw=1.1,
                  label=f"System ceiling, {ceiling:.0f} TWh/yr")
    shown = False
    for i, f in enumerate(feas):
        if not f:
            ax[0].plot(i + 0.19, 22, marker="x", color=C["reject"], markersize=7,
                       markeredgewidth=1.7, linestyle="none",
                       label=None if shown else "No feasible configuration")
            shown = True
    ax[0].set_xticks(xp); ax[0].set_xticklabels(ticks, fontsize=8.2)
    ax[0].set_xlabel("Demand assumed (TWh/yr)")
    ax[0].set_ylabel("Electricity (TWh/yr)")
    ax[0].set_title("Demand and generation", fontweight="bold")
    ax[0].set_ylim(0, 500); ax[0].set_yticks([0, 100, 200, 300, 400])
    ax[0].legend(loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=1)

    ok = [i for i, f in enumerate(feas) if f]
    ax[1].plot([xp[i] for i in ok], [rsh[i] for i in ok], "-o", color=C["s1"],
               label="Renewable share")
    axb = ax[1].twinx(); axb.spines["right"].set_visible(True); axb.grid(False)
    axb.tick_params(axis="x", labelbottom=False, bottom=False)
    axb.plot([xp[i] for i in ok], [cst[i] for i in ok], "-s", color=C["s2"], label="Cost")
    ax[1].axvline(3.5, ls=":", color=C["reject"], lw=1.1)
    ax[1].set_xticks(xp); ax[1].set_xticklabels(ticks, fontsize=8.2)
    ax[1].set_xlabel("Demand assumed (TWh/yr)")
    ax[1].set_ylabel("Renewable share (%)", color=C["s1"])
    axb.set_ylabel("Cost (bn USD/yr)", color=C["s2"])
    ax[1].set_title("Response to the demand value", fontweight="bold")
    ax[1].set_ylim(11.5, 19.5); ax[1].set_yticks([12, 13, 14, 15])
    axb.set_ylim(25.5, 32.5); axb.set_yticks([26, 27, 28, 29, 30])
    h1, l1 = ax[1].get_legend_handles_labels(); h2, l2 = axb.get_legend_handles_labels()
    h1.append(Line2D([0], [0], ls=":", color=C["reject"], lw=1.1)); l1.append("Feasibility limit")
    ax[1].legend(h1 + h2, l1 + l2, loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=1)
    fig.savefig("figs/fig_demand.png")
    plt.close(fig)


def fig_solar():
    """Figure 5. Build required under three solar model forms."""
    df = m.ablation_solar_model_form()
    fig, ax = plt.subplots(figsize=(4.4, 2.7))
    fig.subplots_adjust(bottom=0.26)
    xp = np.arange(len(df))
    ax.bar(xp - 0.18, df["Solar capacity added (GW)"], 0.36, color=C["solar"],
           edgecolor="black", linewidth=0.5, label="Solar capacity")
    ax.bar(xp + 0.18, df["Total added (GW)"], 0.36, color=C["neutral"],
           edgecolor="black", linewidth=0.5, label="Total new capacity")
    for i, (a, b) in enumerate(zip(df["Solar capacity added (GW)"], df["Total added (GW)"])):
        ax.text(i - 0.18, a + 0.45, f"{a:.1f}", ha="center", fontsize=8.0)
        ax.text(i + 0.18, b + 0.45, f"{b:.1f}", ha="center", fontsize=8.0)
    ax.set_xticks(xp)
    ax.set_xticklabels(["0.162\nretained", "0.20\noptimistic", "0.12\nconservative"], fontsize=8.2)
    ax.set_xlabel("Assumed solar capacity factor")
    ax.set_ylabel("Capacity added (GW)")
    ax.set_title("Build required under three model forms", fontweight="bold")
    ax.set_ylim(0, 25)
    ax.legend(loc="upper left", ncol=1)
    fig.savefig("figs/fig_solar.png")
    plt.close(fig)


def fig_frontier():
    """Figure 6. Trade-off frontier."""
    df = m.tradeoff_frontier(n=25)
    fig, ax = plt.subplots(1, 2, figsize=(6.5, 2.7))
    fig.subplots_adjust(wspace=0.46, bottom=0.32)

    ax[0].plot(df["Achieved renewable share (%)"], df["Cost (bn USD/yr)"], "-o",
               color=C["s2"], markersize=3.5)
    ax[0].axvline(R_TGT, ls="--", color="black", lw=1.0)
    ax[0].set_xlabel("Renewable share achieved (%)")
    ax[0].set_ylabel("Cost (bn USD/yr)")
    ax[0].set_title("Cost against renewable share", fontweight="bold")
    lo, hi = df["Cost (bn USD/yr)"].min(), df["Cost (bn USD/yr)"].max()
    ax[0].set_ylim(lo - 0.05 * (hi - lo), hi + 0.55 * (hi - lo))
    ax[0].locator_params(axis="y", nbins=5)

    ax[1].plot(df["Achieved renewable share (%)"], df["Total added (GW)"], "-o",
               color=C["accept"], markersize=3.5)
    ax[1].axvline(R_TGT, ls="--", color="black", lw=1.0)
    ax[1].set_xlabel("Renewable share achieved (%)")
    ax[1].set_ylabel("New capacity (GW)")
    ax[1].set_title("Capacity against renewable share", fontweight="bold")

    handles = [Line2D([0], [0], ls="--", color="black", lw=1.0,
                      label=f"Stated requirement, {R_TGT:.0f} percent")]
    fig.legend(handles=handles, loc="lower center", ncol=1, bbox_to_anchor=(0.5, -0.07))
    fig.savefig("figs/fig_frontier.png")
    plt.close(fig)


def fig_weights():
    """Figure 7. Weight sweep on the renewable goal."""
    df = m.weight_sweep(n=21)
    w = df["Weight on the renewable goal"].values
    fig, ax = plt.subplots(1, 2, figsize=(6.5, 3.0))
    fig.subplots_adjust(wspace=0.60, bottom=0.44)

    ax[0].plot(w, df["Renewable share (%)"], "-o", color=C["s1"], label="Renewable share")
    axb = ax[0].twinx(); axb.spines["right"].set_visible(True); axb.grid(False)
    axb.tick_params(axis="x", labelbottom=False, bottom=False)
    axb.plot(w, df["Cost (bn USD/yr)"], "-s", color=C["s2"], label="Cost")
    ax[0].set_xlabel("Weight on the renewable goal")
    ax[0].set_ylabel("Renewable share (%)", color=C["s1"])
    axb.set_ylabel("Cost (bn USD/yr)", color=C["s2"])
    ax[0].set_title("Performance achieved", fontweight="bold")
    ax[0].set_ylim(12.0, 14.5)
    axb.set_ylim(28.0, 29.5)
    h1, l1 = ax[0].get_legend_handles_labels(); h2, l2 = axb.get_legend_handles_labels()
    ax[0].legend(h1 + h2, l1 + l2, loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=1)

    cols = [f"{m.TECH_LABEL[t]} (GW)" for t in m.CANDIDATES]
    ax[1].stackplot(w, *[df[c].values for c in cols],
                    labels=[m.TECH_LABEL[t] for t in m.CANDIDATES],
                    colors=[C["solar"], C["hydro"], C["geothermal"], C["biofuel"]],
                    alpha=0.95, edgecolor="white", linewidth=0.3)
    ax[1].set_xlabel("Weight on the renewable goal")
    ax[1].set_ylabel("Capacity added (GW)")
    ax[1].set_title("Capacity mix recommended", fontweight="bold")
    ax[1].set_ylim(0, 19.5)
    ax[1].set_yticks([0, 5, 10, 15])
    ax[1].legend(loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=2)
    fig.savefig("figs/fig_weights.png")
    plt.close(fig)


def fig_ablation():
    """Figure 8. What residual dispatch contributes."""
    df = m.ablation_fixed_gas()
    names = [n.replace("-", "-\n") for n in df["Configuration"]]
    xp = np.arange(len(df))
    fig, ax = plt.subplots(figsize=(4.4, 2.8))
    fig.subplots_adjust(bottom=0.28)
    ax.bar(xp - 0.18, df.iloc[:, 1], 0.36, color=C["accept"], edgecolor="black",
           linewidth=0.5, label="With residual dispatch")
    ax.bar(xp + 0.18, df.iloc[:, 2], 0.36, color=C["neutral"], edgecolor="black",
           linewidth=0.5, label="Gas fixed at full output")
    ax.axhline(E_TGT, ls="--", color="black", lw=1.0, label="Emissions requirement")
    ax.set_xticks(xp); ax.set_xticklabels(names, fontsize=7.8)
    ax.set_ylabel("Emissions (Mt CO$_2$/yr)")
    ax.set_title("Emissions response to the decision", fontweight="bold")
    ax.set_ylim(155, 186)
    ax.legend(loc="upper left", ncol=1)
    fig.savefig("figs/fig_ablation.png")
    plt.close(fig)


FIGURES = [("fig_procedure", fig_procedure), ("fig_screening", fig_screening),
           ("fig_baselines", fig_baselines), ("fig_demand", fig_demand),
           ("fig_solar", fig_solar), ("fig_frontier", fig_frontier),
           ("fig_weights", fig_weights), ("fig_ablation", fig_ablation)]

if __name__ == "__main__":
    from PIL import Image
    for name, fn in FIGURES:
        fn()
        px = Image.open(f"figs/{name}.png").size
        print(f"  {name:15s} {str(px):14s} -> insert {round(px[0] / 300 * 96)} x "
              f"{round(px[1] / 300 * 96)} px ({px[0] / 300:.2f} in wide)")
