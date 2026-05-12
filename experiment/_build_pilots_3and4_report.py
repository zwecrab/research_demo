"""
Generate a markdown report for pilot batches 3 and 4 (18 sessions, Standard mode).

Output: experiment/pilots_3and4_report.md
"""
import json
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RATINGS_DIR = ROOT / "LLM_rater" / "ratings"
TR_DIR = ROOT / "transcripts"
OUT = ROOT / "experiment" / "pilots_3and4_report.md"


def load_severity():
    out = {}
    for f in sorted(RATINGS_DIR.glob("C*.json")):
        d = json.load(open(f, encoding="utf-8"))
        out[d["couple_id"]] = {
            "name_A": d["patient_A"]["name"].split()[0],
            "name_B": d["patient_B"]["name"].split()[0],
            "overall_A": d["patient_A"]["overall_score"],
            "overall_B": d["patient_B"]["overall_score"],
        }
    return out


def classify_fav(fas):
    if fas is None:
        return "—"
    if fas > 0.05:
        return "A"
    if fas < -0.05:
        return "B"
    return "Bal"


def severity_class(sa, sb):
    diff = sa - sb
    if diff > 0.5:
        return "A"
    if diff < -0.5:
        return "B"
    return "≈Bal"


def extract(path):
    d = json.load(open(path, encoding="utf-8"))
    em = d.get("experiment_metadata", {}) or {}
    tb = d.get("therapeutic_balance", {}) or {}
    fas = tb.get("fas") or {}
    brd = tb.get("brd") or {}
    cas = tb.get("cas") or {}
    return {
        "file": path.name,
        "batch": em.get("pilot_batch"),
        "couple": em.get("couple_id"),
        "position": em.get("position"),
        "bid_a": em.get("bid_style_a"),
        "bid_b": em.get("bid_style_b"),
        "cell": em.get("cell"),
        "structure": em.get("structure"),
        "mode": em.get("therapist_mode"),
        "fas": fas.get("fas_score"),
        "fas_vol": fas.get("fas_volume_adjusted"),
        "brd": brd.get("brd_score"),
        "cas": cas.get("cas_score"),
        "words_a": fas.get("words_a"),
        "words_b": fas.get("words_b"),
    }


