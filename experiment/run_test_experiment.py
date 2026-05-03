"""
Test Experiment Batch Runner [HISTORICAL - pre-V2 persona pipeline]
====================================================================
Runs the 36-session Llama 8B + 70B validation experiment.

Design: 9 bid-style pairs x 2 models x 2 positions (alpha/beta) = 36 sessions.
All sessions use: Sequential structure, Individual Focus therapist mode,
temperature 0.3, 30 fixed turns.

DEPRECATION NOTE (2026-04-29): This runner uses `setup_session_parameters`,
which loads V1 legacy personas from `trigger-personas.json`. It was used to
generate the historical 36-session test batch (transcripts/test_cell*.json)
and is preserved here only for reproducing those specific results. For new
research runs, use `run_pilot_batch.py` or `run_pilot_batch_2.py`, which
both use the V2 persona pipeline (personas_v2.json + bid-style overlays).

Usage:
    python experiment/run_test_experiment.py
    python experiment/run_test_experiment.py --start-cell 4   # resume from cell 4
    python experiment/run_test_experiment.py --dry-run         # print plan only
"""

import sys
import os
import json
import time
import shutil
import traceback
from datetime import datetime
from pathlib import Path

# Add parent directory to path so we can import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_loader import load_all_assets
from session_setup import setup_session_parameters, initialize_session_state, log_session_start
from main import run_session_loop, run_panas_analysis
from output_manager import save_session_json, display_session_summary, export_transcript_text
from evaluate_therapist import evaluate_therapeutic_alliance
from evaluate_balance import (
    calculate_fas, calculate_brd, calculate_cas,
    calculate_nas, calculate_tsi,
)

# ============================================================================
# EXPERIMENT CONFIGURATION
# ============================================================================

EXPERIMENT_DIR = Path(__file__).parent
TRANSCRIPT_DIR = EXPERIMENT_DIR / "transcripts"
TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

TEMPERATURE = 0.3
TURN_LIMIT = 30
STRUCTURE = "Sequential"
THERAPIST_MODE = "individual_focus"

# Llama model identifiers (OpenRouter)
LLAMA_8B = "meta-llama/llama-3.1-8b-instruct"
LLAMA_70B = "meta-llama/llama-3.1-70b-instruct"

MODEL_LABELS = {
    LLAMA_8B: "llama8b",
    LLAMA_70B: "llama70b",
}

# 9 bid-style pairs with persona assignments and topics
# Topic names must match EXACTLY the keys in Final_therapy_discussion.json
CELL_DEFINITIONS = [
    {
        "cell": 1,
        "a_bid": "aggressive", "b_bid": "aggressive",
        "patient_a": "Monica Garcia", "patient_b": "Gregory Adams",
        "topic": "ANGER",
    },
    {
        "cell": 2,
        "a_bid": "aggressive", "b_bid": "assertive",
        "patient_a": "Victoria Hayes", "patient_b": "James Anderson",
        "topic": "COMMUNICATION",
    },
    {
        "cell": 3,
        "a_bid": "aggressive", "b_bid": "passive",
        "patient_a": "Ashley Turner", "patient_b": "Emma Johnson",
        "topic": "Separation and Divorce",
    },
    {
        "cell": 4,
        "a_bid": "assertive", "b_bid": "aggressive",
        "patient_a": "Marcus Thompson", "patient_b": "Kevin Murphy",
        "topic": "ANGER",
    },
    {
        "cell": 5,
        "a_bid": "assertive", "b_bid": "assertive",
        "patient_a": "Rachel Kim", "patient_b": "Carlos Martinez",
        "topic": "COMMUNICATION",
    },
    {
        "cell": 6,
        "a_bid": "assertive", "b_bid": "passive",
        "patient_a": "Diana Rodriguez", "patient_b": "Tyler Brooks",
        "topic": "EATING DISORDERS",
    },
    {
        "cell": 7,
        "a_bid": "passive", "b_bid": "aggressive",
        "patient_a": "Sophie Chen", "patient_b": "Brandon Collins",
        "topic": "Sexual Abuse",
    },
    {
        "cell": 8,
        "a_bid": "passive", "b_bid": "assertive",
        "patient_a": "Daniel Wright", "patient_b": "Carlos Martinez",
        "topic": "Separation and Divorce",
        # NOTE: Carlos Martinez is also in Cell 5 (all assertive personas exhausted)
    },
    {
        "cell": 9,
        "a_bid": "passive", "b_bid": "passive",
        "patient_a": "Jessica Park", "patient_b": "Nathan Pierce",
        "topic": "ANGER",
    },
]


