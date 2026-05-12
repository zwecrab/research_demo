"""
Rerun the 4-pair temperature=0.7 batch with the new 'open' therapist prompt
(therapist_prompt_open.txt) instead of individual_focus.

Matches original pilot_temp t=0.7 parameters exactly:
  couples:    C3, C4, C8, C9
  bids:       neutral+neutral (LL)
  structure:  LLM-Based Selection
  temp:       0.7
  model:      GPT-4o

Only change: therapist_mode = 'open' instead of 'individual_focus'.
Output files: pilot_open_<couple>_LL_t07_<position>.json

Run:
  PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python experiment/run_pilot_opentherapist.py
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

THERAPIST_MODE = "open"
STRUCTURE = "LLM-Based Selection"
TEMPERATURE = 0.7
THERAPIST_MODEL = "openai/gpt-4o"
BID_A = "neutral"
BID_B = "neutral"
CELL = "LL"

COUPLES = [
    ("C3", +0.99),
    ("C4", +2.93),
    ("C8", -0.23),
    ("C9", -0.83),
]


def run_one(assets, couple, sev_diff, position):
    label = f"pilot_open_{couple}_{CELL}_t07_{position}"
    first_speaker = "Patient A" if position == "alpha" else "Patient B"

    print(f"\n{'='*72}\n  SESSION: {label}  (sev_diff={sev_diff:+.2f}, temp={TEMPERATURE})")
    print(f"  Mode: {THERAPIST_MODE}  Structure: {STRUCTURE}")
    print('='*72)

    members = assets["v2_couples"][couple]
    pa = copy.deepcopy(members[0])
    pb = copy.deepcopy(members[1])
    apply_bid_style_overlay(pa, assets["bid_styles"][BID_A])
    apply_bid_style_overlay(pb, assets["bid_styles"][BID_B])

    header, details, participants, notes = setup_v2_session(pa, pb, STRUCTURE)
    output = initialize_session_state(header, details, participants, notes,
                                       STRUCTURE, first_speaker)
    output["experiment_metadata"] = {
        "pilot_batch": "open_therapist",
        "couple_id": couple, "position": position,
        "bid_style_a": BID_A, "bid_style_b": BID_B, "cell": CELL,
        "severity_diff_expected": sev_diff,
        "therapist_mode": THERAPIST_MODE, "structure": STRUCTURE,
        "therapist_model": THERAPIST_MODEL, "temperature": TEMPERATURE,
        "prompt_file": "therapist_prompt_open.txt",
    }

    log_session_start(header, STRUCTURE, first_speaker)
    output, history = run_session_loop(
        output, participants, notes, STRUCTURE, first_speaker, TEMPERATURE,
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
    print(f"  T1: {transcript[0].get('dialogue','')[:140]}")
    return output


def summarize(results):
    print("\n" + "=" * 88)
    print("  OPEN THERAPIST (t=0.7) SUMMARY — compare with pilot_temp_*_t07_*")
    print("=" * 88)
    print(f"  {'couple':<6} {'pos':<6} {'sev':>7} {'FAS':>7} {'FAS-vol':>8} {'BRD':>7} {'CAS':>5} "
          f"{'wA':>5} {'wB':>5}")
    for r in results:
        meta = r["experiment_metadata"]
        b = r.get("therapeutic_balance", {})
        f = b.get("fas", {}) or {}
        br = b.get("brd", {}) or {}
        c = b.get("cas", {}) or {}
        sev = meta.get("severity_diff_expected", 0)
        wa, wb = f.get("words_a") or 0, f.get("words_b") or 0
        print(f"  {meta['couple_id']:<6} {meta['position']:<6} {sev:>+7.2f} "
              f"{f.get('fas_score', 0) or 0:>+7.3f} "
              f"{f.get('fas_volume_adjusted', 0) or 0:>+8.3f} "
              f"{br.get('brd_score', 0) or 0:>+7.2f} "
              f"{c.get('cas_score', 0):>+5} {wa:>5} {wb:>5}")


def main():
    print(f"\n  OPEN THERAPIST PILOT: {len(COUPLES)*2} sessions")
    print(f"  temp={TEMPERATURE}, mode={THERAPIST_MODE}, prompt=therapist_prompt_open.txt")
    print(f"  Comparing against: pilot_temp_C3/C4/C8/C9_t07_alpha/beta.json\n")

    assets = load_all_assets()
    results = []

    for couple, sev_diff in COUPLES:
        for position in ["alpha", "beta"]:
            try:
                r = run_one(assets, couple, sev_diff, position)
                results.append(r)
            except Exception as e:
                import traceback
                print(f"  !! FAILED: {e}")
                traceback.print_exc()
            time.sleep(3)

    summarize(results)


if __name__ == "__main__":
    main()
