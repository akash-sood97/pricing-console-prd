"""The 'tool layer' the assistant may call: precomputed facts from the pricing engine (P1 snapshot).

In v1 the what-if tool only serves the scenarios the engine has already solved. Anything else is
'not computed', and the assistant must say so instead of doing its own arithmetic.
"""
from pathlib import Path

import pandas as pd

SNAP = Path(__file__).resolve().parent.parent / "data" / "p1_snapshot" / "scenarios.csv"
NAMES = {"status_quo": "Status quo", "demand_only": "Single-sided (in-sample)", "two_sided": "Two-sided (in-sample)",
         "two_sided_full_band": "Two-sided (full band)"}
FLOOR, SERVICE_TARGET, OBSERVED_MAX_MOVE = 220.0, 0.90, 5.0   # ₹/job, peak-week fulfilment, +% inside observed range


def _row(r) -> dict:
    return dict(price_multiple=round(float(r.r), 3), move_pct=round((float(r.r) - 1) * 100, 1), conversion_pct=round(float(r.conversion) * 100, 1),
                partner_earnings=round(float(r.earn)), churn_pct=round(float(r.churn) * 100), peak_fulfilment_pct=round(float(r.serv_peak) * 100),
                contribution_k=round(float(r.net) / 1e3), status=str(r.status) if isinstance(r.status, str) else "",
                floor_gap=round(float(r.floor_gap)), extrapolated=bool(r.extrapolated))


class Tools:
    def __init__(self):
        self.df = pd.read_csv(SNAP)
        self.segments = sorted(self.df.segment.unique())

    def recommendation(self, segment: str) -> dict:
        d = self.df[self.df.segment == segment]
        out = {"segment": segment}
        for key, name in NAMES.items():
            out[key] = _row(d[d.scenario == name].iloc[0])
        return out

    def whatif(self, segment: str, move_pct: float):
        """Return a precomputed scenario within 0.5 points of the requested move, else None."""
        rec = self.recommendation(segment)
        for key in NAMES:
            if abs(rec[key]["move_pct"] - move_pct) <= 0.5:
                return {"segment": segment, "scenario": key, **rec[key]}
        return None

    def find_segment(self, text: str):
        t = text.lower()
        for s in self.segments:
            city, job = [x.strip().lower() for x in s.split("/")]
            if city in t and job.split()[0] in t:
                return s
        return None
