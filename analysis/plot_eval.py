"""Chart of the assistant eval results:  python analysis/plot_eval.py  (run assistant_eval.run_eval first)"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import viz  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

viz.setup()
C = viz.C
sm = pd.read_csv(ROOT / "outputs/eval_summary.csv", index_col=0)
cats = [c for c in sm.columns if c != "ALL"]
order = ["Reference template", "Grounded, no guardrails", "Ungrounded LLM (simulated)"]
cols = [C["blue"], C["orange"], C["neutral"]]
fig, ax = plt.subplots(figsize=(10, 5.4))
w = 0.26
for i, (name, col) in enumerate(zip(order, cols)):
    v = sm.loc[name, cats].to_numpy() * 100
    b = ax.bar(np.arange(len(cats)) + (i - 1) * w, v, w * 0.92, color=col, label=f"{name}  ({sm.loc[name, 'ALL']*100:.0f}% overall)", zorder=3)
    for x, val in zip(np.arange(len(cats)) + (i - 1) * w, v):
        ax.text(x, val + 2, f"{val:.0f}", ha="center", fontsize=8.5)
ax.set_xticks(range(len(cats)), [c.replace(" (", "\n(") for c in cats], fontsize=9.5)
ax.set_ylim(0, 128); ax.set_ylabel("Cases passed (%)"); ax.grid(axis="x", visible=False)
ax.legend(loc="upper center", ncol=3, fontsize=8.6, bbox_to_anchor=(0.5, 1.02), columnspacing=1.2, handlelength=1.2)
viz.header(fig, "The checks tell a grounded answer from a helpful-sounding one that breaks the guardrails",
           "24 labelled cases · pass = every applicable check passes · no language model was called; responders are simulated", top=0.985)
fig.subplots_adjust(left=0.08, right=0.98, top=0.8, bottom=0.14)
viz.footnote(fig, "The reference responder is built against the same rubric, so its score shows the harness works, not that a real model will pass. A real model is the true test.")
viz.save(fig, ROOT / "figures/07_assistant_eval.png")
