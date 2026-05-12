"""
Temperature sensitivity pilot.

Compares conversation-generation temperature 0.0, 0.3, 0.7 on 4 pairs
across the severity range. All other conditions match pilot 2:
    GPT-4o, individual_focus, LLM-Based Selection, 30 turns.

Pairs (all LL neutral+neutral):
    C4 Sofia/Kenji (sev=+2.93)   — baseline 0.3 already in pilot 2
    C3 David/James (sev=+0.99)   — baseline 0.3 already in pilot 2
    C8 Avery/Marcus (sev=-0.23)  — NEW 0.3 baseline (pilot 2 used HL agg+pas)
    C9 Lena/Naomi (sev=-0.83)    — baseline 0.3 already in pilot 2

Run plan (18 new sessions):
    C4: temps {0.0, 0.7}              ->  4 sessions
    C3: temps {0.0, 0.7}              ->  4 sessions
    C8: temps {0.0, 0.3, 0.7}         ->  6 sessions  (extra 0.3 baseline)
    C9: temps {0.0, 0.7}              ->  4 sessions

Output: transcripts/pilot_temp_<couple>_<temp>_<position>.json

Run:
    PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python experiment/run_pilot_temperature.py
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

THERAPIST_MODE = "individual_focus"
STRUCTURE = "LLM-Based Selection"
THERAPIST_MODEL = "openai/gpt-4o"
BID_A = "neutral"
BID_B = "neutral"
CELL = "LL"

# (couple, sev_diff, list of temperatures to run)
RUNS = [
    ("C4", +2.93, [0.0, 0.7]),
    ("C3", +0.99, [0.0, 0.7]),
    ("C8", -0.23, [0.0, 0.3, 0.7]),
    ("C9", -0.83, [0.0, 0.7]),
]


def run_one(assets, couple, sev_diff, temperature, position):
    label = f"pilot_temp_{couple}_t{int(temperature*10):02d}_{position}"
    first_speaker = "Patient A" if position == "alpha" else "Patient B"

    print(f"\n{'='*72}\n  SESSION: {label}  (sev_diff={sev_diff:+.2f}, temp={temperature})")
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
        "pilot_batch": "temperature",
        "couple_id": couple, "position": position,
        "bid_style_a": BID_A, "bid_style_b": BID_B, "cell": CELL,
        "severity_diff_expected": sev_diff,
        "therapist_mode": THERAPIST_MODE, "structure": STRUCTURE,
        "therapist_model": THERAPIST_MODEL, "temperature": temperature,
    }

    log_session_start(header, STRUCTURE, first_speaker)
    output, history = run_session_loop(
        output, participants, notes, STRUCTURE, first_speaker, temperature,
        assets["prompts"], assets["baseline_panas"],
        therapist_mode=THERAPIST_MODE, therapist_model=THERAPIST_MODEL,
    )

    print("\n  Scoring...")
    try:
        output, _ = run_panas_analysis(output, assets["baseline_panas"], history)
    except Exception as e:
        print(f"  PANAS failed: {e}")
    try:
        output["therapist_alliance"] = evaluate_therapeutic_alliance(
            output["session_transcript"]
        )
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
    return output


def summarize(results):
    print("\n" + "=" * 88)
    print("  TEMPERATURE PILOT SUMMARY")
    print("=" * 88)
    print(f"  {'pair':<12} {'temp':>5} {'pos':<6} {'sev':>7} "
          f"{'FAS':>7} {'FAS-vol':>8} {'BRD':>7} {'CAS':>5} {'wA':>5} {'wB':>5}")
    for r in results:
        meta = r["experiment_metadata"]
        b = r.get("therapeutic_balance", {})
        f = b.get("fas", {}) or {}
        br = b.get("brd", {}) or {}
        c = b.get("cas", {}) or {}
        sev = meta.get("severity_diff_expected", 0)
        wa, wb = f.get("words_a") or 0, f.get("words_b") or 0
        print(f"  {meta['couple_id']:<12} {meta['temperature']:>5.1f} "
              f"{meta['position']:<6} {sev:>+7.2f} "
              f"{f.get('fas_score', 0) or 0:>+7.3f} "
              f"{f.get('fas_volume_adjusted', 0) or 0:>+8.3f} "
              f"{br.get('brd_score', 0) or 0:>+7.2f} "
              f"{c.get('cas_score', 0):>+5} {wa:>5} {wb:>5}")


def main():
    total = sum(len(temps) * 2 for _, _, temps in RUNS)
    print(f"\n  TEMPERATURE PILOT: {total} sessions across "
          f"{len(RUNS)} couples\n")
    for c, sev, temps in RUNS:
        print(f"    {c} (sev={sev:+.2f}): temps {temps}")
    print()

    assets = load_all_assets()
    results = []

    for couple, sev_diff, temps in RUNS:
        for temp in temps:
            for position in ["alpha", "beta"]:
                try:
                    r = run_one(assets, couple, sev_diff, temp, position)
                    results.append(r)
                except Exception as e:
                    import traceback
                    print(f"  !! FAILED: {e}")
                    traceback.print_exc()
                time.sleep(3)

    summarize(results)


if __name__ == "__main__":
    main()
