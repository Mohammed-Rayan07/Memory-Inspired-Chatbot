"""Create all report figures from results/results.json (colour-blind-safe Okabe-Ito palette)."""
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from memchat.memory import base_level

R = json.load(open(ROOT / "results" / "results.json"))
FIG = ROOT / "report" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
C = {"Stateless": "#999999", "Sliding window": "#E69F00", "Plain RAG (FIFO)": "#56B4E9", "Memory-inspired": "#009E73",
     "ref": "#444444"}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 100,
                     "savefig.dpi": 200, "savefig.bbox": "tight", "font.family": "DejaVu Sans"})


def save(name):
    plt.savefig(FIG / f"{name}.png"); plt.close()


# ---------------------------------------------------------------- Fig 1: architecture
def box(ax, x, y, w, h, text, fc, ec="#333", fs=9, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", wrap=True)


def arrow(ax, a, b, text=None, rad=0.0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=14, lw=1.3, color="#333", connectionstyle=f"arc3,rad={rad}"))
    if text:
        ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 0.12, text, ha="center", fontsize=7.5, style="italic", color="#444")


fig, ax = plt.subplots(figsize=(12, 6.4))
ax.set_xlim(0, 12); ax.set_ylim(0, 6.6); ax.axis("off")
box(ax, 0.1, 2.7, 1.5, 1.0, "User\nutterance", "#F2F2F2", bold=True)
box(ax, 2.0, 2.2, 2.3, 2.0, "PERCEPTION &\nATTENTION\n\nfact extraction\nsalience score\nattention gate", "#FFE8B3", bold=False)
box(ax, 4.8, 2.2, 2.0, 2.0, "WORKING MEMORY\n(capacity 7)\n\nrecent turns,\nrehearsal count,\nfast decay", "#CFE8F7")
ax.add_patch(FancyBboxPatch((7.3, 1.2), 3.0, 4.0, boxstyle="round,pad=0.02,rounding_size=0.1", fc="#EAF6F0", ec="#009E73", lw=1.6))
ax.text(8.8, 4.95, "LONG-TERM MEMORY", ha="center", fontsize=9.5, fontweight="bold", color="#006B4F")
box(ax, 7.5, 3.0, 2.6, 1.55, "Episodic store\nraw utterances (\"what was said\")\nBM25 + activation", "#FFFFFF", fs=8.5)
box(ax, 7.5, 1.4, 2.6, 1.35, "Semantic store\nslot = value facts\nsupersession on update", "#FFFFFF", fs=8.5)
box(ax, 10.6, 2.9, 1.3, 1.6, "Retrieval\n+ Reader\n\nanswer or\n\"I don't know\"", "#F8D9D9", fs=8.5, bold=False)
box(ax, 7.5, 0.1, 2.6, 0.8, "FORGETTING: lowest activation\nevicted when budget exceeded", "#F5F5F5", fs=8)
box(ax, 0.1, 0.1, 4.4, 0.95, "USER CONTROL & TRANSPARENCY\n/memory (inspect traces)   /forget (delete)", "#E8E0F0", fs=8.5)
box(ax, 3.2, 5.35, 8.7, 0.7, "Activation  B = ln Σ (now − t_j)^−d   +  salience   (ACT-R base-level learning; rehearsal adds t_j)", "#FFFFFF", fs=8.5)
arrow(ax, (1.6, 3.2), (2.0, 3.2)); arrow(ax, (4.3, 3.2), (4.8, 3.2)); arrow(ax, (6.8, 3.3), (7.5, 3.7)); ax.text(6.55, 4.35, "displaced items\nare encoded", ha="center", fontsize=7.5, style="italic", color="#444")
arrow(ax, (6.8, 3.0), (7.5, 2.2)); arrow(ax, (10.1, 3.8), (10.6, 3.8)); arrow(ax, (10.1, 2.2), (10.6, 3.2))
arrow(ax, (8.8, 1.4), (8.8, 0.9)); arrow(ax, (11.25, 2.9), (11.25, 2.2)); ax.text(11.25, 2.0, "reply", ha="center", fontsize=8, style="italic")
ax.text(0.15, 6.3, "Cognitive mapping:  attention → working memory → episodic / semantic LTM → forgetting & rehearsal",
        fontsize=9.5, fontweight="bold", color="#333")
save("fig1_architecture")

