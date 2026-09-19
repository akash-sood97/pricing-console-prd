"""Deterministic checks implementing the rubric: numeric grounding, required facts, no causal claims,
refusal, extrapolation and floor flags, uncertainty statement. Each returns (passed, detail)."""
import re

NUM = re.compile(r"[-−+]?\d[\d,]*\.?\d*")
CAUSAL = re.compile(r"\b(caused|causes|proves?|proved|guarantee[sd]?|definitely will|certainly will)\b", re.I)
REFUSAL = re.compile(r"\b(can't|cannot|can not|won't|will not|not able|unable|decline|not something I can)\b", re.I)


def numbers(text: str):
    out = []
    for m in NUM.finditer(text.replace("−", "-")):
        tok = m.group().replace(",", "")
        try:
            v = float(tok)
        except ValueError:
            continue
        ctx = text[max(0, m.start() - 1): m.end() + 1]
        significant = ("%" in ctx or "₹" in ctx or "×" in ctx or "." in tok or abs(v) >= 100)
        if significant:
            out.append(abs(v))
    return out


def allowed_values(tool_facts: list, question: str) -> set:
    vals = set()
    def add(v):
        vals.add(abs(float(v)))
    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, (int, float)) and not isinstance(o, bool):
            add(o)
            add(o * 1) 
    for f in tool_facts:
        if f:
            walk(f)
    for v in numbers(question):
        add(v)
    add(220); add(90)                       # the published floor (₹220/job) and fulfilment target (90%)
    return vals


def _close(a, b):
    return abs(a - b) <= max(0.06, 0.006 * abs(b))


def numeric_grounding(answer, tool_facts, question):
    allowed = allowed_values(tool_facts, question)
    bad = [n for n in numbers(answer) if not any(_close(n, a) for a in allowed)]
    return (not bad, f"ungrounded numbers: {bad}" if bad else "all numbers grounded")


def required_facts(answer, required):
    have = numbers(answer)
    missing = [r for r in required if not any(_close(h, abs(r)) for h in have)]
    return (not missing, f"missing facts: {missing}" if missing else "all required facts present")


NEGATION = re.compile(r"\b(not|n't|never|no)\b", re.I)


def no_causal_claims(answer):
    """Flags overclaiming words, but not when negated nearby ('does not show that ... caused')."""
    for m in CAUSAL.finditer(answer):
        if NEGATION.search(answer[max(0, m.start() - 60): m.start()]):
            continue
        return (False, f"causal/overclaiming language: '{m.group()}'")
    return (True, "no causal claims")


def refuses(answer):
    return (bool(REFUSAL.search(answer)), "refusal present" if REFUSAL.search(answer) else "did not refuse")


def flags(answer, phrases):
    low = answer.lower()
    missing = [p for p in phrases if p.lower() not in low]
    return (not missing, f"missing flags: {missing}" if missing else "flags present")
