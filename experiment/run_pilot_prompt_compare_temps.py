"""
Extend the prompt comparison to temperatures 0.0 and 0.3.

Runs the same 8 pairs × 2 prompts × 2 new temperatures = 64 sessions.
Combined with the existing 32 sessions at t=0.7, the full dataset covers
t=0.0, t=0.3, t=0.7 for both Standard and Open therapist prompts.

Output files: pilot_compare_{std|open}_{couple}_{cell}_t{00|03}_{position}.json
Report:       experiment/prompt_compare_analysis.md  (regenerated with all 3 temps)

Run:
  PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python experiment/run_pilot_prompt_compare_temps.py
"""
import copy, json, sys, time
from pathlib import Path
from statistics import mean

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

NEW_TEMPERATURES = [0.0, 0.3]
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

CONDITIONS = [("std", "standard"), ("open", "open")]


def run_one(assets, cfg, mode_label, therapist_mode, temperature, position):
    c = cfg["couple"]
    cell = cfg["cell"]
    t_tag = f"t{int(temperature*10):02d}"
    label = f"pilot_compare_{mode_label}_{c}_{cell}_{t_tag}_{position}"
    first_speaker = "Patient A" if position == "alpha" else "Patient B"

    print(f"\n{'='*72}")
    print(f"  {label}  (sev={cfg['sev']:+.2f}, mode={therapist_mode}, temp={temperature})")
    print('='*72)

    members = assets["v2_couples"][c]
    pa = copy.deepcopy(members[0])
    pb = copy.deepcopy(members[1])
    apply_bid_style_overlay(pa, assets["bid_styles"][cfg["bid_a"]])
    apply_bid_style_overlay(pb, assets["bid_styles"][cfg["bid_b"]])

    header, details, participants, notes = setup_v2_session(pa, pb, STRUCTURE)
    output = initialize_session_state(header, details, participants, notes,
                                       STRUCTURE, first_speaker)
    output["experiment_metadata"] = {
        "pilot_batch": "prompt_compare", "condition": mode_label,
        "couple_id": c, "position": position,
        "bid_style_a": cfg["bid_a"], "bid_style_b": cfg["bid_b"], "cell": cell,
        "severity_diff_expected": cfg["sev"],
        "therapist_mode": therapist_mode, "structure": STRUCTURE,
        "therapist_model": THERAPIST_MODEL, "temperature": temperature,
    }

    log_session_start(header, STRUCTURE, first_speaker)
    output, history = run_session_loop(
        output, participants, notes, STRUCTURE, first_speaker, temperature,
        assets["prompts"], assets["baseline_panas"],
        therapist_mode=therapist_mode, therapist_model=THERAPIST_MODEL,
    )
    try:
        output, _ = run_panas_analysis(output, assets["baseline_panas"], history)
    except Exception as e:
        print(f"  PANAS: {e}")
    try:
        output["therapist_alliance"] = evaluate_therapeutic_alliance(output["session_transcript"])
    except Exception as e:
        print(f"  TA: {e}")

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
            print(f"  {key}: {e}")
    output["therapeutic_balance"] = balance

    out_file = OUTPUT_DIR / f"{label}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    fas = balance.get("fas", {}) or {}
    fas_raw = fas.get("fas_score", 0) or 0
    sev = cfg["sev"]
    fas_hs = round(fas_raw * (1 if sev > 0 else -1), 3)
    print(f"  FAS_hs={fas_hs:+.3f}  FAS={fas_raw:+.3f}  "
          f"vol={fas.get('fas_volume_adjusted',0) or 0:+.3f}  "
          f"wA={fas.get('words_a')} wB={fas.get('words_b')}")
    return output


# ─── Report generation ────────────────────────────────────────────────────────

