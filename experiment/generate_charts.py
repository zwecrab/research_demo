"""
Generate stacked column charts for test experiment analysis.

Chart 1: Position Effect -- DELTA metrics (alpha - beta) per swapped pair
Chart 2: Bid-Style Pairing -- Mean DELTA metrics grouped by bid-style

Usage:
    python experiment/generate_charts.py
"""

import json
from pathlib import Path
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

EXPERIMENT_DIR = Path(__file__).parent
TRANSCRIPT_DIR = EXPERIMENT_DIR / "transcripts"
OUTPUT_DIR = EXPERIMENT_DIR

CELL_META = {
    1: {"a_bid": "aggressive", "b_bid": "aggressive", "label": "Aggr+Aggr"},
    2: {"a_bid": "aggressive", "b_bid": "assertive",  "label": "Aggr+Assert"},
    3: {"a_bid": "aggressive", "b_bid": "passive",    "label": "Aggr+Pass"},
    4: {"a_bid": "assertive",  "b_bid": "aggressive",  "label": "Assert+Aggr"},
    5: {"a_bid": "assertive",  "b_bid": "assertive",   "label": "Assert+Assert"},
    6: {"a_bid": "assertive",  "b_bid": "passive",     "label": "Assert+Pass"},
    7: {"a_bid": "passive",    "b_bid": "aggressive",   "label": "Pass+Aggr"},
    8: {"a_bid": "passive",    "b_bid": "assertive",    "label": "Pass+Assert"},
    9: {"a_bid": "passive",    "b_bid": "passive",      "label": "Pass+Pass"},
}

COLORS = {
    "FAS": "#E74C3C",   # red
    "BRD": "#27AE60",   # green
    "CAS": "#2980B9",   # blue
}


def load_transcript(filepath):
    with open(filepath, encoding="utf-8") as f:
        d = json.load(f)
    tb = d.get("therapeutic_balance", {})
    fname = Path(filepath).stem
    parts = fname.split("_")
    cell_num = int(parts[1].replace("cell", ""))
    model = parts[2]
    position = parts[3]
    return {
        "file": fname,
        "cell": cell_num,
        "model": model,
        "position": position,
        "fas": tb.get("fas", {}).get("fas_score"),
        "brd": tb.get("brd", {}).get("brd_score"),
        "cas": tb.get("cas", {}).get("cas_score"),
    }


def load_all():
    records = []
    for f in sorted(TRANSCRIPT_DIR.glob("test_cell*.json")):
        records.append(load_transcript(f))
    return records


def compute_deltas(records):
    pairs = defaultdict(dict)
    for r in records:
        pairs[(r["cell"], r["model"])][r["position"]] = r

    deltas = []
    for (cell, model), pos_dict in sorted(pairs.items()):
        if "alpha" not in pos_dict or "beta" not in pos_dict:
            continue
        a = pos_dict["alpha"]
        b = pos_dict["beta"]
        d_fas = (a["fas"] - b["fas"]) if a["fas"] is not None and b["fas"] is not None else None
        d_brd = (a["brd"] - b["brd"]) if a["brd"] is not None and b["brd"] is not None else None
        d_cas = (a["cas"] - b["cas"]) if a["cas"] is not None and b["cas"] is not None else None
        bid_label = CELL_META.get(cell, {}).get("label", "?")
        deltas.append({
            "cell": cell, "model": model, "bid_label": bid_label,
            "d_fas": d_fas, "d_brd": d_brd, "d_cas": d_cas,
        })
    return deltas


# =========================================================================
# CHART 1: Position Effect (per swapped pair)
# =========================================================================

