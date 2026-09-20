# Dynamic Pricing Console: PRD, roadmap and a tested AI-assistant spec

**A model that changes no prices is a hobby. This is the product spec that would put one in a category manager's hands — and the reason it ships read-only first.**

- **Situation.** Pricing is set in spreadsheets, one city at a time, from a customer-demand view only. The [pricing engine](https://github.com/akash-sood97/two-sided-pricing-engine) showed that ignoring the partner side is what makes a price cut lose money — but a model nobody can act on changes nothing.
- **Task.** What does the product actually need to be, for a category manager to change a price safely? And where should an AI assistant sit in it, if anywhere?
- **Action.** Wrote the PRD — one screen showing both sides of the market, guardrails that block unsafe changes, a metrics tree, a release roadmap — then **sized the price experiments** and **built a working evaluation harness** for the AI assistant rather than describing one.
- **Result.** Ship v1 **read-only and guardrail-first**. Small price moves go out as guarded rollouts, not A/B tests, because the arithmetic says a +5% test would run **61 weeks**. The assistant does not reach a user until it passes **100%** of faithfulness and refusal cases.
- **The trade-off.** Read-only means the console cannot change a price in v1, and the approval workflow managers will ask for first is deliberately sequenced last.

> **Data and honesty**
> - **No console and no language model were built.** This is a specification plus an executable evaluation harness.
> - The evidence comes from a synthetic pricing model, so targets and gates are **proposals, not measurements**.
> - The harness scores three stand-in responders written by me. That proves the harness works — **not** that a real model would pass.

**[Read the full PRD →](docs/PRD.md)**

| | | |
|---|---|---|
| **61 weeks → 4.5** | **1 of 3** | **24 cases** |
| how long an A/B test of a +5% price move would run, versus +20% — the reason v1 ships guarded rollouts | assistant versions that clear the release bar of 100% on faithfulness and refusals | labelled test cases in the evaluation harness, with unit-tested checks, runnable today |

---

## 1. The product: one screen, both sides

![A low-fidelity wireframe of the recommendation view, showing the recommended price move alongside four consequence tiles and guardrail chips.](figures/01_console_recommendation.png)

*The recommendation view. Numbers are from the pricing engine; the fidelity is deliberately low.*

| # | What it shows | Why |
|---|---|---|
| 1 | Recommended move per segment, in plain language | No unexplained number |
| 2 | Four consequence tiles together: contribution, peak-week fulfilment, partner drop-off, partner earnings | The partner side is where a demand-only price fails |
| 3 | The demand-only alternative | Shows what the manager would have shipped, and what it costs |
| 4 | Guardrail chips that change the screen on breach | See the next figure |
| 5 | Simulate, request approval, ask the assistant | v1 is read-only; the rest arrives by release |

- Showing both sides is worth **+7.1% vs +3.2%** contribution in the pricing engine — that gap is the case for building this at all.

![When a price cannot clear the partner-earnings floor, the console blocks the change and offers a guarded rollout or a price test instead.](figures/02_guardrail_state.png)

*The same screen on a guardrail breach. The unsafe path is removed, not merely flagged.*

- When a price cannot meet the partner-earnings floor inside the observed range, the console **does not warn and let it ship**.
- It **blocks** the change and offers two safe paths: a guarded rollout, or a price test.
- **So what.** A guardrail that can be clicked through is decoration. This one removes the option.

## 2. The finding that shapes the roadmap: you cannot A/B test small price moves

Sized from the pricing model's fitted demand — two arms, 5% significance, 80% power:

| Move | Single segment (best case) | Six "raise" segments pooled |
|---|---|---|
| +5% | 11 weeks | **61 weeks** |
| +10% | 3 weeks | 16 weeks |
| +20% | about 1 week | **4.5 weeks** |

- At **+5%**, only **one of ten** segments could detect the change within a quarter — the expected effect is about one percentage point and lead volume is low.
- **So what.** The console must not offer an A/B test the arithmetic says would run for a year.
- Small moves therefore ship as **guarded rollouts** with stop-loss thresholds; only larger, pooled steps get a real test.

## 3. Measurement and sequencing

![A metrics tree with a north-star that only counts a price change if no guardrail metric moves the wrong way.](figures/04_metrics_tree.png)

*The metrics tree. The guardrail condition is built into the north-star, not bolted beside it.*

![A four-release roadmap that sequences guardrails and instrumentation before the approval workflow, with the assistant last.](figures/05_roadmap.png)

*The roadmap, prioritised by reach, impact, confidence and effort.*

- The **north-star only counts a price change if no guardrail metric moves the wrong way**, so it cannot be gamed by shipping risky changes.
- Every release has an **exit gate** it must clear before the next one starts.
- Guardrails and instrumentation come **before** the approval workflow. The assistant comes **last** — lowest confidence of anything on the roadmap.
- **So what.** The sequencing is the argument: the thing managers ask for first is not the thing that makes the product safe.

## 4. The AI assistant: scoped, and held to a bar

![A wireframe of the assistant panel, which explains numbers it is handed and refuses to invent any.](figures/03_assistant_panel.png)

*The assistant panel. Its job is to explain a recommendation, never to produce one.*

![The assistant architecture: numbers come from tools only, with a templated explanation as the always-available fallback.](figures/06_assistant_architecture.png)

*Architecture. The fallback path matters more than the model path.*

- **Build vs buy.** A hosted model with tool use scores best, but the always-available fallback is a **templated explanation**. Full scorecard in the PRD.
- **Fine-tuning is rejected.** The assistant explains numbers it is handed, so there is no domain knowledge to learn.
- **Specified, not defaulted:** temperature 0; a context budget of one segment card plus four scenario rows; one segment per retrieval chunk; **every number from tools only**.
- **What it will never say:** no causal claims, no number it was not given, no recommendation that breaches the earnings floor or the fulfilment target, no invented driver.

![The evaluation harness separates a grounded answer from a helpful-sounding one, with the reference passing 100%, the unguarded version 33% and the ungrounded one 0%.](figures/07_assistant_eval.png)

*Three stand-in responders against 24 labelled cases. The middle bar is the dangerous one: helpful, fluent, and wrong.*

- The rubric is **implemented, not described**: 24 labelled cases with deterministic checks.
- The checks separate a grounded answer from a **helpful-sounding one** that invents a number or agrees to relax a guardrail.
- **Limits.** No language model was called, and the reference responder was written against the same rubric. Its score shows the **harness** works, not that a real model will pass.
- **So what.** The release rule is 100% on faithfulness and refusals, and a real model is the actual test.

## What this does not show

- **No console was built.** The wireframes are low fidelity and **no user has seen them**. The PRD's discovery plan lists what to validate first; no findings are claimed.
- **The evidence is a synthetic model.** Partner response is calibrated, not measured, and cost inputs are assumptions.
- **Prioritisation scores, build-vs-buy weights and roadmap gates are judgement,** shown so they can be argued with rather than hidden.

## Terms, in plain English

<details>
<summary>Six terms this project leans on</summary>

- **PRD** — product requirements document. What the thing is, who it is for, what it must do, how success is measured, and what is deliberately out of scope.
- **Guardrail** — a limit the product refuses to cross, such as partner pay falling below a floor. Distinct from a warning, which can be ignored.
- **Guarded rollout** — releasing a change gradually with pre-set stop-loss thresholds, used where a proper A/B test would take too long to be useful.
- **North-star metric** — the single number the team steers by. Here it only counts a price change if no guardrail moved the wrong way.
- **Faithfulness** — whether an assistant's answer is supported by the numbers it was actually given, rather than plausible-sounding invention.
- **Evaluation harness** — runnable code that scores an assistant against labelled cases, so "it seems good" is replaced by a pass rate.

</details>

## Run it

```bash
pip install -r requirements.txt
python tests/test_checks.py            # unit tests for the eval checks
python -m assistant_eval.run_eval      # score the three responders on the 24-case set
python analysis/experiment_power.py    # price-test sizing
python analysis/make_diagrams.py       # wireframes and diagrams (PNG export needs rsvg-convert)
python analysis/plot_eval.py           # eval chart
python analysis/build_prd.py           # regenerate docs/PRD.md from the computed numbers above
```

`rsvg-convert` is a system binary, not a Python package: install it with `brew install librsvg` (macOS) or `apt install librsvg2-bin` (Debian/Ubuntu). Everything except the diagram export runs without it.

## Repo layout

```
docs/PRD.md         the full document
figures/            wireframes, metrics tree, roadmap, architecture (SVG source + PNG), eval chart
assistant_eval/     tools, 24 cases, checks, three responders, runner
analysis/           test sizing, diagram and PRD generators
data/p1_snapshot/   the pricing engine's outputs this document is grounded in
```

**Author:** Akash Sood · ISB AMPBA · [portfolio](https://akash-sood97.github.io) · [GitHub](https://github.com/akash-sood97)