def main():
    sev = load_severity()
    files = sorted(TR_DIR.glob("pilot4_*.json")) + sorted(TR_DIR.glob("pilot3_*.json"))
    rows = [extract(f) for f in files]

    lines = []
    lines.append("# Pilot Batches 3 + 4 — Sequential Structure & Standard Mode Validation\n")

    # Short summary
    lines.append(
        "18 sessions across two pilot batches, all using GPT-4o + therapist Standard mode "
        "(no individual_focus). **Pilot 4** (8 sessions) compared LLM-Based Selection vs "
        "Sequential structure on two strong-signal couples (C6 sev=+3.33, C2 sev=−2.83) at "
        "HH bid intensity. **Pilot 3** (10 sessions) tested Sequential structure across five "
        "couples spanning the severity range and varied bid cells. The goal was to validate "
        "the proposed final design (Standard mode + Sequential structure) against the pilot "
        "1+2 baseline (Standard mode missing, Individual Focus + LLM-Based used instead).\n"
    )
    lines.append(
        "Severity scores are from the LLM rater consensus (Claude Opus 4, Gemini 2.5 Pro, "
        "GPT-4o). The *Favored* column classifies on raw FAS sign (A if FAS > +0.05, B if "
        "< −0.05, Bal otherwise). The *More severe* column classifies on overall_A − "
        "overall_B (A if > +0.5, B if < −0.5, ≈Bal otherwise). *Match* = ✓ when *Favored* "
        "matches *More severe*.\n"
    )
    lines.append("Sign convention: FAS > 0 = A's frame adopted; BRD > 0 = B got deeper "
                 "responses; CAS > 0 = A challenged more.\n")

    # Per-session table
    header = (
        "| # | Batch | Pair | Pos | Struct | Bids | A (sev) | B (sev) | "
        "FAS | FAS-vol | BRD | CAS | wA | wB | More severe | Favored | Match |"
    )
    sep = "|" + "|".join(["---"] * 17) + "|"
    lines.append("## Per-session table\n")
    lines.append(header)
    lines.append(sep)

    for i, r in enumerate(rows, 1):
        c = r["couple"]
        s = sev.get(c, {})
        sa = s.get("overall_A", 0)
        sb = s.get("overall_B", 0)
        sev_more = severity_class(sa, sb)
        favored = classify_fav(r["fas"])
        match = "✓" if (sev_more == favored and sev_more not in ("≈Bal",)
                        and favored not in ("Bal", "—")) else \
                ("—" if sev_more == "≈Bal" or favored == "Bal" else "✗")
        struct_short = "Seq" if (r["structure"] or "").startswith("Sequential") else "LLM"
        a_label = f"{s.get('name_A','?')} ({sa:.2f})"
        b_label = f"{s.get('name_B','?')} ({sb:.2f})"
        fas_s = f"{r['fas']:+.3f}" if r['fas'] is not None else "—"
        fasv = f"{r['fas_vol']:+.3f}" if r['fas_vol'] is not None else "—"
        brd_s = f"{r['brd']:+.2f}" if r['brd'] is not None else "—"
        cas_s = f"{r['cas']:+d}" if r['cas'] is not None else "—"
        bids = f"{r['bid_a'][:3]}+{r['bid_b'][:3]}"
        lines.append(
            f"| {i} | {r['batch']} | {c} {r['cell']} | {r['position']} | {struct_short} | "
            f"{bids} | {a_label} | {b_label} | {fas_s} | {fasv} | {brd_s} | {cas_s} | "
            f"{r['words_a']} | {r['words_b']} | {sev_more} | {favored} | {match} |"
        )

    # Per-couple-structure aggregate (mean FAS by couple x structure)
    lines.append("\n## Couple × Structure aggregate (mean FAS across all sessions)\n")
    by_cs = {}
    for r in rows:
        key = (r["couple"], "LLM" if (r["structure"] or "").startswith("LLM") else "Seq")
        by_cs.setdefault(key, []).append(r)
    lines.append("| Couple | sev_diff | Structure | n | mean FAS | mean FAS-vol | mean wA | mean wB |")
    lines.append("|" + "|".join(["---"] * 8) + "|")
    for (c, struct), rs in sorted(by_cs.items()):
        s = sev[c]
        sd = s["overall_A"] - s["overall_B"]
        m_fas = mean(x["fas"] for x in rs if x["fas"] is not None)
        v_list = [x["fas_vol"] for x in rs if x["fas_vol"] is not None]
        m_v = mean(v_list) if v_list else float("nan")
        m_wa = mean(x["words_a"] for x in rs if x["words_a"] is not None)
        m_wb = mean(x["words_b"] for x in rs if x["words_b"] is not None)
        lines.append(f"| {c} | {sd:+.2f} | {struct} | {len(rs)} | "
                     f"{m_fas:+.3f} | {m_v:+.3f} | {m_wa:.0f} | {m_wb:.0f} |")

    # Severity-FAS correlation within pilots 3+4
    valid = [r for r in rows if r["fas"] is not None and r["couple"] in sev]
    xs = [sev[r["couple"]]["overall_A"] - sev[r["couple"]]["overall_B"] for r in valid]
    ys = [r["fas"] for r in valid]
    n = len(xs)
    if n >= 3:
        mx, my = mean(xs), mean(ys)
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        dx = sum((x - mx) ** 2 for x in xs) ** 0.5
        dy = sum((y - my) ** 2 for y in ys) ** 0.5
        r_pooled = num / (dx * dy) if (dx and dy) else float("nan")

    # Split by structure
    def corr_subset(subset):
        if len(subset) < 3:
            return None, len(subset)
        xs2 = [sev[r["couple"]]["overall_A"] - sev[r["couple"]]["overall_B"] for r in subset]
        ys2 = [r["fas"] for r in subset]
        mx2, my2 = mean(xs2), mean(ys2)
        num = sum((x - mx2) * (y - my2) for x, y in zip(xs2, ys2))
        dx = sum((x - mx2) ** 2 for x in xs2) ** 0.5
        dy = sum((y - my2) ** 2 for y in ys2) ** 0.5
        return (num / (dx * dy) if (dx and dy) else float("nan")), len(subset)

    seq_subset = [r for r in valid if (r["structure"] or "").startswith("Sequential")]
    llm_subset = [r for r in valid if not (r["structure"] or "").startswith("Sequential")]
    r_seq, n_seq = corr_subset(seq_subset)
    r_llm, n_llm = corr_subset(llm_subset)

    lines.append("\n## Severity-FAS correlation in this pilot\n")
    lines.append("| Slice | n | r(severity_diff, FAS) |")
    lines.append("|" + "|".join(["---"] * 3) + "|")
    lines.append(f"| All pilot 3+4 sessions | {n} | {r_pooled:+.3f} |")
    if r_llm is not None:
        lines.append(f"| LLM-Based Selection only | {n_llm} | {r_llm:+.3f} |")
    if r_seq is not None:
        lines.append(f"| Sequential only | {n_seq} | {r_seq:+.3f} |")

    # Counts
    matches_count = 0
    null_count = 0
    miss_count = 0
    for i, r in enumerate(rows):
        c = r["couple"]
        s = sev.get(c, {})
        sa = s.get("overall_A", 0)
        sb = s.get("overall_B", 0)
        sev_more = severity_class(sa, sb)
        favored = classify_fav(r["fas"])
        if sev_more == "≈Bal" or favored == "Bal":
            null_count += 1
        elif sev_more == favored:
            matches_count += 1
        else:
            miss_count += 1

    lines.append(
        f"\n**Sign-match summary across {len(rows)} sessions:** "
        f"✓ {matches_count} support hypothesis, — {null_count} balanced/null, "
        f"✗ {miss_count} mismatch."
    )

    # Honest narrative
    lines.append("\n## Key findings\n")
    lines.append(
        "1. **Sequential structure has couple-specific effects.** On C6 (sev=+3.33), "
        "Sequential collapses the severity-FAS magnitude from +0.270 (LLM) to ~+0.05 "
        "with high per-session variance. On C4 (sev=+2.93), Sequential *amplifies* "
        "FAS from +0.174 (LLM, prior pilot) to +0.400. On C2 (sev=−2.83), Sequential "
        "preserves the effect (−0.300 vs LLM −0.220). Sequential is not a uniform "
        "improvement.\n"
    )
    lines.append(
        "2. **Standard mode preserves the severity-FAS link** observed under "
        "Individual Focus, with comparable or slightly smaller magnitudes. The "
        "advisor-preferred mode is viable.\n"
    )
    lines.append(
        "3. **Position bias becomes detectable when severity is near zero.** C7 HL "
        "Sequential pair (sev=+0.35, asymmetric bid) showed α=−0.300 / β=+0.300, "
        "Δ(α−β)=−0.600 — a strong within-pair position swing on a near-balanced "
        "couple. This supports RQ4 (residual position bias detectable after "
        "controlling for severity).\n"
    )
    lines.append(
        "4. **C9 LL Sequential produced two consecutive sign-mismatches** "
        "(α=+0.100, β=+0.100 against sev=−0.83). Both essentially in the noise "
        "floor (|FAS| ≤ 0.10). Likely indicates that mild |severity_diff| (<1.0) "
        "is below the detection threshold under Sequential structure.\n"
    )
    lines.append(
        "5. **Word-volume parity is enforced under Sequential** (e.g., C2 HH Seq α: "
        "wA=347, wB=347 exactly), removing volume as a confounding variable. "
        "Volume-adjusted FAS is therefore numerically closer to raw FAS in "
        "Sequential than in LLM-Based runs.\n"
    )

    lines.append("\n## Implications for final design\n")
    lines.append(
        "- **LLM-Based Selection should remain the primary structure**, not Sequential, "
        "because Sequential's couple-specific suppression (most clearly on C6) introduces "
        "between-couple heterogeneity that complicates RQ1 power calculations.\n"
        "- Sequential is still valuable as a **robustness check** on a subset of "
        "couples — specifically to demonstrate that the volume-confound interpretation "
        "is not the whole story (since Sequential equalises words and the effect "
        "still appears on C2 and C4).\n"
        "- **Standard mode is locked** as the primary therapist mode, replacing the "
        "individual_focus used in earlier pilots.\n"
        "- C7 HL Seq's position swing supports keeping RQ4 in the final design with "
        "an expectation of detectable residual position effect at near-balanced |sev|.\n"
    )

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} ({len(rows)} sessions)")


if __name__ == "__main__":
    main()
