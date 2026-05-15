"""
Prompt comparison: Standard vs Open therapist at temperature 0.7.

Runs the same 8 pairs twice:
  1. therapist_prompt.txt      (standard, clinical-judgment addressing)
  2. therapist_prompt_open.txt (open, no individual-focus constraint)

8 pairs per condition = 16 pairs = 32 sessions total.
All: GPT-4o, LLM-Based Selection, temperature 0.7.

Pair design (3 HH + 3 LL + 2 HL):
  C4 HH agg+agg  (sev +2.93) -- strong A-sev, amplified bids
  C2 HH agg+agg  (sev -2.83) -- strong B-sev, amplified bids
  C6 HH agg+agg  (sev +3.33) -- strongest A-sev, amplified bids
  C3 LL neu+neu  (sev +0.99) -- moderate A-sev, quiet bids
  C9 LL neu+neu  (sev -0.83) -- mild B-sev, quiet bids
  C4 LL neu+neu  (sev +2.93) -- C4 replicated: HH vs LL comparison
  C2 HL agg+neu  (sev -2.83) -- high-sev B is the quiet partner (neutral)
  C3 HL agg+neu  (sev +0.99) -- high-sev A is the loud partner (aggressive)

Output files: pilot_compare_{std|open}_{couple}_{cell}_t07_{position}.json
Analysis A report: experiment/prompt_compare_analysis.md

Run:
  PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python experiment/run_pilot_prompt_compare.py
"""
import copy, json, sys, time
from pathlib import Path
from statistics import mean, stdev

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data_loader import load_all_assets, apply_bid_style_overlay
from session_setup import setup_v2_session, initialize_session_state, log_session_start
from main import run_session_loop, run_panas_analysis
from evaluate_therapist import evaluate_therapeutic_alliance
from evaluate_balance import calculate_fas, calculate_brd, calculate_cas, calculate_nas, calculate_tsi

OUTPUT_DIR = ROOT / "transcripts"
OUTPUT_DIR.mkdir(exist_ok=True)
REPORT_OUT = ROOT / "experiment" / "prompt_compare_analysis.md"

TEMPERATURE = 0.7
STRUCTURE = "LLM-Based Selection"
THERAPIST_MODEL = "openai/gpt-4o"
NEAR_BALANCED_THRESH = 0.40

PAIRS = [
    {"couple": "C4", "bid_a": "aggressive", "bid_b": "aggressive", "cell": "HH", "sev": +2.93},
    {"couple": "C2", "bid_a": "aggressive", "bid_b": "aggressive", "cell": "HH", "sev": -2.83},
    {"couple": "C6", "bid_a": "aggressive", "bid_b": "aggressive", "cell": "HH", "sev": +3.33},
    {"couple": "C3", "bid_a": "neutral",    "bid_b": "neutral",    "cell": "LL", "sev": +0.99},
    {"couple": "C9", "bid_a": "neutral",    "bid_b": "neutral",    "cell": "LL", "sev": -0.83},
    {"couple": "C4", "bid_a": "neutral",    "bid_b": "neutral",    "cell": "LL", "sev": +2.93},
    {"couple": "C2", "bid_a": "aggressive", "bid_b": "neutral",    "cell": "HL", "sev": -2.83},
    {"couple": "C3", "bid_a": "aggressive", "bid_b": "neutral",    "cell": "HL", "sev": +0.99},
]

CONDITIONS = [
    ("std",  "standard"),
    ("open", "open"),
]


def run_one(assets, cfg, mode_label, therapist_mode, position):
    c = cfg["couple"]
    cell = cfg["cell"]
    bid_a, bid_b = cfg["bid_a"], cfg["bid_b"]
    label = f"pilot_compare_{mode_label}_{c}_{cell}_t07_{position}"
    first_speaker = "Patient A" if position == "alpha" else "Patient B"

    print(f"\n{'='*72}")
    print(f"  {label}  (sev={cfg['sev']:+.2f}, mode={therapist_mode})")
    print('='*72)

    members = assets["v2_couples"][c]
    pa = copy.deepcopy(members[0])
    pb = copy.deepcopy(members[1])
    apply_bid_style_overlay(pa, assets["bid_styles"][bid_a])
    apply_bid_style_overlay(pb, assets["bid_styles"][bid_b])

    header, details, participants, notes = setup_v2_session(pa, pb, STRUCTURE)
    output = initialize_session_state(header, details, participants, notes,
                                       STRUCTURE, first_speaker)
    output["experiment_metadata"] = {
        "pilot_batch": "prompt_compare", "condition": mode_label,
        "couple_id": c, "position": position,
        "bid_style_a": bid_a, "bid_style_b": bid_b, "cell": cell,
        "severity_diff_expected": cfg["sev"],
        "therapist_mode": therapist_mode, "structure": STRUCTURE,
        "therapist_model": THERAPIST_MODEL, "temperature": TEMPERATURE,
    }

    log_session_start(header, STRUCTURE, first_speaker)
    output, history = run_session_loop(
        output, participants, notes, STRUCTURE, first_speaker, TEMPERATURE,
        assets["prompts"], assets["baseline_panas"],
        therapist_mode=therapist_mode, therapist_model=THERAPIST_MODEL,
    )

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

    fas = balance.get("fas", {}) or {}
    sev = cfg["sev"]
    fas_raw = fas.get("fas_score", 0) or 0
    fas_hs = round(fas_raw * (1 if sev > 0 else -1), 3)
    print(f"  FAS={fas_raw:+.3f}  FAS_hs={fas_hs:+.3f}  "
          f"vol-adj={fas.get('fas_volume_adjusted', 0) or 0:+.3f}  "
          f"wA={fas.get('words_a')} wB={fas.get('words_b')}")
    return output


