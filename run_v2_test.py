"""
Test script: Run 2 sessions with v2 personas + bid-style overlay.

Couple 5 (Al-Rashid): Nadia (aggressive) + Farah (passive)
Individual Focus mode, Sequential structure, alpha + beta positions.

Usage:
    python run_v2_test.py
"""

import copy
import json
import time
from pathlib import Path

from data_loader import load_all_assets, apply_bid_style_overlay
from session_setup import setup_v2_session, initialize_session_state, log_session_start
from main import run_session_loop, run_panas_analysis
from evaluate_therapist import evaluate_therapeutic_alliance
from evaluate_balance import (
    calculate_fas, calculate_brd, calculate_cas,
    calculate_nas, calculate_tsi,
)
from output_manager import save_session_json

COUPLE_ID = "C5"
BID_A = "aggressive"
BID_B = "passive"
THERAPIST_MODE = "individual_focus"
STRUCTURE = "Sequential"
TEMPERATURE = 0.3
THERAPIST_MODEL = "openai/gpt-4o"

OUTPUT_DIR = Path(__file__).parent / "transcripts"
OUTPUT_DIR.mkdir(exist_ok=True)


def run_one_session(assets, persona_a, persona_b, position, bid_a_id, bid_b_id):
    """Run a single session and return the output JSON."""
    label = f"v2test_{COUPLE_ID}_{bid_a_id}+{bid_b_id}_{position}"
    print(f"\n{'='*70}")
    print(f"  SESSION: {label}")
    print(f"  Patient A: {persona_a['name']} ({bid_a_id})")
    print(f"  Patient B: {persona_b['name']} ({bid_b_id})")
    print(f"  Position: {position} ({'A speaks first' if position == 'alpha' else 'B speaks first'})")
    print(f"{'='*70}")

    # Determine first speaker from position
    first_speaker = "Patient A" if position == "alpha" else "Patient B"

    header, details, participants, discussion_notes = setup_v2_session(
        persona_a, persona_b, STRUCTURE
    )

    output_json = initialize_session_state(
        header, details, participants, discussion_notes,
        STRUCTURE, first_speaker
    )
    # Record experiment metadata
    output_json["experiment_metadata"] = {
        "couple_id": COUPLE_ID,
        "position": position,
        "bid_style_a": bid_a_id,
        "bid_style_b": bid_b_id,
        "therapist_mode": THERAPIST_MODE,
        "structure": STRUCTURE,
        "therapist_model": THERAPIST_MODEL,
        "temperature": TEMPERATURE,
    }

    log_session_start(header, STRUCTURE, first_speaker)

    # Run the conversation
    output_json, conversation_history = run_session_loop(
        output_json, participants, discussion_notes,
        STRUCTURE, first_speaker, TEMPERATURE,
        assets["prompts"], assets["baseline_panas"],
        therapist_mode=THERAPIST_MODE,
        therapist_model=THERAPIST_MODEL,
    )

    # Post-session scoring
    print("\n  Running post-session scoring...")

    # PANAS
    try:
        output_json, panas_summaries = run_panas_analysis(
            output_json, assets["baseline_panas"], conversation_history
        )
    except Exception as e:
        print(f"  PANAS scoring failed: {e}")

    # Therapeutic alliance
    try:
        alliance = evaluate_therapeutic_alliance(output_json.get("session_transcript", []))
        output_json["therapist_alliance"] = alliance
    except Exception as e:
        print(f"  TA scoring failed: {e}")

    # FAS / BRD / CAS
    transcript = output_json.get("session_transcript", [])
    pa_name = participants["patient_A"]["name"]
    pb_name = participants["patient_B"]["name"]
    balance = {}
    try:
        balance["fas"] = calculate_fas(transcript, pa_name, pb_name)
        print(f"  FAS: {balance['fas'].get('fas_score', 'N/A')}")
    except Exception as e:
        print(f"  FAS scoring failed: {e}")
    try:
        balance["brd"] = calculate_brd(transcript, pa_name, pb_name)
        print(f"  BRD: {balance['brd'].get('brd_score', 'N/A')}")
    except Exception as e:
        print(f"  BRD scoring failed: {e}")
    try:
        balance["cas"] = calculate_cas(transcript, pa_name, pb_name)
        print(f"  CAS: {balance['cas'].get('cas_score', 'N/A')}")
    except Exception as e:
        print(f"  CAS scoring failed: {e}")
    try:
        balance["nas"] = calculate_nas(transcript, pa_name, pb_name)
        print(f"  NAS: {balance['nas'].get('nas_score', 'N/A')}")
    except Exception as e:
        print(f"  NAS scoring failed: {e}")
    try:
        balance["tsi"] = calculate_tsi(transcript, pa_name, pb_name)
        print(f"  TSI: {balance['tsi'].get('tsi', 'N/A')}")
    except Exception as e:
        print(f"  TSI scoring failed: {e}")
    output_json["therapeutic_balance"] = balance

    # Save
    out_file = OUTPUT_DIR / f"{label}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {out_file}")

    return output_json


def main():
    print("\n  V2 Persona Test: Couple 5 (Al-Rashid), Aggressive+Passive")
    print("  Individual Focus, Sequential, Alpha + Beta\n")

    assets = load_all_assets()

    # Get Couple 5 personas
    couples = assets["v2_couples"]
    if COUPLE_ID not in couples:
        print(f"  Couple {COUPLE_ID} not found. Available: {list(couples.keys())}")
        return
    members = couples[COUPLE_ID]
    bid_styles = assets["bid_styles"]

    for position in ["alpha", "beta"]:
        # Deep-copy to avoid mutating originals between runs
        pa = copy.deepcopy(members[0])
        pb = copy.deepcopy(members[1])

        # Apply bid-style overlays
        apply_bid_style_overlay(pa, bid_styles[BID_A])
        apply_bid_style_overlay(pb, bid_styles[BID_B])

        run_one_session(assets, pa, pb, position, BID_A, BID_B)

        print("\n  Pausing 5s between sessions...")
        time.sleep(5)

    print("\n  All sessions complete.")


if __name__ == "__main__":
    main()
