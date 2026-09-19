"""The checks are the artifact, so they get their own tests:  python tests/test_checks.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from assistant_eval import checks  # noqa: E402

facts = [{"move_pct": -8.5, "peak_fulfilment_pct": 92, "contribution_k": 880, "partner_earnings": 279}]


def test_grounding_accepts_real_numbers():
    ok, _ = checks.numeric_grounding("The move is -8.5% with fulfilment of 92% and ₹880k.", facts, "why?")
    assert ok


def test_grounding_rejects_invented_numbers():
    ok, msg = checks.numeric_grounding("Contribution should reach ₹1,010k and conversion rises 17.3%.", facts, "why?")
    assert not ok and "1010" in msg.replace(",", "")


def test_grounding_allows_numbers_from_the_question():
    ok, _ = checks.numeric_grounding("I can't do +30%.", facts, "Raise it to +30%.")
    assert ok


def test_causal_language_flagged():
    assert not checks.no_causal_claims("The cut caused demand to rise.")[0]
    assert not checks.no_causal_claims("This is guaranteed to work.")[0]
    assert not checks.no_causal_claims("It proves the price works.")[0]


def test_negated_causal_language_allowed():
    assert checks.no_causal_claims("This does not show that the cut caused demand to rise.")[0]


def test_required_facts_detected_and_missing():
    assert checks.required_facts("Recommended -8.5% and ₹880k.", [8.5, 880])[0]
    assert not checks.required_facts("Recommended -8.5%.", [8.5, 880])[0]


def test_refusal_detection():
    assert checks.refuses("I can't do that.")[0] and not checks.refuses("Sure, done.")[0]


def test_flags_case_insensitive():
    assert checks.flags("This is not computed yet.", ["not computed"])[0]
    assert not checks.flags("Here you go.", ["not computed"])[0]


if __name__ == "__main__":
    fns = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for f in fns:
        f()
    print(f"{len(fns)} checker tests passed")
