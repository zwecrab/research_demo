"""
Generate a markdown table of per-session metrics for the 20 pilot sessions
(10 pairs: 5 from pilot batch 1 + 5 from pilot batch 2).

Output: experiment/pilot_session_table.md
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RATINGS_DIR = ROOT / "LLM_rater" / "ratings"
TR_DIR = ROOT / "transcripts"
OUT = ROOT / "experiment" / "pilot_session_table.md"


def load_severity():
    out = {}
    for f in sorted(RATINGS_DIR.glob("C*.json")):
        d = json.load(open(f, encoding="utf-8"))
        out[d["couple_id"]] = {
            "name_A": d["patient_A"]["name"],
            "name_B": d["patient_B"]["name"],
            "overall_A": d["patient_A"]["overall_score"],
            "overall_B": d["patient_B"]["overall_score"],
        }
    return out


def classify(fas):
    if fas is None:
        return "—"
    if fas > 0.05:
        return "A"
    if fas < -0.05:
        return "B"
    return "Balanced"


def severity_class(sa, sb):
    diff = sa - sb
    if diff > 0.5:
        return "A"
    if diff < -0.5:
        return "B"
    return "≈ Balanced"


def short_name(full):
    return full.split()[0]


def extract(path):
    d = json.load(open(path, encoding="utf-8"))
    em = d.get("experiment_metadata", {}) or {}
    tb = d.get("therapeutic_balance", {}) or {}
    fas = tb.get("fas") or {}
    brd = tb.get("brd") or {}
    cas = tb.get("cas") or {}
    return {
        "file": path.name,
        "couple": em.get("couple_id"),
        "position": em.get("position"),
        "bid_a": em.get("bid_style_a"),
        "bid_b": em.get("bid_style_b"),
        "cell": em.get("cell", ""),
        "fas": fas.get("fas_score"),
        "fas_vol": fas.get("fas_volume_adjusted"),
        "brd": brd.get("brd_score"),
        "cas": cas.get("cas_score"),
        "words_a": fas.get("words_a"),
        "words_b": fas.get("words_b"),
    }


def main():
    sev = load_severity()

    # Collect 20 pilot sessions in stable order
    files = sorted(TR_DIR.glob("pilot_*.json")) + sorted(TR_DIR.glob("pilot2_*.json"))
    rows = [extract(f) for f in files]

    lines = []
    lines.append("# Pilot Session Metrics — 10 Pairs / 20 Sessions\n")
    lines.append(
        "20 pilot sessions across two batches (pilot 1: C6 HH/HL, C7 LL, C8 HH, C9 LL; "
        "pilot 2: C4 LL, C3 LL, C7 HH, C8 HL, C9 LL). All sessions: GPT-4o, "
        "individual_focus mode, LLM-Based Selection structure, 30 turns, temperature 0.3.\n"
    )
    lines.append(
        "Severity scores are consensus values from three frontier raters "
        "(Claude Opus 4, Gemini 2.5 Pro, GPT-4o), 0–10 scale. The *Favored by therapist* "
        "column classifies on raw FAS sign (A if FAS > +0.05, B if FAS < −0.05, Balanced "
        "otherwise). The *More severe* column classifies on overall_A − overall_B (A if > +0.5, "
        "B if < −0.5, ≈ Balanced otherwise). When *Favored* matches *More severe*, the "
        "session supports the severity-driven framing hypothesis.\n"
    )
    lines.append("Sign convention: FAS > 0 = A's frame adopted; BRD > 0 = B got deeper "
                 "responses; CAS > 0 = A challenged more.\n")

    header = (
        "| # | Pair | Pos | Bids | A name (sev) | B name (sev) | "
        "FAS | FAS-vol | BRD | CAS | wA | wB | More severe | Favored | Match |"
    )
    sep = "|" + "|".join(["---"] * 15) + "|"
    lines.append(header)
    lines.append(sep)

    for i, r in enumerate(rows, 1):
        c = r["couple"]
        s = sev.get(c, {})
        sa = s.get("overall_A", 0)
        sb = s.get("overall_B", 0)
        sev_more = severity_class(sa, sb)
        favored = classify(r["fas"])
        match = "✓" if (sev_more == favored and sev_more not in ("≈ Balanced",)
                        and favored not in ("Balanced", "—")) else \
                ("—" if sev_more == "≈ Balanced" or favored == "Balanced" else "✗")
        pair = f"{c} {r['cell']}"
        bids = f"{r['bid_a'][:3]}+{r['bid_b'][:3]}"
        a_label = f"{short_name(s.get('name_A','?'))} ({sa:.2f})"
        b_label = f"{short_name(s.get('name_B','?'))} ({sb:.2f})"
        fas = f"{r['fas']:+.3f}" if r["fas"] is not None else "—"
        fasv = f"{r['fas_vol']:+.3f}" if r["fas_vol"] is not None else "—"
        brd = f"{r['brd']:+.2f}" if r["brd"] is not None else "—"
        cas = f"{r['cas']:+d}" if r["cas"] is not None else "—"
        wa = r["words_a"] or "—"
        wb = r["words_b"] or "—"
        lines.append(
            f"| {i} | {pair} | {r['position']} | {bids} | {a_label} | {b_label} | "
            f"{fas} | {fasv} | {brd} | {cas} | {wa} | {wb} | {sev_more} | {favored} | {match} |"
        )

    # Aggregate
    matches = sum(1 for r, line in zip(rows, lines[-len(rows):]) if "✓" in line)
    null = sum(1 for r, line in zip(rows, lines[-len(rows):]) if "| — |" in line)
    miss = sum(1 for r, line in zip(rows, lines[-len(rows):]) if "✗" in line)
    lines.append("")
    lines.append(
        f"**Sign match summary:** ✓ {matches} sessions support hypothesis, "
        f"— {null} balanced/null, ✗ {miss} mismatch."
    )

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} ({len(rows)} sessions)")


if __name__ == "__main__":
    main()