# ---------------------------------------------------------------- Fig 2: forgetting & rehearsal curves
fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
t = np.logspace(1, 6.5, 200)
for d, lab, col in ((0.5, "episodic d=0.5", "#D55E00"), (0.25, "semantic d=0.25", "#009E73"), (0.7, "d=0.7", "#999999")):
    ax[0].plot(t / 3600, [base_level([0.0], x, d) for x in t], label=lab, color=col, lw=2)
ax[0].set_xscale("log"); ax[0].set_xlabel("time since encoding (hours, log)"); ax[0].set_ylabel("activation B")
ax[0].set_title("(a) Decay: single encoding"); ax[0].legend(frameon=False, fontsize=8)
tt = np.linspace(1, 14 * 86400, 600)
for reh, lab, col in (([0.0], "no rehearsal", "#D55E00"), ([0.0, 1 * 86400], "1 rehearsal (day 1)", "#E69F00"),
                       ([0.0, 1 * 86400, 3 * 86400, 6 * 86400], "3 rehearsals (spaced)", "#009E73")):
    ax[1].plot(tt / 86400, [base_level([r for r in reh if r < x], x, 0.5) if x > 1 else np.nan for x in tt], label=lab, color=col, lw=2)
ax[1].set_xlabel("days"); ax[1].set_ylabel("activation B"); ax[1].set_title("(b) Rehearsal re-strengthens traces (d=0.5)")
ax[1].legend(frameon=False, fontsize=8)
plt.tight_layout(); save("fig2_decay_rehearsal")

# ---------------------------------------------------------------- Fig 3: budget sweep
fig, ax = plt.subplots(figsize=(6.4, 4))
Bs = sorted(int(b) for b in R["sweep"])
for name in ("Sliding window", "Plain RAG (FIFO)", "Memory-inspired"):
    y = [R["sweep"][str(b)][name]["acc"] for b in Bs]
    lo = [R["sweep"][str(b)][name]["ci"][0] for b in Bs]; hi = [R["sweep"][str(b)][name]["ci"][1] for b in Bs]
    ax.plot(Bs, y, marker="o", label=name, color=C[name], lw=2.2 if name == "Memory-inspired" else 1.6)
    ax.fill_between(Bs, lo, hi, color=C[name], alpha=0.15)
ax.axhline(R["main"]["Stateless"]["acc"], color=C["Stateless"], ls=":", label="Stateless")
ax.set_xlabel("memory budget (items held; conversation = 120 turns)"); ax.set_ylabel("answer accuracy")
ax.set_title("Accuracy vs. memory budget (test set, 95% CI)"); ax.legend(frameon=False, fontsize=8, loc="upper left")
save("fig3_budget_sweep")

# ---------------------------------------------------------------- Fig 4: main by type
fig, ax = plt.subplots(figsize=(7.5, 4))
names = ["Stateless", "Sliding window", "Plain RAG (FIFO)", "Memory-inspired"]
types = [("fact", "Fact"), ("update", "Update"), ("unanswerable", "Unanswerable"), ("episodic", "Episodic detail"), ("acc", "Overall")]
w = 0.2
for i, n in enumerate(names):
    ax.bar(np.arange(len(types)) + (i - 1.5) * w, [R["main"][n][k] for k, _ in types], w, label=n, color=C[n])
ax.set_xticks(range(len(types))); ax.set_xticklabels([l for _, l in types]); ax.set_ylabel("accuracy"); ax.set_ylim(0, 1.05)
ax.set_title("Accuracy by question type (budget = 40 items, test set)"); ax.legend(frameon=False, fontsize=8, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.1))
save("fig4_by_type")

# ---------------------------------------------------------------- Fig 5: ablations
fig, axs = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
for a, B in zip(axs, ("20", "40")):
    items = list(R["ablation"][B].items())
    vals = [v["acc"] for _, v in items]
    cols = ["#009E73"] + ["#999999"] * (len(items) - 1)
    a.barh([k for k, _ in items][::-1], vals[::-1], color=cols[::-1])
    for i, (k, v) in enumerate(items[::-1]):
        a.text(v["acc"] + 0.005, i, f"{v['acc']:.3f}", va="center", fontsize=8)
    a.set_xlim(0.3, 0.8); a.set_xticks([0.3, 0.5, 0.7]); a.set_title(f"Budget = {B}"); a.set_xlabel("accuracy")
plt.tight_layout(); save("fig5_ablation")