def classify(r):
    sev = r["sev"]
    pos = r["pos"]
    if abs(sev) < NEAR_BALANCED_THRESH:
        return "BAL"
    if sev > 0:
        return "HL" if pos == "alpha" else "LH"
    return "HL" if pos == "beta" else "LH"


def fas_hs(r):
    sev = r["sev"]
    return round(r["fas"] * (1 if sev > 0 else -1), 3)


def build_analysis_a(rows, condition_label, prompt_file):
    sev_by_couple = {r["couple"]: r["sev"] for r in rows}

    hl = [r for r in rows if classify(r) == "HL"]
    lh = [r for r in rows if classify(r) == "LH"]

    def table(session_rows, title):
        lines = [f"#### {title} (n={len(session_rows)})\n"]
        lines.append("| # | Couple | High-sev | sev_diff | Cell | Pos | "
                     "FAS | FAS-vol | FAS_hs | BRD | CAS | wA | wB |")
        lines.append("|" + "|".join(["---"]*13) + "|")
        for i, r in enumerate(session_rows, 1):
            hs_name = r.get("high_sev_name", "?")
            lines.append(
                f"| {i} | {r['couple']} | {hs_name} | {r['sev']:+.2f} | {r['cell']} | {r['pos']} | "
                f"{r['fas']:+.3f} | {r['fas_vol']:+.3f} | **{fas_hs(r):+.3f}** | "
                f"{r['brd']:+.2f} | {r['cas']:+d} | {r['wA']} | {r['wB']} |"
            )
        if session_rows:
            m_fas = round(mean(r["fas"] for r in session_rows), 3)
            m_fasv = round(mean(r["fas_vol"] for r in session_rows), 3)
            m_hs = round(mean(fas_hs(r) for r in session_rows), 3)
            m_brd = round(mean(r["brd"] for r in session_rows), 3)
            m_cas = round(mean(r["cas"] for r in session_rows), 3)
            m_wa = round(mean(r["wA"] for r in session_rows))
            m_wb = round(mean(r["wB"] for r in session_rows))
            lines.append(
                f"| **Mean** | — | — | — | — | — | **{m_fas:+.3f}** | {m_fasv:+.3f} | "
                f"**{m_hs:+.3f}** | {m_brd:+.2f} | {m_cas:+.2f} | {m_wa} | {m_wb} |"
            )
        return "\n".join(lines)

    lines = [f"### Condition: {condition_label} (`{prompt_file}`)\n"]
    lines.append(table(hl, "Table HL — high-severity patient speaks first"))
    lines.append("\n")
    lines.append(table(lh, "Table LH — low-severity patient speaks first"))
    return "\n".join(lines), hl, lh


def extract_row(output):
    em = output.get("experiment_metadata", {}) or {}
    tb = output.get("therapeutic_balance", {}) or {}
    fas = (tb.get("fas") or {})
    brd = (tb.get("brd") or {})
    cas = (tb.get("cas") or {})
    sev = em.get("severity_diff_expected", 0)
    # Infer high_sev_name from participants
    pd = output.get("participant_details", {}) or {}
    pa_name = (pd.get("patient_A") or {}).get("name", "A").split()[0]
    pb_name = (pd.get("patient_B") or {}).get("name", "B").split()[0]
    high_sev_name = pa_name if sev > 0 else pb_name
    return {
        "couple": em.get("couple_id"),
        "pos": em.get("position"),
        "cell": em.get("cell"),
        "sev": sev,
        "high_sev_name": high_sev_name,
        "fas": fas.get("fas_score", 0) or 0,
        "fas_vol": fas.get("fas_volume_adjusted", 0) or 0,
        "brd": brd.get("brd_score", 0) or 0,
        "cas": cas.get("cas_score", 0) or 0,
        "wA": fas.get("words_a", 0) or 0,
        "wB": fas.get("words_b", 0) or 0,
    }


