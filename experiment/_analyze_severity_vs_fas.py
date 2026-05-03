"""
Analyze whether the therapist favors the more-severely-presenting patient.

For each session:
  severity_diff = overall_A - overall_B  (positive = A more severe)
  FAS_signed    = raw FAS                (positive = A favored)

If therapist favors severity, sign(FAS) should track sign(severity_diff)
and r(FAS, severity_diff) should be > 0.

Scope:
  - 5 pilot pairs (10 sessions): pilot_*.json
  - earlier 2-session C7 sample: sample_C7_*.json
  - C5 batch (40 sessions, T349-T388 range): therapy_transcript_*.json
"""
import json
import re
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RATINGS_DIR = ROOT / "LLM_rater" / "ratings"
TR_DIR = ROOT / "transcripts"


def load_severity():
    out = {}
    for f in sorted(RATINGS_DIR.glob("C*.json")):
        d = json.load(open(f, encoding="utf-8"))
        cid = d["couple_id"]
        a_overall = d["patient_A"]["overall_score"]
        b_overall = d["patient_B"]["overall_score"]
        a_vec = d["patient_A"]["consensus_vector"]
        b_vec = d["patient_B"]["consensus_vector"]
        out[cid] = {
            "name_A": d["patient_A"]["name"],
            "name_B": d["patient_B"]["name"],
            "overall_A": a_overall,
            "overall_B": b_overall,
            "diff": round(a_overall - b_overall, 2),
            "vec_A": a_vec,
            "vec_B": b_vec,
        }
    return out


def extract_session(path):
    d = json.load(open(path, encoding="utf-8"))
    em = d.get("experiment_metadata", {}) or {}
    cid = em.get("couple_id")
    pos = em.get("position")
    bid_a = em.get("bid_style_a")
    bid_b = em.get("bid_style_b")
    if cid is None:
        # try participant_details for couple inference
        couple_id = (d.get("participant_details", {}).get("patient_A", {})
                     .get("couple_id"))
        cid = couple_id
    tb = d.get("therapeutic_balance", {}) or {}
    fas_obj = tb.get("fas") or {}
    brd_obj = tb.get("brd") or {}
    cas_obj = tb.get("cas") or {}
    return {
        "file": path.name,
        "couple": cid,
        "position": pos,
        "bid_a": bid_a, "bid_b": bid_b,
        "fas": fas_obj.get("fas_score"),
        "fas_vol": fas_obj.get("fas_volume_adjusted"),
        "words_a": fas_obj.get("words_a"),
        "words_b": fas_obj.get("words_b"),
        "brd": brd_obj.get("brd_score"),
        "cas": cas_obj.get("cas_score"),
    }


def corr(xs, ys):
    if len(xs) < 3:
        return float("nan")
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return num / (dx * dy) if (dx and dy) else float("nan")


