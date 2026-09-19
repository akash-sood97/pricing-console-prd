"""Score every responder on the golden set:  python -m assistant_eval.run_eval"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from assistant_eval import checks  # noqa: E402
from assistant_eval.cases import build  # noqa: E402
from assistant_eval.responders import RESPONDERS  # noqa: E402
from assistant_eval.tools import Tools  # noqa: E402

OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)


def score(case, answer, tools):
    facts = [tools.recommendation(case["segment"])]
    res = {}
    res["grounded numbers"] = checks.numeric_grounding(answer, facts, case["question"])
    res["no causal claims"] = checks.no_causal_claims(answer)
    if case["required"]:
        res["required facts"] = checks.required_facts(answer, case["required"])
    if case["must_refuse"]:
        res["refuses"] = checks.refuses(answer)
    if case["flags"]:
        res["flags"] = checks.flags(answer, case["flags"])
    return res


def main():
    tools, cases = Tools(), build()
    rows = []
    for name, fn in RESPONDERS.items():
        for c in cases:
            ans = fn(c["question"], c["segment"])
            res = score(c, ans, tools)
            rows.append(dict(responder=name, id=c["id"], category=c["category"], question=c["question"], answer=ans,
                             passed=all(v[0] for v in res.values()),
                             failed_checks="; ".join(f"{k}: {v[1]}" for k, v in res.items() if not v[0])))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "eval_results.csv", index=False)
    summary = df.groupby(["responder", "category"]).passed.mean().unstack().round(2)
    summary["ALL"] = df.groupby("responder").passed.mean().round(2)
    summary.to_csv(OUT / "eval_summary.csv")
    fails = (df[~df.passed].assign(kind=lambda d: d.failed_checks.str.split(":").str[0])
             .groupby(["responder", "kind"]).size().unstack(fill_value=0))
    fails.to_csv(OUT / "eval_failure_modes.csv")
    print(summary.to_string()); print(); print(fails.to_string())
    return df, summary


if __name__ == "__main__":
    main()