def build_delta_table(std_hl, std_lh, open_hl, open_lh):
    lines = ["### Delta table: Open minus Standard (FAS_hs)\n"]
    lines.append(
        "Positive delta = open prompt produced MORE high-severity-favoring framing than standard.\n"
    )
    lines.append("| Condition | n | Std mean FAS_hs | Open mean FAS_hs | Delta (Open - Std) |")
    lines.append("|---|---:|---:|---:|---:|")
    for label, s_rows, o_rows in [("HL", std_hl, open_hl), ("LH", std_lh, open_lh)]:
        if s_rows and o_rows:
            s_m = round(mean(fas_hs(r) for r in s_rows), 3)
            o_m = round(mean(fas_hs(r) for r in o_rows), 3)
            delta = round(o_m - s_m, 3)
            lines.append(f"| {label} | {len(s_rows)}/{len(o_rows)} | {s_m:+.3f} | {o_m:+.3f} | **{delta:+.3f}** |")

    lines.append("")
    lines.append("#### Per-couple FAS_hs delta (Open - Standard, mean across positions)\n")
    lines.append("| Couple | sev_diff | Cell | Std FAS_hs | Open FAS_hs | Delta |")
    lines.append("|---|---:|---|---:|---:|---:|")
    by_key = {}
    for rows, cond in [(std_hl + std_lh, "std"), (open_hl + open_lh, "open")]:
        for r in rows:
            if abs(r["sev"]) < NEAR_BALANCED_THRESH:
                continue
            key = (r["couple"], r["cell"])
            by_key.setdefault(key, {}).setdefault(cond, []).append(fas_hs(r))
    for (couple, cell), d in sorted(by_key.items()):
        s_vals = d.get("std", [])
        o_vals = d.get("open", [])
        if s_vals and o_vals:
            s_m = round(mean(s_vals), 3)
            o_m = round(mean(o_vals), 3)
            sev_d = next((r["sev"] for r in std_hl + std_lh
                          if r["couple"] == couple and r["cell"] == cell), 0)
            lines.append(f"| {couple} | {sev_d:+.2f} | {cell} | {s_m:+.3f} | {o_m:+.3f} | **{round(o_m-s_m,3):+.3f}** |")
    return "\n".join(lines)


def main():
    total = len(PAIRS) * len(CONDITIONS) * 2
    print(f"\n  PROMPT COMPARISON PILOT: {total} sessions")
    print(f"  {len(PAIRS)} pairs × {len(CONDITIONS)} conditions × 2 positions")
    print(f"  temp={TEMPERATURE}, model={THERAPIST_MODEL}")
    for cfg in PAIRS:
        print(f"    {cfg['couple']} {cfg['cell']} {cfg['bid_a']}+{cfg['bid_b']} sev={cfg['sev']:+.2f}")
    print()

    assets = load_all_assets()
    all_results = {"std": [], "open": []}

    for mode_label, therapist_mode in CONDITIONS:
        print(f"\n{'#'*70}")
        print(f"  CONDITION: {mode_label} ({therapist_mode})")
        print('#'*70)
        for cfg in PAIRS:
            for position in ["alpha", "beta"]:
                try:
                    r = run_one(assets, cfg, mode_label, therapist_mode, position)
                    all_results[mode_label].append(extract_row(r))
                except Exception as e:
                    import traceback
                    print(f"  !! FAILED: {e}")
                    traceback.print_exc()
                time.sleep(3)

    # Build report
    std_rows = all_results["std"]
    open_rows = all_results["open"]

    report_lines = ["# Prompt Comparison Analysis (Analysis A format)\n"]
    report_lines.append(
        f"**Design:** {len(PAIRS)} pairs × 2 conditions (Standard vs Open therapist prompt) × 2 positions "
        f"= {len(PAIRS)*4} sessions total. Temperature={TEMPERATURE}, GPT-4o, LLM-Based Selection. "
        "Near-balanced couples (|sev_diff| < 0.40) excluded from HL/LH classification.\n"
    )
    report_lines.append("---\n")

    std_section, std_hl, std_lh = build_analysis_a(
        std_rows, "Standard", "therapist_prompt.txt")
    open_section, open_hl, open_lh = build_analysis_a(
        open_rows, "Open", "therapist_prompt_open.txt")

    report_lines.append(std_section)
    report_lines.append("\n---\n")
    report_lines.append(open_section)
    report_lines.append("\n---\n")
    report_lines.append(build_delta_table(std_hl, std_lh, open_hl, open_lh))

    REPORT_OUT.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\n  Report written: {REPORT_OUT}")


if __name__ == "__main__":
    main()