def main():
    sev = load_severity()
    print("=" * 78)
    print("SEVERITY PROFILE PER COUPLE (overall_A - overall_B; +ve = A more severe)")
    print("=" * 78)
    print(f"{'couple':<6} {'A':<22} {'B':<22} {'A-overall':>10} {'B-overall':>10} {'diff':>7}")
    for c, s in sorted(sev.items()):
        print(f"{c:<6} {s['name_A']:<22} {s['name_B']:<22} "
              f"{s['overall_A']:>10.2f} {s['overall_B']:>10.2f} {s['diff']:>+7.2f}")

    # Gather pilot sessions
    sessions = []
    for p in sorted(TR_DIR.glob("pilot_*.json")):
        sessions.append(extract_session(p))
    for p in sorted(TR_DIR.glob("pilot2_*.json")):
        sessions.append(extract_session(p))
    for p in sorted(TR_DIR.glob("sample_C*.json")):
        sessions.append(extract_session(p))
    # C5 matrix-run sessions (those with experiment_metadata.matrix_run)
    for p in sorted(TR_DIR.glob("therapy_transcript_*.json")):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        em = d.get("experiment_metadata", {}) or {}
        if not em.get("matrix_run"):
            continue
        sessions.append(extract_session(p))

    # Attach severity_diff
    for s in sessions:
        if s["couple"] in sev and s["fas"] is not None:
            s["sev_diff"] = sev[s["couple"]]["diff"]
        else:
            s["sev_diff"] = None

    valid = [s for s in sessions if s["sev_diff"] is not None and s["fas"] is not None]
    print(f"\nLoaded {len(valid)} sessions with severity + FAS")

    # 1. Pilot batch view
    pilots = [s for s in valid if s["file"].startswith("pilot_")]
    print("\n" + "=" * 78)
    print(f"PILOT BATCH ({len(pilots)} sessions)")
    print("=" * 78)
    print(f"{'file':<48} {'cpl':<4} {'pos':<5} {'sev_diff':>9} {'FAS':>7} {'FAS_vol':>8} {'sign_match':>11}")
    for s in pilots:
        match = "y" if (s["sev_diff"] != 0 and s["fas"] != 0
                        and ((s["sev_diff"] > 0) == (s["fas"] > 0))) else \
                ("0" if s["fas"] == 0 or s["sev_diff"] == 0 else "n")
        print(f"{s['file']:<48} {s['couple']:<4} {s['position']:<5} "
              f"{s['sev_diff']:>+9.2f} {s['fas']:>+7.3f} "
              f"{s['fas_vol'] if s['fas_vol'] is not None else 0:>+8.3f} {match:>11}")

    # Correlations
    def safe_pairs(rows, k):
        xs = [r["sev_diff"] for r in rows if r.get(k) is not None]
        ys = [r[k] for r in rows if r.get(k) is not None]
        return xs, ys

    print("\n--- Correlations across pilot sessions (n={}):".format(len(pilots)))
    for k in ("fas", "fas_vol", "brd", "cas"):
        xs, ys = safe_pairs(pilots, k)
        r = corr(xs, ys)
        print(f"  r(severity_diff, {k:<8}) = {r:+.3f}  (n={len(xs)})")

    # 2. All pooled (pilot + sample + matrix C5)
    print("\n" + "=" * 78)
    print(f"POOLED ({len(valid)} sessions: pilot + sample + C5 matrix)")
    print("=" * 78)
    print("--- Correlations across all sessions:")
    for k in ("fas", "fas_vol", "brd", "cas"):
        xs, ys = safe_pairs(valid, k)
        r = corr(xs, ys)
        print(f"  r(severity_diff, {k:<8}) = {r:+.3f}  (n={len(xs)})")

    # 3. Per-couple aggregate FAS (mean across sessions for that couple)
    print("\n--- Per-couple mean FAS vs severity diff:")
    print(f"{'cpl':<4} {'sev_diff':>9} {'n_sess':>7} {'mean_FAS':>10} "
          f"{'mean_FAS_vol':>14} {'mean_BRD':>10}")
    by_couple = {}
    for s in valid:
        by_couple.setdefault(s["couple"], []).append(s)
    for c, rows in sorted(by_couple.items()):
        sd = sev[c]["diff"]
        mfas = mean(r["fas"] for r in rows if r["fas"] is not None)
        mfasv_list = [r["fas_vol"] for r in rows if r["fas_vol"] is not None]
        mfasv = mean(mfasv_list) if mfasv_list else float("nan")
        mbrd_list = [r["brd"] for r in rows if r["brd"] is not None]
        mbrd = mean(mbrd_list) if mbrd_list else float("nan")
        print(f"{c:<4} {sd:>+9.2f} {len(rows):>7} {mfas:>+10.3f} "
              f"{mfasv:>+14.3f} {mbrd:>+10.3f}")

    # Compute couple-level correlation (1 pt per couple)
    cs = sorted(by_couple.keys())
    sds = [sev[c]["diff"] for c in cs]
    mfas_c = [mean(r["fas"] for r in by_couple[c] if r["fas"] is not None) for c in cs]
    mbrd_c = []
    for c in cs:
        b = [r["brd"] for r in by_couple[c] if r["brd"] is not None]
        mbrd_c.append(mean(b) if b else 0.0)
    print(f"\n--- Couple-level correlation (n={len(cs)} couples):")
    print(f"  r(severity_diff, mean_FAS) = {corr(sds, mfas_c):+.3f}")
    print(f"  r(severity_diff, mean_BRD) = {corr(sds, mbrd_c):+.3f}")

    # 4. Per-dimension severity check on pilots (which dimension predicts FAS best?)
    print("\n" + "=" * 78)
    print("PER-DIMENSION SEVERITY DIFF vs PILOT FAS")
    print("=" * 78)
    dims = ["anxiety", "depression", "trauma", "attachment_disorganisation",
            "escalation_tendency"]
    print(f"  Pearson r between dim_diff (A-B) and FAS, across {len(pilots)} pilot sessions:")
    for d in dims:
        xs = []
        ys = []
        for s in pilots:
            if s["fas"] is None or s["couple"] not in sev:
                continue
            va = sev[s["couple"]]["vec_A"][d]
            vb = sev[s["couple"]]["vec_B"][d]
            xs.append(va - vb)
            ys.append(s["fas"])
        r = corr(xs, ys)
        print(f"  r({d:<28} diff, FAS) = {r:+.3f}  (n={len(xs)})")


if __name__ == "__main__":
    main()
