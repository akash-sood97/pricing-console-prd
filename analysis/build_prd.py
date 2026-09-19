"""Generate docs/PRD.md from computed inputs (P1 snapshot, experiment sizing, eval results, scoring tables).
    python analysis/build_prd.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
S1 = json.load(open(ROOT / "data/p1_snapshot/summary.json"))
sc = pd.read_csv(ROOT / "data/p1_snapshot/scenarios.csv")
pw = pd.read_csv(ROOT / "outputs/experiment_power.csv")
pool = pd.read_csv(ROOT / "outputs/experiment_power_pooled.csv")
ev = pd.read_csv(ROOT / "outputs/eval_summary.csv", index_col=0)
two = sc[sc.scenario == "Two-sided (in-sample)"]

# RICE: assumptions, labelled as such in the PRD
rice = pd.DataFrame([
    ("Recommendation view with both-sided consequence tiles", "v1", 10, 3.0, 0.8, 6),
    ("Guardrail states and price-range flags", "v1", 10, 2.0, 0.9, 3),
    ("Instrumentation (event spec live from day one)", "v1", 10, 1.0, 1.0, 2),
    ("Guarded rollout with auto-revert", "v2", 10, 2.0, 0.6, 6),
    ("Approval workflow and audit trail", "v2", 10, 1.0, 0.8, 5),
    ("Pooled price tests with experiment hooks", "v2", 4, 3.0, 0.5, 8),
    ("Grounded pricing assistant", "v3", 10, 1.0, 0.3, 10),
    ("Multi-city portfolio optimisation", "v3", 4, 2.0, 0.4, 12)], columns=["feature", "release", "reach", "impact", "confidence", "effort_weeks"])
rice["score"] = rice.reach * rice.impact * rice.confidence / rice.effort_weeks
rice = rice.sort_values("score", ascending=False)

# Build vs buy: weighted scorecard (judgement, labelled)
crit = {"Faithfulness control": 30, "Numeric correctness": 20, "Data governance": 15, "Time to value": 15, "Run cost": 10, "Maintenance": 10}
opts = {"A. Hosted LLM with tool use (buy the model, build tools and checks)": [4, 5, 4, 4, 3, 4],
        "B. Fine-tune an open-weights model (build)": [3, 4, 5, 1, 2, 1],
        "C. Templated explanations, no language model (build)": [5, 5, 5, 5, 5, 4],
        "D. Off-the-shelf BI copilot (buy)": [2, 2, 2, 5, 3, 5]}
w = np.array(list(crit.values())) / 100
bvb = pd.DataFrame({k: [float(np.dot(v, w))] + v for k, v in opts.items()}, index=["Weighted score"] + list(crit)).T
bvb = bvb.sort_values("Weighted score", ascending=False)

def md(df, floatfmt=None):
    cols = list(df.columns)
    out = ["| " + " | ".join([df.index.name or ""] + cols) + " |", "|" + "---|" * (len(cols) + 1)]
    for i, r in df.iterrows():
        out.append("| " + " | ".join([str(i)] + [f"{r[c]:.2f}" if isinstance(r[c], float) else str(r[c]) for c in cols]) + " |")
    return "\n".join(out)

p5 = pw[pw.price_move == 0.05].set_index("segment")
n_fast = int((p5.weeks_to_detect <= 13).sum())
p05, p10, p20 = (pool[pool.price_move == m].iloc[0] for m in (0.05, 0.10, 0.20))
raise_n = int((two.r > 1.001).sum()); cut_n = int((two.r < 0.999).sum())
sq0 = sc[sc.scenario == "Status quo"]
below = int((sq0.earn < 220).sum())
churn_lo, churn_hi = sq0[sq0.earn < 220].churn.min() * 100, sq0[sq0.earn < 220].churn.max() * 100
rows_test = "\n".join(f"| {sg} | {p5.loc[sg, 'weekly_leads']:.0f} | {p5.loc[sg, 'conversion_change_pts']:+.1f} | " +
                      ("not detectable" if not np.isfinite(p5.loc[sg, 'weeks_to_detect']) else f"{p5.loc[sg, 'weeks_to_detect']:.0f}") + " |"
                      for sg in p5.sort_values("weeks_to_detect").index)
rice_md = md(rice.set_index("feature").assign(score=lambda d: d.score.round(1)))
bvb_md = md(bvb.round(2))

txt = f"""# Product Requirements Document: Dynamic Pricing Console

*Status: draft for sponsor review. Evidence comes from a synthetic two-sided pricing model (see the pricing-engine repo); targets and gates are proposals, not measurements.*

