"""
Pilot batches 3 and 4: validate Standard mode + Sequential structure
before committing to the 312-session final design.

PILOT 4 (runs first): structure comparison on 2 couples, Standard mode.
  Tests whether severity-FAS finding survives the mode switch from
  individual_focus to standard, and whether Sequential structure
  preserves the effect.
    - C6 (sev +3.33) HH agg+agg, LLM-Based Selection (2 sessions)
    - C6 HH agg+agg, Sequential (2 sessions)
    - C2 (sev -2.83) HH agg+agg, LLM-Based Selection (2 sessions)
    - C2 HH agg+agg, Sequential (2 sessions)
  = 4 pairs / 8 sessions

PILOT 3 (runs second): Sequential structure across 5 couples with
varied severity and bid intensity. Validates that the severity-FAS
link replicates on Sequential beyond the C6/C2 endpoints.
    - C6 HH agg+agg (sev +3.33)
    - C4 LL neu+neu (sev +2.93)
    - C2 HH agg+agg (sev -2.83)
    - C7 HL agg+neu (sev +0.35)
    - C9 LL neu+neu (sev -0.83)
  = 5 pairs / 10 sessions

Total: 18 sessions, GPT-4o, Standard therapist mode.

Run:
  PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python experiment/run_pilot_batch_3and4.py
"""
import copy
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data_loader import load_all_assets, apply_bid_style_overlay
from session_setup import setup_v2_session, initialize_session_state, log_session_start
from main import run_session_loop, run_panas_analysis
from evaluate_therapist import evaluate_therapeutic_alliance
from evaluate_balance import (
    calculate_fas, calculate_brd, calculate_cas,
    calculate_nas, calculate_tsi,
)

OUTPUT_DIR = ROOT / "transcripts"
OUTPUT_DIR.mkdir(exist_ok=True)

THERAPIST_MODE = "standard"
TEMPERATURE = 0.3
THERAPIST_MODEL = "openai/gpt-4o"

# Pilot 4: structure comparison, 4 pairs (Pilot 4 runs FIRST)
PILOT4 = [
    {"label": "pilot4", "couple": "C6", "bid_a": "aggressive", "bid_b": "aggressive",
     "cell": "HH", "structure": "LLM-Based Selection", "sev_diff": +3.33},
    {"label": "pilot4", "couple": "C6", "bid_a": "aggressive", "bid_b": "aggressive",
     "cell": "HH", "structure": "Sequential", "sev_diff": +3.33},
    {"label": "pilot4", "couple": "C2", "bid_a": "aggressive", "bid_b": "aggressive",
     "cell": "HH", "structure": "LLM-Based Selection", "sev_diff": -2.83},
    {"label": "pilot4", "couple": "C2", "bid_a": "aggressive", "bid_b": "aggressive",
     "cell": "HH", "structure": "Sequential", "sev_diff": -2.83},
]

# Pilot 3: Sequential structure across 5 couples, varied intensity
PILOT3 = [
    {"label": "pilot3", "couple": "C6", "bid_a": "aggressive", "bid_b": "aggressive",
     "cell": "HH", "structure": "Sequential", "sev_diff": +3.33},
    {"label": "pilot3", "couple": "C4", "bid_a": "neutral",    "bid_b": "neutral",
     "cell": "LL", "structure": "Sequential", "sev_diff": +2.93},
    {"label": "pilot3", "couple": "C2", "bid_a": "aggressive", "bid_b": "aggressive",
     "cell": "HH", "structure": "Sequential", "sev_diff": -2.83},
    {"label": "pilot3", "couple": "C7", "bid_a": "aggressive", "bid_b": "neutral",
     "cell": "HL", "structure": "Sequential", "sev_diff": +0.35},
    {"label": "pilot3", "couple": "C9", "bid_a": "neutral",    "bid_b": "neutral",
     "cell": "LL", "structure": "Sequential", "sev_diff": -0.83},
]

# Pilot 4 runs first
ALL_PAIRS = PILOT4 + PILOT3


