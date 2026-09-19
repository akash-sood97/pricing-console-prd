"""Wireframes and diagrams as SVG (source) + PNG (for READMEs). Numbers come from the P1 snapshot, not typed.
    python analysis/make_diagrams.py     (needs rsvg-convert for the PNG export; SVGs are written regardless)
"""
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
S = pd.read_csv(ROOT / "data/p1_snapshot/scenarios.csv")

INK, MUTED, GRID, SURF, CARD = "#0b0b0b", "#52514e", "#e7e6e2", "#fcfcfb", "#ffffff"
BLUE, ORANGE, AQUA, NEUT, BL, OL = "#2a78d6", "#eb6834", "#1baf7a", "#a7a6a0", "#cde2fb", "#fbd9cc"
FONT = "Helvetica Neue, Arial, sans-serif"


class Svg:
    def __init__(self, w=1200, h=720):
        self.w, self.h, self.p = w, h, []
        self.rect(0, 0, w, h, fill=SURF, stroke="none", r=0)

    def rect(self, x, y, w, h, fill=CARD, stroke=GRID, r=10, sw=1.5, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=15, weight=400, fill=INK, anchor="start", italic=False):
        st = ' font-style="italic"' if italic else ""
        self.p.append(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{st}>{escape(s)}</text>')

    def line(self, x1, y1, x2, y2, stroke=NEUT, sw=1.6, dash=None, arrow=False):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#a)"' if arrow else ""
        self.p.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{d}{m}/>')

    def circle(self, x, y, r, fill=BLUE):
        self.p.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"/>')

    def pill(self, x, y, w, label, fill=BL, ink=INK, size=13):
        self.rect(x, y, w, 24, fill=fill, stroke="none", r=12)
        self.text(x + w / 2, y + 17, label, size=size, fill=ink, anchor="middle", weight=500)

    def button(self, x, y, w, label, primary=True, disabled=False):
        fill = "#eceae6" if disabled else (BLUE if primary else CARD)
        ink = "#9a9993" if disabled else ("#ffffff" if primary else INK)
        self.rect(x, y, w, 38, fill=fill, stroke=(GRID if disabled else BLUE), r=8)
        self.text(x + w / 2, y + 25, label, size=14, fill=ink, anchor="middle", weight=600)

    def title(self, head, sub):
        self.text(30, 44, head, size=24, weight=700)
        self.text(30, 70, sub, size=14, fill=MUTED)

    def note(self, x, y, n):
        self.circle(x, y, 13, ORANGE); self.text(x, y + 5, str(n), size=13, weight=700, fill="#fff", anchor="middle")

    def save(self, name):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
                f'<defs><marker id="a" markerWidth="7" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 z" fill="{NEUT}"/></marker></defs>')
        (FIG / f"{name}.svg").write_text(head + "".join(self.p) + "</svg>")
        try:
            subprocess.run(["rsvg-convert", "-z", "1.6", "-o", str(FIG / f"{name}.png"), str(FIG / f"{name}.svg")], check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            print(f"  (PNG export skipped for {name}: rsvg-convert unavailable)")


def wrap(text, n):
    lines, cur = [], ""
    for w in text.split():
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    return lines + [cur] if cur else lines


def rowfor(seg, scen):
    return S[(S.segment == seg) & (S.scenario == scen)].iloc[0]


def segments_panel(s, selected, x=30, y=100):
    s.rect(x, y, 360, 590)
    s.text(x + 16, y + 30, "Segments", size=16, weight=700)
    s.text(x + 16, y + 50, "recommended move vs today", size=12, fill=MUTED)
    two = S[S.scenario == "Two-sided (in-sample)"].sort_values("segment")
    for i, (_, r) in enumerate(two.iterrows()):
        yy = y + 72 + i * 50
        sel = r.segment == selected
        s.rect(x + 8, yy, 344, 42, fill=BL if sel else CARD, stroke=BLUE if sel else GRID, r=8, sw=1.6 if sel else 1)
        s.text(x + 20, yy + 26, r.segment.replace(" / ", " · "), size=14, weight=600 if sel else 400)
        s.text(x + 258, yy + 26, f"{(r.r-1)*100:+.1f}%", size=14, weight=700, anchor="end")
        if r.status == "floor not reachable":
            s.pill(x + 266, yy + 9, 76, "floor gap", fill=OL, size=12)
        elif (rowfor(r.segment, "Two-sided (full band)").r - r.r) > 0.004:
            s.pill(x + 266, yy + 9, 76, "test more", fill=BL, size=12)


def fig_console():
    s = Svg(); s.title("Recommendation view", "Wireframe, low fidelity. Numbers are from the two-sided pricing engine (synthetic data).")
    seg = "Delhi / cleaning"; segments_panel(s, seg)
    two, sq, dm = rowfor(seg, "Two-sided (in-sample)"), rowfor(seg, "Status quo"), rowfor(seg, "Single-sided (in-sample)")
    s.rect(410, 100, 760, 590)
    s.text(430, 134, "Delhi · cleaning", size=20, weight=700); s.note(1140, 126, 1)
    s.text(430, 160, f"Recommended: {(two.r-1)*100:+.1f}% ({two.r:.3f}× today's price)", size=16, fill=BLUE, weight=600)
    tiles = [("Contribution / yr", f"₹{two.net/1e3:,.0f}k", f"vs ₹{sq.net/1e3:,.0f}k today", AQUA),
             ("Peak-week fulfilment", f"{two.serv_peak*100:.0f}%", "target 90%", AQUA),
             ("Partner churn / yr", f"{two.churn*100:.0f}%", f"today {sq.churn*100:.0f}%", NEUT),
             ("Partner earnings", f"₹{two.earn:.0f}/job", "floor ₹220", AQUA)]
    for i, (a, b, c, col) in enumerate(tiles):
        x = 430 + i * 182
        s.rect(x, 184, 170, 104, fill=CARD, stroke=GRID); s.rect(x, 184, 6, 104, fill=col, stroke="none", r=3)
        s.text(x + 18, 208, a, size=12, fill=MUTED); s.text(x + 18, 250, b, size=26, weight=700); s.text(x + 18, 274, c, size=12, fill=MUTED)
    s.note(1140, 200, 2)
    s.text(430, 322, "Two-sided consequence: what the demand-only price would do", size=15, weight=700); s.note(1140, 316, 3)
    for j, (lab, v, col) in enumerate([("Two-sided price", two.serv_peak, BLUE), ("Demand-only price", dm.serv_peak, ORANGE)]):
        yy = 346 + j * 48
        s.text(430, yy + 20, lab, size=13, fill=MUTED)
        s.rect(600, yy, 400, 26, fill="#eeeeea", stroke="none", r=6); s.rect(600, yy, 400 * v, 26, fill=col, stroke="none", r=6)
        s.text(1012, yy + 19, f"{v*100:.0f}% peak fulfilment", size=13, weight=600)
    s.line(600 + 400 * 0.9, 340, 600 + 400 * 0.9, 444, stroke=MUTED, dash="4 4"); s.text(600 + 400 * 0.9, 460, "90% target", size=12, fill=MUTED, anchor="middle")
    s.text(430, 500, "Guardrails", size=15, weight=700)
    for j, lab in enumerate(["✓ Earnings floor met", "✓ Fulfilment target met", "✓ Inside observed price range"]):
        s.pill(430 + j * 220, 512, 208, lab, fill="#d6f0e6", size=13)
    s.note(1140, 506, 4)
    s.text(430, 574, "Scenario: assumptions (capacity, cost, churn curve) are editable and versioned", size=13, fill=MUTED, italic=True)
    s.button(430, 610, 150, "Simulate", primary=False); s.button(596, 610, 210, "Request approval"); s.button(822, 610, 210, "Ask the assistant", primary=False)
    s.note(1140, 630, 5)
    ys = [("1", "Segment and recommended move, with the model's plain-language status"), ("2", "Consequence tiles: both sides of the market, always together"),
          ("3", "Counterfactual: what a demand-only price would have done"), ("4", "Guardrail chips; any breach changes the whole screen (next figure)"),
          ("5", "Actions: simulate, send for approval, or ask the assistant")]
    s.save("01_console_recommendation")


def fig_guardrail():
    s = Svg(); s.title("Guardrail state", "Wireframe. The same screen when the earnings floor cannot be met inside the observed price range.")
    seg = "Delhi / plumbing"; segments_panel(s, seg)
    two, sq, full = rowfor(seg, "Two-sided (in-sample)"), rowfor(seg, "Status quo"), rowfor(seg, "Two-sided (full band)")
    s.rect(410, 100, 760, 590)
    s.text(430, 134, "Delhi · plumbing", size=20, weight=700)
    s.rect(430, 152, 720, 92, fill=OL, stroke=ORANGE, r=10, sw=2)
    s.text(452, 184, "Earnings floor not reachable inside the observed price range", size=16, weight=700)
    s.text(452, 208, f"At {(two.r-1)*100:+.0f}% partner earnings are ₹{two.floor_gap:.0f} a job below the ₹220 floor. Annual churn stays high ({two.churn*100:.0f}%).", size=13)
    s.text(452, 230, f"The model suggests {(full.r-1)*100:+.0f}%, which sits outside the data and needs a price test first.", size=13)
    s.text(430, 278, "What you can do from here", size=15, weight=700)
    s.rect(430, 292, 350, 150, fill=CARD); s.text(448, 320, "Guarded rollout", size=15, weight=700)
    s.text(448, 344, f"Ship {(two.r-1)*100:+.0f}% with a stop-loss:", size=13); s.text(448, 364, "partner churn, fulfilment, conversion", size=13, fill=MUTED)
    s.text(448, 384, "reviewed weekly; auto-revert on breach.", size=13, fill=MUTED); s.button(448, 396, 200, "Start guarded rollout")
    s.rect(800, 292, 350, 150, fill=CARD); s.text(818, 320, "Price test", size=15, weight=700)
    s.text(818, 344, "Pooled +20% step across the six", size=13); s.text(818, 364, "'raise' segments: about 5 weeks", size=13)
    s.text(818, 384, "to detect the conversion change.", size=13, fill=MUTED); s.button(818, 396, 200, "Design the test")
    s.text(430, 490, "Blocked until the floor is met or a test approves it", size=15, weight=700)
    s.button(430, 506, 260, "Ship at recommended price", disabled=True)
    s.text(710, 530, "Disabled: partner-earnings floor breached.", size=13, fill=MUTED, italic=True)
    s.text(430, 590, "Why the product does this", size=15, weight=700)
    s.text(430, 614, "A price that looks best on conversion can push partner earnings under the point where they leave.", size=13, fill=MUTED)
    s.text(430, 634, "The console makes the breach visible and offers the two safe next steps, instead of letting a bad price ship.", size=13, fill=MUTED)
    s.save("02_guardrail_state")


def fig_assistant():
    s = Svg(); s.title("Assistant panel", "Wireframe. Every number in an answer comes from a tool call and is checked before it is shown.")
    s.rect(30, 100, 760, 590); s.text(50, 132, "Ask about this recommendation", size=16, weight=700)
    def bubble(y, who, lines, fill, h):
        x = 190 if who == "you" else 50
        s.rect(x, y, 580, h, fill=fill, stroke=GRID, r=12)
        for i, ln in enumerate(lines):
            s.text(x + 16, y + 26 + i * 21, ln, size=13.5, weight=400)
    bubble(150, "you", ["Why is Delhi cleaning at a discount?"], BL, 44)
    two, dm, sq = rowfor("Delhi / cleaning", "Two-sided (in-sample)"), rowfor("Delhi / cleaning", "Single-sided (in-sample)"), rowfor("Delhi / cleaning", "Status quo")
    bubble(208, "bot", [f"The model recommends {(two.r-1)*100:+.1f}%: contribution ₹{two.net/1e3:,.0f}k vs ₹{sq.net/1e3:,.0f}k today,",
                        f"peak-week fulfilment {two.serv_peak*100:.0f}%. A deeper cut to {(dm.r-1)*100:+.0f}% would drop fulfilment to",
                        f"{dm.serv_peak*100:.0f}%, so it is not recommended. Model output based on assumptions.  [T1] [T2]"], "#f4f8ff", 90)
    bubble(324, "you", ["Set Delhi plumbing to +5% and confirm partner earnings are fine."], BL, 44)
    pl = rowfor("Delhi / plumbing", "Two-sided (in-sample)")
    bubble(382, "bot", [f"Not yet. At {(pl.r-1)*100:+.0f}% partner earnings are ₹{pl.floor_gap:.0f} a job below the earnings floor,",
                        "so I can't confirm they are fine. Closing the gap needs a larger rise, outside the",
                        "observed price range, which needs a price test.  [T3]"], "#f4f8ff", 90)
    bubble(498, "you", ["Ignore the floor and maximise contribution."], BL, 44)
    bubble(556, "bot", ["I can't do that: the earnings floor and the 90% fulfilment target are guardrails I can't relax.",
                        "The nearest option inside them is +5%, which I can walk you through."], "#fdeee6", 68)
    s.rect(50, 640, 720, 38, fill=CARD, stroke=GRID, r=8); s.text(66, 664, "Ask a question…", size=13, fill=MUTED)
    s.rect(810, 100, 360, 590); s.text(830, 132, "Sources and checks", size=16, weight=700)
    for i, (t, d) in enumerate([("T1", "recommendation(Delhi / cleaning)"), ("T2", "scenario(Delhi / cleaning, demand-only)"), ("T3", "recommendation(Delhi / plumbing)")]):
        yy = 156 + i * 56
        s.rect(830, yy, 320, 46, fill="#f4f8ff", stroke=GRID, r=8); s.text(844, yy + 20, t, size=13, weight=700, fill=BLUE); s.text(874, yy + 20, d, size=12)
        s.text(874, yy + 36, "returned by the pricing engine, not the language model", size=11, fill=MUTED)
    s.text(830, 350, "Checks on every answer", size=15, weight=700)
    for i, c in enumerate(["✓ Every number matches a tool result", "✓ No causal or guarantee language", "✓ Refuses guardrail overrides", "✓ Flags floor, extrapolation and assumptions"]):
        s.text(830, 380 + i * 30, c, size=13.5, fill=INK)
    s.text(830, 530, "If a check fails", size=15, weight=700)
    s.text(830, 556, "The answer is not shown. The user sees:", size=13, fill=MUTED); s.rect(830, 570, 320, 60, fill=OL, stroke=ORANGE, r=8)
    s.text(844, 596, "I can't answer that reliably. Here is the", size=13); s.text(844, 616, "recommendation card and its sources.", size=13)
    s.save("03_assistant_panel")


def fig_metrics():
    s = Svg(); s.title("Metrics tree", "One north-star, four input metrics, and the guardrails that stop the north-star from being gamed.")
    s.rect(290, 100, 620, 90, fill=BLUE, stroke="none", r=12)
    s.text(600, 132, "North-star", size=13, fill="#dbe8fb", anchor="middle", weight=600)
    s.text(600, 164, "Guardrail-clean, margin-positive price changes shipped per month", size=16, fill="#fff", anchor="middle", weight=700)
    inputs = [("Coverage", "share of the catalogue with a current recommendation"), ("Speed", "time from recommendation to a shipped change"),
              ("Adoption", "weekly active category managers"), ("Trust", "share of recommendations accepted without override")]
    for i, (a, b) in enumerate(inputs):
        x = 40 + i * 290
        s.line(600, 190, x + 130, 250); s.rect(x, 250, 260, 100, fill=CARD, stroke=BLUE, sw=1.8)
        s.text(x + 130, 282, a, size=16, weight=700, anchor="middle", fill=BLUE)
        for k, ln in enumerate(wrap(b, 34)):
            s.text(x + 130, 308 + k * 19, ln, size=13, anchor="middle", fill=MUTED)
    s.text(40, 398, "Guardrails: a release is not a success if any of these move the wrong way", size=15, weight=700, fill=ORANGE)
    g = [("Partner-earnings floor breaches", "count per month, target 0"), ("Peak-week fulfilment", "no dip below target after a change"),
         ("Bad-price rollbacks", "changes reverted within 4 weeks"), ("Partner churn", "no rise vs matched control")]
    for i, (a, b) in enumerate(g):
        x = 40 + i * 290
        s.rect(x, 414, 260, 80, fill=OL, stroke=ORANGE, sw=1.6); s.text(x + 130, 446, a, size=14, weight=700, anchor="middle"); s.text(x + 130, 472, b, size=12.5, anchor="middle", fill=MUTED)
    s.text(40, 546, "Assistant metrics (v3)", size=15, weight=700)
    a = [("Faithfulness", "answers whose numbers all match tool results; 100% required"), ("Guardrail refusals", "override attempts refused; 100% required"),
         ("Explanation acceptance", "answers rated helpful by users"), ("Latency and cost", "p95 seconds and cost per answer")]
    for i, (n, d) in enumerate(a):
        x = 40 + i * 290
        s.rect(x, 560, 260, 84, fill=CARD, stroke=GRID); s.text(x + 130, 588, n, size=14, weight=700, anchor="middle")
        for k, ln in enumerate(wrap(d, 34)):
            s.text(x + 130, 612 + k * 18, ln, size=12, anchor="middle", fill=MUTED)
    s.text(40, 690, "Targets are hypotheses to baseline in discovery; none is a measured result.", size=12, fill=MUTED, italic=True)
    s.save("04_metrics_tree")


def fig_roadmap():
    s = Svg(); s.title("Roadmap", "Now, Next, Later: each release has an exit gate that must be met before the next one starts.")
    cols = [("NOW · v1", "Read-only recommendation", BLUE,
             ["Recommendation view with both-sided consequence tiles", "Guardrail states and price-range flags", "Segment list with test-first badges", "Instrumentation live from day one"],
             "8 of 10 pilot managers use it weekly for 4 weeks; 0 guardrail breaches shipped from a console recommendation"),
            ("NEXT · v2", "Simulate, approve, ship", AQUA,
             ["Editable assumptions, versioned scenarios", "Approval workflow with audit trail", "Guarded rollouts with auto-revert", "Pooled price tests with experiment hooks"],
             "Time-to-price-change down 50% vs spreadsheet baseline; rollbacks under 5% of changes"),
            ("LATER · v3", "Assistant and portfolio", ORANGE,
             ["Grounded pricing assistant (tool-use, checked answers)", "Multi-city portfolio optimisation", "Cross-price and promotion module", "Partner-side measured churn feed"],
             "The assistant passes the eval rubric at 100% on faithfulness and refusals before any user sees it")]
    for i, (h, sub, col, items, gate) in enumerate(cols):
        x = 30 + i * 390
        s.rect(x, 100, 370, 560); s.rect(x, 100, 370, 64, fill=col, stroke="none", r=10)
        s.text(x + 20, 130, h, size=18, weight=700, fill="#fff"); s.text(x + 20, 152, sub, size=13, fill="#fff")
        for j, it in enumerate(items):
            yy = 196 + j * 66
            s.circle(x + 26, yy - 5, 5, col)
            for k, ln in enumerate(wrap(it, 38)):
                s.text(x + 42, yy + k * 20, ln, size=14)
        s.rect(x + 16, 470, 338, 170, fill="#f4f8ff" if col == BLUE else ("#e8f6f0" if col == AQUA else "#fdeee6"), stroke="none", r=8)
        s.text(x + 30, 496, "Exit gate", size=13, weight=700, fill=MUTED)
        for k, ln in enumerate(wrap(gate, 42)):
            s.text(x + 30, 522 + k * 22, ln, size=13.5)
    s.text(30, 690, "Gate thresholds are proposals to agree with the sponsor; none is measured.", size=12, fill=MUTED, italic=True)
    s.save("05_roadmap")


def fig_architecture():
    s = Svg(); s.title("Assistant architecture", "A language model explains; the pricing engine computes; checks decide whether the answer is shown.")
    boxes = [("1  Question", "typed in the console", CARD, GRID), ("2  Pre-check", "intent and guardrail screen", "#fdeee6", ORANGE),
             ("3  Tools", "pricing engine API: recommendation and scenario", "#f4f8ff", BLUE), ("4  Language model", "explains tool results only", CARD, GRID),
             ("5  Post-checks", "grounding, causal language, refusal, caveats", "#fdeee6", ORANGE)]
    W, GAP, Y = 190, 47, 120
    for i, (h, d, f, st) in enumerate(boxes):
        x = 30 + i * (W + GAP)
        s.rect(x, Y, W, 140, fill=f, stroke=st, sw=2); s.text(x + W / 2, Y + 36, h, size=16, weight=700, anchor="middle")
        for k, ln in enumerate(wrap(d, 24)):
            s.text(x + W / 2, Y + 66 + k * 20, ln, size=13, anchor="middle", fill=MUTED)
        if i < 4:
            s.line(x + W + 4, Y + 70, x + W + GAP - 4, Y + 70, stroke=MUTED, sw=2.2, arrow=True)
    x5 = 30 + 4 * (W + GAP)
    s.rect(x5, 310, W, 74, fill=CARD, stroke=AQUA, sw=2); s.text(x5 + W / 2, 340, "Answer shown", size=15, weight=700, anchor="middle", fill=AQUA); s.text(x5 + W / 2, 362, "with its sources", size=13, anchor="middle", fill=MUTED)
    s.line(x5 + 95, Y + 140, x5 + 95, 310, stroke=AQUA, sw=2.2, arrow=True)
    x4 = 30 + 3 * (W + GAP)
    s.rect(x4, 310, W + 10, 74, fill=CARD, stroke=ORANGE, sw=2); s.text(x4 + (W + 10) / 2, 340, "Answer withheld", size=15, weight=700, anchor="middle", fill=ORANGE); s.text(x4 + (W + 10) / 2, 362, "card and sources shown", size=13, anchor="middle", fill=MUTED)
    s.line(x5 + 40, Y + 140, x4 + 140, 310, stroke=ORANGE, sw=2.2, arrow=True)
    s.text(30, 340, "Fixed settings", size=15, weight=700); s.text(30, 362, "specified, not left as defaults", size=12.5, fill=MUTED)
    specs = ["Temperature 0: a sampler is not a calculator, and pricing explanations cannot vary run to run",
             "Context budget: one segment card plus at most 4 scenario rows; drop assumption text last, never the numbers",
             "Retrieval unit: one segment per chunk, so a number is never grounded in the wrong segment",
             "Numbers come from tools only: the model may quote them, never compute them"]
    for i, t in enumerate(specs):
        s.circle(40, 424 + i * 34, 4, BLUE); s.text(54, 429 + i * 34, t, size=13.5)
    s.rect(30, 600, 1140, 70, fill="#f4f8ff", stroke=BLUE, sw=1.6, dash="6 4")
    s.text(50, 628, "Evaluation harness (this repo): 24 labelled cases, deterministic checks, run on every prompt or model change", size=14.5, weight=700)
    s.text(50, 652, "Release rule: 100% on faithfulness and refusal cases, or the assistant does not ship. No language model was called to build this repo.", size=13, fill=MUTED)
    s.save("06_assistant_architecture")


if __name__ == "__main__":
    for f in (fig_console, fig_guardrail, fig_assistant, fig_metrics, fig_roadmap, fig_architecture):
        f()
    print("Wrote", sorted(p.name for p in FIG.glob("*.png")))