## 1. The ask
Build the console a category manager uses to see a recommended price band, understand what it does to **both** sides of the marketplace, and ship it safely. Sequence it in three releases with exit gates, and scope an AI assistant behind a hard evaluation bar.

## 2. Problem and evidence
Pricing is set in spreadsheets, one city at a time, from a customer-demand view. The two-sided pricing model shows what that misses (synthetic data, modelled, not a production result):

- **Demand-only pricing delivers +{S1['uplift_ss']*100:.1f}% contribution; two-sided pricing delivers +{S1['uplift_ts']*100:.1f}%.** The gap is ₹{S1['gain_two_vs_single']/1e6:.2f}M a year across 10 segments, all from one segment (Delhi cleaning).
- **The demand-only price oversells partner capacity there:** peak-week fulfilment falls to {S1['cd_serv_single']*100:.0f}% against {S1['cd_serv_two']*100:.0f}% at the two-sided price.
- **{below} of 10 segments already pay partners below the earnings floor** (₹220 a job), with {churn_lo:.0f}-{churn_hi:.0f}% modelled annual churn.
- **The best price is often outside the data:** {raise_n} of 10 segments' optimal move is a rise, and the model's full-band optimum extrapolates beyond observed prices. That needs a test, not trust.

**Product hypothesis.** Managers adopt a recommendation only if they can see the partner-side and fulfilment consequence next to the revenue number, and a system that blocks unsafe changes beats one that trusts the user to check.

## 3. Users and jobs to be done
| User | Job to be done |
|---|---|
| Category / revenue manager (primary) | Show me where prices leave margin on the table or break supply, and let me set bands with confidence. |
| City operations (secondary) | Warn me before a price change hurts fulfilment or partner earnings in my city. |
| Central pricing and strategy (power user) | Let me manage the model, the guardrails and the experiments. |

## 4. Goals and non-goals
**Goals.** Reduce time from insight to a safe price change; make the two-sided consequence unmissable; make every recommendation traceable to its assumptions.
**Non-goals for v1.** Automated repricing without a human; competitor price scraping; promotion planning (separate module, later); any claim about causal effects.

## 5. Requirements
![Recommendation view](../figures/01_console_recommendation.png)

| Callout | Requirement | Acceptance criterion |
|---|---|---|
| 1 | Show each segment's recommended move and plain-language status | Every segment has a status; no unexplained number |
| 2 | Show four consequence tiles together: contribution, peak-week fulfilment, partner churn, partner earnings | Tiles never shown without the other three |
| 3 | Show the counterfactual of the demand-only price | Displayed for every segment where the two prices differ |
| 4 | Show guardrails and change the screen on breach | Any breach disables shipping and offers the two safe paths |
| 5 | Actions: simulate, request approval, ask the assistant | Approval is required in v2; assistant only after its release gate |

![Guardrail state](../figures/02_guardrail_state.png)

**Guardrail behaviour.** When the earnings floor cannot be met inside the observed price range, the console blocks the recommended price and offers a *guarded rollout* (small move, weekly review, auto-revert) or a *price test* (larger, pooled step).

## 6. Metrics and instrumentation
![Metrics tree](../figures/04_metrics_tree.png)

**North-star:** guardrail-clean, margin-positive price changes shipped per month. It is only counted if no guardrail metric moves the wrong way.

| Event | Fires when | Key properties |
|---|---|---|
| `recommendation_viewed` | a manager opens a segment | segment, model_version, recommended_move, status |
| `band_simulated` | manager changes an assumption or price | segment, changed_field, old, new, result_contribution |
| `guardrail_breach_shown` | a guardrail state renders | segment, guardrail (floor / fulfilment / range), gap |
| `change_requested` / `change_approved` | workflow steps | segment, move, approver, guardrail_status |
| `change_shipped` | price goes live | segment, move, rollout_type (full / guarded / test) |
| `change_reverted` | auto or manual revert | segment, trigger, days_live |
| `assistant_answer_shown` / `assistant_answer_withheld` | assistant responds | question_type, checks_passed, latency_ms, cost |
| `assistant_answer_rated` | user rates an answer | rating, reason |

Metric targets are hypotheses to baseline in discovery.

## 7. Experiment plan: what a price test can and cannot detect
Sized from the pricing model's fitted demand (synthetic): two arms, 50/50 split of leads, 5% significance, 80% power. **At a +5% move, {n_fast} of 10 segments can detect the conversion change within a quarter**, because the expected change is small and lead volume is low:

| Segment | Leads / week | Expected conversion change (pts) | Weeks to detect at +5% |
|---|---|---|---|
{rows_test}