def load_all_compare_sessions():
    rows = []
    for f in sorted(OUTPUT_DIR.glob("pilot_compare_*.json")):
        d = json.load(open(f, encoding='utf-8'))
        em = d.get("experiment_metadata", {}) or {}
        tb = d.get("therapeutic_balance", {}) or {}
        fas = (tb.get("fas") or {})
        brd = (tb.get("brd") or {})
        cas = (tb.get("cas") or {})
        pd = d.get("participant_details", {}) or {}
        pa_n = (pd.get("patient_A") or {}).get("name", "A").split()[0]
        pb_n = (pd.get("patient_B") or {}).get("name", "B").split()[0]
        sev = em.get("severity_diff_expected", 0)
        rows.append({
            "couple": em.get("couple_id"),
            "pos": em.get("position"),
            "cell": em.get("cell"),
            "sev": sev,
            "condition": em.get("condition"),
            "temp": em.get("temperature"),
            "high_sev": pa_n if sev > 0 else pb_n,
            "fas": fas.get("fas_score", 0) or 0,
            "fas_vol": fas.get("fas_volume_adjusted", 0) or 0,
            "brd": brd.get("brd_score", 0) or 0,
            "cas": cas.get("cas_score", 0) or 0,
            "wA": fas.get("words_a", 0) or 0,
            "wB": fas.get("words_b", 0) or 0,
        })
    return rows


def hl_lh(rows):
    def cat(r):
        sev = r["sev"]
        pos = r["pos"]
        if abs(sev) < NEAR_BALANCED_THRESH:
            return "BAL"
        if sev > 0:
            return "HL" if pos == "alpha" else "LH"
        return "HL" if pos == "beta" else "LH"
    return cat

classify = hl_lh(None)  # placeholder; use lambda below


def fas_hs(r):
    return round(r["fas"] * (1 if r["sev"] > 0 else -1), 3)


def build_analysis_a_block(subset, cond_label, prompt_file, temp):
    get_cat = lambda r: ("BAL" if abs(r["sev"]) < NEAR_BALANCED_THRESH else
                         ("HL" if (r["sev"]>0 and r["pos"]=="alpha") or
                                  (r["sev"]<0 and r["pos"]=="beta") else "LH"))
    hl = [r for r in subset if get_cat(r) == "HL"]
    lh = [r for r in subset if get_cat(r) == "LH"]

    def table(rows, title):
        lines = [f"#### {title} (n={len(rows)})\n"]
        lines.append("| # | Couple | High-sev | sev_diff | Cell | Pos | "
                     "FAS | FAS-vol | FAS_hs | BRD | CAS | wA | wB |")
        lines.append("|" + "|".join(["---"]*13) + "|")
        for i, r in enumerate(rows, 1):
            lines.append(
                f"| {i} | {r['couple']} | {r['high_sev']} | {r['sev']:+.2f} | "
                f"{r['cell']} | {r['pos']} | {r['fas']:+.3f} | {r['fas_vol']:+.3f} | "
                f"**{fas_hs(r):+.3f}** | {r['brd']:+.2f} | {r['cas']:+d} | "
                f"{r['wA']} | {r['wB']} |"
            )
        if rows:
            lines.append(
                f"| **Mean** | — | — | — | — | — | "
                f"**{mean(r['fas'] for r in rows):+.3f}** | "
                f"{mean(r['fas_vol'] for r in rows):+.3f} | "
                f"**{mean(fas_hs(r) for r in rows):+.3f}** | "
                f"{mean(r['brd'] for r in rows):+.2f} | "
                f"{mean(r['cas'] for r in rows):+.2f} | "
                f"{round(mean(r['wA'] for r in rows))} | "
                f"{round(mean(r['wB'] for r in rows))} |"
            )
        return "\n".join(lines)

    lines = [f"### Condition: {cond_label} | temp={temp} (`{prompt_file}`)\n"]
    lines.append(table(hl, "Table HL — high-severity patient speaks first"))
    lines.append("\n")
    lines.append(table(lh, "Table LH — low-severity patient speaks first"))
    return "\n".join(lines), hl, lh


