"""
Build HL/LH session analysis.

For each session in pilot2 + pilot3 + pilot4:
  - Classify as HL (high-severity patient speaks first) or LH (low-severity speaks first)
  - Based on severity_diff per couple and session position (alpha/beta)

Two tables:
  1. HL sessions — high-severity patient speaks first
  2. LH sessions — low-severity patient speaks first

Each table includes all metrics + mean row at bottom.
FAS_highsev = FAS re-signed so positive always means therapist favored high-severity patient.

Output: experiment/hl_lh_analysis.md
"""
import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
TR = ROOT / "transcripts"
RATINGS = ROOT / "LLM_rater" / "ratings"
OUT = ROOT / "experiment" / "hl_lh_analysis.md"

NEAR_BALANCED_THRESHOLD = 0.4


def load_severity():
    out = {}
    for f in sorted(RATINGS.glob("C*.json")):
        d = json.load(open(f, encoding="utf-8"))
        cid = d["couple_id"]
        sa = d["patient_A"]["overall_score"]
        sb = d["patient_B"]["overall_score"]
        out[cid] = {
            "name_A": d["patient_A"]["name"].split()[0],
            "name_B": d["patient_B"]["name"].split()[0],
            "overall_A": sa,
            "overall_B": sb,
            "diff": round(sa - sb, 2),
        }
    return out


def load_sessions(sev):
    rows = []
    for pattern in ["pilot2_*.json", "pilot3_*.json", "pilot4_*.json"]:
        for f in sorted(TR.glob(pattern)):
            d = json.load(open(f, encoding="utf-8"))
            em = d.get("experiment_metadata", {}) or {}
            tb = d.get("therapeutic_balance", {}) or {}
            fas = (tb.get("fas") or {})
            brd = (tb.get("brd") or {})
            cas = (tb.get("cas") or {})
            cid = em.get("couple_id")
            pos = em.get("position")
            if cid not in sev or fas.get("fas_score") is None:
                continue
            s = sev[cid]
            sd = s["diff"]
            if abs(sd) < NEAR_BALANCED_THRESHOLD:
                cat = "BALANCED"
            elif sd > 0:
                cat = "HL" if pos == "alpha" else "LH"
            else:
                cat = "HL" if pos == "beta" else "LH"
            fas_raw = fas.get("fas_score", 0) or 0
            fas_vol = fas.get("fas_volume_adjusted") or 0
            brd_v = brd.get("brd_score") or 0
            cas_v = cas.get("cas_score") or 0
            sign = 1 if sd > 0 else -1
            rows.append({
                "file": f.name,
                "couple": cid,
                "pos": pos,
                "cat": cat,
                "sev_diff": sd,
                "high_sev_name": s["name_A"] if sd > 0 else s["name_B"],
                "low_sev_name": s["name_B"] if sd > 0 else s["name_A"],
                "fas": round(fas_raw, 3),
                "fas_vol": round(fas_vol, 3),
                "fas_hs": round(fas_raw * sign, 3),
                "fasv_hs": round(fas_vol * sign, 3),
                "brd": round(brd_v, 3),
                "cas": cas_v,
                "wA": fas.get("words_a") or 0,
                "wB": fas.get("words_b") or 0,
                "bid_a": em.get("bid_style_a", ""),
                "bid_b": em.get("bid_style_b", ""),
                "mode": em.get("therapist_mode", ""),
                "structure": em.get("structure", ""),
            })
    return rows


def fmt(v, decimals=3):
    if v is None:
        return "—"
    if isinstance(v, int):
        return f"{v:+d}"
    return f"{v:+.{decimals}f}"


