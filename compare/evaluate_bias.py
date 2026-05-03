"""
Position Bias Evaluation Framework
===================================
Compares PANAS emotional trajectories across position-swapped session pairs
to characterize the effect of speaking order on patient outcomes.

For each patient, PANAS deltas (post - pre) are extracted from both conditions
(speaking first vs. speaking second) and compared side-by-side.

DEPRECATED FIELDS (advisor decision, 2026-03-05): the report dict still contains
`spdi`, `pcr`, `overall_pcr`, and `overall_spdi_magnitude` keys with zero/empty
placeholder values. These metrics were removed from the active analysis pipeline.
The keys are retained ONLY for backward compatibility with the Streamlit demo
DB (`app/experiments_db.py` reads `overall_pcr` and `overall_spdi_magnitude`).
Active research uses FAS / BRD / CAS / TA / PANAS Delta only.

Usage:
    python evaluate_bias.py
    python evaluate_bias.py --t1 T1.json --t2 T2.json
"""

import json
import argparse
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

# Transcripts: same personas, swapped speaker order
T_A_FIRST = "../transcripts/therapy_transcript_21.json"   # Patient A speaks first
T_B_FIRST = "../transcripts/therapy_transcript_22.json"   # Patient B speaks first

# PANAS emotion categories
POSITIVE_AFFECT = [
    "Interested", "Excited", "Strong", "Enthusiastic", "Proud",
    "Alert", "Inspired", "Determined", "Attentive", "Active"
]
NEGATIVE_AFFECT = [
    "Distressed", "Upset", "Guilty", "Scared", "Hostile",
    "Irritable", "Ashamed", "Nervous", "Jittery", "Afraid"
]
ALL_EMOTIONS = POSITIVE_AFFECT + NEGATIVE_AFFECT


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def load_transcript(filepath):
    """Load and return a transcript JSON."""
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def extract_deltas(transcript, role_key):
    """Extract PANAS delta dict {emotion: (before, after, delta)} for a role."""
    delta_list = transcript.get(f"{role_key}_PANAS_DELTA", [])
    result = {}
    for entry in delta_list:
        feeling = entry["feeling"]
        before = entry["before_score"]
        after = entry["after_score"]
        result[feeling] = {
            "before": before,
            "after": after,
            "delta": after - before
        }
    return result


def aggregate_panas(deltas, emotion_list):
    """Compute sum of deltas for a subset of emotions."""
    return sum(deltas.get(e, {}).get("delta", 0) for e in emotion_list)


# ============================================================================
# REPORT GENERATION
# ============================================================================

def print_header(text, char="=", width=90):
    print(f"\n{char * width}")
    print(f"  {text}")
    print(f"{char * width}")


def print_delta_table(deltas_first, deltas_second, label):
    """Print per-emotion delta comparison table."""
    print(f"\n  {label}")
    print(f"  {'Emotion':<15} {'When First':>10} {'When Second':>11} {'Diff':>6}")
    print(f"  {'-'*15} {'-'*10} {'-'*11} {'-'*6}")

    for emotion in ALL_EMOTIONS:
        d_first = deltas_first.get(emotion, {}).get("delta")
        d_second = deltas_second.get(emotion, {}).get("delta")
        if d_first is not None and d_second is not None:
            diff = d_first - d_second
            flag = " *" if abs(diff) > 1 else ""
            print(f"  {emotion:<15} {d_first:>+10d} {d_second:>+11d} {diff:>+6d}{flag}")


# ============================================================================
# REPORT GENERATION API
# ============================================================================

