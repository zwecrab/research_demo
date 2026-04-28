import streamlit as st
import pandas as pd
import json
import os
import sys

# Add parent directory to path since app.py is now in 'app/' folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import backend modules
from experiments_db import init_db, add_experiment_result, get_all_experiments, clear_all_experiments
from batch_experiment import run_v2_experiment
from compare.evaluate_bias import generate_evaluation_report
from data_loader import load_all_assets, apply_bid_style_overlay

# PANAS EMOTION LISTS
POSITIVE_EMOTIONS = ["Interested", "Excited", "Strong", "Enthusiastic", "Proud", "Alert", "Inspired", "Determined", "Attentive", "Active"]
NEGATIVE_EMOTIONS = ["Distressed", "Upset", "Guilty", "Scared", "Hostile", "Irritable", "Ashamed", "Nervous", "Jittery", "Afraid"]

def calculate_panas_shift(json_path, patient_key):
    """Calculate Positive, Negative, and Net PANAS shift from a JSON transcript file."""
    try:
        if not os.path.exists(json_path):
            return 0, 0, 0
            
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        deltas = data.get(f"{patient_key}_PANAS_DELTA", [])
        if not deltas:
            return 0, 0, 0
            
        pos_change = sum([d.get("difference", 0) for d in deltas if d.get("feeling", "").title() in POSITIVE_EMOTIONS])
        neg_change = sum([d.get("difference", 0) for d in deltas if d.get("feeling", "").title() in NEGATIVE_EMOTIONS])
        net_change = pos_change - neg_change
        
        return pos_change, neg_change, net_change
    except Exception as e:
        return 0, 0, 0

def get_structure_from_file(json_path):
    """Extract conversation structure from JSON file."""
    try:
        if not os.path.exists(json_path):
            return "Unknown"
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("conversation_structure", "Unknown")
    except:
        return "Unknown"

def get_alliance_scores(json_path):
    """Extract therapeutic alliance scores from JSON file."""
    try:
        if not os.path.exists(json_path):
            return 0.0, 0.0, 0.0, 0.0
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        ta_data = data.get("therapist_alliance", {})
        validation = ta_data.get("validation", 0.0)
        neutrality = ta_data.get("neutrality", 0.0)
        guidance = ta_data.get("guidance", 0.0)
        overall = ta_data.get("overall", 0.0)
        return validation, neutrality, guidance, overall
    except:
        return 0.0, 0.0, 0.0, 0.0


def get_balance_scores(json_path):
    """
    Extract FAS, BRD, and CAS therapeutic balance scores from a JSON transcript.

    FAS (Framing Adoption Score): -1.0 to +1.0
        Positive = therapist adopts Patient A's framing; negative = Patient B's.
    BRD (Bid Responsiveness Differential): unbounded, typically -3 to +3
        Positive = more depth toward Patient B; negative = more toward Patient A.
    CAS (Challenge Asymmetry Score): integer
        Positive = more challenges to Patient A; negative = more to Patient B.

    Returns (fas, brd, cas) or (None, None, None) if data is absent.
    """
    try:
        if not os.path.exists(json_path):
            return None, None, None
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        balance = data.get("therapeutic_balance", {})
        fas = balance.get("fas", {}).get("fas_score", None)
        brd = balance.get("brd", {}).get("brd_score", None)
        cas = balance.get("cas", {}).get("cas_score", None)
        return fas, brd, cas
    except:
        return None, None, None


# ============================================================================
# BID-STYLE MATRIX HELPERS
# ============================================================================

ALL_BID_STYLES = ["neutral", "passive", "assertive", "aggressive"]
BID_LABELS = {"neutral": "Neutral", "passive": "Passive", "assertive": "Assertive", "aggressive": "Aggressive"}
BID_ORDER = ["passive", "assertive", "aggressive"]  # default matrix; overridden by UI selection

# Short descriptive labels for each couple (paired with couple_id in UI selectors)
COUPLE_TOPIC_LABELS = {
    "C1": "emotional disconnection after parenthood",
    "C2": "silent compliance then eruption (cross-cultural)",
    "C3": "empty-nest transition anxiety",
    "C4": "blended-family gatekeeping",
    "C5": "career vs domestic-labor imbalance",
}

# Fixed experimental parameters for the bid-style matrix (controls for confounds)
MATRIX_FIXED_TEMPERATURE = 0.3
MATRIX_FIXED_TURNS = 30
MATRIX_FIXED_PROGRESS_ARC = False
MATRIX_FIXED_SWAP_MODE = "Position Swap"  # personas stay in slot; only speaking order changes


def extract_cell_metrics(output_json):
    """Extract all grid-relevant metrics from a session output JSON.

    Handles both the new metrics_summary format and the legacy
    therapeutic_balance/therapist_alliance layout.
    """
    ms = output_json.get("metrics_summary") or {}
    if ms.get("fas"):
        fas = ms["fas"].get("score")
        brd = (ms.get("brd") or {}).get("score")
        cas = (ms.get("cas") or {}).get("score")
        ta = (ms.get("therapeutic_alliance") or {}).get("overall")
        pa_net = (ms.get("panas_patient_a") or {}).get("net_change")
        pb_net = (ms.get("panas_patient_b") or {}).get("net_change")
        if pa_net is not None and pb_net is not None:
            return {"fas": fas, "brd": brd, "cas": cas, "ta": ta,
                    "panas_a": pa_net, "panas_b": pb_net}

    balance = output_json.get("therapeutic_balance", {})
    fas = balance.get("fas", {}).get("fas_score")
    brd = balance.get("brd", {}).get("brd_score")
    cas = balance.get("cas", {}).get("cas_score")
    ta = output_json.get("therapist_alliance", {}).get("overall")

    pa_delta = output_json.get("Patient_A_PANAS_DELTA", [])
    pb_delta = output_json.get("Patient_B_PANAS_DELTA", [])
    pa_pos = sum(d.get("difference", 0) for d in pa_delta if d.get("feeling", "").title() in POSITIVE_EMOTIONS)
    pa_neg = sum(d.get("difference", 0) for d in pa_delta if d.get("feeling", "").title() in NEGATIVE_EMOTIONS)
    pb_pos = sum(d.get("difference", 0) for d in pb_delta if d.get("feeling", "").title() in POSITIVE_EMOTIONS)
    pb_neg = sum(d.get("difference", 0) for d in pb_delta if d.get("feeling", "").title() in NEGATIVE_EMOTIONS)

    return {
        "fas": fas,
        "brd": brd,
        "cas": cas,
        "ta": ta,
        "panas_a": pa_pos - pa_neg,
        "panas_b": pb_pos - pb_neg,
    }