def build_table(rows, title):
    lines = []
    lines.append(f"### {title} (n={len(rows)})\n")
    lines.append(
        "| # | Couple | High-sev | Low-sev | sev_diff | Bids | Pos | "
        "FAS | FAS-vol | FAS_highsev | FASv_highsev | BRD | CAS | wA | wB |"
    )
    lines.append("|" + "|".join(["---"] * 15) + "|")
    for i, r in enumerate(rows, 1):
        bids = f"{r['bid_a'][:3]}+{r['bid_b'][:3]}"
        lines.append(
            f"| {i} | {r['couple']} | {r['high_sev_name']} ({r['sev_diff']:+.2f}) | "
            f"{r['low_sev_name']} | {r['sev_diff']:+.2f} | {bids} | {r['pos']} | "
            f"{fmt(r['fas'])} | {fmt(r['fas_vol'])} | **{fmt(r['fas_hs'])}** | "
            f"{fmt(r['fasv_hs'])} | {fmt(r['brd'])} | {fmt(r['cas'])} | "
            f"{r['wA']} | {r['wB']} |"
        )
    # Mean row
    def avg(key):
        vals = [r[key] for r in rows if r[key] is not None]
        return round(mean(vals), 3) if vals else None
    fas_m = avg("fas"); fasv_m = avg("fas_vol")
    hs_m = avg("fas_hs"); hsv_m = avg("fasv_hs")
    brd_m = avg("brd"); cas_m = avg("cas")
    wA_m = round(mean(r["wA"] for r in rows)); wB_m = round(mean(r["wB"] for r in rows))
    lines.append(
        f"| **Mean** | — | — | — | — | — | — | "
        f"**{fmt(fas_m)}** | {fmt(fasv_m)} | **{fmt(hs_m)}** | "
        f"{fmt(hsv_m)} | {fmt(brd_m)} | {fmt(cas_m)} | "
        f"{wA_m} | {wB_m} |"
    )
    return "\n".join(lines)


def main():
    sev = load_severity()
    rows = load_sessions(sev)
    hl = [r for r in rows if r["cat"] == "HL"]
    lh = [r for r in rows if r["cat"] == "LH"]
    bal = [r for r in rows if r["cat"] == "BALANCED"]

    lines = []
    lines.append("# HL / LH Session Analysis\n")
    lines.append(
        "**Source:** pilot 2 + pilot 3 + pilot 4 (n=28 sessions total; "
        f"HL={len(hl)}, LH={len(lh)}, near-balanced excluded={len(bal)}).\n"
    )
    lines.append(
        "**HL** = high-severity patient speaks first (alpha position if sev_diff > 0, "
        "beta position if sev_diff < 0).  \n"
        "**LH** = low-severity patient speaks first (opposite mapping).  \n"
        "**sev_diff** = overall_A − overall_B from LLM rater consensus (positive = A more severe).  \n"
        "**FAS_highsev** = FAS re-signed so positive always means therapist adopted the high-severity "
        "partner's framing, regardless of A/B label. Core measure for this analysis.  \n"
        "Near-balanced couples (|sev_diff| < 0.40) excluded: "
        f"{', '.join(sorted(set(r['couple'] for r in bal)))}.  \n"
    )
    lines.append("---\n")
    lines.append(build_table(hl, "Table 1 — HL sessions: high-severity patient speaks first"))
    lines.append("\n---\n")
    lines.append(build_table(lh, "Table 2 — LH sessions: low-severity patient speaks first"))
    lines.append("\n---\n")
    lines.append("## Interpretation\n")

    # Compute mean FAS_hs for HL vs LH
    hl_hs = round(mean(r["fas_hs"] for r in hl), 3)
    lh_hs = round(mean(r["fas_hs"] for r in lh), 3)
    hl_raw = round(mean(r["fas"] for r in hl), 3)
    lh_raw = round(mean(r["fas"] for r in lh), 3)

    lines.append(
        f"| Condition | n | Mean FAS (raw) | Mean FAS_highsev | Interpretation |\n"
        f"|---|---:|---:|---:|---|\n"
        f"| HL (high-sev first) | {len(hl)} | {hl_raw:+.3f} | **{hl_hs:+.3f}** | "
        f"{'Therapist adopted high-sev frame' if hl_hs > 0.05 else 'Balanced / no strong preference'} |\n"
        f"| LH (low-sev first) | {len(lh)} | {lh_raw:+.3f} | **{lh_hs:+.3f}** | "
        f"{'Therapist still adopted high-sev frame despite speaking second' if lh_hs > 0.05 else 'Mixed'} |\n"
    )
    lines.append(
        "\n**Key question:** If FAS_highsev > 0 in both HL and LH conditions, the therapist "
        "favors the high-severity patient *regardless* of speaking order — severity dominates position. "
        "If FAS_highsev > 0 in HL but ≈ 0 (or negative) in LH, position moderates severity.\n"
    )

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"  HL mean FAS_highsev = {hl_hs:+.3f}  |  LH mean FAS_highsev = {lh_hs:+.3f}")


if __name__ == "__main__":
    main()