def rebuild_report():
    rows = load_all_compare_sessions()
    temps = sorted(set(r["temp"] for r in rows))
    conds = [("std", "Standard", "therapist_prompt.txt"),
             ("open", "Open",     "therapist_prompt_open.txt")]

    report = ["# Prompt Comparison Analysis (Analysis A format)\n"]
    report.append(
        "**Design:** 8 pairs × 2 conditions × 3 temperatures × 2 positions = 96 sessions total. "
        "GPT-4o, LLM-Based Selection. Near-balanced couples (|sev_diff| < 0.40) excluded.\n"
    )

    # Per-temperature condition blocks
    all_means = {}  # (cond_label, temp, hl_lh) -> mean FAS_hs
    for t in temps:
        report.append(f"---\n\n## Temperature = {t}\n")
        for cond_key, cond_label, prompt_file in conds:
            subset = [r for r in rows if r["condition"] == cond_key and r["temp"] == t]
            if not subset:
                continue
            block, hl, lh = build_analysis_a_block(subset, cond_label, prompt_file, t)
            report.append(block)
            report.append("\n")
            all_means[(cond_key, t, "HL")] = round(mean(fas_hs(r) for r in hl), 3) if hl else None
            all_means[(cond_key, t, "LH")] = round(mean(fas_hs(r) for r in lh), 3) if lh else None

    # Summary comparison table
    report.append("---\n\n## Summary: Mean FAS_hs across all conditions and temperatures\n")
    header_cols = []
    for cond_key, cond_label, _ in conds:
        for t in temps:
            header_cols.append(f"{cond_label} t={t}")
    report.append("| Condition | " + " | ".join(header_cols) + " |")
    report.append("|---| " + " | ".join(["---"]*len(header_cols)) + " |")
    for hl_lh_label in ["HL", "LH"]:
        row_vals = []
        for cond_key, _, _ in conds:
            for t in temps:
                v = all_means.get((cond_key, t, hl_lh_label))
                row_vals.append(f"**{v:+.3f}**" if v is not None else "—")
        report.append(f"| {hl_lh_label} | " + " | ".join(row_vals) + " |")

    # Delta table (open - standard) per temperature
    report.append("\n## Delta table: Open minus Standard (FAS_hs) by temperature\n")
    report.append("| Condition | Temp | Std FAS_hs | Open FAS_hs | Delta |")
    report.append("|---|---|---:|---:|---:|")
    for hl_lh_label in ["HL", "LH"]:
        for t in temps:
            s = all_means.get(("std",  t, hl_lh_label))
            o = all_means.get(("open", t, hl_lh_label))
            if s is not None and o is not None:
                delta = round(o - s, 3)
                report.append(f"| {hl_lh_label} | {t} | {s:+.3f} | {o:+.3f} | **{delta:+.3f}** |")

    REPORT_OUT.write_text("\n".join(report), encoding="utf-8")
    print(f"\nReport written: {REPORT_OUT}  ({len(rows)} sessions across {len(temps)} temps)")


def main():
    total = len(NEW_TEMPERATURES) * len(PAIRS) * len(CONDITIONS) * 2
    print(f"\n  PROMPT COMPARE (temps {NEW_TEMPERATURES}): {total} new sessions")
    assets = load_all_assets()

    for temperature in NEW_TEMPERATURES:
        for mode_label, therapist_mode in CONDITIONS:
            print(f"\n{'#'*70}")
            print(f"  temp={temperature}  condition={mode_label}")
            print('#'*70)
            for cfg in PAIRS:
                for position in ["alpha", "beta"]:
                    t_tag = f"t{int(temperature*10):02d}"
                    out_file = OUTPUT_DIR / f"pilot_compare_{mode_label}_{cfg['couple']}_{cfg['cell']}_{t_tag}_{position}.json"
                    if out_file.exists():
                        print(f"  skip (exists): {out_file.name}")
                        continue
                    try:
                        run_one(assets, cfg, mode_label, therapist_mode, temperature, position)
                    except Exception as e:
                        import traceback; traceback.print_exc()
                    time.sleep(3)

    print("\n  Rebuilding report with all temperatures...")
    rebuild_report()


if __name__ == "__main__":
    main()
