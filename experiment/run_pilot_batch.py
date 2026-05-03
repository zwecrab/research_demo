"""
Pilot batch under Path A framing: 5 alpha/beta pairs (10 sessions) on
new couples C6-C9, varied bid intensity cells, all individual_focus mode.

Design:
  1. C6 (finance)    aggressive+aggressive   HH max-arousal
  2. C7 (illness)    neutral+neutral         LL baseline
  3. C8 (ND/NT)      assertive+assertive     HH regulated-direct
  4. C9 (infidelity) passive+passive         LL withdrawn
  5. C6 (finance)    aggressive+neutral      HL asymmetric

All: GPT-4o, individual_focus, LLM-Based Selection, temperature 0.3, 30 turns.

Run:
  PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python experiment/run_pilot_batch.py
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
TEMPERATURE = 0.3
THERAPIST_MODEL = "openai/gpt-4o"

PAIRS = [
    {"couple": "C6", "bid_a": "aggressive", "bid_b": "aggressive", "cell": "HH"},
    {"couple": "C7", "bid_a": "neutral",    "bid_b": "neutral",    "cell": "LL"},
    {"couple": "C8", "bid_a": "assertive",  "bid_b": "assertive",  "cell": "HH"},
    {"couple": "C9", "bid_a": "passive",    "bid_b": "passive",    "cell": "LL"},
    {"couple": "C6", "bid_a": "aggressive", "bid_b": "neutral",    "cell": "HL"},
]


def run_one(assets, cfg, position):
    couple = cfg["couple"]
    bid_a = cfg["bid_a"]
    bid_b = cfg["bid_b"]
    label = f"pilot_{couple}_{bid_a}+{bid_b}_{cfg['cell']}_{position}"
    first_speaker = "Patient A" if position == "alpha" else "Patient B"

    print(f"\n{'='*70}\n  SESSION: {label}")
    print(f"  Position: {position} ({first_speaker} first)")
    print('='*70)

    members = assets["v2_couples"][couple]
    pa = copy.deepcopy(members[0])
    pb = copy.deepcopy(members[1])
    apply_bid_style_overlay(pa, assets["bid_styles"][bid_a])
    apply_bid_style_overlay(pb, assets["bid_styles"][bid_b])

    header, details, participants, notes = setup_v2_session(pa, pb, STRUCTURE)
    output = initialize_session_state(header, details, participants, notes,
                                       STRUCTURE, first_speaker)
    output["experiment_metadata"] = {
        "pilot_batch": True,
        "couple_id": couple, "position": position,
        "bid_style_a": bid_a, "bid_style_b": bid_b, "cell": cfg["cell"],
        "therapist_mode": THERAPIST_MODE, "structure": STRUCTURE,
        "therapist_model": THERAPIST_MODEL, "temperature": TEMPERATURE,
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
    print(f"  T1: {transcript[0].get('dialogue', '')[:160]}...")
    return output


def summarize(results):
    print("\n" + "=" * 78)
    print("  PILOT BATCH SUMMARY")
    print("=" * 78)
    print(f"  {'pair':<22} {'pos':<5} {'FAS':>7} {'FAS-vol':>8} {'BRD':>7} {'CAS':>5} "
          f"{'wA':>5} {'wB':>5} {'bias':>6}")
    for r in results:
        meta = r["experiment_metadata"]
        b = r.get("therapeutic_balance", {})
        f = b.get("fas", {}) or {}
        br = b.get("brd", {}) or {}
        c = b.get("cas", {}) or {}
        label = f"{meta['couple_id']}_{meta['cell']}_{meta['bid_style_a'][:3]}+{meta['bid_style_b'][:3]}"
        wa, wb = f.get("words_a") or 0, f.get("words_b") or 0
        print(f"  {label:<22} {meta['position']:<5} "
              f"{f.get('fas_score', 0):>+7.3f} {f.get('fas_volume_adjusted', 0) or 0:>+8.3f} "
              f"{br.get('brd_score', 0) or 0:>+7.2f} {c.get('cas_score', 0):>+5} "
              f"{wa:>5} {wb:>5} {wa-wb:>+6}")

    print("\n  PAIR-LEVEL DELTAS (alpha - beta):")
    print(f"  {'pair':<22} {'dFAS':>7} {'dFAS-vol':>8} {'dBRD':>7} {'dCAS':>5} {'dwordbias':>10}")
    pair_groups = {}
    for r in results:
        m = r["experiment_metadata"]
        key = (m["couple_id"], m["bid_style_a"], m["bid_style_b"])
        pair_groups.setdefault(key, {})[m["position"]] = r
    for key, pair in pair_groups.items():
        if "alpha" in pair and "beta" in pair:
            a = pair["alpha"].get("therapeutic_balance", {})
            b = pair["beta"].get("therapeutic_balance", {})
            af = a.get("fas", {}) or {}
            bf = b.get("fas", {}) or {}
            abr = a.get("brd", {}) or {}
            bbr = b.get("brd", {}) or {}
            ac = a.get("cas", {}) or {}
            bc = b.get("cas", {}) or {}
            label = f"{key[0]}_{key[1][:3]}+{key[2][:3]}"
            d_fas = (af.get("fas_score") or 0) - (bf.get("fas_score") or 0)
            d_fasv = (af.get("fas_volume_adjusted") or 0) - (bf.get("fas_volume_adjusted") or 0)
            d_brd = (abr.get("brd_score") or 0) - (bbr.get("brd_score") or 0)
            d_cas = (ac.get("cas_score") or 0) - (bc.get("cas_score") or 0)
            wba = (af.get("words_a") or 0) - (af.get("words_b") or 0)
            wbb = (bf.get("words_a") or 0) - (bf.get("words_b") or 0)
            print(f"  {label:<22} {d_fas:>+7.3f} {d_fasv:>+8.3f} {d_brd:>+7.2f} "
                  f"{d_cas:>+5} {wba-wbb:>+10}")


def main():
    print(f"\n  PILOT BATCH: 5 pairs (10 sessions), individual_focus, GPT-4o")
    for i, p in enumerate(PAIRS, 1):
        print(f"    {i}. {p['couple']} {p['bid_a']}+{p['bid_b']} ({p['cell']})")
    print()

    assets = load_all_assets()

    results = []
    for i, cfg in enumerate(PAIRS, 1):
        print(f"\n>>> PAIR {i}/{len(PAIRS)}: {cfg['couple']} {cfg['bid_a']}+{cfg['bid_b']} <<<")
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