def chart_position_effect(deltas):
    """Grouped bar chart: DELTA_FAS, DELTA_BRD, DELTA_CAS per swapped pair."""
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    fig.suptitle("Position Effect: Delta Metrics (Alpha - Beta) per Swapped Pair",
                 fontsize=14, fontweight="bold", y=0.98)

    labels = [f"C{d['cell']}\n{d['model'][:3].upper()}" for d in deltas]
    x = np.arange(len(deltas))
    width = 0.6

    metrics = [
        ("DELTA_FAS", "d_fas", COLORS["FAS"], "Framing Adoption Score"),
        ("DELTA_BRD", "d_brd", COLORS["BRD"], "Bid Responsiveness Differential"),
        ("DELTA_CAS", "d_cas", COLORS["CAS"], "Challenge Asymmetry Score"),
    ]

    for ax, (metric_name, key, color, title) in zip(axes, metrics):
        vals = [d[key] if d[key] is not None else 0 for d in deltas]
        bar_colors = [color if v >= 0 else "#95A5A6" for v in vals]

        bars = ax.bar(x, vals, width, color=bar_colors, edgecolor="white", linewidth=0.5)
        ax.axhline(y=0, color="black", linewidth=0.8, linestyle="-")
        ax.set_ylabel(metric_name, fontsize=10, fontweight="bold")
        ax.set_title(title, fontsize=10, loc="left", style="italic", color="#555")
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Add value labels on bars
        for bar, val in zip(bars, vals):
            if val != 0:
                va = "bottom" if val >= 0 else "top"
                ax.text(bar.get_x() + bar.get_width() / 2, val,
                        f"{val:+.1f}", ha="center", va=va, fontsize=6.5, fontweight="bold")

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(labels, fontsize=7, rotation=0)
    axes[-1].set_xlabel("Cell / Model (8B = Llama 8B, 70B = Llama 70B)", fontsize=9)

    # Add annotation
    fig.text(0.5, 0.01,
             "Positive = first speaker (A) advantage  |  Negative = second speaker (B) advantage  |  Gray bars = negative values",
             ha="center", fontsize=8, color="#666", style="italic")

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    out_path = OUTPUT_DIR / "chart_position_effect.png"
    plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  Saved: {out_path}")
    return out_path


# =========================================================================
# CHART 2: Bid-Style Pairing Effect
# =========================================================================

