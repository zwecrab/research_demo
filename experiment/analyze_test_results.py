"""
Test Experiment Analysis
========================
Quantitative analysis of the Llama 8B + 70B test experiment.

Three analyses:
  1. Position effect: alpha vs beta (paired deltas, sign consistency)
  2. Bid-style pairing: per-cell metric comparison
  3. Model comparison: Llama 8B vs 70B

Usage:
    python experiment/analyze_test_results.py
    python experiment/analyze_test_results.py --max-cell 7   # only cells 1-7
"""

import json
import glob
import os
import sys
from pathlib import Path
from collections import defaultdict
import argparse

EXPERIMENT_DIR = Path(__file__).parent
TRANSCRIPT_DIR = EXPERIMENT_DIR / "transcripts"

# Cell metadata (must match run_test_experiment.py)
CELL_META = {
    1: {"a_bid": "aggressive", "b_bid": "aggressive", "label": "Aggr+Aggr"},
    2: {"a_bid": "aggressive", "b_bid": "assertive",  "label": "Aggr+Assert"},
    3: {"a_bid": "aggressive", "b_bid": "passive",    "label": "Aggr+Pass"},
    4: {"a_bid": "assertive",  "b_bid": "aggressive",  "label": "Assert+Aggr"},
    5: {"a_bid": "assertive",  "b_bid": "assertive",   "label": "Assert+Assert"},
    6: {"a_bid": "assertive",  "b_bid": "passive",     "label": "Assert+Pass"},
    7: {"a_bid": "passive",    "b_bid": "aggressive",   "label": "Pass+Aggr"},
    8: {"a_bid": "passive",    "b_bid": "assertive",    "label": "Pass+Assert"},
    9: {"a_bid": "passive",    "b_bid": "passive",      "label": "Pass+Pass"},
}


def load_transcript(filepath):
    """Load a transcript JSON and extract key metrics."""
    with open(filepath, encoding="utf-8") as f:
        d = json.load(f)

    tb = d.get("therapeutic_balance", {})
    fas_obj = tb.get("fas", {})
    brd_obj = tb.get("brd", {})
    cas_obj = tb.get("cas", {})

    # TA: handle dict-based 'overall'
    ta_obj = d.get("therapist_alliance", {})
    if isinstance(ta_obj, dict):
        ta_overall = ta_obj.get("overall", {})
        if isinstance(ta_overall, dict):
            ta = ta_overall.get("score", None)
        else:
            ta = ta_overall
    else:
        ta = None

    # PANAS: list of 20 items with before/after/difference
    def calc_panas(panas_data):
        if not isinstance(panas_data, list) or len(panas_data) == 0:
            return None
        return sum(item.get("difference", 0) for item in panas_data if isinstance(item, dict))

    # Parse filename for metadata
    fname = Path(filepath).stem
    parts = fname.split("_")
    cell_num = int(parts[1].replace("cell", ""))
    model = parts[2]
    position = parts[3]

    return {
        "file": fname,
        "cell": cell_num,
        "model": model,
        "position": position,
        "fas": fas_obj.get("fas_score"),
        "brd": brd_obj.get("brd_score"),
        "cas": cas_obj.get("cas_score"),
        "fas_count_a": fas_obj.get("count_a", 0),
        "fas_count_b": fas_obj.get("count_b", 0),
        "fas_count_n": fas_obj.get("count_neutral", 0),
        "brd_depth_a": brd_obj.get("mean_depth_a"),
        "brd_depth_b": brd_obj.get("mean_depth_b"),
        "cas_to_a": cas_obj.get("challenges_to_a", 0),
        "cas_to_b": cas_obj.get("challenges_to_b", 0),
        "ta": ta,
        "panas_a": calc_panas(d.get("Patient_A_PANAS_DELTA")),
        "panas_b": calc_panas(d.get("Patient_B_PANAS_DELTA")),
        "turns": len(d.get("session_transcript", [])),
    }


def load_all(max_cell=9):
    """Load all transcripts up to max_cell."""
    records = []
    for f in sorted(TRANSCRIPT_DIR.glob("test_cell*.json")):
        rec = load_transcript(f)
        if rec["cell"] <= max_cell:
            records.append(rec)
    return records


