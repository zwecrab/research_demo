"""
Batch Experiment Runner
=======================
Runs multiple experiments non-interactively with specified parameters.
Replicates T21/T22 parameters but with different conversation structures.

Usage:
    python batch_experiment.py
"""

import sys
import time
from datetime import datetime
import traceback

from data_loader import load_all_assets
from session_setup import setup_session_parameters, initialize_session_state, log_session_start
from main import run_session_loop, run_panas_analysis
from output_manager import save_session_json, display_session_summary, export_transcript_text

# ============================================================================
# EXPERIMENT CONFIGURATION
# ============================================================================

# Replicate T21/T22 parameters
TOPIC_NAME = "Blended Family Problems"
PATIENT_A = "Nathan Pierce"
PATIENT_B = "Victoria Hayes"
TEMPERATURE = 0.7  # Default balanced temperature

# Experiments to run:
# Each tuple: (structure, first_speaker, description)
EXPERIMENTS = [
    # T27: Sequential (Nathan first)
    ("Sequential", "Patient A", "T27: Sequential - Nathan first"),
    # T28: Sequential (Victoria first)
    ("Sequential", "Patient B", "T28: Sequential - Victoria first"),
]


def run_single_experiment(assets, structure, first_speaker, description,
                          patient_a_name, patient_b_name, topic_name, turn_limit=None, temperature=0.7,
                          turn_callback=None, enable_goals=True, enable_progress=False, therapist_mode='standard',
                          therapist_model=None):
    """Run a single experiment with the given parameters."""
    
    print("\n" + "=" * 70)
    print(f"  {description}")
    print("=" * 70)
    
    # Setup session parameters
    # Note: topic_name key must exist in assets["therapy_plans"]
    if topic_name not in assets["therapy_plans"]:
        raise ValueError(f"Topic '{topic_name}' not found in therapy plans.")

    header, details, participants, discussion_notes = setup_session_parameters(
        assets["therapy_plans"][topic_name],
        assets["personas"],
        structure,
        patient_a_name=patient_a_name,
        patient_b_name=patient_b_name
    )
    
    if not enable_goals:
        details["long_term_goals"] = []
        details["short_term_objectives"] = []
        discussion_notes["goals"] = []
        discussion_notes["objectives"] = []
    
    # Initialize output JSON
    output_json = initialize_session_state(
        header, details, participants, discussion_notes,
        structure, first_speaker
    )
    
    log_session_start(header, structure, first_speaker)
    
    # Run simulation
    output_json, conversation_history = run_session_loop(
        output_json,
        participants,
        discussion_notes,
        structure,
        first_speaker,
        temperature,
        prompts=assets["prompts"],
        baseline_panas=assets["baseline_panas"],
        max_turns_override=turn_limit,
        turn_callback=turn_callback,
        enable_progress=enable_progress,
        therapist_mode=therapist_mode,
        therapist_model=therapist_model
    )
    
    # Post-session PANAS analysis
    output_json, panas_summaries = run_panas_analysis(
        output_json,
        assets["baseline_panas"],
        conversation_history
    )
    
    # Evaluate Therapist
    from evaluate_therapist import evaluate_therapeutic_alliance
    alliance_scores = evaluate_therapeutic_alliance(output_json.get('session_transcript', []))
    output_json['therapist_alliance'] = alliance_scores

    # Evaluate Therapeutic Balance (FAS, BRD, CAS)
    from evaluate_balance import calculate_fas, calculate_brd, calculate_cas
    p_details = output_json.get('participant_details', {})
    p_a_name = p_details.get('patient_A', {}).get('name', 'Patient A')
    p_b_name = p_details.get('patient_B', {}).get('name', 'Patient B')
    t_name = p_details.get('therapist', {}).get('name', 'Therapist')
    transcript = output_json.get('session_transcript', [])
    fas_result = calculate_fas(transcript, p_a_name, p_b_name, t_name)
    brd_result = calculate_brd(transcript, p_a_name, p_b_name, t_name)
    cas_result = calculate_cas(transcript, p_a_name, p_b_name, t_name)
    output_json['therapeutic_balance'] = {
        'fas': fas_result,
        'brd': brd_result,
        'cas': cas_result
    }

    # Save transcript
    saved_file = save_session_json(output_json)
    display_session_summary(output_json, panas_summaries)
    export_transcript_text(output_json)
    
    print(f"\n✅ Experiment complete: {saved_file}")
    return saved_file


def main():
    """Run all experiments in batch."""
    
    print("\n" + "=" * 70)
    print("🧪 BATCH EXPERIMENT RUNNER")
    print("=" * 70)
    print(f"\nTopic:      {TOPIC_NAME}")
    print(f"Patient A:  {PATIENT_A}")
    print(f"Patient B:  {PATIENT_B}")
    print(f"Temperature: {TEMPERATURE}")
    print(f"Experiments: {len(EXPERIMENTS)}")
    print()
    
    for i, (structure, speaker, trigger, desc) in enumerate(EXPERIMENTS, 1):
        print(f"  {i}. {desc}")
    
    print(f"\nStarting in 3 seconds...")
    time.sleep(3)
    
    # Load assets once
    assets = load_all_assets()
    
    # Run each experiment
    results = []
    for i, (structure, first_speaker, description) in enumerate(EXPERIMENTS, 1):
        try:
            full_desc = f"EXPERIMENT {i}: {description}"
            saved_file = run_single_experiment(
                assets, structure, first_speaker, full_desc,
                PATIENT_A, PATIENT_B, TOPIC_NAME, turn_limit=None
            )
            results.append((description, saved_file, "SUCCESS"))
        except Exception as e:
            print(f"\n❌ Experiment {i} FAILED: {e}")
            traceback.print_exc()
            results.append((description, "FAILED", str(e)))
    
    # Print summary
    print("\n" + "=" * 70)
    print("🧪 BATCH EXPERIMENT RESULTS")
    print("=" * 70)
    for desc, filepath, status in results:
        print(f"  {status:10s}  {desc}")
        if filepath:
            print(f"             → {filepath}")
    
    print(f"\nAll {len(EXPERIMENTS)} experiments complete.")
    print("Run evaluate_bias.py with --t1 and --t2 to compare swapped pairs.")


if __name__ == "__main__":
    main()