def chart_bid_style(deltas):
    """Grouped bar chart: Mean DELTA metrics grouped by bid-style pairing."""
    bid_order = ["Aggr+Aggr", "Aggr+Assert", "Aggr+Pass",
                 "Assert+Aggr", "Assert+Assert", "Assert+Pass",
                 "Pass+Aggr", "Pass+Assert", "Pass+Pass"]

    by_bid = defaultdict(list)
    for d in deltas:
        by_bid[d["bid_label"]].append(d)

    # Compute means per bid style
    bid_labels = []
    mean_fas = []
    mean_brd = []
    mean_cas = []
    n_pairs = []

    for bid in bid_order:
        ds = by_bid.get(bid, [])
        if not ds:
            continue
        bid_labels.append(bid)
        n_pairs.append(len(ds))
        fas_vals = [d["d_fas"] for d in ds if d["d_fas"] is not None]
        brd_vals = [d["d_brd"] for d in ds if d["d_brd"] is not None]
        cas_vals = [d["d_cas"] for d in ds if d["d_cas"] is not None]
        mean_fas.append(sum(fas_vals) / len(fas_vals) if fas_vals else 0)
        mean_brd.append(sum(brd_vals) / len(brd_vals) if brd_vals else 0)
        mean_cas.append(sum(cas_vals) / len(cas_vals) if cas_vals else 0)

    x = np.arange(len(bid_labels))
    width = 0.25

    fig, ax = plt.subplots(figsize=(14, 6))
    fig.suptitle("Bid-Style Pairing Effect: Mean Delta Metrics (Alpha - Beta)",
                 fontsize=14, fontweight="bold")

    bars_fas = ax.bar(x - width, mean_fas, width, label="DELTA_FAS",
                      color=COLORS["FAS"], edgecolor="white", linewidth=0.5)
    bars_brd = ax.bar(x, mean_brd, width, label="DELTA_BRD",
                      color=COLORS["BRD"], edgecolor="white", linewidth=0.5)
    bars_cas = ax.bar(x + width, mean_cas, width, label="DELTA_CAS",
                      color=COLORS["CAS"], edgecolor="white", linewidth=0.5)

    ax.axhline(y=0, color="black", linewidth=0.8, linestyle="-")
    ax.set_ylabel("Mean Delta (Alpha - Beta)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Bid-Style Pairing (Patient A + Patient B)", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(bid_labels, fontsize=9, rotation=30, ha="right")
    ax.legend(fontsize=9, loc="upper left", framealpha=0.9)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Value labels
    for bars in [bars_fas, bars_brd, bars_cas]:
        for bar in bars:
            val = bar.get_height()
            if abs(val) > 0.05:
                va = "bottom" if val >= 0 else "top"
                ax.text(bar.get_x() + bar.get_width() / 2, val,
                        f"{val:+.2f}", ha="center", va=va, fontsize=7, fontweight="bold")

    # Add n per group
    for i, n in enumerate(n_pairs):
        ax.text(x[i], ax.get_ylim()[0] * 0.95, f"n={n}", ha="center",
                fontsize=7, color="#888", style="italic")

    # Annotation
    fig.text(0.5, -0.02,
             "Positive = first speaker advantage  |  Negative = second speaker advantage  |  n = swapped pairs per group",
             ha="center", fontsize=8, color="#666", style="italic")

    plt.tight_layout()
    out_path = OUTPUT_DIR / "chart_bid_style_effect.png"
    plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  Saved: {out_path}")
    return out_path


# =========================================================================
# CHART 3: Model Comparison
# =========================================================================

def chart_model_comparison(deltas):
    """Grouped bar chart: Mean DELTA metrics by model."""
    by_model = defaultdict(list)
    for d in deltas:
        by_model[d["model"]].append(d)

    models = ["llama8b", "llama70b"]
    model_display = {"llama8b": "Llama 3.1 8B", "llama70b": "Llama 3.1 70B"}

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.suptitle("Model Comparison: Delta Metrics by Model Scale",
                 fontsize=14, fontweight="bold")

    metrics = [
        ("DELTA_FAS", "d_fas", COLORS["FAS"]),
        ("DELTA_BRD", "d_brd", COLORS["BRD"]),
        ("DELTA_CAS", "d_cas", COLORS["CAS"]),
    ]

    for ax, (metric_name, key, color) in zip(axes, metrics):
        means = []
        abs_means = []
        labels = []
        for model in models:
            ds = by_model.get(model, [])
            vals = [d[key] for d in ds if d[key] is not None]
            m = sum(vals) / len(vals) if vals else 0
            am = sum(abs(v) for v in vals) / len(vals) if vals else 0
            means.append(m)
            abs_means.append(am)
            labels.append(model_display.get(model, model))

        x = np.arange(len(models))
        width = 0.35

        bars1 = ax.bar(x - width/2, means, width, label="Mean Delta",
                       color=color, edgecolor="white", alpha=0.8)
        bars2 = ax.bar(x + width/2, abs_means, width, label="|Mean Delta|",
                       color=color, edgecolor="white", alpha=0.4, hatch="//")

        ax.axhline(y=0, color="black", linewidth=0.8)
        ax.set_ylabel(metric_name, fontsize=10, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9)
        ax.legend(fontsize=7, loc="upper right")
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                val = bar.get_height()
                if abs(val) > 0.01:
                    ax.text(bar.get_x() + bar.get_width() / 2, val,
                            f"{val:+.2f}", ha="center",
                            va="bottom" if val >= 0 else "top",
                            fontsize=8, fontweight="bold")

    plt.tight_layout()
    out_path = OUTPUT_DIR / "chart_model_comparison.png"
    plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  Saved: {out_path}")
    return out_path


def main():
    print("\n  Loading transcripts...")
    records = load_all()
    print(f"  Loaded {len(records)} sessions")

    deltas = compute_deltas(records)
    print(f"  Computed {len(deltas)} swapped-pair deltas")

    print("\n  Generating charts...")
    chart_position_effect(deltas)
    chart_bid_style(deltas)
    chart_model_comparison(deltas)

    print("\n  All charts generated.")


if __name__ == "__main__":
    main()
