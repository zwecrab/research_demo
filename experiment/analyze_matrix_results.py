"""
Matrix Experiment Analysis
==========================
Analyzes v2 matrix sessions from `transcripts/therapy_transcript_*.json`,
reading the `metrics_summary` block that `output_manager.build_metrics_summary()`
writes at the top of each file.

Reports means, SDs, ranges, and absolute magnitudes (spread) for every metric.
Groups by any `session_metadata` field (therapist_mode by default) so Standard
vs Individual Focus contrasts are directly visible.

Usage:
    python experiment/analyze_matrix_results.py                      # all couples
    python experiment/analyze_matrix_results.py --couple C2          # filter
    python experiment/analyze_matrix_results.py --group-by structure # alt group
    python experiment/analyze_matrix_results.py --last 36            # recent N

The script is deliberately read-only: it will not touch transcripts and does
not depend on any runtime module beyond the Python standard library.
"""

import argparse
import glob
import json
import os
import statistics as st
from collections import defaultdict
from pathlib import Path

DEFAULT_TRANSCRIPT_GLOB = "transcripts/therapy_transcript_*.json"
METRIC_KEYS = ["fas", "brd", "cas", "ta", "panas_a", "panas_b", "panas_couple"]


def load_matrix_records(glob_path, only_matrix_flag=True, last_n=None, couple=None):
    files = sorted(glob.glob(glob_path), key=os.path.getmtime)
    if last_n:
        files = files[-last_n:]
    records = []
    for path in files:
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            continue
        em = data.get("experiment_metadata") or {}
        ms = data.get("metrics_summary") or {}
        if only_matrix_flag and not em.get("matrix_run"):
            continue
        sm = ms.get("session_metadata") or {}
        couple_id = em.get("couple_id") or sm.get("couple_id")
        if couple and couple_id != couple:
            continue
        fas = (ms.get("fas") or {}).get("score")
        if fas is None:
            continue
        rec = {
            "file": os.path.basename(path),
            "couple": couple_id,
            "position": em.get("position") or sm.get("position"),
            "bid_a": em.get("bid_style_a") or sm.get("bid_style_a"),
            "bid_b": em.get("bid_style_b") or sm.get("bid_style_b"),
            "therapist_mode": em.get("therapist_mode") or sm.get("therapist_mode"),
            "structure": em.get("structure") or sm.get("structure"),
            "therapist_model": em.get("therapist_model") or sm.get("therapist_model"),
            "fas": fas,
            "brd": (ms.get("brd") or {}).get("score"),
            "cas": (ms.get("cas") or {}).get("score"),
            "ta": (ms.get("therapeutic_alliance") or {}).get("overall"),
            "panas_a": (ms.get("panas_patient_a") or {}).get("net_change"),
            "panas_b": (ms.get("panas_patient_b") or {}).get("net_change"),
            "panas_couple": ms.get("panas_couple_net"),
        }
        records.append(rec)
    return records


def summary_row(values):
    vals = [v for v in values if isinstance(v, (int, float))]
    if not vals:
        return {"n": 0}
    mean = st.mean(vals)
    sd = st.pstdev(vals) if len(vals) > 1 else 0.0
    abs_vals = [abs(v) for v in vals]
    return {
        "n": len(vals),
        "mean": mean,
        "sd": sd,
        "min": min(vals),
        "max": max(vals),
        "abs_mean": st.mean(abs_vals),
        "abs_max": max(abs_vals),
    }


def print_group_summary(records, group_by):
    groups = defaultdict(list)
    for r in records:
        groups[r.get(group_by)].append(r)

    header_groups = sorted(groups.keys(), key=lambda x: (x is None, str(x)))
    print(f"\n{'='*92}")
    print(f"  GROUP-BY: {group_by}")
    print(f"{'='*92}")

    col_fmt = f"  {{:<14}} {{:>4}} {{:>9}} {{:>8}} {{:>8}} {{:>8}} {{:>9}} {{:>9}}"
    print(col_fmt.format("metric", "n", "mean", "sd", "min", "max", "|mean|", "|max|"))
    print("  " + "-" * 82)

    for group_key in header_groups:
        group_recs = groups[group_key]
        label = group_key if group_key is not None else "(unset)"
        print(f"\n  --- {group_by} = {label}  (n_sessions={len(group_recs)}) ---")
        for metric in METRIC_KEYS:
            vals = [r[metric] for r in group_recs]
            s = summary_row(vals)
            if s["n"] == 0:
                continue
            print(col_fmt.format(
                metric, s["n"],
                f"{s['mean']:+.2f}",
                f"{s['sd']:.2f}",
                f"{s['min']:+.1f}",
                f"{s['max']:+.1f}",
                f"{s['abs_mean']:.2f}",
                f"{s['abs_max']:.1f}",
            ))