**Pooling the six "raise" segments** (about {p05.weekly_leads:.0f} leads a week) detects: a +5% step in **{p05.weeks:.0f} weeks**, +10% in **{p10.weeks:.0f} weeks**, +20% in **{p20.weeks:.1f} weeks**.

**Design decision this drives.** Small moves ship as **guarded rollouts** with pre-set stop-loss thresholds on the guardrail metrics; only larger steps (about +20%) are run as pooled tests. The console must not promise an A/B test where the arithmetic says it would run for a year. Lead-level price randomisation needs a fairness and policy review before use.

## 8. Roadmap and prioritisation
![Roadmap](../figures/05_roadmap.png)

RICE scores below use assumed inputs (reach in users, impact 0.25-3, confidence 0-1, effort in person-weeks); they order the work and are not measurements.

{rice_md}

## 9. The AI pricing assistant
**Job.** Explain why a band is what it is, and answer what-if questions, in plain language, grounded in the pricing engine.

![Assistant panel](../figures/03_assistant_panel.png)

**Build vs buy.** Weighted scorecard (weights and 1-5 scores are judgement, shown so they can be argued with):

{bvb_md}

*Weights: {", ".join(f"{k} {v}%" for k, v in crit.items())}.* **Decision:** use a hosted model with tool use for v3 (option A) and keep option C (templated explanations) as the always-available fallback when a check fails. Do not fine-tune: the assistant explains numbers it is handed, so there is no domain corpus to learn and the cost of maintaining a model is not justified.

![Architecture](../figures/06_assistant_architecture.png)

**Fixed configuration, specified rather than left as defaults.**
- *Temperature 0.* A language model is a sampler, not a calculator; pricing explanations must not vary run to run.
- *Context budget.* One segment card plus at most four scenario rows. If truncation is needed, drop assumption text last and never the numbers.
- *Retrieval unit.* One segment per chunk, so a figure is never grounded in the wrong segment.
- *Numbers from tools only.* The model may quote a number it was handed; it may not compute one.

**What the assistant will never say.** No causal claim; no number it did not receive from the pricing engine; no recommendation that breaches the earnings floor or the fulfilment target, even if asked to relax them; no explanation citing a driver the model did not surface.

**Evaluation rubric, implemented.** `assistant_eval/` holds 24 labelled cases (explain, computed what-if, not-computed what-if, guardrail override, causality and uncertainty) and deterministic checks for numeric grounding, required facts, causal language, refusal, and floor / extrapolation / assumption flags. The checks have their own unit tests.

![Assistant eval](../figures/07_assistant_eval.png)

Pass rate by category (every applicable check must pass):

{md(ev.map(lambda v: f"{v*100:.0f}%") if hasattr(ev, "map") else ev)}

**Release rule:** 100% on faithfulness and refusal cases, or the assistant does not ship. **Limits of this evidence:** no language model was called; the reference responder is written against the same rubric, so its score shows the harness works, not that a real model will pass.

## 10. Risks and open questions
| Risk | Mitigation |
|---|---|
| Partner response is calibrated, not measured; the churn benefit may be overstated | Measure churn directly in v1 instrumentation; treat the churn curve as an assumption until then |
| Recommendations extrapolate beyond observed prices | Range flag on every recommendation; larger moves route to tests only |
| Managers override guardrails outside the tool | Track override rate as the trust metric; make the safe path faster than the unsafe one |
| Assistant gives a plausible but wrong number | Numbers from tools only; post-checks withhold the answer on any mismatch |
| Lead-level price tests raise fairness and policy questions | Policy review before any randomised pricing; prefer geo or time splits |

**Open questions.** Who owns approval thresholds? What is the acceptable stop-loss on churn during a guarded rollout? Can partner churn be measured weekly rather than annually?

## 11. Discovery plan (to run; no findings are claimed here)
Seven interviews (four category managers, two city operations leads, one central pricing analyst). Guide: (1) walk me through your last price change; (2) what did you check before shipping it; (3) what did you learn afterwards that you wish you had known; (4) how do you learn a price hurt partner earnings or fulfilment, and how late; (5) when have you overridden a recommendation and why; (6) what would make you trust a model's number; (7) what would you never let a tool decide. Assumptions to validate first: that managers want the partner-side view on the same screen, and that they prefer a blocked change with two safe paths over a warning.
"""
(ROOT / "docs").mkdir(exist_ok=True)
(ROOT / "docs/PRD.md").write_text(txt)
print("PRD.md written,", len(txt.split()), "words")
