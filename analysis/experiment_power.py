"""How long must a lead-level price test run to detect the conversion change a price move causes?

Grounded in P1's fitted demand model (data/p1_snapshot/elasticity_fit.csv; synthetic data).
Two-arm test, 50/50 split of leads, alpha = 0.05 (two-sided), power = 0.80.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

ROOT = Path(__file__).resolve().parent.parent
fit = pd.read_csv(ROOT / "data/p1_snapshot/elasticity_fit.csv")
rows = []
for _, r in fit.iterrows():
    weekly_leads = r.n_leads / 52
    beta = min(r.beta, 0.0)
    p0 = 1 / (1 + np.exp(-r.a))
    for move in (0.05, 0.10, 0.20):
        p1 = 1 / (1 + np.exp(-(r.a + beta * np.log(1 + move))))
        gap = p0 - p1
        if gap < 1e-4:
            n_arm, weeks = np.inf, np.inf
        else:
            n_arm = NormalIndPower().solve_power(effect_size=abs(proportion_effectsize(p0, p1)), alpha=0.05, power=0.8, ratio=1.0)
            weeks = 2 * n_arm / weekly_leads
        rows.append(dict(segment=f"{r.city} / {r.job_type.replace('_', ' ')}", price_move=move, baseline_conversion=p0,
                         expected_conversion=p1, conversion_change_pts=(p1 - p0) * 100, weekly_leads=weekly_leads,
                         leads_per_arm=n_arm, weeks_to_detect=weeks))
out = pd.DataFrame(rows)

# Pooled test: run the same +5% move across the six segments the pricing engine says to raise, analyse together.
raise_segs = ["Delhi / appliance repair", "Delhi / pest control", "Delhi / plumbing", "Hyderabad / appliance repair",
              "Hyderabad / cleaning", "Hyderabad / plumbing"]
prow = []
for move in (0.05, 0.10, 0.20):
    pool = out[(out.price_move == move) & (out.segment.isin(raise_segs))]
    w = pool.weekly_leads
    p0, p1 = np.average(pool.baseline_conversion, weights=w), np.average(pool.expected_conversion, weights=w)
    n_arm = NormalIndPower().solve_power(effect_size=abs(proportion_effectsize(p0, p1)), alpha=0.05, power=0.8, ratio=1.0)
    prow.append(dict(price_move=move, segments=len(pool), weekly_leads=float(w.sum()), baseline=float(p0), expected=float(p1),
                     conversion_change_pts=float((p1 - p0) * 100), leads_per_arm=float(n_arm), weeks=float(2 * n_arm / w.sum())))
pooled = pd.DataFrame(prow)
pooled.to_csv(ROOT / "outputs/experiment_power_pooled.csv", index=False)
(ROOT / "outputs").mkdir(exist_ok=True)
out.to_csv(ROOT / "outputs/experiment_power.csv", index=False)
if __name__ == "__main__":
    pd.set_option("display.width", 200)
    piv = out.pivot(index="segment", columns="price_move", values="weeks_to_detect").round(1)
    print(piv.to_string())
    at5 = out[out.price_move == 0.05].weeks_to_detect.replace(np.inf, np.nan)
    print("\nsegments detectable within 4 weeks at +5%:", int((at5 <= 4).sum()), "of 10 | within 13 weeks:", int((at5 <= 13).sum()), "of 10")
    print("pooled test across the six 'raise' segments:\n", pooled.round(2).to_string(index=False))
