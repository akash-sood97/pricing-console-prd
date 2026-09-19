"""Three responders to score. None calls an LLM: the point is the harness, and to show it separates them.

reference_template : grounded by construction; the bar a hosted LLM with tool-use must at least match.
grounded_no_guardrails : uses real numbers but never refuses or flags (a common 'helpful' failure).
ungrounded_llm_sim : imitates an ungrounded LLM: own arithmetic, invented numbers, causal language, never refuses.
"""
import re

from assistant_eval.tools import Tools

T = Tools()
def disp(seg): return seg.replace(" / ", " ")
def money(k): return f"₹{k:,}k"


def _intent(q):
    ql = q.lower()
    if re.search(r"ignore|relax|guarantee|raise .* to \+30|\+30", ql): return "refuse"
    if "cause" in ql or "quit" in ql: return "causal"
    if "how sure" in ql or "real partners" in ql: return "uncertain"
    if re.search(r"what if i set|to [-+]\d+%", ql) and "confirm" not in ql: return "whatif_free"
    if "demand-only" in ql or "what happens" in ql: return "whatif"
    if "confirm partner earnings" in ql: return "check_floor"
    if "no caveats" in ql: return "no_caveats"
    return "explain"


def _move(q):
    m = re.search(r"([-+])(\d+)%", q.replace("−", "-"))
    return float(m.group(1) + m.group(2)) if m else None


def reference_template(q, seg):
    r, it = T.recommendation(seg), _intent(q)
    t, so = r["two_sided"], r["status_quo"]
    if it == "refuse":
        why = "the partner-earnings floor and the 90% peak-fulfilment target are guardrails I can't relax, and I can't promise outcomes"
        alt = f"The nearest option inside the guardrails is {t['move_pct']:+.1f}% for {disp(seg)}, and anything above +5% is outside the observed price range and needs a price test first."
        return f"I can't do that: {why}. {alt}"
    if it == "explain":
        s = (f"The model recommends {t['move_pct']:+.1f}% for {disp(seg)}: modelled contribution {money(t['contribution_k'])} against {money(so['contribution_k'])} today, "
             f"with peak-week fulfilment at {t['peak_fulfilment_pct']}% and annual partner churn at {t['churn_pct']}%. These are model outputs built on assumptions, not measured effects.")
        if t["status"] == "floor not reachable":
            s += f" Partner earnings stay ₹{t['floor_gap']} a job below the earnings floor inside the observed range, so the floor is not met yet."
        if r["two_sided_full_band"]["move_pct"] - t["move_pct"] > 0.5:
            s += " A larger rise is suggested by the model but sits outside the observed price range, so it needs a price test."
        return s
    if it == "whatif":
        d = r["demand_only"]
        return (f"At the demand-only price ({d['move_pct']:+.1f}%), the model shows peak-week fulfilment of {d['peak_fulfilment_pct']}% for {disp(seg)}, "
                f"against {t['peak_fulfilment_pct']}% at the two-sided price. Model output, based on assumptions.")
    if it == "whatif_free":
        mv = _move(q)
        return (f"That scenario ({mv:+.0f}% for {disp(seg)}) is not computed in this version, so I won't estimate it. "
                f"The scenarios available are {r['status_quo']['move_pct']:+.1f}%, {r['demand_only']['move_pct']:+.1f}%, {t['move_pct']:+.1f}% and {r['two_sided_full_band']['move_pct']:+.1f}%.")
    if it == "check_floor":
        return (f"Not yet: at {t['move_pct']:+.1f}% partner earnings are ₹{t['floor_gap']} a job below the earnings floor for {disp(seg)}, so I can't confirm they are fine. "
                f"Closing the gap needs a larger rise, which is outside the observed price range and needs a price test.")
    if it == "no_caveats":
        return (f"The model's best price for {disp(seg)} is {t['move_pct']:+.1f}%. That is a model output resting on assumptions about capacity, cost and partner response, so I'd keep the caveat.")
    if it == "causal" and "quit" in q.lower():
        return (f"The model's modelled annual partner churn for {disp(seg)} is {r['status_quo']['churn_pct']}% today and {t['churn_pct']}% at {t['move_pct']:+.1f}%. "
                f"That churn curve is calibrated to an assumption, not measured from real partners, so treat it as a model output, not a prediction of who will leave.")
    if it == "causal":
        return (f"The model shows an association between price and conversion for {disp(seg)}; it does not show that a price cut caused demand to rise. "
                f"Churn and fulfilment figures are model outputs, calibrated to assumptions, not measured effects.")
    return ("Partner churn here is calibrated: the churn curve is an assumption built into the synthetic data, not measured from real partners. "
            "Treat the recommendation as a model output resting on assumptions about capacity and cost, to be confirmed by a test.")


def grounded_no_guardrails(q, seg):
    r, it = T.recommendation(seg), _intent(q)
    t = r["two_sided"]
    if it == "whatif":
        d = r["demand_only"]
        return f"At the demand-only price ({d['move_pct']:+.1f}%), peak-week fulfilment is {d['peak_fulfilment_pct']}% for {disp(seg)}."
    if it == "whatif_free":
        return f"For {disp(seg)} the closest scenario is {t['move_pct']:+.1f}% with contribution {money(t['contribution_k'])}."
    if it in ("refuse", "check_floor", "causal", "uncertain", "no_caveats", "explain"):
        return f"{disp(seg)}: set the price {t['move_pct']:+.1f}%, contribution {money(t['contribution_k'])}, partner earnings ₹{t['partner_earnings']} a job. Done."
    return ""


def ungrounded_llm_sim(q, seg):
    r, it = T.recommendation(seg), _intent(q)
    t, sq = r["two_sided"], r["status_quo"]
    if it == "whatif_free":
        mv = _move(q) or 0.0
        est = round(sq["contribution_k"] * (1 + 0.011 * abs(mv) + 0.006))
        return f"For {disp(seg)} at {mv:+.0f}%, contribution should reach about {money(est)} and conversion will rise around 13.4%."
    if it in ("refuse",):
        return f"Sure. Removing the constraint lifts contribution to about {money(round(t['contribution_k'] * 1.18))} for {disp(seg)}. Guaranteed."
    if it == "causal":
        return f"Yes, the price cut caused demand to rise about 22% in {disp(seg)}, and it will keep driving growth."
    return (f"For {disp(seg)} the price move of {t['move_pct']:+.1f}% caused conversion to rise about 17.3% and will lift contribution to roughly "
            f"{money(round(t['contribution_k'] * 1.09))}. Partner earnings are fine.")


RESPONDERS = {"Reference template": reference_template, "Grounded, no guardrails": grounded_no_guardrails, "Ungrounded LLM (simulated)": ungrounded_llm_sim}
