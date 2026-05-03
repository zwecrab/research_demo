"""
Sample alpha/beta transcript pair on a NEW couple (C7 by default).

Used as a smoke test for the V2 pipeline post-merge:
- Verifies new persona loads
- Verifies new PANAS baseline lookup
- Verifies non-binary handling (if C8 chosen)
- Exercises volume-adjusted FAS

Output: transcripts/sample_<COUPLE>_<bidA>+<bidB>_alpha.json and _beta.json

Override couple/bids via env vars or by editing constants.
"""
import copy
import json
import os
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

COUPLE_ID = os.environ.get("SAMPLE_COUPLE", "C7")
BID_A = os.environ.get("SAMPLE_BID_A", "neutral")
BID_B = os.environ.get("SAMPLE_BID_B", "neutral")
THERAPIST_MODE = os.environ.get("SAMPLE_MODE", "standard")
STRUCTURE = "LLM-Based Selection"
TEMPERATURE = 0.3
THERAPIST_MODEL = os.environ.get("SAMPLE_MODEL", "openai/gpt-4o")

OUTPUT_DIR = ROOT / "transcripts"
OUTPUT_DIR.mkdir(exist_ok=True)


def run_one(assets, pa, pb, position):
    label = f"sample_{COUPLE_ID}_{BID_A}+{BID_B}_{position}"
    first_speaker = "Patient A" if position == "alpha" else "Patient B"

    print(f"\n{'='*70}\n  SESSION: {label}")
    print(f"  Patient A: {pa['name']} ({BID_A})  |  Patient B: {pb['name']} ({BID_B})")
    print(f"  Position: {position}  | Mode: {THERAPIST_MODE}  | Structure: {STRUCTURE}")
    print('='*70)

    header, details, participants, notes = setup_v2_session(pa, pb, STRUCTURE)
    output = initialize_session_state(header, details, participants, notes,
                                       STRUCTURE, first_speaker)
    output["experiment_metadata"] = {
        "couple_id": COUPLE_ID, "position": position,
        "bid_style_a": BID_A, "bid_style_b": BID_B,
        "therapist_mode": THERAPIST_MODE, "structure": STRUCTURE,
        "therapist_model": THERAPIST_MODEL, "temperature": TEMPERATURE,
        "sample_run": True,
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
    fas = balance.get("fas", {})
    print(f"  FAS raw={fas.get('fas_score')} vol-adj={fas.get('fas_volume_adjusted')} "
          f"words A={fas.get('words_a')} B={fas.get('words_b')}")
    return output


def main():
    print(f"\n  Sample pair: {COUPLE_ID}, bids={BID_A}+{BID_B}, model={THERAPIST_MODEL}\n")
    assets = load_all_assets()
    couples = assets["v2_couples"]
    if COUPLE_ID not in couples:
        print(f"  Couple {COUPLE_ID} not found. Available: {list(couples.keys())}")
        return
    members = couples[COUPLE_ID]
    bid_styles = assets["bid_styles"]

    results = {}
    for position in ["alpha", "beta"]:
        pa = copy.deepcopy(members[0])
        pb = copy.deepcopy(members[1])
        apply_bid_style_overlay(pa, bid_styles[BID_A])
        apply_bid_style_overlay(pb, bid_styles[BID_B])
        results[position] = run_one(assets, pa, pb, position)
        if position == "alpha":
            print("\n  Pause 5s...")
            time.sleep(5)

    print("\n" + "=" * 70)
    print("  SAMPLE PAIR SUMMARY")
    print("=" * 70)
    for pos in ["alpha", "beta"]:
        b = results[pos].get("therapeutic_balance", {})
        f = b.get("fas", {}) or {}
        br = b.get("brd", {}) or {}
        c = b.get("cas", {}) or {}
        print(f"\n  {pos.upper()}:")
        print(f"    FAS raw={f.get('fas_score')}  vol-adj={f.get('fas_volume_adjusted')}")
        print(f"    BRD={br.get('brd_score')}   CAS={c.get('cas_score')}")
        print(f"    words A={f.get('words_a')} B={f.get('words_b')} "
              f"(bias A-B={(f.get('words_a') or 0)-(f.get('words_b') or 0)})")


if __name__ == "__main__":
    main()