def build_session_filename(cell_num, model_label, position):
    """Generate standardized filename for experiment transcripts."""
    return f"test_cell{cell_num:02d}_{model_label}_{position}.json"


def save_experiment_transcript(output_json, filepath):
    """Save session data to a specific filepath in the experiment directory."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_json, f, indent=2, ensure_ascii=False)
        print(f"  >> Saved: {filepath.name}")
        return filepath
    except Exception as e:
        print(f"  >> ERROR saving transcript: {e}")
        return None


def run_single_session(assets, cell_def, model, position, description):
    """
    Run one therapy session with the specified parameters.

    Args:
        assets: Loaded assets from load_all_assets()
        cell_def: Cell definition dict from CELL_DEFINITIONS
        model: Therapist model string (e.g., LLAMA_8B)
        position: "alpha" (A speaks first) or "beta" (B speaks first)
        description: Human-readable description for logging

    Returns:
        tuple: (output_json, filepath) or (None, None) on failure
    """
    print(f"\n{'='*70}")
    print(f"  {description}")
    print(f"{'='*70}")

    cell_num = cell_def["cell"]
    patient_a = cell_def["patient_a"]
    patient_b = cell_def["patient_b"]
    topic_name = cell_def["topic"]
    model_label = MODEL_LABELS[model]

    # Map position to first_speaker
    # alpha = A speaks first, beta = B speaks first
    first_speaker = "Patient A" if position == "alpha" else "Patient B"

    print(f"  Cell {cell_num}: {patient_a} ({cell_def['a_bid']}) vs {patient_b} ({cell_def['b_bid']})")
    print(f"  Topic: {topic_name}")
    print(f"  Model: {model_label}")
    print(f"  Position: {position} (first speaker: {first_speaker})")
    print(f"  Temperature: {TEMPERATURE}, Turns: {TURN_LIMIT}, Mode: {THERAPIST_MODE}")

    # Validate topic exists
    if topic_name not in assets["therapy_plans"]:
        print(f"  ERROR: Topic '{topic_name}' not found in therapy plans!")
        available = list(assets["therapy_plans"].keys())
        print(f"  Available topics: {available}")
        return None, None

    # Setup session parameters
    header, details, participants, discussion_notes = setup_session_parameters(
        assets["therapy_plans"][topic_name],
        assets["personas"],
        STRUCTURE,
        patient_a_name=patient_a,
        patient_b_name=patient_b,
    )

    # Initialize output JSON
    output_json = initialize_session_state(
        header, details, participants, discussion_notes,
        STRUCTURE, first_speaker,
    )

    # Add experiment metadata
    output_json["experiment_metadata"] = {
        "experiment": "test_llama_validation",
        "cell": cell_num,
        "a_bid_style": cell_def["a_bid"],
        "b_bid_style": cell_def["b_bid"],
        "therapist_model": model,
        "therapist_model_label": model_label,
        "position": position,
        "first_speaker": first_speaker,
        "temperature": TEMPERATURE,
        "turn_limit": TURN_LIMIT,
        "therapist_mode": THERAPIST_MODE,
        "structure": STRUCTURE,
        "timestamp": datetime.now().isoformat(),
    }

    log_session_start(header, STRUCTURE, first_speaker)

    # Run simulation loop
    output_json, conversation_history = run_session_loop(
        output_json,
        participants,
        discussion_notes,
        STRUCTURE,
        first_speaker,
        TEMPERATURE,
        prompts=assets["prompts"],
        baseline_panas=assets["baseline_panas"],
        max_turns_override=TURN_LIMIT,
        therapist_mode=THERAPIST_MODE,
        therapist_model=model,
    )

    # Post-session PANAS analysis
    output_json, panas_summaries = run_panas_analysis(
        output_json,
        assets["baseline_panas"],
        conversation_history,
    )

    # Therapeutic Alliance evaluation
    alliance_scores = evaluate_therapeutic_alliance(
        output_json.get("session_transcript", [])
    )
    output_json["therapist_alliance"] = alliance_scores

    # Therapeutic Balance (FAS, BRD, CAS)
    p_details = output_json.get("participant_details", {})
    p_a_name = p_details.get("patient_A", {}).get("name", "Patient A")
    p_b_name = p_details.get("patient_B", {}).get("name", "Patient B")
    t_name = p_details.get("therapist", {}).get("name", "Therapist")
    transcript = output_json.get("session_transcript", [])

    fas_result = calculate_fas(transcript, p_a_name, p_b_name, t_name)
    brd_result = calculate_brd(transcript, p_a_name, p_b_name, t_name)
    cas_result = calculate_cas(transcript, p_a_name, p_b_name, t_name)
    nas_result = calculate_nas(transcript, p_a_name, p_b_name, t_name)
    tsi_result = calculate_tsi(transcript, p_a_name, p_b_name, t_name)
    output_json["therapeutic_balance"] = {
        "fas": fas_result,
        "brd": brd_result,
        "cas": cas_result,
        "nas": nas_result,
        "tsi": tsi_result,
    }

    # Save to experiment directory
    filename = build_session_filename(cell_num, model_label, position)
    filepath = TRANSCRIPT_DIR / filename
    save_experiment_transcript(output_json, filepath)

    # Also save to default transcripts/ dir for compatibility
    save_session_json(output_json)

    # Display summary
    display_session_summary(output_json, panas_summaries)

    return output_json, filepath


def print_experiment_plan(start_cell=1):
    """Print the full experiment plan without running anything."""
    print("\n" + "=" * 70)
    print("  TEST EXPERIMENT PLAN (DRY RUN)")
    print("=" * 70)

    session_num = 0
    for cell_def in CELL_DEFINITIONS:
        if cell_def["cell"] < start_cell:
            continue
        for model, model_label in MODEL_LABELS.items():
            for position in ["alpha", "beta"]:
                session_num += 1
                first_speaker = "A first" if position == "alpha" else "B first"
                filename = build_session_filename(cell_def["cell"], model_label, position)
                print(
                    f"  {session_num:2d}. Cell {cell_def['cell']} | "
                    f"{model_label:8s} | {position:5s} ({first_speaker}) | "
                    f"{cell_def['patient_a']} vs {cell_def['patient_b']} | "
                    f"{cell_def['topic']} -> {filename}"
                )

    print(f"\n  Total sessions: {session_num}")
    print("=" * 70)


def main():
    """Run the full 36-session test experiment."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Llama 8B/70B test experiment")
    parser.add_argument("--start-cell", type=int, default=1,
                        help="Resume from this cell number (1-9)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print experiment plan without running")
    parser.add_argument("--cell", type=int, default=None,
                        help="Run only this cell number")
    parser.add_argument("--model", type=str, default=None,
                        choices=["8b", "70b"],
                        help="Run only this model size")
    parser.add_argument("--position", type=str, default=None,
                        choices=["alpha", "beta"],
                        help="Run only this position")
    args = parser.parse_args()

    if args.dry_run:
        print_experiment_plan(args.start_cell)
        return

    print("\n" + "=" * 70)
    print("  LLAMA 8B + 70B TEST EXPERIMENT")
    print("  36 Sessions: 9 bid pairs x 2 models x 2 positions")
    print("=" * 70)
    print(f"  Structure:    {STRUCTURE}")
    print(f"  Therapist:    Individual Focus")
    print(f"  Temperature:  {TEMPERATURE}")
    print(f"  Turns:        {TURN_LIMIT} (fixed)")
    print(f"  Output:       {TRANSCRIPT_DIR}")
    print(f"  Start cell:   {args.start_cell}")
    if args.cell:
        print(f"  Single cell:  {args.cell}")
    if args.model:
        print(f"  Single model: {args.model}")
    if args.position:
        print(f"  Single position: {args.position}")
    print()

    # Filter models if specified
    models_to_run = list(MODEL_LABELS.items())
    if args.model == "8b":
        models_to_run = [(LLAMA_8B, "llama8b")]
    elif args.model == "70b":
        models_to_run = [(LLAMA_70B, "llama70b")]

    # Filter positions if specified
    positions_to_run = ["alpha", "beta"]
    if args.position:
        positions_to_run = [args.position]

    # Build session list
    sessions = []
    for cell_def in CELL_DEFINITIONS:
        if args.cell and cell_def["cell"] != args.cell:
            continue
        if cell_def["cell"] < args.start_cell:
            continue
        for model, model_label in models_to_run:
            for position in positions_to_run:
                sessions.append((cell_def, model, model_label, position))

    total_sessions = len(sessions)
    print(f"  Sessions to run: {total_sessions}")
    print(f"  Starting in 5 seconds... (Ctrl+C to abort)")
    time.sleep(5)

    # Load assets once
    print("\n  Loading assets...")
    assets = load_all_assets()

    # Validate all topics exist before running
    missing_topics = []
    for cell_def in CELL_DEFINITIONS:
        if cell_def["topic"] not in assets["therapy_plans"]:
            missing_topics.append(f"Cell {cell_def['cell']}: '{cell_def['topic']}'")
    if missing_topics:
        print("\n  FATAL: Missing topics in therapy plans:")
        for mt in missing_topics:
            print(f"    - {mt}")
        print("  Aborting. Fix topic names in CELL_DEFINITIONS.")
        sys.exit(1)

    # Validate all personas exist
    missing_personas = []
    for cell_def in CELL_DEFINITIONS:
        if cell_def["patient_a"] not in assets["personas"]:
            missing_personas.append(f"Cell {cell_def['cell']} A: '{cell_def['patient_a']}'")
        if cell_def["patient_b"] not in assets["personas"]:
            missing_personas.append(f"Cell {cell_def['cell']} B: '{cell_def['patient_b']}'")
    if missing_personas:
        print("\n  FATAL: Missing personas:")
        for mp in missing_personas:
            print(f"    - {mp}")
        print("  Aborting. Fix persona names in CELL_DEFINITIONS.")
        sys.exit(1)

    print("  All topics and personas validated.\n")

    # Run experiments
    results = []
    start_time = datetime.now()

    for i, (cell_def, model, model_label, position) in enumerate(sessions, 1):
        session_start = datetime.now()
        description = (
            f"SESSION {i}/{total_sessions} | "
            f"Cell {cell_def['cell']} ({cell_def['a_bid']}+{cell_def['b_bid']}) | "
            f"{model_label} | {position}"
        )

        # Check if transcript already exists (skip if resuming)
        filename = build_session_filename(cell_def["cell"], model_label, position)
        filepath = TRANSCRIPT_DIR / filename
        if filepath.exists():
            print(f"\n  SKIP: {filename} already exists (resuming)")
            results.append({
                "session": i,
                "cell": cell_def["cell"],
                "model": model_label,
                "position": position,
                "status": "SKIPPED",
                "file": filename,
                "duration": "0s",
                "error": None,
            })
            continue

        try:
            output_json, saved_path = run_single_session(
                assets, cell_def, model, position, description
            )

            session_duration = (datetime.now() - session_start).total_seconds()

            if output_json and saved_path:
                # Extract key metrics for summary
                balance = output_json.get("therapeutic_balance", {})
                fas = balance.get("fas", {}).get("fas_score", "N/A")
                brd = balance.get("brd", {}).get("brd_score", "N/A")
                cas = balance.get("cas", {}).get("cas_score", "N/A")

                results.append({
                    "session": i,
                    "cell": cell_def["cell"],
                    "model": model_label,
                    "position": position,
                    "status": "SUCCESS",
                    "file": filename,
                    "duration": f"{session_duration:.0f}s",
                    "fas": fas,
                    "brd": brd,
                    "cas": cas,
                    "error": None,
                })
                print(f"\n  >> Session {i}/{total_sessions} complete ({session_duration:.0f}s)")
                print(f"     FAS={fas}, BRD={brd}, CAS={cas}")
            else:
                results.append({
                    "session": i,
                    "cell": cell_def["cell"],
                    "model": model_label,
                    "position": position,
                    "status": "FAILED",
                    "file": filename,
                    "duration": f"{session_duration:.0f}s",
                    "error": "No output returned",
                })

        except KeyboardInterrupt:
            print("\n\n  INTERRUPTED by user. Saving progress log...")
            break

        except Exception as e:
            session_duration = (datetime.now() - session_start).total_seconds()
            print(f"\n  ERROR in session {i}: {e}")
            traceback.print_exc()
            results.append({
                "session": i,
                "cell": cell_def["cell"],
                "model": model_label,
                "position": position,
                "status": "ERROR",
                "file": filename,
                "duration": f"{session_duration:.0f}s",
                "error": str(e),
            })
            # Continue to next session; do not halt
            continue

        # Brief pause between sessions to avoid rate limits
        if i < total_sessions:
            print(f"  Pausing 3s before next session...")
            time.sleep(3)

    # ========================================================================
    # EXPERIMENT SUMMARY
    # ========================================================================
    total_duration = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 70)
    print("  EXPERIMENT RESULTS SUMMARY")
    print("=" * 70)

    success_count = sum(1 for r in results if r["status"] == "SUCCESS")
    failed_count = sum(1 for r in results if r["status"] in ("FAILED", "ERROR"))
    skipped_count = sum(1 for r in results if r["status"] == "SKIPPED")

    print(f"  Total: {len(results)}/{total_sessions}")
    print(f"  Success: {success_count}")
    print(f"  Failed:  {failed_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Duration: {total_duration/60:.1f} minutes")

    print(f"\n  {'#':>3} {'Cell':>4} {'Model':>8} {'Pos':>5} {'Status':>8} {'Time':>6} {'FAS':>8} {'BRD':>8} {'CAS':>5}  File")
    print(f"  {'-'*3} {'-'*4} {'-'*8} {'-'*5} {'-'*8} {'-'*6} {'-'*8} {'-'*8} {'-'*5}  {'-'*30}")

    for r in results:
        fas_str = f"{r.get('fas', ''):>8}" if r.get("fas") is not None else "     N/A"
        brd_str = f"{r.get('brd', ''):>8}" if r.get("brd") is not None else "     N/A"
        cas_str = f"{r.get('cas', ''):>5}" if r.get("cas") is not None else "  N/A"
        print(
            f"  {r['session']:3d} {r['cell']:4d} {r['model']:>8} {r['position']:>5} "
            f"{r['status']:>8} {r['duration']:>6} {fas_str} {brd_str} {cas_str}  {r['file']}"
        )

    if failed_count > 0:
        print(f"\n  ERRORS:")
        for r in results:
            if r["status"] in ("FAILED", "ERROR"):
                print(f"    Cell {r['cell']} {r['model']} {r['position']}: {r['error']}")

    # Save results log
    log_path = EXPERIMENT_DIR / f"experiment_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "experiment": "test_llama_validation",
            "start_time": start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_duration_seconds": total_duration,
            "total_sessions": total_sessions,
            "success": success_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "results": results,
        }, f, indent=2)
    print(f"\n  Experiment log saved: {log_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