def generate_evaluation_report(t1_path, t2_path, threshold=1, slots_swapped=False):
    """
    Generate a bias evaluation report dictionary for two transcripts.

    Args:
        t1_path: Path to transcript 1 (Patient A speaks first)
        t2_path: Path to transcript 2 (swapped condition)
        threshold: Unused, kept for backward compatibility
        slots_swapped: If True, personas swapped slots in t2 (Persona Swap mode).
    """
    # Load transcripts
    t_a_first = load_transcript(t1_path)
    t_b_first = load_transcript(t2_path)

    # Get patient names from T1 (the reference run)
    pa_name = t_a_first["participant_details"]["patient_A"]["name"]
    pb_name = t_a_first["participant_details"]["patient_B"]["name"]

    # Analyze Patient A
    deltas_a_when_first = extract_deltas(t_a_first, "Patient_A")
    if slots_swapped:
        deltas_a_when_second = extract_deltas(t_b_first, "Patient_B")
    else:
        deltas_a_when_second = extract_deltas(t_b_first, "Patient_A")

    # Analyze Patient B
    deltas_b_when_second = extract_deltas(t_a_first, "Patient_B")
    if slots_swapped:
        deltas_b_when_first = extract_deltas(t_b_first, "Patient_A")
    else:
        deltas_b_when_first = extract_deltas(t_b_first, "Patient_B")

    # Compute per-patient aggregate PANAS shifts
    def patient_summary(deltas_first, deltas_second):
        pos_first = aggregate_panas(deltas_first, POSITIVE_AFFECT)
        neg_first = aggregate_panas(deltas_first, NEGATIVE_AFFECT)
        pos_second = aggregate_panas(deltas_second, POSITIVE_AFFECT)
        neg_second = aggregate_panas(deltas_second, NEGATIVE_AFFECT)
        return {
            "pos_first": pos_first, "neg_first": neg_first,
            "net_first": pos_first - neg_first,
            "pos_second": pos_second, "neg_second": neg_second,
            "net_second": pos_second - neg_second,
        }

    stats_a = patient_summary(deltas_a_when_first, deltas_a_when_second)
    stats_b = patient_summary(deltas_b_when_first, deltas_b_when_second)

    # Construct Report Dictionary (backward-compatible keys)
    return {
        "meta": {
            "transcript_1": os.path.basename(t1_path),
            "transcript_2": os.path.basename(t2_path),
            "pcr_threshold": threshold,
            "patient_a": pa_name,
            "patient_b": pb_name
        },
        "metrics": {
            "overall_pcr": 0.0,
            "overall_spdi_magnitude": 0.0,
            "verdict": "N/A"
        },
        "details": {
            pa_name: {
                "spdi": {},
                "pcr": (0.0, 0, 0),
                "deltas_first": deltas_a_when_first,
                "deltas_second": deltas_a_when_second,
                "stats": {
                    "pos_mean": 0.0,
                    "neg_mean": 0.0,
                    "mag_mean": 0.0
                },
                "panas_summary": stats_a
            },
            pb_name: {
                "spdi": {},
                "pcr": (0.0, 0, 0),
                "deltas_first": deltas_b_when_first,
                "deltas_second": deltas_b_when_second,
                "stats": {
                    "pos_mean": 0.0,
                    "neg_mean": 0.0,
                    "mag_mean": 0.0
                },
                "panas_summary": stats_b
            }
        }
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Position Bias Evaluation (PANAS Delta Comparison)")
    parser.add_argument("--t1", type=str, default=T_A_FIRST,
                        help="Transcript where Patient A speaks first")
    parser.add_argument("--t2", type=str, default=T_B_FIRST,
                        help="Transcript where Patient B speaks first")
    args = parser.parse_args()

    # Generate Report
    print_header("POSITION BIAS EVALUATION REPORT")
    report = generate_evaluation_report(args.t1, args.t2)

    meta = report["meta"]
    dets = report["details"]

    print(f"\n  Transcript 1:  {meta['transcript_1']} (A First)")
    print(f"  Transcript 2:  {meta['transcript_2']} (B First)")
    print(f"  Patients:      {meta['patient_a']} & {meta['patient_b']}")

    # Print Tables
    pa = meta["patient_a"]
    pb = meta["patient_b"]

    print_header("PANAS DELTA COMPARISON", char="-")
    print_delta_table(
        dets[pa]["deltas_first"], dets[pa]["deltas_second"],
        f"Patient A: {pa}"
    )
    print_delta_table(
        dets[pb]["deltas_first"], dets[pb]["deltas_second"],
        f"Patient B: {pb}"
    )

    # Summary
    print_header("AGGREGATE SUMMARY", char="-")
    sa = dets[pa].get("panas_summary", {})
    sb = dets[pb].get("panas_summary", {})
    print(f"\n  {'Metric':<30} {pa:>20} {pb:>20}")
    print(f"  {'-'*30} {'-'*20} {'-'*20}")
    print(f"  {'Net PANAS (when first)':<30} {sa.get('net_first',0):>+20d} {sb.get('net_first',0):>+20d}")
    print(f"  {'Net PANAS (when second)':<30} {sa.get('net_second',0):>+20d} {sb.get('net_second',0):>+20d}")
    print()

    # Export
    output_path = "bias_evaluation_report.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  JSON report saved to: {output_path}")


if __name__ == "__main__":
    main()
