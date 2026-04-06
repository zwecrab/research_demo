# run_bias_experiment.py
# Automates two simulation runs with swapped speaker order
# Run 1: Patient A (Nathan Pierce) speaks first
# Run 2: Patient B (Victoria Hayes) speaks first
# All other parameters held constant

import sys
import os

# Set encoding to prevent emoji crashes on Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add parent directory to path so imports resolve correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_loader import load_all_assets
from session_setup import setup_session_parameters, initialize_session_state, log_session_start
from main import run_session_loop, run_panas_analysis
from output_manager import save_session_json, display_session_summary, display_session_details

# ============================================================================
# CONFIGURATION — matches transcripts T17-T20
# ============================================================================
TOPIC_NAME = "Blended Family Problems"
TEMPERATURE = 0.7
CONVERSATION_STRUCTURE = "LLM with Triggers"
SELECTED_TRIGGER = "Semantic Analysis"
PATIENT_A_NAME = "Nathan Pierce"
PATIENT_B_NAME = "Victoria Hayes"

RUNS = [
    {"label": "Run 1", "first_speaker": "Patient A", "desc": "Nathan (A) speaks first"},
    {"label": "Run 2", "first_speaker": "Patient B", "desc": "Victoria (B) speaks first"},
]

def main():
    print("=" * 70)
    print("BIAS EXPERIMENT — Two runs with swapped speaker order")
    print("=" * 70)
    
    # Load assets once
    assets = load_all_assets()
    
    # Find the topic data
    topic_data = assets["therapy_plans"].get(TOPIC_NAME)
    if not topic_data:
        print(f"ERROR: Topic '{TOPIC_NAME}' not found!")
        print(f"Available: {list(assets['therapy_plans'].keys())}")
        sys.exit(1)
    
    for run_info in RUNS:
        first_speaker = run_info["first_speaker"]
        
        print()
        print("#" * 70)
        print(f"#  {run_info['label']}: {run_info['desc']}")
        print(f"#  First speaker = {first_speaker}")
        print("#" * 70)
        
        # Setup session
        header, details, participants, discussion_notes = setup_session_parameters(
            topic_data,
            assets["personas"],
            SELECTED_TRIGGER,
            CONVERSATION_STRUCTURE,
            patient_a_name=PATIENT_A_NAME,
            patient_b_name=PATIENT_B_NAME
        )
        
        output_json = initialize_session_state(
            header, details, participants, discussion_notes,
            CONVERSATION_STRUCTURE, first_speaker
        )
        
        log_session_start(header, CONVERSATION_STRUCTURE, first_speaker)
        
        # Run simulation
        output_json, conversation_history = run_session_loop(
            output_json,
            participants,
            discussion_notes,
            CONVERSATION_STRUCTURE,
            first_speaker,
            TEMPERATURE,
            assets["prompts"],
            assets["baseline_panas"]
        )
        
        # PANAS analysis
        output_json, panas_summaries = run_panas_analysis(
            output_json,
            assets["baseline_panas"],
            conversation_history
        )
        
        # Save
        saved_file = save_session_json(output_json)
        display_session_summary(output_json, panas_summaries)
        
        print(f"\n{'=' * 70}")
        print(f"  {run_info['label']} COMPLETE — saved to {saved_file}")
        print(f"{'=' * 70}")
    
    print("\n\nBOTH RUNS COMPLETE!")
    print("Check the transcripts directory for the two new files.")

if __name__ == "__main__":
    main()