def mean(values):
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def fmt(val, decimals=3):
    if val is None:
        return "  N/A"
    return f"{val:+.{decimals}f}" if isinstance(val, float) else f"{val:+d}"


def sign(val):
    if val is None:
        return "?"
    if val > 0:
        return "+"
    elif val < 0:
        return "-"
    return "0"


# ==========================================================================
# ANALYSIS 1: Position Effect (Alpha vs Beta)
# ==========================================================================

def analyze_position(records):
    """Compare alpha (A-first) vs beta (B-first) and compute paired deltas."""
    print("\n" + "=" * 80)
    print("  ANALYSIS 1: POSITION EFFECT (Alpha vs Beta)")
    print("  Does speaking first create measurable bias in therapist behavior?")
    print("=" * 80)

    # Group into swapped pairs: (cell, model) -> {alpha: rec, beta: rec}
    pairs = defaultdict(dict)
    for r in records:
        pairs[(r["cell"], r["model"])][r["position"]] = r

    # Compute deltas for complete pairs
    deltas = []
    print(f"\n  {'Pair':<25} {'FAS_a':>7} {'FAS_b':>7} {'D_FAS':>7} {'BRD_a':>7} {'BRD_b':>7} {'D_BRD':>7} {'CAS_a':>7} {'CAS_b':>7} {'D_CAS':>7}")
    print(f"  {'-'*25} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7}")

    for (cell, model), pos_dict in sorted(pairs.items()):
        if "alpha" not in pos_dict or "beta" not in pos_dict:
            continue
        a = pos_dict["alpha"]
        b = pos_dict["beta"]

        d_fas = (a["fas"] - b["fas"]) if a["fas"] is not None and b["fas"] is not None else None
        d_brd = (a["brd"] - b["brd"]) if a["brd"] is not None and b["brd"] is not None else None
        d_cas = (a["cas"] - b["cas"]) if a["cas"] is not None and b["cas"] is not None else None

        label = f"Cell {cell} {model}"
        meta = CELL_META.get(cell, {})
        bid_label = meta.get("label", "?")

        deltas.append({
            "cell": cell, "model": model, "bid_label": bid_label,
            "fas_alpha": a["fas"], "fas_beta": b["fas"], "d_fas": d_fas,
            "brd_alpha": a["brd"], "brd_beta": b["brd"], "d_brd": d_brd,
            "cas_alpha": a["cas"], "cas_beta": b["cas"], "d_cas": d_cas,
        })

        print(f"  {label:<25} {fmt(a['fas']):>7} {fmt(b['fas']):>7} {fmt(d_fas):>7} "
              f"{fmt(a['brd']):>7} {fmt(b['brd']):>7} {fmt(d_brd):>7} "
              f"{fmt(a['cas']):>7} {fmt(b['cas']):>7} {fmt(d_cas):>7}")

    if not deltas:
        print("  No complete pairs found.")
        return deltas

    # Aggregate statistics
    d_fas_vals = [d["d_fas"] for d in deltas if d["d_fas"] is not None]
    d_brd_vals = [d["d_brd"] for d in deltas if d["d_brd"] is not None]
    d_cas_vals = [d["d_cas"] for d in deltas if d["d_cas"] is not None]

    print(f"\n  {'SUMMARY':=<80}")
    print(f"  Complete pairs: {len(deltas)}")
    print(f"\n  {'Metric':<12} {'Mean Delta':>12} {'Median':>10} {'Positive':>10} {'Negative':>10} {'Zero':>8} {'Sign Rate':>12}")
    print(f"  {'-'*12} {'-'*12} {'-'*10} {'-'*10} {'-'*10} {'-'*8} {'-'*12}")

    for name, vals in [("DELTA_FAS", d_fas_vals), ("DELTA_BRD", d_brd_vals), ("DELTA_CAS", d_cas_vals)]:
        if not vals:
            continue
        m = sum(vals) / len(vals)
        sorted_vals = sorted(vals)
        n = len(sorted_vals)
        median = sorted_vals[n // 2] if n % 2 == 1 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
        pos = sum(1 for v in vals if v > 0)
        neg = sum(1 for v in vals if v < 0)
        zero = sum(1 for v in vals if v == 0)
        rate = pos / len(vals) * 100 if vals else 0
        print(f"  {name:<12} {m:>+12.4f} {median:>+10.4f} {pos:>10d} {neg:>10d} {zero:>8d} {rate:>10.1f}%")

    # Interpretation
    print(f"\n  INTERPRETATION:")
    if d_fas_vals:
        fas_mean = sum(d_fas_vals) / len(d_fas_vals)
        fas_pos = sum(1 for v in d_fas_vals if v > 0)
        fas_rate = fas_pos / len(d_fas_vals) * 100
        if fas_rate > 60:
            print(f"  - FAS: {fas_rate:.0f}% of pairs show positive DELTA_FAS (first speaker framing advantage)")
        elif fas_rate < 40:
            print(f"  - FAS: {fas_rate:.0f}% positive (reverse pattern, second speaker advantage)")
        else:
            print(f"  - FAS: {fas_rate:.0f}% positive (no consistent position effect on framing)")
        print(f"    Mean DELTA_FAS = {fas_mean:+.4f} (0 = no bias, +1 = full A-advantage)")

    if d_brd_vals:
        brd_mean = sum(d_brd_vals) / len(d_brd_vals)
        print(f"  - BRD: Mean DELTA_BRD = {brd_mean:+.4f} (positive = deeper response to first speaker)")

    if d_cas_vals:
        cas_mean = sum(d_cas_vals) / len(d_cas_vals)
        print(f"  - CAS: Mean DELTA_CAS = {cas_mean:+.4f} (positive = more challenges to first speaker)")

    return deltas


# ==========================================================================
# ANALYSIS 2: Bid-Style Pairing
# ==========================================================================

def analyze_bid_style(records, deltas):
    """Group metrics by bid-style pairing."""
    print("\n" + "=" * 80)
    print("  ANALYSIS 2: BID-STYLE PAIRING EFFECT")
    print("  Does persona bid-style intensity moderate position bias?")
    print("=" * 80)

    # Group deltas by bid_label
    by_bid = defaultdict(list)
    for d in deltas:
        by_bid[d["bid_label"]].append(d)

    # Group raw sessions by bid style
    raw_by_bid = defaultdict(list)
    for r in records:
        meta = CELL_META.get(r["cell"], {})
        raw_by_bid[meta.get("label", "?")].append(r)

    bid_order = ["Aggr+Aggr", "Aggr+Assert", "Aggr+Pass",
                 "Assert+Aggr", "Assert+Assert", "Assert+Pass",
                 "Pass+Aggr", "Pass+Assert", "Pass+Pass"]

    # Table: raw means by position
    print(f"\n  Raw metric means by bid-style and position:")
    print(f"  {'Bid Pair':<16} {'n':>3} {'FAS_a':>8} {'FAS_b':>8} {'BRD_a':>8} {'BRD_b':>8} {'CAS_a':>8} {'CAS_b':>8}")
    print(f"  {'-'*16} {'-'*3} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")

    for bid in bid_order:
        sessions = raw_by_bid.get(bid, [])
        if not sessions:
            continue
        alphas = [s for s in sessions if s["position"] == "alpha"]
        betas = [s for s in sessions if s["position"] == "beta"]
        n = len(sessions)
        fas_a = mean([s["fas"] for s in alphas])
        fas_b = mean([s["fas"] for s in betas])
        brd_a = mean([s["brd"] for s in alphas])
        brd_b = mean([s["brd"] for s in betas])
        cas_a = mean([s["cas"] for s in alphas])
        cas_b = mean([s["cas"] for s in betas])
        print(f"  {bid:<16} {n:>3} {fmt(fas_a):>8} {fmt(fas_b):>8} {fmt(brd_a):>8} {fmt(brd_b):>8} {fmt(cas_a):>8} {fmt(cas_b):>8}")

    # Paired deltas by bid style
    print(f"\n  Paired deltas (alpha - beta) by bid-style:")
    print(f"  {'Bid Pair':<16} {'Pairs':>5} {'D_FAS':>8} {'D_BRD':>8} {'D_CAS':>8} {'FAS Sign':>10}")
    print(f"  {'-'*16} {'-'*5} {'-'*8} {'-'*8} {'-'*8} {'-'*10}")

    for bid in bid_order:
        ds = by_bid.get(bid, [])
        if not ds:
            continue
        d_fas = mean([d["d_fas"] for d in ds])
        d_brd = mean([d["d_brd"] for d in ds])
        d_cas = mean([d["d_cas"] for d in ds])
        signs = "".join(sign(d["d_fas"]) for d in ds)
        print(f"  {bid:<16} {len(ds):>5} {fmt(d_fas):>8} {fmt(d_brd):>8} {fmt(d_cas):>8} {signs:>10}")

    # Symmetric vs asymmetric
    print(f"\n  SYMMETRIC CELLS (same bid-style both sides, pure positional effect):")
    symmetric = ["Aggr+Aggr", "Assert+Assert", "Pass+Pass"]
    sym_deltas = [d for d in deltas if d["bid_label"] in symmetric]
    if sym_deltas:
        d_fas = mean([d["d_fas"] for d in sym_deltas])
        d_brd = mean([d["d_brd"] for d in sym_deltas])
        print(f"    Mean DELTA_FAS = {fmt(d_fas)} (n={len(sym_deltas)} pairs)")
        print(f"    Mean DELTA_BRD = {fmt(d_brd)}")
        signs = "".join(sign(d["d_fas"]) for d in sym_deltas)
        print(f"    FAS signs: {signs}")

    print(f"\n  ASYMMETRIC CELLS (different bid-styles, persona dominance may override):")
    asym_deltas = [d for d in deltas if d["bid_label"] not in symmetric]
    if asym_deltas:
        d_fas = mean([d["d_fas"] for d in asym_deltas])
        d_brd = mean([d["d_brd"] for d in asym_deltas])
        print(f"    Mean DELTA_FAS = {fmt(d_fas)} (n={len(asym_deltas)} pairs)")
        print(f"    Mean DELTA_BRD = {fmt(d_brd)}")
        signs = "".join(sign(d["d_fas"]) for d in asym_deltas)
        print(f"    FAS signs: {signs}")

    # A-bid-style grouping
    print(f"\n  A-AGGRESSIVE (Patient A has aggressive bid-style):")
    a_aggr = [d for d in deltas if d["bid_label"].startswith("Aggr")]
    if a_aggr:
        d_fas = mean([d["d_fas"] for d in a_aggr])
        print(f"    Mean DELTA_FAS = {fmt(d_fas)} (n={len(a_aggr)})")
        signs = "".join(sign(d["d_fas"]) for d in a_aggr)
        print(f"    FAS signs: {signs}")

    print(f"\n  A-PASSIVE (Patient A has passive bid-style):")
    a_pass = [d for d in deltas if d["bid_label"].startswith("Pass")]
    if a_pass:
        d_fas = mean([d["d_fas"] for d in a_pass])
        print(f"    Mean DELTA_FAS = {fmt(d_fas)} (n={len(a_pass)})")
        signs = "".join(sign(d["d_fas"]) for d in a_pass)
        print(f"    FAS signs: {signs}")


# ==========================================================================
# ANALYSIS 3: Model Comparison (8B vs 70B)
# ==========================================================================

def analyze_model(records, deltas):
    """Compare Llama 8B vs 70B."""
    print("\n" + "=" * 80)
    print("  ANALYSIS 3: MODEL COMPARISON (Llama 8B vs 70B)")
    print("  Does model scale influence bias patterns?")
    print("=" * 80)

    by_model = defaultdict(list)
    for r in records:
        by_model[r["model"]].append(r)

    print(f"\n  Raw metric means by model:")
    print(f"  {'Model':<12} {'n':>4} {'FAS':>8} {'|FAS|':>8} {'BRD':>8} {'|BRD|':>8} {'CAS':>8} {'|CAS|':>8} {'TA':>6}")
    print(f"  {'-'*12} {'-'*4} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*6}")

    for model in ["llama8b", "llama70b"]:
        sessions = by_model.get(model, [])
        if not sessions:
            continue
        fas_vals = [s["fas"] for s in sessions if s["fas"] is not None]
        brd_vals = [s["brd"] for s in sessions if s["brd"] is not None]
        cas_vals = [s["cas"] for s in sessions if s["cas"] is not None]
        ta_vals = [s["ta"] for s in sessions if s["ta"] is not None and s["ta"] != 0]

        m_fas = mean(fas_vals)
        m_abs_fas = mean([abs(v) for v in fas_vals]) if fas_vals else None
        m_brd = mean(brd_vals)
        m_abs_brd = mean([abs(v) for v in brd_vals]) if brd_vals else None
        m_cas = mean(cas_vals)
        m_abs_cas = mean([abs(v) for v in cas_vals]) if cas_vals else None
        m_ta = mean(ta_vals)

        print(f"  {model:<12} {len(sessions):>4} {fmt(m_fas):>8} {fmt(m_abs_fas):>8} "
              f"{fmt(m_brd):>8} {fmt(m_abs_brd):>8} "
              f"{fmt(m_cas):>8} {fmt(m_abs_cas):>8} {fmt(m_ta, 1):>6}")

    # Delta comparison by model
    deltas_8b = [d for d in deltas if d["model"] == "llama8b"]
    deltas_70b = [d for d in deltas if d["model"] == "llama70b"]

    print(f"\n  Paired deltas by model:")
    print(f"  {'Model':<12} {'Pairs':>5} {'D_FAS':>8} {'|D_FAS|':>9} {'D_BRD':>8} {'D_CAS':>8} {'FAS+':>6}")
    print(f"  {'-'*12} {'-'*5} {'-'*8} {'-'*9} {'-'*8} {'-'*8} {'-'*6}")

    for label, ds in [("llama8b", deltas_8b), ("llama70b", deltas_70b)]:
        if not ds:
            continue
        d_fas = mean([d["d_fas"] for d in ds])
        d_abs_fas = mean([abs(d["d_fas"]) for d in ds if d["d_fas"] is not None])
        d_brd = mean([d["d_brd"] for d in ds])
        d_cas = mean([d["d_cas"] for d in ds])
        pos = sum(1 for d in ds if d["d_fas"] is not None and d["d_fas"] > 0)
        print(f"  {label:<12} {len(ds):>5} {fmt(d_fas):>8} {fmt(d_abs_fas):>9} {fmt(d_brd):>8} {fmt(d_cas):>8} {pos:>4}/{len(ds)}")

    # Flag anomalies
    print(f"\n  ANOMALY CHECK:")
    found_anomaly = False
    for r in records:
        issues = []
        if r["ta"] is not None and r["ta"] == 0:
            issues.append("TA=0 (scoring failure)")
        if r["fas"] is not None and abs(r["fas"]) > 0.8:
            issues.append(f"extreme FAS={r['fas']}")
        if r["brd"] is not None and abs(r["brd"]) > 4.0:
            issues.append(f"extreme BRD={r['brd']}")
        if r["cas"] is not None and abs(r["cas"]) > 10:
            issues.append(f"extreme CAS={r['cas']}")
        if issues:
            found_anomaly = True
            print(f"    {r['file']}: {', '.join(issues)}")
    if not found_anomaly:
        print(f"    None found.")


# ==========================================================================
# MAIN
# ==========================================================================

def main():
    parser = argparse.ArgumentParser(description="Analyze test experiment results")
    parser.add_argument("--max-cell", type=int, default=9, help="Only include cells up to this number")
    args = parser.parse_args()

    records = load_all(max_cell=args.max_cell)
    if not records:
        print("No transcripts found.")
        return

    print(f"\n  Loaded {len(records)} sessions (cells 1-{args.max_cell})")
    print(f"  Models: {sorted(set(r['model'] for r in records))}")
    print(f"  Cells: {sorted(set(r['cell'] for r in records))}")

    deltas = analyze_position(records)
    analyze_bid_style(records, deltas)
    analyze_model(records, deltas)

    print("\n" + "=" * 80)
    print("  ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
