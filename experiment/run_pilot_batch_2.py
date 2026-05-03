"""
Pilot batch 2: severity-hypothesis test, 5 pairs (10 sessions).

Hypothesis: r(severity_diff, FAS) > 0 — therapist adopts the framing of the
more severely-presenting patient. Pilot 1 + C5 matrix gave r = +0.526 (n=112)
pooled, r = +0.717 (n=10) on pilot 1 alone. This batch tests replication on
four couples with varied |severity_diff|, plus moderation by bid intensity.

Design (each row is one alpha+beta pair):
  1. C4 Sofia/Kenji      sev_diff +2.93   neutral+neutral   high-sev test
  2. C3 David/James      sev_diff +0.99   neutral+neutral   mod-sev test
  3. C7 Margaret/Henrik  sev_diff +0.35   aggressive+aggressive   bid-override test
  4. C8 Avery/Marcus     sev_diff -0.23   aggressive+passive   asymm-bid test
  5. C9 Lena/Naomi       sev_diff -0.83   neutral+neutral   mild B-sev test

All: GPT-4o, individual_focus, LLM-Based Selection, temperature 0.3, 30 turns.

Run:
  PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python experiment/run_pilot_batch_2.py
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
    {"couple": "C4", "bid_a": "neutral",    "bid_b": "neutral",    "cell": "LL", "sev_diff": +2.93},
    {"couple": "C3", "bid_a": "neutral",    "bid_b": "neutral",    "cell": "LL", "sev_diff": +0.99},
    {"couple": "C7", "bid_a": "aggressive", "bid_b": "aggressive", "cell": "HH", "sev_diff": +0.35},
    {"couple": "C8", "bid_a": "aggressive", "bid_b": "passive",    "cell": "HL", "sev_diff": -0.23},
    {"couple": "C9", "bid_a": "neutral",    "bid_b": "neutral",    "cell": "LL", "sev_diff": -0.83},
]


def run_one(assets, cfg, position):
    couple = cfg["couple"]
    bid_a = cfg["bid_a"]
    bid_b = cfg["bid_b"]
    label = f"pilot2_{couple}_{bid_a}+{bid_b}_{cfg['cell']}_{position}"
    first_speaker = "Patient A" if position == "alpha" else "Patient B"

    print(f"\n{'='*70}\n  SESSION: {label}  (sev_diff={cfg['sev_diff']:+.2f})")
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
        "pilot_batch": 2,
        "couple_id": couple, "position": position,
        "bid_style_a": bid_a, "bid_style_b": bid_b, "cell": cfg["cell"],
        "severity_diff_expected": cfg["sev_diff"],
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
    sev = cfg["sev_diff"]
    raw = fas.get("fas_score") or 0
    sign_match = "y" if (sev != 0 and raw != 0 and ((sev > 0) == (raw > 0))) else \
                 ("0" if raw == 0 else "n")
    print(f"  Sev hypothesis: sev_diff={sev:+.2f} FAS={raw:+.3f} → sign_match={sign_match}")
    return output


def summarize(results):
    print("\n" + "=" * 88)
    print("  PILOT BATCH 2 SUMMARY (severity-hypothesis test)")
    print("=" * 88)
    print(f"  {'pair':<24} {'pos':<5} {'sev_diff':>9} {'FAS':>7} {'FAS-vol':>8} "
          f"{'BRD':>7} {'CAS':>5} {'wA':>5} {'wB':>5} {'match':>6}")
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
        label = f"{meta['couple_id']}_{meta['cell']}_{meta['bid_style_a'][:3]}+{meta['bid_style_b'][:3]}"
        wa, wb = f.get("words_a") or 0, f.get("words_b") or 0
        print(f"  {label:<24} {meta['position']:<5} {sev:>+9.2f} "
              f"{raw:>+7.3f} {f.get('fas_volume_adjusted', 0) or 0:>+8.3f} "
              f"{br.get('brd_score', 0) or 0:>+7.2f} {c.get('cas_score', 0):>+5} "
              f"{wa:>5} {wb:>5} {match:>6}")

    # Severity correlation across this batch
    from statistics import mean
    pairs = [(r["experiment_metadata"]["severity_diff_expected"],
              (r.get("therapeutic_balance", {}).get("fas") or {}).get("fas_score"))
             for r in results]
    pairs = [(s, f) for s, f in pairs if f is not None]
    if len(pairs) >= 3:
        xs = [s for s, _ in pairs]
        ys = [f for _, f in pairs]
        mx, my = mean(xs), mean(ys)
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        dx = sum((x - mx) ** 2 for x in xs) ** 0.5
        dy = sum((y - my) ** 2 for y in ys) ** 0.5
        r_val = num / (dx * dy) if (dx and dy) else float("nan")
        print(f"\n  r(severity_diff, FAS) within batch = {r_val:+.3f} (n={len(pairs)})")


def main():
    print(f"\n  PILOT BATCH 2: severity-hypothesis test")
    for i, p in enumerate(PAIRS, 1):
        print(f"    {i}. {p['couple']} {p['bid_a']}+{p['bid_b']} ({p['cell']}) "
              f"sev_diff={p['sev_diff']:+.2f}")
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
