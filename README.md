# Dynamic Pricing Console: PRD, roadmap and a tested AI-assistant spec

**Status: complete as a product specification with a working evaluation harness.** No console and no language model were built; the numbers come from a synthetic two-sided pricing model (the pricing-engine project). Targets and gates are proposals, not measurements.

## The answer

> **Build v1 as a read-only, guardrail-first recommendation view that shows both sides of the market on one screen and blocks unsafe changes. Ship small price moves as guarded rollouts, and reserve real tests for larger steps. Do not let the AI assistant reach a user until it passes 100% of faithfulness and refusal cases.**

| | | |
|---|---|---|
| **₹0.21M / yr** | **61 → 4.5 weeks** | **100% · 33% · 0%** |
| what showing both sides is worth in the pricing model (+7.1% vs +3.2% contribution): the case for the product | time to detect a +5% vs a +20% price move when six segments are pooled: the case for guarded rollouts | assistant eval pass rate: grounded reference, helpful-but-unguarded, ungrounded |

Full document: **[docs/PRD.md](docs/PRD.md)**.

---

## 1. The product: one screen, both sides

![Recommendation view](figures/01_console_recommendation.png)

| # | What it shows | Why |
|---|---|---|
| 1 | Recommended move per segment, in plain language | No unexplained number |
| 2 | Four consequence tiles together: contribution, peak-week fulfilment, partner churn, partner earnings | The two-sided model's core finding is that the partner side is where a demand-only price fails |
| 3 | The demand-only counterfactual | Shows what the manager would have shipped, and what it costs |
| 4 | Guardrail chips that change the screen on breach | See next figure |
| 5 | Simulate, request approval, ask the assistant | v1 is read-only; the rest arrives by release |

![Guardrail state](figures/02_guardrail_state.png)

**So what.** When a price cannot meet the partner-earnings floor inside the observed price range, the console does not warn and let it ship. It blocks the change and offers two safe paths: a guarded rollout or a price test.

## 2. A finding that shapes the roadmap: you cannot A/B test small price moves

Sized from the pricing model's fitted demand (two arms, 5% significance, 80% power):

| Move | Single segment (best case, Delhi cleaning) | Six "raise" segments pooled |
|---|---|---|
| +5% | 11 weeks | **61 weeks** |
| +10% | 3 weeks | 16 weeks |
| +20% | about 1 week | **4.5 weeks** |

**So what.** At +5%, only one of ten segments can detect the conversion change within a quarter, because the expected change is about one point and lead volume is low. The console must not promise an A/B test where the arithmetic says it would run for a year. Small moves ship as **guarded rollouts** with stop-loss thresholds on the guardrail metrics; only larger, pooled steps are tested.

## 3. Measurement and sequencing

![Metrics tree](figures/04_metrics_tree.png)

![Roadmap](figures/05_roadmap.png)

**So what.** The north-star only counts a price change if no guardrail metric moves the wrong way, so it cannot be gamed by shipping risky changes. Each release has an exit gate; RICE puts guardrails and instrumentation before the approval workflow, and the assistant last (score 0.3, lowest confidence).

## 4. The AI assistant: scoped, and held to a bar

![Assistant panel](figures/03_assistant_panel.png)

![Architecture](figures/06_assistant_architecture.png)

- **Build vs buy:** a hosted model with tool use scores well, but the always-available fallback is a templated explanation (scorecard in the PRD). Fine-tuning is rejected: the assistant explains numbers it is handed, so there is no domain corpus to learn.
- **Specified, not defaulted:** temperature 0; a context budget of one segment card plus four scenario rows; one segment per retrieval chunk; numbers from tools only.
- **What it will never say:** no causal claims, no number it did not receive, no recommendation that breaches the floor or the fulfilment target, no invented driver.

![Assistant eval](figures/07_assistant_eval.png)

**So what.** The rubric is implemented, not described: 24 labelled cases and deterministic checks that separate a grounded answer from a helpful-sounding one that invents a number or agrees to relax a guardrail. **Limits:** no language model was called, and the reference responder is written against the same rubric. Its score shows the harness works, not that a real model will pass. A real model is the true test, and the release rule is 100% on faithfulness and refusals.

## What this does not show

- **No console was built.** The wireframes are low fidelity and no user has seen them; the discovery plan in the PRD lists what to validate first, and no findings are claimed.
- **The evidence is a synthetic model.** Partner response is calibrated, not measured; cost inputs are assumptions.
- **RICE scores, build-vs-buy weights and roadmap gates are judgement,** shown so they can be argued with.

## Run it

```bash
pip install -r requirements.txt
python tests/test_checks.py            # unit tests for the eval checks
python -m assistant_eval.run_eval      # score the three responders on the 24-case golden set
python analysis/experiment_power.py    # price-test sizing
python analysis/make_diagrams.py       # wireframes and diagrams (PNG export needs rsvg-convert)
python analysis/plot_eval.py           # eval chart
python analysis/build_prd.py           # regenerate docs/PRD.md from the computed numbers above
```

```
docs/PRD.md         the full document
figures/            wireframes, metrics tree, roadmap, architecture (SVG source + PNG), eval chart
assistant_eval/     tools, 24 cases, checks, three responders, runner
analysis/           test sizing, diagram and PRD generators
data/p1_snapshot/   the pricing engine's outputs this document is grounded in
```

**Author:** Akash Sood · ISB AMPBA · [portfolio](https://akash-sood97.github.io) · [GitHub](https://github.com/akash-sood97)