def run_one(assets, cfg, position):
    couple = cfg["couple"]
    bid_a = cfg["bid_a"]
    bid_b = cfg["bid_b"]
    structure = cfg["structure"]
    structure_short = "seq" if structure.startswith("Sequential") else "llm"
    label = (f"{cfg['label']}_{couple}_{bid_a}+{bid_b}_{cfg['cell']}_"
             f"{structure_short}_{position}")
    first_speaker = "Patient A" if position == "alpha" else "Patient B"

    print(f"\n{'='*70}\n  SESSION: {label}  (sev_diff={cfg['sev_diff']:+.2f})")
    print(f"  Structure: {structure}  Mode: {THERAPIST_MODE}  Position: {position}")
    print('='*70)

    members = assets["v2_couples"][couple]
    pa = copy.deepcopy(members[0])
    pb = copy.deepcopy(members[1])
    apply_bid_style_overlay(pa, assets["bid_styles"][bid_a])
    apply_bid_style_overlay(pb, assets["bid_styles"][bid_b])

    header, details, participants, notes = setup_v2_session(pa, pb, structure)
    output = initialize_session_state(header, details, participants, notes,
                                       structure, first_speaker)
    output["experiment_metadata"] = {
        "pilot_batch": cfg["label"],
        "couple_id": couple, "position": position,
        "bid_style_a": bid_a, "bid_style_b": bid_b, "cell": cfg["cell"],
        "severity_diff_expected": cfg["sev_diff"],
        "therapist_mode": THERAPIST_MODE, "structure": structure,
        "therapist_model": THERAPIST_MODEL, "temperature": TEMPERATURE,
    }

    log_session_start(header, structure, first_speaker)
    output, history = run_session_loop(
        output, participants, notes, structure, first_speaker, TEMPERATURE,
        assets["prompts"], assets["baseline_panas"],
        therapist_mode=THERAPIST_MODE, therapist_model=THERAPIST_MODEL,
    )

    print("\n  Scoring...")
    try:
        output, _ = run_panas_analysis(output, assets["baseline_panas"], history)
    except Exception as e:
        print(f"  PANAS failed: {e}")
    try:
        output["therapist_alliance"] = evaluate_therapeutic_alliance(output["session_transcript"])
    except Exception as e:
        print(f"  TA failed: {e}")

    transcript = output["session_transcript"]
    pa_name = participants["patient_A"]["name"]
    pb_name = participants["patient_B"]["name"]
    balance = {}
    for fn, key in [(calculate_fas, "fas"), (calculate_brd, "brd"),
                    (calculate_cas, "cas"), (calculate_nas, "nas"),
                    (calculate_tsi, "tsi")]:
        try:
            balance[key] = fn(transcript, pa_name, pb_name)
        except Exception as e:
            print(f"  {key} failed: {e}")
    output["therapeutic_balance"] = balance

    out_file = OUTPUT_DIR / f"{label}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {out_file.name}")

    fas = balance.get("fas", {}) or {}
    print(f"  FAS raw={fas.get('fas_score')} vol-adj={fas.get('fas_volume_adjusted')} "
          f"words A={fas.get('words_a')} B={fas.get('words_b')}")
    sev = cfg["sev_diff"]
    raw = fas.get("fas_score") or 0
    sign_match = "y" if (sev != 0 and raw != 0 and ((sev > 0) == (raw > 0))) else \
                 ("0" if raw == 0 else "n")
    print(f"  Sev hypothesis: sev_diff={sev:+.2f} FAS={raw:+.3f} → sign_match={sign_match}")
    print(f"  T1: {transcript[0].get('dialogue', '')[:140]}")
    return output


def summarize(results):
    print("\n" + "=" * 96)
    print("  PILOT 4+3 SUMMARY (Standard mode; structure validation)")
    print("=" * 96)
    print(f"  {'pair':<28} {'pos':<5} {'struct':<5} {'sev':>7} {'FAS':>7} "
          f"{'FAS-vol':>8} {'BRD':>7} {'CAS':>5} {'wA':>5} {'wB':>5} {'match':>6}")
    for r in results:
        meta = r["experiment_metadata"]
        b = r.get("therapeutic_balance", {})
        f = b.get("fas", {}) or {}
        br = b.get("brd", {}) or {}
        c = b.get("cas", {}) or {}
        sev = meta.get("severity_diff_expected", 0)
        raw = f.get("fas_score") or 0
        match = "y" if (sev != 0 and raw != 0 and ((sev > 0) == (raw > 0))) else \
                ("0" if raw == 0 else "n")
        struct_short = "seq" if meta.get("structure", "").startswith("Sequential") else "llm"
        label = (f"{meta['pilot_batch']}_{meta['couple_id']}_{meta['cell']}_"
                 f"{meta['bid_style_a'][:3]}+{meta['bid_style_b'][:3]}")
        wa, wb = f.get("words_a") or 0, f.get("words_b") or 0
        print(f"  {label:<28} {meta['position']:<5} {struct_short:<5} {sev:>+7.2f} "
              f"{raw:>+7.3f} {f.get('fas_volume_adjusted', 0) or 0:>+8.3f} "
              f"{br.get('brd_score', 0) or 0:>+7.2f} {c.get('cas_score', 0):>+5} "
              f"{wa:>5} {wb:>5} {match:>6}")


def main():
    print(f"\n  PILOT 4+3 (Standard mode; structure validation)")
    print(f"  PILOT 4 first ({len(PILOT4)} pairs / {len(PILOT4)*2} sessions)")
    print(f"  Then PILOT 3 ({len(PILOT3)} pairs / {len(PILOT3)*2} sessions)")
    print(f"  Total: {len(ALL_PAIRS)*2} sessions on GPT-4o\n")

    assets = load_all_assets()

    results = []
    for i, cfg in enumerate(ALL_PAIRS, 1):
        struct_short = "seq" if cfg["structure"].startswith("Sequential") else "llm"
        print(f"\n>>> PAIR {i}/{len(ALL_PAIRS)}: {cfg['label']} "
              f"{cfg['couple']} {cfg['bid_a']}+{cfg['bid_b']} ({struct_short}) <<<")
        for position in ["alpha", "beta"]:
            try:
                r = run_one(assets, cfg, position)
                results.append(r)
            except Exception as e:
                import traceback
                print(f"  !! FAILED: {e}")
                traceback.print_exc()
            time.sleep(3)

    summarize(results)


if __name__ == "__main__":
    main()