def print_paired_deltas(records, group_by):
    """Paired (beta - alpha) deltas per (group, bid_a, bid_b) cell."""
    print(f"\n{'='*92}")
    print(f"  PAIRED DELTAS (beta minus alpha) grouped by {group_by} x bid-combo")
    print(f"{'='*92}")

    # key = (group_value, bid_a, bid_b), val = {alpha: rec, beta: rec}
    pairs = defaultdict(dict)
    for r in records:
        key = (r.get(group_by), r["bid_a"], r["bid_b"])
        pairs[key][r["position"]] = r

    # Per group, accumulate delta values for summary
    group_deltas = defaultdict(lambda: defaultdict(list))

    last_group = object()
    for key in sorted(pairs.keys(), key=lambda k: (str(k[0]), str(k[1]), str(k[2]))):
        g, ba, bb = key
        pd = pairs[key]
        if "alpha" not in pd or "beta" not in pd:
            continue
        a, b = pd["alpha"], pd["beta"]
        if g != last_group:
            print(f"\n  --- {group_by} = {g} ---")
            print(f"  {'bid_A':<12} {'bid_B':<12} {'dFAS':>7} {'dBRD':>7} {'dCAS':>5} "
                  f"{'dTA':>6} {'dPAN_A':>8} {'dPAN_B':>8}")
            last_group = g
        def d(k):
            av, bv = a.get(k), b.get(k)
            if av is None or bv is None:
                return None
            return bv - av
        deltas_row = {m: d(m) for m in METRIC_KEYS}
        for m, v in deltas_row.items():
            if v is not None:
                group_deltas[g][m].append(v)
        print(f"  {ba:<12} {bb:<12} "
              f"{deltas_row['fas']:+.2f}" if deltas_row['fas'] is not None else f"  {ba:<12} {bb:<12}   N/A",
              end="")
        # Finish the row manually for robustness
        tail = (
            f"  {deltas_row['brd']:+7.2f}" if deltas_row['brd'] is not None else "     N/A",
            f"  {deltas_row['cas']:+5d}" if isinstance(deltas_row['cas'], int) else
                (f"  {deltas_row['cas']:+5.1f}" if deltas_row['cas'] is not None else "   N/A"),
            f"  {deltas_row['ta']:+6.2f}" if deltas_row['ta'] is not None else "    N/A",
            f"  {deltas_row['panas_a']:+8.1f}" if deltas_row['panas_a'] is not None else "     N/A",
            f"  {deltas_row['panas_b']:+8.1f}" if deltas_row['panas_b'] is not None else "     N/A",
        )
        print(*tail, sep="")

    # Group-level mean absolute delta (spread proxy)
    print(f"\n{'='*92}")
    print(f"  GROUP SPREAD: mean |delta| and max |delta| per metric")
    print(f"{'='*92}")
    print(f"  {'group':<20} {'metric':<10} {'n':>4} {'mean |d|':>10} {'max |d|':>10} {'mean d':>10}")
    print("  " + "-" * 74)
    for g, mm in group_deltas.items():
        for metric in METRIC_KEYS:
            vals = mm.get(metric, [])
            if not vals:
                continue
            avals = [abs(v) for v in vals]
            print(f"  {str(g):<20} {metric:<10} {len(vals):>4} "
                  f"{st.mean(avals):>10.3f} {max(avals):>10.2f} {st.mean(vals):>+10.3f}")


def print_cross_group_contrast(records, group_by):
    """If group_by has exactly 2 levels, print |metric|-spread contrast."""
    levels = sorted({r.get(group_by) for r in records if r.get(group_by) is not None})
    if len(levels) != 2:
        return
    print(f"\n{'='*92}")
    print(f"  SPREAD CONTRAST: {levels[0]} vs {levels[1]}")
    print(f"{'='*92}")
    print(f"  {'metric':<12} {'|mean| '+str(levels[0]):<18} {'|mean| '+str(levels[1]):<18} {'ratio':>8}")
    print("  " + "-" * 60)
    for metric in METRIC_KEYS:
        by_level = {lvl: [] for lvl in levels}
        for r in records:
            if r.get(group_by) in by_level and r[metric] is not None:
                by_level[r.get(group_by)].append(abs(r[metric]))
        m0 = st.mean(by_level[levels[0]]) if by_level[levels[0]] else None
        m1 = st.mean(by_level[levels[1]]) if by_level[levels[1]] else None
        if m0 is None or m1 is None:
            continue
        ratio = (m1 / m0) if m0 > 0 else float("inf")
        print(f"  {metric:<12} {m0:<18.3f} {m1:<18.3f} {ratio:>8.2f}")


def main():
    ap = argparse.ArgumentParser(description="Matrix experiment analyzer (spread-aware)")
    ap.add_argument("--glob", default=DEFAULT_TRANSCRIPT_GLOB,
                    help="Glob pattern for transcript files")
    ap.add_argument("--last", type=int, default=None,
                    help="Only consider the last N files by mtime")
    ap.add_argument("--couple", default=None,
                    help="Filter by couple_id (e.g. C2)")
    ap.add_argument("--group-by", default="therapist_mode",
                    choices=["therapist_mode", "structure", "therapist_model",
                             "couple", "position"],
                    help="Metadata field to stratify by")
    ap.add_argument("--no-matrix-filter", action="store_true",
                    help="Include non-matrix runs too")
    args = ap.parse_args()

    os.chdir(Path(__file__).parent.parent)  # run relative to repo root
    records = load_matrix_records(
        args.glob,
        only_matrix_flag=not args.no_matrix_filter,
        last_n=args.last,
        couple=args.couple,
    )
    if not records:
        print("No records matched the filters.")
        return

    print(f"\nLoaded {len(records)} sessions")
    print(f"  Couples: {sorted({r['couple'] for r in records if r['couple']})}")
    print(f"  Modes: {sorted({r['therapist_mode'] for r in records if r['therapist_mode']})}")
    print(f"  Models: {sorted({r['therapist_model'] for r in records if r['therapist_model']})}")

    print_group_summary(records, args.group_by)
    print_paired_deltas(records, args.group_by)
    print_cross_group_contrast(records, args.group_by)


if __name__ == "__main__":
    main()