# ---------------------------------------------------------------- Fig 6: oracle perception
fig, ax = plt.subplots(figsize=(6.5, 3.8))
x = np.arange(2)
sub = ["Rule-based perception\n(B=20)", "Oracle perception\n(B=20)", "Rule-based perception\n(B=40)", "Oracle perception\n(B=40)"]
for i, n in enumerate(("Sliding window", "Plain RAG (FIFO)", "Memory-inspired")):
    v = [R["sweep"]["20"][n]["acc"], R["oracle"]["20"][n]["acc"], R["sweep"]["40"][n]["acc"], R["oracle"]["40"][n]["acc"]]
    ax.bar(np.arange(4) + (i - 1) * 0.26, v, 0.26, label=n, color=C[n])
ax.set_xticks(range(4)); ax.set_xticklabels(sub, fontsize=8); ax.set_ylabel("accuracy"); ax.set_ylim(0, 1)
ax.set_title("Perception vs. memory: rule-based vs. oracle fact extraction"); ax.legend(frameon=False, fontsize=8, loc="upper left")
save("fig6_oracle")

# ---------------------------------------------------------------- Fig 7: accuracy vs distance
fig, ax = plt.subplots(figsize=(6.2, 3.8))
labs = list(R["by_distance"]["Memory-inspired"])
for n in ("Sliding window", "Plain RAG (FIFO)", "Memory-inspired"):
    ax.plot(labs, [R["by_distance"][n][l][0] for l in labs], marker="o", label=n, color=C[n], lw=2)
ax.set_xlabel("turns between last supporting statement and question"); ax.set_ylabel("accuracy (fact + update)")
ax.set_title("Recall vs. temporal distance (budget = 40)"); ax.legend(frameon=False, fontsize=8)
save("fig7_distance")

# ---------------------------------------------------------------- Fig 8: scalability
fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
L = sorted(int(k) for k in R["scalability"])
for n, col in (("Plain RAG (unbounded)", C["Plain RAG (FIFO)"]), ("Memory-inspired (unbounded)", "#66C2A5"), ("Memory-inspired (B=40)", C["Memory-inspired"])):
    ax[0].plot(L, [R["scalability"][str(l)][n]["ms"] for l in L], marker="o", label=n, color=col)
    ax[1].plot(L, [R["scalability"][str(l)][n]["size"] for l in L], marker="o", label=n, color=col)
ax[0].set_xlabel("conversation length (turns)"); ax[0].set_ylabel("ms / question"); ax[0].set_title("(a) Query latency")
ax[1].set_xlabel("conversation length (turns)"); ax[1].set_ylabel("items stored"); ax[1].set_title("(b) Memory footprint"); ax[0].legend(frameon=False, fontsize=7)
plt.tight_layout(); save("fig8_scalability")

# ---------------------------------------------------------------- Fig 9: LoCoMo
fig, ax = plt.subplots(figsize=(6.2, 3.8))
keys = ["50", "100", "200", "None"]; xl = ["50", "100", "200", "unbounded"]
for n, key in (("BM25 (FIFO)", "BM25 (FIFO)"), ("Memory-inspired", "Memory-inspired")):
    ax.plot(xl, [R["locomo"][k][key]["recall"]["5"] for k in keys], marker="o", lw=2, label="BM25 + FIFO eviction" if n.startswith("BM25") else n,
            color=C["Plain RAG (FIFO)"] if n.startswith("BM25") else C[n])
ax.set_xlabel("memory budget (turns held; LoCoMo conversations avg. %d turns)" % R["locomo_stats"]["turns"]); ax.set_ylabel("evidence recall@5")
ax.set_title("Real data: LoCoMo evidence retrieval"); ax.legend(frameon=False, fontsize=8)
save("fig9_locomo")

# ---------------------------------------------------------------- Fig 10: sensitivity
gates = [0.0, 0.25, 0.35, 0.5, 0.7]; ds = [0.3, 0.5, 0.7]
M = np.array([[R["sensitivity"][f"{g}|{d}"] for d in ds] for g in gates])
fig, ax = plt.subplots(figsize=(4.6, 3.8))
im = ax.imshow(M, cmap="YlGn", vmin=0.35, vmax=0.62, aspect="auto")
ax.set_xticks(range(3)); ax.set_xticklabels(ds); ax.set_yticks(range(5)); ax.set_yticklabels(gates)
ax.set_xlabel("episodic decay exponent d"); ax.set_ylabel("attention gate threshold")
for i in range(5):
    for j in range(3):
        ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=8)
ax.set_title("Sensitivity (budget = 24)"); plt.colorbar(im, ax=ax, shrink=0.8)
save("fig10_sensitivity")
print("figures:", sorted(p.name for p in FIG.glob("*.png")))