def parse_transcript_record(data, source_name=""):
    """Parse a transcript JSON into a flat record for batch analysis.

    Works with both metrics_summary (new) and legacy formats, and
    with both matrix_run-tagged and manually named files.
    Returns None if the file has no usable metrics.
    """
    em = data.get("experiment_metadata") or {}
    ms = data.get("metrics_summary") or {}
    sm = ms.get("session_metadata") or {}

    metrics = extract_cell_metrics(data)
    if metrics.get("fas") is None:
        return None

    return {
        "source_name": source_name,
        "couple_id": em.get("couple_id") or sm.get("couple_id") or "",
        "position": em.get("position") or sm.get("position") or "",
        "bid_style_a": em.get("bid_style_a") or sm.get("bid_style_a") or "",
        "bid_style_b": em.get("bid_style_b") or sm.get("bid_style_b") or "",
        "therapist_mode": em.get("therapist_mode") or sm.get("therapist_mode") or "",
        "structure": em.get("structure") or sm.get("structure") or "",
        "therapist_model": em.get("therapist_model") or sm.get("therapist_model") or "",
        "metrics": metrics,
    }


def _position_color(delta, scale):
    """Diverging color: warm red = positive (FSA), cool blue = negative (SSA)."""
    if delta is None or scale == 0:
        return "#f5f5f5"
    norm = max(-1.0, min(1.0, delta / scale))
    if norm >= 0:
        g = b = int(245 - norm * 110)
        return f"rgb(255,{g},{b})"
    else:
        r = g = int(245 + norm * 110)
        return f"rgb({r},{g},255)"


def render_metric_grid(cells, metric_key, title, scale=1.0, is_int=False,
                       bid_order=None, grid_mode="delta", fsa_sign=+1):
    # grid_mode: "alpha" | "beta" | "delta". fsa_sign: +1, -1, or 0 (no FSA direction).
    # Coloring: alpha uses value*fsa_sign, beta uses value*(-fsa_sign), delta uses delta*fsa_sign.
    # See memory/feedback_verify_sign_conventions.md.
    if bid_order is None:
        bid_order = BID_ORDER

    if grid_mode == "alpha":
        effective_sign = fsa_sign
        caption_mode = "&alpha; values (A speaks first)"
        num_prefix = ""
    elif grid_mode == "beta":
        effective_sign = -fsa_sign
        caption_mode = "&beta; values (B speaks first)"
        num_prefix = ""
    else:
        effective_sign = fsa_sign
        caption_mode = "Position Effect (&Delta; = &alpha; &minus; &beta;)"
        num_prefix = "&Delta; "

    hdr_style = (
        "padding:10px;text-align:center;border:1px solid #555;"
        "background:transparent;color:#ccc;font-weight:bold;"
    )
    html = (
        "<table style='width:100%;border-collapse:collapse;font-family:sans-serif;"
        "font-size:14px;margin:10px 0;'>"
        f"<caption style='font-weight:bold;margin-bottom:8px;font-size:15px;"
        f"color:#ddd;'>{title} &mdash; {caption_mode}</caption>"
        f"<tr><td style='width:90px;'></td>"
    )
    for bs in bid_order:
        html += f"<th style='{hdr_style}'>B: {BID_LABELS.get(bs, bs)}</th>"
    html += "</tr>"

    for a_bs in bid_order:
        html += f"<tr><th style='{hdr_style}'>A: {BID_LABELS.get(a_bs, a_bs)}</th>"
        for b_bs in bid_order:
            cell = cells.get((a_bs, b_bs), {})
            a_val = cell.get(f"alpha_{metric_key}")
            b_val = cell.get(f"beta_{metric_key}")

            if a_val is not None and b_val is not None:
                if grid_mode == "alpha":
                    value = a_val
                elif grid_mode == "beta":
                    value = b_val
                else:
                    value = a_val - b_val

                color_input = value * effective_sign if fsa_sign != 0 else value
                bg = _position_color(color_input, scale)
                v_str = f"{int(value):+d}" if is_int else f"{value:+.2f}"

                if grid_mode == "delta":
                    a_sub = f"{int(a_val):d}" if is_int else f"{a_val:.2f}"
                    b_sub = f"{int(b_val):d}" if is_int else f"{b_val:.2f}"
                    subtext = (
                        f"<br><span style='font-size:11px;color:#444;'>"
                        f"&alpha;:{a_sub} | &beta;:{b_sub}</span>"
                    )
                else:
                    subtext = ""

                html += (
                    f"<td style='padding:12px;text-align:center;border:1px solid #555;"
                    f"background:{bg};'>"
                    f"<b style='font-size:17px;color:#1a1a1a;'>{num_prefix}{v_str}</b>"
                    f"{subtext}</td>"
                )
            else:
                html += (
                    "<td style='padding:12px;text-align:center;border:1px solid #555;"
                    "color:#888;'>&mdash;</td>"
                )
        html += "</tr>"

    html += "</table>"
    if fsa_sign == 0:
        html += (
            "<div style='font-size:11px;color:#aaa;text-align:center;margin-top:4px;'>"
            "<span style='background:rgb(255,135,135);padding:2px 8px;border-radius:3px;"
            "color:#1a1a1a;'>higher value</span> &nbsp; "
            "<span style='background:rgb(135,135,255);padding:2px 8px;border-radius:3px;"
            "color:#1a1a1a;'>lower value</span> &nbsp;"
            "<i>(no FSA direction for this metric)</i></div>"
        )
    else:
        html += (
            "<div style='font-size:11px;color:#aaa;text-align:center;margin-top:4px;'>"
            "<span style='background:rgb(255,135,135);padding:2px 8px;border-radius:3px;"
            "color:#1a1a1a;'>First Speaker Advantage</span> &nbsp; "
            "<span style='background:rgb(135,135,255);padding:2px 8px;border-radius:3px;"
            "color:#1a1a1a;'>Second Speaker Advantage</span></div>"
        )
    return html


# Page Config
st.set_page_config(
    page_title="AI Therapy Experiment Dashboard",
    page_icon="🧠",
    layout="wide"
)

# Initialize DB
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# Load Assets (Cached)
@st.cache_resource
def get_assets():
    return load_all_assets()

try:
    assets = get_assets()
    # Ensure topics are available
    if "therapy_plans" not in assets:
        st.error("Failed to load therapy plans from assets.")
        st.stop()
    topics = list(assets["therapy_plans"].keys())
except Exception as e:
    st.error(f"Error loading assets: {e}")
    st.stop()


# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Run Experiment", "Bid-Style Matrix", "Compare Transcripts", "Results Dashboard", "Batch Results"])

st.sidebar.markdown("---")
st.sidebar.info("🧪 **Bias Evaluation Tool** v1.0\n\nRuns paired simulations (swapping positions) to measure Position Bias (FAS, BRD, CAS, PANAS).")

# ============================================================================
# PAGE: RUN EXPERIMENT
# ============================================================================
if page == "Run Experiment":
    import copy as _copy

    st.title("Run Paired Experiment")
    st.markdown("Run one alpha+beta pair (2 sessions) for a single couple and bid-style combination.")

    v2_couples = assets.get("v2_couples", {})
    bid_styles = assets.get("bid_styles", {})

    if not v2_couples or not bid_styles:
        st.error("V2 personas or bid-styles not loaded.")
        st.stop()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Configuration")

        couple_ids = sorted(v2_couples.keys())
        selected_couple = st.selectbox(
            "Couple", couple_ids,
            format_func=lambda c: f"{c} ({COUPLE_TOPIC_LABELS.get(c, '')})" if c in COUPLE_TOPIC_LABELS else c,
            key="run_couple",
        )
        members = v2_couples[selected_couple]
        st.caption(f"{members[0]['name']} (A) & {members[1]['name']} (B)")

        structure_options = ["Sequential", "LLM-Based Selection"]
        conversation_structure = st.selectbox("Structure", structure_options, key="run_struct")

        therapist_mode = "individual_focus" if st.radio(
            "Therapist Mode", ["Standard", "Individual Focus"], key="run_tmode"
        ) == "Individual Focus" else "standard"

        from config import THERAPIST_MODEL_OPTIONS
        therapist_model_name = st.selectbox(
            "Therapist Model", list(THERAPIST_MODEL_OPTIONS.keys()), key="run_model")
        therapist_model = THERAPIST_MODEL_OPTIONS[therapist_model_name]["model"]

        bid_a = st.selectbox("Bid-style A", ALL_BID_STYLES,
                             format_func=lambda x: BID_LABELS[x], key="run_bid_a")
        bid_b = st.selectbox("Bid-style B", ALL_BID_STYLES,
                             format_func=lambda x: BID_LABELS[x], key="run_bid_b")

        temperature = st.slider("Temperature", 0.0, 1.5, 0.3, 0.1, key="run_temp")
        turn_count = st.number_input("Turns", 5, 100, 30, key="run_turns")

    with col2:
        st.subheader("Experiment Plan")
        st.info(f"""
**Position Swap** (alpha + beta)

1. **Alpha:** {members[0]['name']} (A) speaks first
2. **Beta:** {members[1]['name']} (B) speaks first

Same personas stay in same slots. Both use the unified symmetric prompt. Only speaking order changes.

Bid-style overlay: A = {BID_LABELS[bid_a]}, B = {BID_LABELS[bid_b]}
""")

        if st.button("Start Paired Run", type="primary", key="run_start"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            raw_a, raw_b = members[0], members[1]
            pa = _copy.deepcopy(raw_a)
            pb = _copy.deepcopy(raw_b)
            apply_bid_style_overlay(pa, bid_styles[bid_a])
            apply_bid_style_overlay(pb, bid_styles[bid_b])

            results = {}
            for run_idx, position in enumerate(["alpha", "beta"], 1):
                first_speaker = "Patient A" if position == "alpha" else "Patient B"
                label = f"Run {run_idx}/2 ({position})"
                status_text.text(f"{label}...")

                st.markdown(f"#### {label}: {first_speaker} speaks first")
                stream = st.empty()
                lines = []

                def _stream_cb(speaker, text, emotion_label=None, trajectory=None, _l=lines, _s=stream):
                    badge = ""
                    if emotion_label:
                        icon = {"escalating": "^", "de-escalating": "v", "stable": "-"}.get(trajectory, "")
                        badge = f" `{emotion_label}` {icon}"
                    _l.append(f"**{speaker}**{badge}: {text}")
                    _s.info("\n\n".join(_l))

                metadata = {
                    "matrix_run": False,
                    "couple_id": selected_couple,
                    "position": position,
                    "bid_style_a": bid_a,
                    "bid_style_b": bid_b,
                    "therapist_mode": therapist_mode,
                    "structure": conversation_structure,
                    "therapist_model": therapist_model,
                    "temperature": temperature,
                }

                try:
                    saved_path, output_json = run_v2_experiment(
                        assets, _copy.deepcopy(pa), _copy.deepcopy(pb),
                        conversation_structure, first_speaker,
                        temperature=temperature, turn_limit=turn_count,
                        therapist_mode=therapist_mode, therapist_model=therapist_model,
                        turn_callback=_stream_cb, experiment_metadata=metadata,
                    )
                    results[position] = {"path": saved_path, "json": output_json}
                    st.success(f"{label} saved: {os.path.basename(saved_path)}")
                except Exception as e:
                    st.error(f"{label} failed: {e}")
                    st.exception(e)

                progress_bar.progress(run_idx / 2)

            if len(results) == 2:
                status_text.text("Evaluating position bias...")
                report = generate_evaluation_report(
                    results["alpha"]["path"], results["beta"]["path"],
                    threshold=1, slots_swapped=False,
                )
                add_experiment_result(
                    "V2", turn_count, members[0]["name"], members[1]["name"],
                    str(results["alpha"]["path"]), str(results["beta"]["path"]),
                    report, structure=conversation_structure, swap_mode="Position Swap",
                )
                progress_bar.progress(1.0)
                status_text.text("Complete!")
                st.balloons()
                st.divider()
                st.subheader("Results")
                metrics_a = extract_cell_metrics(results["alpha"]["json"])
                metrics_b = extract_cell_metrics(results["beta"]["json"])
                mc1, mc2, mc3 = st.columns(3)
                d_fas = (metrics_a["fas"] or 0) - (metrics_b["fas"] or 0)
                d_brd = (metrics_a["brd"] or 0) - (metrics_b["brd"] or 0)
                d_cas = (metrics_a["cas"] or 0) - (metrics_b["cas"] or 0)
                mc1.metric("DELTA FAS", f"{d_fas:+.2f}")
                mc2.metric("DELTA BRD", f"{d_brd:+.2f}")
                mc3.metric("DELTA CAS", f"{d_cas:+.1f}")
                with st.expander("Full evaluation report"):
                    st.json(report)

# ============================================================================
# PAGE: BID-STYLE MATRIX
# ============================================================================
elif page == "Bid-Style Matrix":
    st.title("Bid-Style Matrix (V2)")
    st.markdown("Run all 9 bid-style combinations for one couple. Each combo runs in alpha (A first) and beta (B first) positions (18 sessions total).")

    v2_couples = assets.get("v2_couples", {})
    bid_styles = assets.get("bid_styles", {})

    if not v2_couples or not bid_styles:
        st.error("V2 personas or bid-styles not loaded. Check prompts/personas_v2.json and prompts/bid_styles.json.")
        st.stop()

    # Fixed experimental parameters (controls for confounds — not user-selectable)
    from config import DEFAULT_V2_THERAPY_TOPIC
    st.markdown("### Fixed Experimental Parameters")
    st.info(
        f"""
These parameters are **fixed across all matrix runs** to isolate the position-bias signal:

- **Therapy topic:** `{DEFAULT_V2_THERAPY_TOPIC}` (standardized across couples; each couple's `topic_context` feeds the therapist's session goals)
- **Temperature:** `{MATRIX_FIXED_TEMPERATURE}` (low — favors reproducibility over creativity)
- **Turns per session:** `{MATRIX_FIXED_TURNS}` (standardized session length)
- **Session progress arc:** `OFF` (no phase signal — patients receive no Early/Middle/Late cue)
- **Swap mode:** `Position Swap` — personas stay in their slot; bid styles stay attached to their persona; **only speaking order changes** between alpha and beta runs
"""
    )

    col_cfg, col_preview = st.columns([1, 1])

    with col_cfg:
        st.subheader("Configuration")

        couple_ids = sorted(v2_couples.keys())
        def _couple_label(cid):
            topic = COUPLE_TOPIC_LABELS.get(cid, "")
            return f"{cid} ({topic})" if topic else cid
        selected_couple = st.selectbox(
            "Couple",
            couple_ids,
            format_func=_couple_label,
            key="matrix_couple",
        )
        members = v2_couples[selected_couple]
        st.caption(f"{members[0]['name']} (A) & {members[1]['name']} (B)")

        from config import THERAPIST_MODEL_OPTIONS
        model_name = st.selectbox("Therapist Model", list(THERAPIST_MODEL_OPTIONS.keys()), key="matrix_model")
        therapist_model = THERAPIST_MODEL_OPTIONS[model_name]["model"]

        structure = st.selectbox("Structure", ["Sequential", "LLM-Based Selection"], key="matrix_struct")

        therapist_mode_label = st.radio("Therapist Mode", ["Standard", "Individual Focus"], key="matrix_tmode")
        therapist_mode = "individual_focus" if therapist_mode_label == "Individual Focus" else "standard"

        selected_bids = st.multiselect(
            "Bid-styles to include",
            ALL_BID_STYLES,
            default=["passive", "assertive", "aggressive"],
            format_func=lambda x: BID_LABELS[x],
            key="matrix_bids",
            help="Select 'Neutral' for RQ1 (pure position bias, no bid-style overlay).",
        )
        if not selected_bids:
            selected_bids = ["passive", "assertive", "aggressive"]

        temperature = MATRIX_FIXED_TEMPERATURE
        turn_count = MATRIX_FIXED_TURNS

    with col_preview:
        n_bids = len(selected_bids)
        n_cells = n_bids ** 2
        n_sessions = n_cells * 2
        st.subheader(f"{n_bids}x{n_bids} Matrix ({n_sessions} sessions)")
        bid_abbr = {"neutral": "neu", "passive": "pas", "assertive": "ass", "aggressive": "agg"}
        header = "| | " + " | ".join(f"B: {BID_LABELS[b]}" for b in selected_bids) + " |"
        sep = "|---|" + "|".join(["---"] * n_bids) + "|"
        rows_md = ""
        for a in selected_bids:
            cells_md = " | ".join(f"{bid_abbr.get(a,'?')}+{bid_abbr.get(b,'?')}" for b in selected_bids)
            rows_md += f"| **A: {BID_LABELS[a]}** | {cells_md} |\n"
        st.markdown(f"{header}\n{sep}\n{rows_md}\nEach cell = 2 sessions (alpha + beta) = **{n_sessions} sessions total**.")
        est_minutes = turn_count * n_sessions * 4 // 60
        st.info(f"Estimated time: ~{est_minutes} minutes")

    if st.button(f"Run {n_bids}x{n_bids} Matrix", type="primary", key="matrix_run"):
        import copy

        raw_a, raw_b = members[0], members[1]
        total_sessions = n_sessions
        session_num = 0
        cells = {}

        progress = st.progress(0)
        status = st.status("Running bid-style matrix...", expanded=True)

        for bid_a in selected_bids:
            for bid_b in selected_bids:
                cell_data = {}

                for position in ["alpha", "beta"]:
                    session_num += 1
                    first_speaker = "Patient A" if position == "alpha" else "Patient B"
                    label = f"{bid_a}+{bid_b} {position}"

                    status.update(label=f"Session {session_num}/{total_sessions}: {label}")
                    status.write(f"Starting {label}...")

                    pa = copy.deepcopy(raw_a)
                    pb = copy.deepcopy(raw_b)
                    apply_bid_style_overlay(pa, bid_styles[bid_a])
                    apply_bid_style_overlay(pb, bid_styles[bid_b])

                    metadata = {
                        "matrix_run": True,
                        "couple_id": selected_couple,
                        "position": position,
                        "bid_style_a": bid_a,
                        "bid_style_b": bid_b,
                        "therapist_mode": therapist_mode,
                        "structure": structure,
                        "therapist_model": therapist_model,
                        "temperature": temperature,
                    }

                    try:
                        saved_path, output_json = run_v2_experiment(
                            assets, pa, pb, structure, first_speaker,
                            temperature=temperature,
                            turn_limit=turn_count,
                            therapist_mode=therapist_mode,
                            therapist_model=therapist_model,
                            experiment_metadata=metadata,
                        )
                        metrics = extract_cell_metrics(output_json)
                        cell_data[f"{position}_path"] = saved_path
                        for k, v in metrics.items():
                            cell_data[f"{position}_{k}"] = v

                        fas_v = metrics.get("fas", "?")
                        brd_v = metrics.get("brd", "?")
                        cas_v = metrics.get("cas", "?")
                        status.write(f"  {label}: FAS={fas_v}, BRD={brd_v}, CAS={cas_v}")

                    except Exception as e:
                        status.write(f"  {label} FAILED: {e}")

                    progress.progress(session_num / total_sessions)

                cells[(bid_a, bid_b)] = cell_data

        st.session_state.matrix_results = {
            "couple_id": selected_couple,
            "couple_names": f"{members[0]['name']} & {members[1]['name']}",
            "model": model_name,
            "structure": structure,
            "therapist_mode": therapist_mode_label,
            "cells": cells,
            "bid_order": list(selected_bids),
        }
        status.update(label="Matrix complete!", state="complete")
        st.balloons()

    # --- Results Display ---
    if "matrix_results" in st.session_state:
        res = st.session_state.matrix_results
        cells = res["cells"]
        res_bid_order = res.get("bid_order", BID_ORDER)

        st.divider()
        st.subheader(f"Results: {res['couple_names']} | {res['model']} | {res['structure']} | {res['therapist_mode']}")

        metrics_cfg = [
            ("fas", "FAS (Framing Adoption)", 0.5, False, +1),
            ("brd", "BRD (Bid Responsiveness)", 2.0, False, -1),
            ("cas", "CAS (Challenge Asymmetry)", 5.0, True, +1),
            ("ta", "TA (Therapeutic Alliance)", 3.0, False, 0),
            ("panas_a", "PANAS-A (Patient A Outcome)", 10.0, True, +1),
            ("panas_b", "PANAS-B (Patient B Outcome)", 10.0, True, -1),
        ]

        tab_labels = [c[1].split("(")[0].strip() for c in metrics_cfg]
        tabs = st.tabs(tab_labels)

        grid_modes = [("alpha", "Alpha (A speaks first)"),
                      ("beta",  "Beta (B speaks first)"),
                      ("delta", "Delta (&alpha; &minus; &beta;)")]

        for tab, (key, label, scale, is_int, fsa_sign) in zip(tabs, metrics_cfg):
            with tab:
                for mode_key, mode_label in grid_modes:
                    st.markdown(f"**{mode_label}**", unsafe_allow_html=True)
                    grid_html = render_metric_grid(
                        cells, key, label, scale, is_int,
                        bid_order=res_bid_order,
                        grid_mode=mode_key, fsa_sign=fsa_sign,
                    )
                    st.markdown(grid_html, unsafe_allow_html=True)

        st.divider()
        st.subheader("Summary Statistics")
        summary_rows = []
        for a_bs in res_bid_order:
            for b_bs in res_bid_order:
                cell = cells.get((a_bs, b_bs), {})
                row = {"A Bid": BID_LABELS.get(a_bs, a_bs), "B Bid": BID_LABELS.get(b_bs, b_bs)}
                for key, _, _, is_int, _ in metrics_cfg:
                    a_v = cell.get(f"alpha_{key}")
                    b_v = cell.get(f"beta_{key}")
                    if a_v is not None and b_v is not None:
                        delta = a_v - b_v
                        row[f"{key.upper()} alpha"] = int(a_v) if is_int else round(a_v, 3)
                        row[f"{key.upper()} beta"] = int(b_v) if is_int else round(b_v, 3)
                        row[f"{key.upper()} delta"] = int(delta) if is_int else round(delta, 3)
                summary_rows.append(row)

        import pandas as pd
        summary_df = pd.DataFrame(summary_rows)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        if st.button("Clear Matrix Results", key="matrix_clear"):
            del st.session_state.matrix_results
            st.rerun()


# ============================================================================
# PAGE: COMPARE TRANSCRIPTS
# ============================================================================
elif page == "Compare Transcripts":
    st.title("⚖️ Compare Transcripts")
    st.markdown("Upload two existing transcripts (JSON) to evaluate Position Bias. Parameters must match.")

    compare_swap_mode = st.radio(
        "Were these transcripts generated with Persona Swap?",
        ["No (Position Swap)", "Yes (Persona Swap)"],
        index=0,
        key="compare_swap_mode",
        help="If Persona Swap was used, personas swapped slots in Transcript 2 — names will be in opposite Patient A/B slots."
    )
    compare_is_swapped = (compare_swap_mode == "Yes (Persona Swap)")

    f1 = st.file_uploader("Upload Transcript 1 (Before Swapped)", type="json", key="f1")
    f2 = st.file_uploader("Upload Transcript 2 (After Swapped)", type="json", key="f2")

    if f1 and f2:
        try:
            t1 = json.load(f1)
            f1.seek(0) # Reset stream
            t2 = json.load(f2)
            f2.seek(0)

            # --- Validation ---
            st.subheader("Validation")
            errors = []

            # Check Structure
            if t1.get("conversation_structure") != t2.get("conversation_structure"):
                errors.append(f"Structure mismatch: '{t1.get('conversation_structure')}' vs '{t2.get('conversation_structure')}'")

            # Check Topic
            if t1.get("session_topic_header") != t2.get("session_topic_header"):
                errors.append(f"Topic mismatch: '{t1.get('session_topic_header')}' vs '{t2.get('session_topic_header')}'")

            # Check Participants (Names)
            pa1 = t1.get("participant_details", {}).get("patient_A", {}).get("name")
            pb1 = t1.get("participant_details", {}).get("patient_B", {}).get("name")
            pa2 = t2.get("participant_details", {}).get("patient_A", {}).get("name")
            pb2 = t2.get("participant_details", {}).get("patient_B", {}).get("name")

            if compare_is_swapped:
                # In Persona Swap mode, T2 has names in opposite slots
                if pa1 != pb2 or pb1 != pa2:
                    errors.append(f"Participant swap mismatch: T1=({pa1}, {pb1}), T2=({pa2}, {pb2}). Expected T2=({pb1}, {pa1}).")
            else:
                if pa1 != pa2 or pb1 != pb2:
                    errors.append(f"Participant mismatch: ({pa1}, {pb1}) vs ({pa2}, {pb2})")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                st.success("✅ Parameters Match! Ready to compare.")
                
                if st.button("Run Comparison Analysis", type="primary"):
                    with st.spinner("Analyzing..."):
                        # Save temp files for evaluate_bias.py
                        temp_dir = "temp_uploads"
                        os.makedirs(temp_dir, exist_ok=True)
                        
                        p1 = os.path.join(temp_dir, f1.name)
                        p2 = os.path.join(temp_dir, f2.name)
                        
                        # Save content
                        with open(p1, "w", encoding='utf-8') as f:
                            json.dump(t1, f, indent=2)
                        with open(p2, "w", encoding='utf-8') as f:
                            json.dump(t2, f, indent=2)
                            
                        # Run Evaluation
                        report = generate_evaluation_report(
                            p1, p2, threshold=1, slots_swapped=compare_is_swapped
                        )

                        # Save to DB
                        trigger = t1.get("participant_details", {}).get("selected_trigger_type", "Unknown")
                        turns = t1.get("session_transcript", [])[-1].get("turn", 0) if t1.get("session_transcript") else 0

                        structure = t1.get("conversation_structure", "Unknown")
                        cmp_swap_label = "Persona Swap" if compare_is_swapped else "Position Swap"
                        add_experiment_result(
                            trigger, turns, pa1, pb1,
                            p1, p2, report, structure=structure,
                            swap_mode=cmp_swap_label
                        )
                        
                        st.balloons()
                        
                        st.divider()
                        st.subheader("📝 Comparison Results")
                        with st.expander("View JSON Report"):
                            st.json(report)

        except Exception as e:
            st.error(f"Error reading files: {e}")


# ============================================================================
# PAGE: RESULTS DASHBOARD
# ============================================================================
elif page == "Results Dashboard":
    st.title("📊 Results Dashboard")
    
    # Load Data
    df = get_all_experiments()
    
    if df.empty:
        st.warning("No experiments found. Go to 'Run Experiment' to create some data.")
    else:
        # Filters
        st.sidebar.subheader("Filters")
        if "structure" in df.columns:
            structures = st.sidebar.multiselect("Structure", df["structure"].unique(), default=df["structure"].unique())
            df_filtered = df[df["structure"].isin(structures)] 
        
        if "trigger_type" in df.columns:
            triggers = st.sidebar.multiselect("Trigger Type", df["trigger_type"].unique(), default=df["trigger_type"].unique())
            filtered_df = df_filtered[df_filtered["trigger_type"].isin(triggers)].copy() if "structure" in df.columns else df[df["trigger_type"].isin(triggers)].copy()
        else:
            filtered_df = df.copy()

        st.sidebar.divider()
        st.sidebar.subheader("Danger Zone")
        if st.sidebar.button("🗑️ Clear All Data", type="primary"):
            clear_all_experiments()
            st.rerun()

        # Prepare Data for Display (Exploding Rows)
        display_rows = []
        
        for index, row in filtered_df.iterrows():
            t1 = row['t1_path']
            t2 = row['t2_path']
            
            s_struct = get_structure_from_file(t1) # Should be same for both
            
            # --- ROW 1 (Transcript 1 - Patient A First) ---
            a1_pos, a1_neg, a1_net = calculate_panas_shift(t1, "Patient_A")
            b1_pos, b1_neg, b1_net = calculate_panas_shift(t1, "Patient_B")
            ta1_val, ta1_neu, ta1_gui, ta1_ovr = get_alliance_scores(t1)
            fas1, brd1, cas1 = get_balance_scores(t1)

            display_rows.append({
                "ID": row['id'],
                "Run": "Run 1",
                "Timestamp": row['timestamp'],
                "Transcript": os.path.basename(t1),
                "Structure": s_struct,
                "Trigger Type": row.get('trigger_type', ''),
                "Patient A": row['patient_a'],
                "Patient B": row['patient_b'],
                "PA Pos": a1_pos, "PA Neg": a1_neg, "PA Net": a1_net,
                "PB Pos": b1_pos, "PB Neg": b1_neg, "PB Net": b1_net,
                "TA Val": ta1_val, "TA Neu": ta1_neu, "TA Gui": ta1_gui, "TA Ovr": ta1_ovr,
                "FAS": fas1, "BRD": brd1, "CAS": cas1,
            })

            # --- ROW 2 (Transcript 2 - Swapped) ---
            row_swap_mode = row.get('swap_mode', 'Position Swap')
            is_personality_swap = (row_swap_mode == "Persona Swap")

            if is_personality_swap:
                # In Persona Swap mode, original Patient A is now in slot B in t2,
                # and original Patient B is in slot A. Cross-reference PANAS keys.
                a2_pos, a2_neg, a2_net = calculate_panas_shift(t2, "Patient_B")
                b2_pos, b2_neg, b2_net = calculate_panas_shift(t2, "Patient_A")
            else:
                a2_pos, a2_neg, a2_net = calculate_panas_shift(t2, "Patient_A")
                b2_pos, b2_neg, b2_net = calculate_panas_shift(t2, "Patient_B")

            ta2_val, ta2_neu, ta2_gui, ta2_ovr = get_alliance_scores(t2)
            fas2, brd2, cas2 = get_balance_scores(t2)

            # In Persona Swap mode, negate FAS/BRD/CAS so positive still
            # means "original Patient A-aligned" across both runs.
            if is_personality_swap and fas2 is not None:
                fas2 = -fas2
            if is_personality_swap and brd2 is not None:
                brd2 = -brd2
            if is_personality_swap and cas2 is not None:
                cas2 = -cas2

            display_rows.append({
                "ID": row['id'],
                "Run": "Run 2" + (" (Swapped)" if is_personality_swap else ""),
                "Timestamp": row['timestamp'],
                "Transcript": os.path.basename(t2),
                "Structure": s_struct,
                "Trigger Type": row.get('trigger_type', ''),
                "Patient A": row['patient_a'],
                "Patient B": row['patient_b'],
                "PA Pos": a2_pos, "PA Neg": a2_neg, "PA Net": a2_net,
                "PB Pos": b2_pos, "PB Neg": b2_neg, "PB Net": b2_net,
                "TA Val": ta2_val, "TA Neu": ta2_neu, "TA Gui": ta2_gui, "TA Ovr": ta2_ovr,
                "FAS": fas2, "BRD": brd2, "CAS": cas2,
            })

        display_df = pd.DataFrame(display_rows)

        st.subheader("Overview")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Experiments", len(filtered_df))
        if not display_df.empty:
            c2.metric("Avg PA Net Shift", f"{display_df['PA Net'].mean():.2f}")
            c3.metric("Avg PB Net Shift", f"{display_df['PB Net'].mean():.2f}")

        # Main Table
        st.subheader("Experiment History")
        
        final_cols = [
            "ID", "Run", "Transcript", "Structure",
            "Patient A", "Patient B",
            "PA Pos", "PA Neg", "PA Net",
            "PB Pos", "PB Neg", "PB Net",
            "TA Val", "TA Neu", "TA Gui", "TA Ovr",
            "FAS", "BRD", "CAS",
        ]
        
        if not display_df.empty:
            st.dataframe(
                display_df[final_cols],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No data to display.")
        
        # Detail View
        st.subheader("Experiment Details")
        exp_ids = filtered_df["id"].tolist()
        if exp_ids:
            selected_id = st.selectbox("Select Experiment ID to View Details", exp_ids)
            
            if selected_id:
                row = filtered_df[filtered_df["id"] == selected_id].iloc[0]
                report = json.loads(row["report_json"])
                
                st.markdown(f"#### Experiment #{selected_id}: {row['patient_a']} vs {row['patient_b']}")
                
                tab1, tab2, tab3 = st.tabs(["Metrics", "Transcript Viewer", "Metadata"])
                
                with tab1:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"**Patient A ({row['patient_a']})**")
                        det_a = report["details"][row["patient_a"]]
                        panas_a = det_a.get("panas_summary", {})
                        if panas_a:
                            st.write(f"Net PANAS (first): {panas_a.get('net_first', 'N/A')}")
                            st.write(f"Net PANAS (second): {panas_a.get('net_second', 'N/A')}")

                    with col_b:
                        st.markdown(f"**Patient B ({row['patient_b']})**")
                        det_b = report["details"][row["patient_b"]]
                        panas_b = det_b.get("panas_summary", {})
                        if panas_b:
                            st.write(f"Net PANAS (first): {panas_b.get('net_first', 'N/A')}")
                            st.write(f"Net PANAS (second): {panas_b.get('net_second', 'N/A')}")
                
                with tab2:
                    # Utility to load text content from session transcript
                    def get_transcript_dialogue(path):
                        if os.path.exists(path):
                            try:
                                with open(path, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                return data.get('session_transcript', [])
                            except:
                                return []
                        return []

                    t1_turns = get_transcript_dialogue(row['t1_path'])
                    t2_turns = get_transcript_dialogue(row['t2_path'])
                    
                    t_col1, t_col2 = st.columns(2)
                    
                    with t_col1:
                        st.markdown(f"**Run 1: {row['patient_a']} First**")
                        for turn in t1_turns:
                            spk = turn.get('speaker', 'Unknown')
                            txt = turn.get('dialogue', '')
                            if spk == "Therapist":
                                st.info(f"**{spk}**: {txt}")
                            elif spk == row['patient_a']:
                                st.warning(f"**{spk}**: {txt}")
                            else:
                                st.success(f"**{spk}**: {txt}")

                    with t_col2:
                        st.markdown(f"**Run 2: {row['patient_b']} First**")
                        for turn in t2_turns:
                            spk = turn.get('speaker', 'Unknown')
                            txt = turn.get('dialogue', '')
                            if spk == "Therapist":
                                st.info(f"**{spk}**: {txt}")
                            elif spk == row['patient_a']:
                                st.warning(f"**{spk}**: {txt}")
                            else:
                                st.success(f"**{spk}**: {txt}")

                with tab3:
                    st.write(f"**Run 1 Path:** `{row['t1_path']}`")
                    st.write(f"**Run 2 Path:** `{row['t2_path']}`")
                    st.json(report["meta"])


# ============================================================================
# PAGE: BATCH RESULTS
# ============================================================================
elif page == "Batch Results":
    import glob as glib
    import statistics as _st

    st.title("Batch Results")
    st.markdown("Load saved transcript JSONs from a previous matrix batch. Renders the bid-style grid, summary table, and spread statistics.")

    source = st.radio("Source", ["Scan transcripts/ folder", "Upload JSON files"], horizontal=True, key="batch_source")

    records = []

    if source == "Upload JSON files":
        uploaded = st.file_uploader("Drop transcript JSON files", type="json", accept_multiple_files=True, key="batch_upload")
        for f in uploaded or []:
            try:
                data = json.load(f)
                f.seek(0)
                rec = parse_transcript_record(data, source_name=f.name)
                if rec:
                    records.append(rec)
            except Exception as e:
                st.warning(f"{f.name}: {e}")
    else:
        col_pat, col_btn = st.columns([3, 1])
        pattern = col_pat.text_input("Glob pattern", "transcripts/therapy_transcript_*.json", key="batch_glob")
        only_matrix = st.checkbox("Only matrix_run sessions", value=True, key="batch_matrix_flag")
        if col_btn.button("Scan", key="batch_scan"):
            found = 0
            for path in sorted(glib.glob(pattern), key=os.path.getmtime):
                try:
                    with open(path, encoding="utf-8") as fh:
                        data = json.load(fh)
                    if only_matrix:
                        em = data.get("experiment_metadata") or {}
                        if not em.get("matrix_run"):
                            continue
                    rec = parse_transcript_record(data, source_name=os.path.basename(path))
                    if rec:
                        records.append(rec)
                        found += 1
                except Exception:
                    pass
            st.session_state["batch_records"] = records
            st.caption(f"Found {found} valid sessions.")

    if source == "Scan transcripts/ folder" and "batch_records" in st.session_state:
        records = st.session_state["batch_records"]

    if not records:
        st.info("No sessions loaded yet. Scan a folder or upload files to begin.")
        st.stop()

    # --- Filters ---
    st.divider()
    all_couples = sorted({r["couple_id"] for r in records if r["couple_id"]})
    all_modes = sorted({r["therapist_mode"] for r in records if r["therapist_mode"]})
    all_models = sorted({r["therapist_model"] for r in records if r["therapist_model"]})
    all_structs = sorted({r["structure"] for r in records if r["structure"]})

    fc1, fc2, fc3, fc4 = st.columns(4)
    sel_couple = fc1.selectbox("Couple", all_couples, key="br_couple") if all_couples else ""
    sel_mode = fc2.selectbox("Therapist Mode", all_modes, key="br_mode") if all_modes else ""
    sel_model = fc3.selectbox("Model", all_models, key="br_model") if all_models else ""
    sel_struct = fc4.selectbox("Structure", all_structs, key="br_struct") if all_structs else ""

    filtered = [r for r in records
                if (not sel_couple or r["couple_id"] == sel_couple)
                and (not sel_mode or r["therapist_mode"] == sel_mode)
                and (not sel_model or r["therapist_model"] == sel_model)
                and (not sel_struct or r["structure"] == sel_struct)]

    st.caption(f"{len(filtered)} sessions matched filters.")
    if not filtered:
        st.stop()

    cells = {}
    for r in filtered:
        key = (r["bid_style_a"], r["bid_style_b"])
        c = cells.setdefault(key, {})
        pos = r["position"]
        for m in ["fas", "brd", "cas", "ta", "panas_a", "panas_b"]:
            c[f"{pos}_{m}"] = r["metrics"].get(m)
        c[f"{pos}_path"] = r["source_name"]

    data_bids = sorted({r["bid_style_a"] for r in filtered} | {r["bid_style_b"] for r in filtered},
                       key=lambda x: ALL_BID_STYLES.index(x) if x in ALL_BID_STYLES else 99)

    st.divider()
    st.subheader("Position Effect Grids")

    metrics_cfg = [
        ("fas", "FAS (Framing Adoption)", 0.5, False, +1),
        ("brd", "BRD (Bid Responsiveness)", 2.0, False, -1),
        ("cas", "CAS (Challenge Asymmetry)", 5.0, True, +1),
        ("ta", "TA (Therapeutic Alliance)", 3.0, False, 0),
        ("panas_a", "PANAS-A (Patient A Outcome)", 10.0, True, +1),
        ("panas_b", "PANAS-B (Patient B Outcome)", 10.0, True, -1),
    ]

    tab_labels = [c[1].split("(")[0].strip() for c in metrics_cfg]
    tabs = st.tabs(tab_labels)

    grid_modes = [("alpha", "Alpha (A speaks first)"),
                  ("beta",  "Beta (B speaks first)"),
                  ("delta", "Delta (&alpha; &minus; &beta;)")]

    for tab, (key, label, scale, is_int, fsa_sign) in zip(tabs, metrics_cfg):
        with tab:
            for mode_key, mode_label in grid_modes:
                st.markdown(f"**{mode_label}**", unsafe_allow_html=True)
                grid_html = render_metric_grid(
                    cells, key, label, scale, is_int,
                    bid_order=data_bids,
                    grid_mode=mode_key, fsa_sign=fsa_sign,
                )
                st.markdown(grid_html, unsafe_allow_html=True)

    st.divider()
    st.subheader("Summary Table")
    summary_rows = []
    for a_bs in data_bids:
        for b_bs in data_bids:
            cell = cells.get((a_bs, b_bs), {})
            row = {"A Bid": BID_LABELS.get(a_bs, a_bs), "B Bid": BID_LABELS.get(b_bs, b_bs)}
            for key, _, _, is_int, _ in metrics_cfg:
                a_v = cell.get(f"alpha_{key}")
                b_v = cell.get(f"beta_{key}")
                if a_v is not None and b_v is not None:
                    delta = a_v - b_v
                    row[f"{key.upper()} alpha"] = int(a_v) if is_int else round(a_v, 3)
                    row[f"{key.upper()} beta"] = int(b_v) if is_int else round(b_v, 3)
                    row[f"{key.upper()} delta"] = int(delta) if is_int else round(delta, 3)
            summary_rows.append(row)

    summary_df = pd.DataFrame(summary_rows)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    # --- Spread Statistics ---
    st.divider()
    st.subheader("Spread Statistics")
    st.caption("SD and |mean| measure how much the metric varies across sessions. Higher = more discriminative.")

    spread_rows = []
    for key, label, _, _, _ in metrics_cfg:
        vals = [r["metrics"].get(key) for r in filtered if r["metrics"].get(key) is not None]
        if not vals:
            continue
        abs_vals = [abs(v) for v in vals]
        spread_rows.append({
            "Metric": label.split("(")[0].strip(),
            "n": len(vals),
            "Mean": round(_st.mean(vals), 3),
            "SD": round(_st.pstdev(vals), 3),
            "Min": round(min(vals), 2),
            "Max": round(max(vals), 2),
            "|Mean|": round(_st.mean(abs_vals), 3),
            "|Max|": round(max(abs_vals), 2),
        })
    if spread_rows:
        st.dataframe(pd.DataFrame(spread_rows), use_container_width=True, hide_index=True)

    # --- Paired Delta Spread ---
    delta_vals = {key: [] for key, _, _, _, _ in metrics_cfg}
    for a_bs in data_bids:
        for b_bs in data_bids:
            cell = cells.get((a_bs, b_bs), {})
            for key, _, _, _, _ in metrics_cfg:
                a_v = cell.get(f"alpha_{key}")
                b_v = cell.get(f"beta_{key}")
                if a_v is not None and b_v is not None:
                    delta_vals[key].append(a_v - b_v)

    st.subheader("Paired Position Deltas (alpha minus beta)")
    delta_rows = []
    for key, label, _, _, _ in metrics_cfg:
        dv = delta_vals.get(key, [])
        if not dv:
            continue
        abs_dv = [abs(v) for v in dv]
        delta_rows.append({
            "Metric": label.split("(")[0].strip(),
            "Pairs": len(dv),
            "Mean delta": round(_st.mean(dv), 3),
            "Mean |delta|": round(_st.mean(abs_dv), 3),
            "Max |delta|": round(max(abs_dv), 2),
        })
    if delta_rows:
        st.dataframe(pd.DataFrame(delta_rows), use_container_width=True, hide_index=True)

    # --- Cross-mode comparison (if multiple modes present in unfiltered data) ---
    mode_levels = sorted({r["therapist_mode"] for r in records if r["therapist_mode"] and r["couple_id"] == sel_couple})
    if len(mode_levels) == 2 and sel_couple:
        st.divider()
        st.subheader(f"Spread Contrast: {mode_levels[0]} vs {mode_levels[1]}")
        st.caption("Compares |metric| means between the two therapist modes for the selected couple. Ratio > 1 means the second mode produces wider spread.")

        contrast_recs = [r for r in records if r["couple_id"] == sel_couple]
        contrast_rows = []
        for key, label, _, _, _ in metrics_cfg:
            by_mode = {m: [] for m in mode_levels}
            for r in contrast_recs:
                v = r["metrics"].get(key)
                if v is not None and r["therapist_mode"] in by_mode:
                    by_mode[r["therapist_mode"]].append(abs(v))
            m0 = _st.mean(by_mode[mode_levels[0]]) if by_mode[mode_levels[0]] else None
            m1 = _st.mean(by_mode[mode_levels[1]]) if by_mode[mode_levels[1]] else None
            if m0 is not None and m1 is not None:
                ratio = (m1 / m0) if m0 > 0 else float("inf")
                contrast_rows.append({
                    "Metric": label.split("(")[0].strip(),
                    f"|mean| {mode_levels[0]}": round(m0, 3),
                    f"|mean| {mode_levels[1]}": round(m1, 3),
                    "Ratio": round(ratio, 2),
                })
        if contrast_rows:
            st.dataframe(pd.DataFrame(contrast_rows), use_container_width=True, hide_index=True)

    # --- CSV export ---
    st.divider()
    export_rows = []
    for r in filtered:
        row = {k: v for k, v in r.items() if k != "metrics"}
        row.update(r["metrics"])
        export_rows.append(row)
    if export_rows:
        csv_data = pd.DataFrame(export_rows).to_csv(index=False)
        st.download_button("Download filtered data as CSV", csv_data, "batch_results.csv", "text/csv")
