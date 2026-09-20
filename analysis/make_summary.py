"""Collect this project's computed numbers into outputs/summary.json, then draw the
one-picture decision card.

Run last, after experiment_power.py and assistant_eval.run_eval have written their CSVs.
Every value here is read back out of those committed CSVs, so nothing is typed by hand
and the README, the PRD and the portfolio page can all read from one file.

    python analysis/make_summary.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analysis import viz  # noqa: E402

OUT, FIG = ROOT / "outputs", ROOT / "figures"
FIG.mkdir(exist_ok=True)
C = viz.C
viz.setup()

POOLED = "experiment_power_pooled.csv"


def build():
    pooled = pd.read_csv(OUT / POOLED)
    per_seg = pd.read_csv(OUT / "experiment_power.csv")
    ev = pd.read_csv(OUT / "eval_summary.csv").set_index("responder")
    cases = pd.read_csv(OUT / "eval_results.csv")

    def weeks(move):
        row = pooled[(pooled.price_move - move).abs() < 1e-9]
        assert len(row) == 1, f"{POOLED} has {len(row)} rows for price_move={move}"
        return float(row.weeks.iloc[0])

    S = dict(
        weeks_5pct=weeks(0.05),
        weeks_10pct=weeks(0.10),
        weeks_20pct=weeks(0.20),
        segments=float(pooled.segments.iloc[0]),
        conv_change_5pct=float(pooled[(pooled.price_move - 0.05).abs() < 1e-9]
                               .conversion_change_pts.iloc[0]),
        eval_ref_all=float(ev.loc["Reference template", "ALL"]),
        eval_noguard_all=float(ev.loc["Grounded, no guardrails", "ALL"]),
        eval_ungrounded_all=float(ev.loc["Ungrounded LLM (simulated)", "ALL"]),
        eval_noguard_guardrail=float(ev.loc["Grounded, no guardrails", "guardrail"]),
        eval_cases=float(cases.id.nunique()),
        eval_responders=float(cases.responder.nunique()),
        eval_clearing_bar=float((ev["ALL"] >= 1.0).sum()),
    )
    # a single segment can detect +5% inside a quarter only if it needs <= 13 weeks
    q = per_seg[(per_seg.price_move - 0.05).abs() < 1e-9]
    S["segments_detectable_5pct"] = float((q.weeks_to_detect <= 13).sum())
    S["segments_total"] = float(len(q))
    return S


def decision_card(S):
    def draw(ax):
        names = ["+5%\nprice move", "+10%", "+20%"]
        vals = [S["weeks_5pct"], S["weeks_10pct"], S["weeks_20pct"]]
        cols = [C["orange"], C["neutral"], C["aqua"]]
        ax.bar(names, vals, color=cols, width=0.58, zorder=3)
        ax.axhline(13, color=C["muted"], lw=1.4, ls=(0, (4, 3)), zorder=4)
        ax.text(-0.42, 15, "one quarter", fontsize=10.5, color=C["muted"],
                ha="left", va="bottom")
        for i, v in enumerate(vals):
            ax.text(i, v + 1.6, f"{v:.0f} wks" if v >= 10 else f"{v:.1f} wks",
                    ha="center", fontsize=12.5, fontweight="bold", color=C["ink"])
        ax.set_ylim(0, 74)
        ax.set_ylabel("Weeks to detect the change", fontsize=11.5)
        ax.tick_params(axis="x", labelsize=11.5)
        ax.tick_params(axis="y", labelsize=10.5)
        ax.grid(axis="x", visible=False)

    viz.decision_card(
        FIG / "00_decision.png",
        f"A +5% price test would run {S['weeks_5pct']:.0f} weeks. Ship guarded "
        f"rollouts instead, and test only the big moves.",
        [(f"{S['weeks_5pct']:.0f} → {S['weeks_20pct']:.1f} wks",
          "to detect a +5% versus a +20% move, six segments pooled"),
         (f"{S['eval_clearing_bar']:.0f} of {S['eval_responders']:.0f}",
          "assistant versions clearing the release bar"),
         (f"{S['eval_cases']:.0f} cases", "in the runnable evaluation harness")],
        draw,
        note="Sized from the pricing engine's fitted demand on synthetic data. Targets and gates are proposals, not measurements.",
    )


if __name__ == "__main__":
    S = build()
    (OUT / "summary.json").write_text(json.dumps(S, indent=2))
    decision_card(S)
    print(f"Wrote outputs/summary.json ({len(S)} keys) and figures/00_decision.png")
    for k in ["weeks_5pct", "weeks_20pct", "eval_ref_all", "eval_cases", "eval_clearing_bar"]:
        print(f"  {k}: {S[k]}")
